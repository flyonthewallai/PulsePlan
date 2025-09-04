"""
iOS Push Notification Service for PulsePlan.
Handles Apple Push Notification service (APNs) integration for sending push notifications to iOS devices.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import ssl
import aiohttp
from dataclasses import dataclass

from app.config.supabase import get_supabase_client
from app.services.cache_service import get_cache_service
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class APNsEnvironment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class NotificationPriority(Enum):
    LOW = "5"
    NORMAL = "10"
    HIGH = "10"


@dataclass
class APNsConfig:
    """Configuration for Apple Push Notification service"""
    team_id: str
    key_id: str
    private_key: str
    bundle_id: str
    environment: APNsEnvironment
    
    @property
    def apns_url(self) -> str:
        """Get APNs URL based on environment"""
        if self.environment == APNsEnvironment.DEVELOPMENT:
            return "https://api.development.push.apple.com"
        return "https://api.push.apple.com"


@dataclass
class DeviceToken:
    """iOS device token information"""
    user_id: str
    device_token: str
    device_model: str
    ios_version: str
    app_version: str
    is_active: bool
    registered_at: datetime
    last_used_at: datetime


class iOSNotificationService:
    """Service for sending iOS push notifications via APNs"""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.cache_service = get_cache_service()
        
        # Initialize APNs configuration
        self.apns_config = self._load_apns_config()
        
        # JWT token for APNs authentication
        self._jwt_token: Optional[str] = None
        self._jwt_expires_at: Optional[datetime] = None
    
    def _load_apns_config(self) -> APNsConfig:
        """Load APNs configuration from settings"""
        return APNsConfig(
            team_id=self.settings.APNS_TEAM_ID,
            key_id=self.settings.APNS_KEY_ID,
            private_key=self.settings.APNS_PRIVATE_KEY,
            bundle_id=self.settings.APNS_BUNDLE_ID,
            environment=APNsEnvironment(self.settings.APNS_ENVIRONMENT)
        )
    
    async def send_notification(
        self, 
        user_id: str, 
        notification: Dict[str, Any],
        scheduled_for: Optional[datetime] = None
    ) -> bool:
        """
        Send push notification to user's iOS devices
        
        Args:
            user_id: Target user ID
            notification: Notification payload
            scheduled_for: Optional scheduling time (for future notifications)
            
        Returns:
            True if notification was sent successfully to at least one device
        """
        try:
            # Get user's active device tokens
            device_tokens = await self._get_user_device_tokens(user_id)
            
            if not device_tokens:
                logger.info(f"No active iOS devices found for user {user_id}")
                return False
            
            # If scheduled for future, store in database and return
            if scheduled_for and scheduled_for > datetime.utcnow():
                await self._schedule_notification(user_id, notification, scheduled_for)
                logger.info(f"Scheduled notification for user {user_id} at {scheduled_for}")
                return True
            
            # Send notification to all user's devices
            success_count = 0
            
            for device_token in device_tokens:
                try:
                    success = await self._send_to_device(device_token.device_token, notification)
                    if success:
                        success_count += 1
                        # Update last used timestamp
                        await self._update_device_last_used(device_token.device_token)
                    else:
                        # Mark device as potentially inactive if sending fails repeatedly
                        await self._handle_failed_device(device_token.device_token)
                        
                except Exception as e:
                    logger.error(f"Failed to send notification to device {device_token.device_token}: {e}")
            
            # Log notification sending
            await self._log_notification_send(user_id, notification, success_count, len(device_tokens))
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            return False
    
    async def send_bulk_notifications(
        self, 
        notifications: List[Dict[str, Any]], 
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Send bulk notifications with batching and rate limiting
        
        Args:
            notifications: List of notification dicts with user_id and notification data
            batch_size: Number of notifications to process in each batch
            
        Returns:
            Results summary with success/failure counts
        """
        start_time = datetime.utcnow()
        results = {
            "total_notifications": len(notifications),
            "successful_sends": 0,
            "failed_sends": 0,
            "processed_users": set(),
            "errors": []
        }
        
        try:
            # Process notifications in batches
            for i in range(0, len(notifications), batch_size):
                batch = notifications[i:i + batch_size]
                batch_tasks = []
                
                for notification_data in batch:
                    user_id = notification_data.get("user_id")
                    notification = notification_data.get("notification")
                    scheduled_for = notification_data.get("scheduled_for")
                    
                    if not user_id or not notification:
                        results["failed_sends"] += 1
                        results["errors"].append(f"Invalid notification data: {notification_data}")
                        continue
                    
                    task = asyncio.create_task(
                        self.send_notification(user_id, notification, scheduled_for)
                    )
                    batch_tasks.append((task, user_id))
                
                # Wait for batch completion
                batch_results = await asyncio.gather(*[task for task, _ in batch_tasks], return_exceptions=True)
                
                # Process batch results
                for (task, user_id), result in zip(batch_tasks, batch_results):
                    results["processed_users"].add(user_id)
                    
                    if isinstance(result, Exception):
                        results["failed_sends"] += 1
                        results["errors"].append(f"User {user_id}: {str(result)}")
                    elif result:
                        results["successful_sends"] += 1
                    else:
                        results["failed_sends"] += 1
                
                # Rate limiting - small delay between batches
                if i + batch_size < len(notifications):
                    await asyncio.sleep(0.1)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["execution_time"] = execution_time
            results["processed_users"] = len(results["processed_users"])
            
            logger.info(
                f"Bulk notification send completed. "
                f"Success: {results['successful_sends']}, "
                f"Failed: {results['failed_sends']} in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk notification send failed: {e}")
            results["errors"].append(f"Bulk send error: {str(e)}")
            return results
    
    async def register_device(
        self, 
        user_id: str, 
        device_token: str,
        device_info: Dict[str, Any]
    ) -> bool:
        """
        Register a new iOS device for push notifications
        
        Args:
            user_id: User ID
            device_token: APNs device token
            device_info: Device information (model, iOS version, app version)
            
        Returns:
            True if registration successful
        """
        try:
            # Validate device token format
            if not self._validate_device_token(device_token):
                logger.warning(f"Invalid device token format for user {user_id}")
                return False
            
            # Check if device token already exists
            existing_device = await self._get_device_by_token(device_token)
            
            if existing_device:
                # Update existing device registration
                await self._update_device_registration(
                    device_token, user_id, device_info
                )
                logger.info(f"Updated device registration for user {user_id}")
            else:
                # Register new device
                await self._create_device_registration(
                    user_id, device_token, device_info
                )
                logger.info(f"Registered new device for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register device for user {user_id}: {e}")
            return False
    
    async def unregister_device(self, device_token: str) -> bool:
        """
        Unregister an iOS device from push notifications
        
        Args:
            device_token: APNs device token to unregister
            
        Returns:
            True if unregistration successful
        """
        try:
            await self.supabase.table("ios_devices").update({
                "is_active": False,
                "unregistered_at": datetime.utcnow().isoformat()
            }).eq("device_token", device_token).execute()
            
            logger.info(f"Unregistered device token: {device_token}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister device {device_token}: {e}")
            return False
    
    async def get_user_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Notification statistics
        """
        try:
            # Get device count
            devices_response = await self.supabase.table("ios_devices").select(
                "device_token, is_active, registered_at, last_used_at"
            ).eq("user_id", user_id).execute()
            
            devices = devices_response.data or []
            active_devices = [d for d in devices if d["is_active"]]
            
            # Get recent notification logs (last 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            logs_response = await self.supabase.table("notification_logs").select(
                "notification_type, success, sent_at"
            ).eq("user_id", user_id).gte("sent_at", thirty_days_ago).execute()
            
            logs = logs_response.data or []
            
            # Calculate statistics
            total_sent = len(logs)
            successful_sends = len([log for log in logs if log["success"]])
            failed_sends = total_sent - successful_sends
            
            # Group by notification type
            type_stats = {}
            for log in logs:
                notification_type = log["notification_type"]
                if notification_type not in type_stats:
                    type_stats[notification_type] = {"sent": 0, "success": 0}
                
                type_stats[notification_type]["sent"] += 1
                if log["success"]:
                    type_stats[notification_type]["success"] += 1
            
            return {
                "user_id": user_id,
                "devices": {
                    "total": len(devices),
                    "active": len(active_devices)
                },
                "notifications_30_days": {
                    "total_sent": total_sent,
                    "successful": successful_sends,
                    "failed": failed_sends,
                    "success_rate": successful_sends / total_sent if total_sent > 0 else 0
                },
                "by_type": type_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification stats for user {user_id}: {e}")
            return {}
    
    async def _send_to_device(self, device_token: str, notification: Dict[str, Any]) -> bool:
        """Send notification to a specific device"""
        try:
            # Ensure we have a valid JWT token
            await self._ensure_jwt_token()
            
            # Build APNs payload
            payload = self._build_apns_payload(notification)
            
            # Send HTTP/2 request to APNs
            headers = {
                "authorization": f"bearer {self._jwt_token}",
                "apns-topic": self.apns_config.bundle_id,
                "apns-priority": notification.get("priority", "10"),
                "content-type": "application/json"
            }
            
            # Add expiration if specified
            if "expiry" in notification:
                headers["apns-expiration"] = str(int(notification["expiry"].timestamp()))
            
            url = f"{self.apns_config.apns_url}/3/device/{device_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return True
                    
                    # Handle APNs error responses
                    response_text = await response.text()
                    
                    if response.status == 400:
                        logger.warning(f"Bad request to APNs for device {device_token}: {response_text}")
                    elif response.status == 403:
                        logger.warning(f"APNs authentication failed: {response_text}")
                        # Clear JWT token to force refresh
                        self._jwt_token = None
                    elif response.status == 410:
                        # Device token is no longer valid
                        logger.info(f"Device token invalid, unregistering: {device_token}")
                        await self.unregister_device(device_token)
                    else:
                        logger.warning(f"APNs error {response.status} for device {device_token}: {response_text}")
                    
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send notification to device {device_token}: {e}")
            return False
    
    def _build_apns_payload(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Build APNs-compatible payload"""
        aps = {
            "alert": {
                "title": notification["title"],
                "body": notification["body"]
            }
        }
        
        # Add badge if specified
        if "badge" in notification:
            aps["badge"] = notification["badge"]
        
        # Add sound
        aps["sound"] = notification.get("sound", "default")
        
        # Add category for interactive notifications
        if "category" in notification:
            aps["category"] = notification["category"]
        
        # Add thread-id for notification grouping
        if "thread_id" in notification:
            aps["thread-id"] = notification["thread_id"]
        
        # Build full payload
        payload = {"aps": aps}
        
        # Add custom data
        if "data" in notification:
            payload.update(notification["data"])
        
        return payload
    
    async def _ensure_jwt_token(self):
        """Ensure we have a valid JWT token for APNs authentication"""
        if (self._jwt_token and self._jwt_expires_at and 
            datetime.utcnow() < self._jwt_expires_at - timedelta(minutes=5)):
            return
        
        # Generate new JWT token
        self._jwt_token = await self._generate_jwt_token()
        self._jwt_expires_at = datetime.utcnow() + timedelta(minutes=55)  # APNs tokens expire after 1 hour
    
    async def _generate_jwt_token(self) -> str:
        """Generate JWT token for APNs authentication"""
        try:
            import jwt
            from cryptography.hazmat.primitives import serialization
            
            # Load private key
            private_key = serialization.load_pem_private_key(
                self.apns_config.private_key.encode(),
                password=None,
            )
            
            # Create JWT payload
            now = datetime.utcnow()
            payload = {
                "iss": self.apns_config.team_id,
                "iat": int(now.timestamp())
            }
            
            # Generate JWT
            token = jwt.encode(
                payload,
                private_key,
                algorithm="ES256",
                headers={"kid": self.apns_config.key_id}
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate JWT token: {e}")
            raise
    
    async def _get_user_device_tokens(self, user_id: str) -> List[DeviceToken]:
        """Get all active device tokens for a user"""
        try:
            response = await self.supabase.table("ios_devices").select(
                "user_id, device_token, device_model, ios_version, app_version, is_active, registered_at, last_used_at"
            ).eq("user_id", user_id).eq("is_active", True).execute()
            
            devices = response.data or []
            
            return [
                DeviceToken(
                    user_id=device["user_id"],
                    device_token=device["device_token"],
                    device_model=device["device_model"],
                    ios_version=device["ios_version"],
                    app_version=device["app_version"],
                    is_active=device["is_active"],
                    registered_at=datetime.fromisoformat(device["registered_at"]),
                    last_used_at=datetime.fromisoformat(device["last_used_at"]) if device["last_used_at"] else datetime.utcnow()
                )
                for device in devices
            ]
            
        except Exception as e:
            logger.error(f"Failed to get device tokens for user {user_id}: {e}")
            return []
    
    async def _get_device_by_token(self, device_token: str) -> Optional[Dict[str, Any]]:
        """Get device information by device token"""
        try:
            response = await self.supabase.table("ios_devices").select("*").eq(
                "device_token", device_token
            ).single().execute()
            
            return response.data
            
        except Exception as e:
            logger.debug(f"Device token not found: {device_token}")
            return None
    
    async def _create_device_registration(self, user_id: str, device_token: str, device_info: Dict[str, Any]):
        """Create new device registration"""
        registration_data = {
            "user_id": user_id,
            "device_token": device_token,
            "device_model": device_info.get("model", "Unknown"),
            "ios_version": device_info.get("ios_version", "Unknown"),
            "app_version": device_info.get("app_version", "Unknown"),
            "is_active": True,
            "registered_at": datetime.utcnow().isoformat(),
            "last_used_at": datetime.utcnow().isoformat()
        }
        
        await self.supabase.table("ios_devices").insert(registration_data).execute()
    
    async def _update_device_registration(self, device_token: str, user_id: str, device_info: Dict[str, Any]):
        """Update existing device registration"""
        update_data = {
            "user_id": user_id,
            "device_model": device_info.get("model", "Unknown"),
            "ios_version": device_info.get("ios_version", "Unknown"),
            "app_version": device_info.get("app_version", "Unknown"),
            "is_active": True,
            "last_used_at": datetime.utcnow().isoformat()
        }
        
        await self.supabase.table("ios_devices").update(update_data).eq(
            "device_token", device_token
        ).execute()
    
    async def _update_device_last_used(self, device_token: str):
        """Update device last used timestamp"""
        await self.supabase.table("ios_devices").update({
            "last_used_at": datetime.utcnow().isoformat()
        }).eq("device_token", device_token).execute()
    
    async def _handle_failed_device(self, device_token: str):
        """Handle device that failed to receive notification"""
        # Increment failure count or mark as inactive after multiple failures
        # Implementation depends on your failure handling strategy
        pass
    
    async def _schedule_notification(self, user_id: str, notification: Dict[str, Any], scheduled_for: datetime):
        """Store notification for future sending"""
        scheduled_data = {
            "user_id": user_id,
            "notification_data": json.dumps(notification),
            "scheduled_for": scheduled_for.isoformat(),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await self.supabase.table("scheduled_notifications").insert(scheduled_data).execute()
    
    async def _log_notification_send(self, user_id: str, notification: Dict[str, Any], success_count: int, total_devices: int):
        """Log notification sending for analytics"""
        log_entry = {
            "user_id": user_id,
            "notification_type": notification.get("data", {}).get("type", "unknown"),
            "title": notification["title"],
            "success": success_count > 0,
            "devices_targeted": total_devices,
            "devices_successful": success_count,
            "sent_at": datetime.utcnow().isoformat()
        }
        
        await self.supabase.table("notification_logs").insert(log_entry).execute()
    
    def _validate_device_token(self, device_token: str) -> bool:
        """Validate APNs device token format"""
        if not device_token or len(device_token) != 64:
            return False
        
        try:
            # Check if it's a valid hex string
            int(device_token, 16)
            return True
        except ValueError:
            return False


# Global iOS notification service instance
_ios_notification_service: Optional[iOSNotificationService] = None

def get_ios_notification_service() -> iOSNotificationService:
    """Get global iOS notification service instance"""
    global _ios_notification_service
    if _ios_notification_service is None:
        _ios_notification_service = iOSNotificationService()
    return _ios_notification_service