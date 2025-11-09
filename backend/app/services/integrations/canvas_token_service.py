"""
Canvas token service with envelope encryption
Handles secure storage and retrieval of Canvas API tokens in oauth_tokens table
Supports both local AES-256-GCM and AWS KMS encryption
"""
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.database.repositories.integration_repositories import (
    OAuthTokenRepository,
    get_oauth_token_repository
)
from app.database.repositories.task_repositories import (
    TaskRepository,
    get_task_repository
)
from app.security.encryption import get_encryption_service
from app.database.models import IntegrationStatus
from app.config.core.settings import settings

logger = logging.getLogger(__name__)


class CanvasTokenService:
    """
    Service for securely storing and managing Canvas API tokens

    Supports two encryption modes:
    1. Local AES-256-GCM (default): User-specific key derivation from master key
    2. AWS KMS (when USE_KMS=true): Envelope encryption with KMS-managed keys
    """

    def __init__(
        self,
        oauth_token_repository: Optional[OAuthTokenRepository] = None,
        task_repository: Optional[TaskRepository] = None
    ):
        self._oauth_token_repository = oauth_token_repository
        self._task_repository = task_repository
        self.encryption_service = get_encryption_service()
        self.use_kms = getattr(settings, 'USE_KMS', False)
    
    @property
    def oauth_token_repository(self) -> OAuthTokenRepository:
        """Lazy-load OAuth token repository"""
        if self._oauth_token_repository is None:
            self._oauth_token_repository = get_oauth_token_repository()
        return self._oauth_token_repository
    
    @property
    def task_repository(self) -> TaskRepository:
        """Lazy-load task repository"""
        if self._task_repository is None:
            self._task_repository = get_task_repository()
        return self._task_repository

    async def store_canvas_token(
        self,
        user_id: str,
        canvas_url: str,
        api_token: str
    ) -> Dict[str, Any]:
        """
        Store Canvas API token with encryption in oauth_tokens table

        Encryption method depends on USE_KMS setting:
        - If USE_KMS=false: Uses local AES-256-GCM with user-derived key
        - If USE_KMS=true: Uses AWS KMS envelope encryption

        Args:
            user_id: User ID
            canvas_url: Canvas base URL
            api_token: Canvas API token to encrypt and store

        Returns:
            Dict with storage result
        """
        try:
            # Encrypt the token using the encryption service (KMS or local)
            encrypted_token = self.encryption_service.encrypt_token(api_token, user_id)

            # Generate encryption metadata for tracking
            encryption_method = "kms" if self.use_kms else f"aes256-gcm-v{self.encryption_service.key_version}"
            kms_key_id = None

            if self.use_kms:
                # For KMS, generate a tracking ID
                kms_key_id = f"canvas_kms_{user_id}_{secrets.token_hex(8)}"

            # Store in oauth_tokens table using repository
            # Canvas tokens expire 120 days from creation
            expires_at = datetime.utcnow() + timedelta(days=120)

            token_data = {
                "user_id": user_id,
                "provider": "canvas",
                "service_type": "canvas",  # Add service_type to match constraint
                "access_token": encrypted_token,
                "refresh_token": encrypted_token,  # Store same encrypted token
                "expires_at": expires_at.isoformat(),  # Canvas tokens expire in 120 days
                "scopes": [],  # Canvas doesn't use OAuth scopes
                "provider_url": canvas_url,  # Store Canvas URL in dedicated field
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await self.oauth_token_repository.upsert_token(
                token_data=token_data,
                conflict_columns="user_id,provider,service_type"
            )

            logger.info(f"Canvas token stored successfully for user {user_id} using {encryption_method}")

            return {
                "success": True,
                "user_id": user_id,
                "canvas_url": canvas_url,
                "status": "stored",
                "encryption_method": encryption_method,
                "stored_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to store Canvas token for user {user_id}: {e}")
            raise

    async def retrieve_canvas_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt Canvas API token for user from oauth_tokens table

        Automatically detects encryption method (KMS or local) from token format

        Args:
            user_id: User ID

        Returns:
            Dict with token and metadata, or None if not found
        """
        try:
            # Get Canvas token from oauth_tokens using repository
            token_data = await self.oauth_token_repository.get_by_provider(
                user_id=user_id,
                provider="canvas"
            )

            if not token_data:
                return None

            # Check if active
            if not token_data.get("is_active", True):
                logger.warning(f"Canvas integration inactive for user {user_id}")
                return None

            # Decrypt token (automatically handles KMS vs local based on token format)
            decrypted_token = self.encryption_service.decrypt_token(
                token_data["access_token"],
                user_id
            )

            # Get Canvas URL from provider_url field
            canvas_url = token_data.get("provider_url")

            return {
                "api_token": decrypted_token,
                "base_url": canvas_url,  # Retrieved from provider_url field
                "status": "ok" if token_data.get("is_active") else "inactive",
                "user_id": user_id
            }

        except Exception as e:
            logger.error(f"Failed to retrieve Canvas token for user {user_id}: {e}")
            await self._mark_integration_error(user_id, "token_retrieval_failed")
            return None

    async def mark_needs_reauth(self, user_id: str, error_code: str = "401_unauthorized"):
        """Mark Canvas integration as needing reauthorization"""
        try:
            update_data = {
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.oauth_token_repository.update_by_user_and_provider(
                user_id=user_id,
                provider="canvas",
                update_data=update_data
            )

            logger.info(f"Canvas integration marked needs reauth for user {user_id}: {error_code}")

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
            # Delete Canvas token from oauth_tokens using repository
            await self.oauth_token_repository.delete_by_provider(
                user_id=user_id,
                provider="canvas"
            )

            # TODO: Create ExternalCursorRepository and use it here
            # For now, keep direct Supabase access for external_cursor (low priority table)
            from app.config.database.supabase import get_supabase_client
            supabase = get_supabase_client()
            
            # Delete external cursors
            supabase.table("external_cursor").delete().eq(
                "user_id", user_id
            ).eq("source", "canvas").execute()

            # Clear Canvas-sourced tasks using task repository
            # Note: TaskRepository doesn't have delete_by_filters yet, so we'd need to add it
            # For now, using direct access
            supabase.table("tasks").delete().eq(
                "user_id", user_id
            ).eq("external_source", "canvas").execute()

            logger.info(f"Canvas integration deleted for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete Canvas integration for user {user_id}: {e}")
            return False

    async def _mark_integration_error(self, user_id: str, error_code: str):
        """Mark integration as having an error"""
        try:
            update_data = {
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }
            await self.oauth_token_repository.update_by_user_and_provider(
                user_id=user_id,
                provider="canvas",
                update_data=update_data
            )
            logger.info(f"Marked Canvas integration as error for user {user_id}: {error_code}")
        except Exception as e:
            logger.error(f"Failed to mark integration error for user {user_id}: {e}")

    async def _mark_integration_ok(self, user_id: str):
        """Mark integration as OK"""
        try:
            update_data = {
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            await self.oauth_token_repository.update_by_user_and_provider(
                user_id=user_id,
                provider="canvas",
                update_data=update_data
            )
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