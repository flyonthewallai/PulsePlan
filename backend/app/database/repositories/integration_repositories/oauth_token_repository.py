"""
OAuth Token Repository
Handles database operations for OAuth tokens
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class OAuthTokenRepository(BaseRepository):
    """Repository for OAuth token operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "oauth_tokens"

    async def get_expiring_tokens(
        self,
        expiry_threshold: datetime,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get tokens that are expiring soon
        
        Args:
            expiry_threshold: Datetime threshold for expiry
            limit: Maximum number of tokens to return
        
        Returns:
            List of token dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .filter("expires_at", "lte", expiry_threshold.isoformat())\
                .eq("is_active", True)\
                .neq("refresh_token", None)\
                .order("expires_at", desc=False)\
                .limit(limit)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching expiring tokens: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_expiring_tokens",
                details={"expiry_threshold": expiry_threshold.isoformat(), "limit": limit}
            )

    async def update_token_after_refresh(
        self,
        token_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update token after successful refresh
        
        Args:
            token_id: Token ID
            update_data: Dictionary with fields to update
        
        Returns:
            True if update successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("id", token_id)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error updating token {token_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_token_after_refresh",
                details={"token_id": token_id, "update_data": update_data}
            )

    async def mark_token_inactive(
        self,
        token_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Mark a token as inactive
        
        Args:
            token_id: Token ID
            reason: Optional reason for marking inactive
        
        Returns:
            True if update successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            update_data = {
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Log the reason if provided (error_log column doesn't exist in schema)
            if reason:
                logger.info(f"Marking token {token_id} inactive. Reason: {reason}")
            
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("id", token_id)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error marking token {token_id} inactive: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="mark_token_inactive",
                details={"token_id": token_id, "reason": reason}
            )
    
    async def get_active_by_user(
        self,
        user_id: str,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active tokens for a user, optionally filtered by provider
        
        Args:
            user_id: User ID
            provider: Optional provider filter
        
        Returns:
            List of token dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .neq("refresh_token", None)
            
            if provider:
                query = query.eq("provider", provider)
            
            response = query.execute()
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching active tokens for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_active_by_user",
                details={"user_id": user_id, "provider": provider}
            )

    async def upsert_token(
        self,
        token_data: Dict[str, Any],
        conflict_columns: str = "user_id,provider,service_type"
    ) -> Optional[Dict[str, Any]]:
        """
        Upsert a token (insert or update on conflict)
        
        Args:
            token_data: Token data dictionary
            conflict_columns: Columns to check for conflicts
        
        Returns:
            Upserted token dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .upsert(token_data, on_conflict=conflict_columns)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error upserting token: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert_token",
                details={"token_data": token_data}
            )

    async def get_by_provider(
        self,
        user_id: str,
        provider: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get token by user ID and provider
        
        Args:
            user_id: User ID
            provider: Provider name
        
        Returns:
            Token dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .single()\
                .execute()
            
            return response.data if response.data else None
        
        except Exception as e:
            logger.error(f"Error fetching token for user {user_id}, provider {provider}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_provider",
                details={"user_id": user_id, "provider": provider}
            )

    async def delete_by_provider(
        self,
        user_id: str,
        provider: str
    ) -> bool:
        """
        Delete token by user ID and provider
        
        Args:
            user_id: User ID
            provider: Provider name
        
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error deleting token for user {user_id}, provider {provider}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_by_provider",
                details={"user_id": user_id, "provider": provider}
            )


    async def update_by_user_and_provider(
        self,
        user_id: str,
        provider: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update token by user ID and provider
        
        Args:
            user_id: User ID
            provider: Provider name
            update_data: Fields to update
        
        Returns:
            True if update successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(
                f"Error updating token for user {user_id}, provider {provider}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_by_user_and_provider",
                details={"user_id": user_id, "provider": provider}
            )
    
    async def upsert_token(
        self,
        user_id: str,
        provider: str,
        service_type: str,
        token_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Insert or update token for user/provider/service
        
        Args:
            user_id: User ID
            provider: Provider name
            service_type: Service type (calendar, gmail, etc.)
            token_data: Token fields
        
        Returns:
            Created/updated token dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Check if exists
            existing = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .eq("service_type", service_type)\
                .execute()
            
            if existing.data:
                # Update
                response = self.supabase.table(self.table_name)\
                    .update(token_data)\
                    .eq("id", existing.data[0]["id"])\
                    .execute()
            else:
                # Insert
                full_data = {
                    "user_id": user_id,
                    "provider": provider,
                    "service_type": service_type,
                    **token_data
                }
                response = self.supabase.table(self.table_name)\
                    .insert(full_data)\
                    .execute()
            
            return response.data[0] if response.data else None
        
        except Exception as e:
            logger.error(
                f"Error upserting token for user {user_id}, provider {provider}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert_token",
                details={"user_id": user_id, "provider": provider, "service_type": service_type}
            )
    
    async def delete_by_user_provider_service(
        self,
        user_id: str,
        provider: str,
        service_type: str
    ) -> bool:
        """
        Delete token by user, provider, and service type
        
        Args:
            user_id: User ID
            provider: Provider name
            service_type: Service type
        
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .eq("service_type", service_type)\
                .execute()
            
            return response.data is not None
        
        except Exception as e:
            logger.error(
                f"Error deleting token for user {user_id}, provider {provider}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_by_user_provider_service",
                details={"user_id": user_id, "provider": provider, "service_type": service_type}
            )
    
    async def check_provider_exists(
        self,
        user_id: str,
        provider: str
    ) -> bool:
        """
        Check if user has any token for a provider
        
        Args:
            user_id: User ID
            provider: Provider name
        
        Returns:
            True if provider connection exists, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .limit(1)\
                .execute()
            
            return len(response.data) > 0 if response.data else False
        
        except Exception as e:
            logger.error(
                f"Error checking provider for user {user_id}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="check_provider_exists",
                details={"user_id": user_id, "provider": provider}
            )


def get_oauth_token_repository() -> OAuthTokenRepository:
    """Dependency injection function"""
    return OAuthTokenRepository()

