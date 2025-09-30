"""
Canvas token service with envelope encryption
Handles secure storage and retrieval of Canvas API tokens
"""
import logging
import secrets
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config.database.supabase import get_supabase_client
from app.security.encryption import get_encryption_service
from app.database.models import CanvasIntegrationModel, IntegrationStatus

logger = logging.getLogger(__name__)


class CanvasTokenService:
    """Service for securely storing and managing Canvas API tokens"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.encryption_service = get_encryption_service()

    async def store_canvas_token(
        self,
        user_id: str,
        canvas_url: str,
        api_token: str
    ) -> Dict[str, Any]:
        """
        Store Canvas API token with envelope encryption

        Args:
            user_id: User ID
            canvas_url: Canvas base URL
            api_token: Canvas API token to encrypt and store

        Returns:
            Dict with storage result
        """
        try:
            # Generate user-specific encryption key
            user_key = await self._generate_user_key(user_id)

            # Encrypt the token using envelope encryption
            encrypted_token = await self._encrypt_token(api_token, user_key)

            # Store KMS key ID for the user key
            kms_key_id = await self._store_user_key(user_id, user_key)

            # Create integration record
            integration = CanvasIntegrationModel(
                user_id=user_id,
                base_url=canvas_url.rstrip('/'),
                token_ciphertext=encrypted_token,
                kms_key_id=kms_key_id,
                status=IntegrationStatus.OK,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Store in database
            result = self.supabase.table("integration_canvas").upsert(
                integration.to_supabase_insert(),
                on_conflict="user_id"
            ).execute()

            logger.info(f"Canvas token stored successfully for user {user_id}")

            return {
                "success": True,
                "user_id": user_id,
                "canvas_url": canvas_url,
                "status": "stored",
                "stored_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to store Canvas token for user {user_id}: {e}")
            raise

    async def retrieve_canvas_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt Canvas API token for user

        Args:
            user_id: User ID

        Returns:
            Dict with token and metadata, or None if not found
        """
        try:
            # Get integration record
            response = self.supabase.table("integration_canvas").select("*").eq(
                "user_id", user_id
            ).single().execute()

            if not response.data:
                return None

            integration_data = response.data

            # Check integration status
            if integration_data.get("status") == IntegrationStatus.NEEDS_REAUTH:
                logger.warning(f"Canvas integration needs reauth for user {user_id}")
                return None

            # Retrieve user key
            user_key = await self._retrieve_user_key(
                user_id,
                integration_data["kms_key_id"]
            )

            if not user_key:
                logger.error(f"Could not retrieve user key for {user_id}")
                await self._mark_integration_error(user_id, "key_retrieval_failed")
                return None

            # Decrypt token
            decrypted_token = await self._decrypt_token(
                integration_data["token_ciphertext"],
                user_key
            )

            return {
                "api_token": decrypted_token,
                "base_url": integration_data["base_url"],
                "status": integration_data["status"],
                "last_sync": integration_data.get("last_full_sync_at"),
                "user_id": user_id
            }

        except Exception as e:
            logger.error(f"Failed to retrieve Canvas token for user {user_id}: {e}")
            await self._mark_integration_error(user_id, "token_retrieval_failed")
            return None

    async def mark_needs_reauth(self, user_id: str, error_code: str = "401_unauthorized"):
        """Mark Canvas integration as needing reauthorization"""
        try:
            self.supabase.table("integration_canvas").update({
                "status": IntegrationStatus.NEEDS_REAUTH,
                "last_error_code": error_code,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()

            logger.info(f"Canvas integration marked needs reauth for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to mark needs reauth for user {user_id}: {e}")

    async def validate_token_direct(self, canvas_url: str, api_token: str) -> bool:
        """
        Validate Canvas token directly without storing it

        Args:
            canvas_url: Canvas base URL
            api_token: Canvas API token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            import httpx

            headers = {"Authorization": f"Bearer {api_token}"}
            url = f"{canvas_url}/api/v1/users/self"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Direct token validation failed: {e}")
            return False

    async def validate_token(self, user_id: str) -> bool:
        """
        Validate Canvas token by making a test API call

        Args:
            user_id: User ID

        Returns:
            True if token is valid, False otherwise
        """
        try:
            token_data = await self.retrieve_canvas_token(user_id)
            if not token_data:
                return False

            # Test API call to /api/v1/users/self
            import httpx

            headers = {"Authorization": f"Bearer {token_data['api_token']}"}
            url = f"{token_data['base_url']}/api/v1/users/self"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)

                if response.status_code == 401:
                    await self.mark_needs_reauth(user_id, "401_unauthorized")
                    return False
                elif response.status_code == 200:
                    # Token is valid, ensure status is OK
                    await self._mark_integration_ok(user_id)
                    return True
                else:
                    logger.warning(f"Unexpected response {response.status_code} for user {user_id}")
                    return False

        except Exception as e:
            logger.error(f"Token validation failed for user {user_id}: {e}")
            return False

    async def delete_canvas_integration(self, user_id: str) -> bool:
        """Delete Canvas integration and all associated data"""
        try:
            # Delete integration record (this cascades to other tables via foreign keys)
            self.supabase.table("integration_canvas").delete().eq("user_id", user_id).execute()

            # Delete user key from KMS
            await self._delete_user_key(user_id)

            # Delete external cursors
            self.supabase.table("external_cursor").delete().eq(
                "user_id", user_id
            ).eq("source", "canvas").execute()

            # Clear Canvas-sourced tasks
            self.supabase.table("tasks").delete().eq(
                "user_id", user_id
            ).eq("external_source", "canvas").execute()

            logger.info(f"Canvas integration deleted for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete Canvas integration for user {user_id}: {e}")
            return False

    async def _generate_user_key(self, user_id: str) -> bytes:
        """Generate a unique encryption key for the user"""
        # Create deterministic but secure key based on user ID and system secret
        system_secret = self.encryption_service.get_master_key()

        # Use PBKDF2 to derive user-specific key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_id.encode(),
            iterations=100000,
        )

        return kdf.derive(system_secret)

    async def _encrypt_token(self, token: str, key: bytes) -> str:
        """Encrypt token using Fernet symmetric encryption"""
        f = Fernet(base64.urlsafe_b64encode(key))
        encrypted_token = f.encrypt(token.encode())
        return base64.b64encode(encrypted_token).decode()

    async def _decrypt_token(self, encrypted_token: str, key: bytes) -> str:
        """Decrypt token using Fernet symmetric encryption"""
        f = Fernet(base64.urlsafe_b64encode(key))
        token_bytes = base64.b64decode(encrypted_token.encode())
        decrypted_token = f.decrypt(token_bytes)
        return decrypted_token.decode()

    async def _store_user_key(self, user_id: str, user_key: bytes) -> str:
        """Store user key using KMS (simplified implementation)"""
        # In production, this would use AWS KMS, Azure Key Vault, etc.
        # For now, we'll use a simple key ID
        key_id = f"canvas_key_{user_id}_{secrets.token_hex(8)}"

        # In a real implementation, you'd store this in your KMS
        # Here we'll just return the key ID
        return key_id

    async def _retrieve_user_key(self, user_id: str, kms_key_id: str) -> Optional[bytes]:
        """Retrieve user key from KMS"""
        # In production, this would retrieve from KMS
        # For now, regenerate the deterministic key
        return await self._generate_user_key(user_id)

    async def _delete_user_key(self, user_id: str):
        """Delete user key from KMS"""
        # In production, this would delete from KMS
        # For now, this is a no-op since we use deterministic keys
        pass

    async def _mark_integration_error(self, user_id: str, error_code: str):
        """Mark integration as having an error"""
        try:
            self.supabase.table("integration_canvas").update({
                "status": IntegrationStatus.ERROR,
                "last_error_code": error_code,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"Failed to mark integration error for user {user_id}: {e}")

    async def _mark_integration_ok(self, user_id: str):
        """Mark integration as OK"""
        try:
            self.supabase.table("integration_canvas").update({
                "status": IntegrationStatus.OK,
                "last_error_code": None,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"Failed to mark integration OK for user {user_id}: {e}")


# Global service instance
_canvas_token_service: Optional[CanvasTokenService] = None

def get_canvas_token_service() -> CanvasTokenService:
    """Get global Canvas token service instance"""
    global _canvas_token_service
    if _canvas_token_service is None:
        _canvas_token_service = CanvasTokenService()
    return _canvas_token_service