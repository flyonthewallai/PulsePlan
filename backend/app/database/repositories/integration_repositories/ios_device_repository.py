"""
iOS Device Repository
Handles database operations for ios_devices table
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class IOSDeviceRepository(BaseRepository):
    """Repository for ios_devices table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "ios_devices"

    async def update_device_status(
        self,
        device_token: str,
        is_active: bool,
        inactive_reason: Optional[str] = None
    ) -> bool:
        """
        Update device active status
        
        Args:
            device_token: Device token
            is_active: Whether device is active
            inactive_reason: Reason for inactivity if applicable
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            update_data = {
                "is_active": is_active,
                "inactive_reason": inactive_reason,
                "last_checked_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("device_token", device_token)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error updating device status for {device_token}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_device_status",
                details={"device_token": device_token}
            )

    async def get_devices_by_user(
        self,
        user_id: str,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all devices for a user
        
        Args:
            user_id: User ID
            active_only: If True, only return active devices
        
        Returns:
            List of device records
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)
            
            if active_only:
                query = query.eq("is_active", True)
            
            response = query.execute()
            return response.data if response.data else []
        
        except Exception as e:
            logger.error(f"Error getting devices for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_devices_by_user",
                details={"user_id": user_id}
            )

    async def get_device_by_token(self, device_token: str) -> Optional[Dict[str, Any]]:
        """
        Get device by token
        
        Args:
            device_token: Device token
        
        Returns:
            Device record or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("device_token", device_token)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error getting device by token {device_token}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_device_by_token",
                details={"device_token": device_token}
            )

    async def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new device registration
        
        Args:
            device_data: Device registration data
        
        Returns:
            Created device record
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .insert(device_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="Failed to create device registration",
                table=self.table_name,
                operation="create_device"
            )
        
        except RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Error creating device: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create_device",
                details={"device_data": device_data}
            )

    async def update_device(
        self,
        device_token: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update device information
        
        Args:
            device_token: Device token
            update_data: Data to update
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("device_token", device_token)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error updating device {device_token}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_device",
                details={"device_token": device_token}
            )

    async def get_stale_devices(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get devices that haven't been used in the specified number of days
        
        Args:
            days: Number of days to consider a device stale
        
        Returns:
            List of stale device records
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("is_active", True)\
                .lt("last_used_at", cutoff.isoformat())\
                .execute()
            
            return response.data if response.data else []
        
        except Exception as e:
            logger.error(f"Error getting stale devices: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_stale_devices",
                details={"days": days}
            )


def get_ios_device_repository() -> IOSDeviceRepository:
    """Dependency injection function"""
    return IOSDeviceRepository()

