"""
Calendar Background Synchronization Worker
Handles periodic calendar sync, webhook processing, and conflict resolution
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import json

from ..config.supabase import get_supabase_client
from ..config.redis import get_redis_client
from ..services.calendar_sync_service import get_calendar_sync_service, get_calendar_webhook_service
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class CalendarBackgroundWorker:
    """Background worker for calendar synchronization tasks"""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.redis_client = get_redis_client()
        self.calendar_sync_service = get_calendar_sync_service()
        self.webhook_service = get_calendar_webhook_service()
        self.is_running = False
        self.worker_tasks = []
    
    async def start(self):
        """Start the background worker"""
        if self.is_running:
            logger.warning("Calendar background worker is already running")
            return
        
        self.is_running = True
        logger.info("Starting Calendar Background Worker")
        
        # Start background tasks
        self.worker_tasks = [
            asyncio.create_task(self._periodic_sync_worker()),
            asyncio.create_task(self._webhook_processor_worker()),
            asyncio.create_task(self._conflict_resolver_worker()),
            asyncio.create_task(self._cleanup_worker())
        ]
        
        # Wait for all tasks
        try:
            await asyncio.gather(*self.worker_tasks)
        except asyncio.CancelledError:
            logger.info("Calendar background worker tasks cancelled")
        except Exception as e:
            logger.error(f"Error in calendar background worker: {e}")
    
    async def stop(self):
        """Stop the background worker"""
        if not self.is_running:
            return
        
        logger.info("Stopping Calendar Background Worker")
        self.is_running = False
        
        # Cancel all running tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
    
    async def _periodic_sync_worker(self):
        """Worker that performs periodic calendar synchronization"""
        logger.info("Started periodic sync worker")
        
        while self.is_running:
            try:
                # Get users who have auto-sync enabled
                users_to_sync = await self._get_users_for_auto_sync()
                
                logger.info(f"Found {len(users_to_sync)} users for periodic sync")
                
                # Process users in batches to avoid overwhelming the APIs
                batch_size = 5
                for i in range(0, len(users_to_sync), batch_size):
                    if not self.is_running:
                        break
                    
                    batch = users_to_sync[i:i + batch_size]
                    sync_tasks = [
                        self._sync_user_calendar(user)
                        for user in batch
                    ]
                    
                    # Execute batch with timeout
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*sync_tasks, return_exceptions=True),
                            timeout=300  # 5 minutes timeout per batch
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"Batch sync timed out for users: {[u['user_id'] for u in batch]}")
                    
                    # Small delay between batches
                    await asyncio.sleep(2)
                
                # Wait for next sync interval (default: 10 minutes)
                sync_interval = 600  # 10 minutes
                await asyncio.sleep(sync_interval)
                
            except Exception as e:
                logger.error(f"Error in periodic sync worker: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _webhook_processor_worker(self):
        """Worker that processes calendar webhook notifications"""
        logger.info("Started webhook processor worker")
        
        while self.is_running:
            try:
                # Process pending webhook notifications from Redis queue
                webhook_data = await self._get_pending_webhooks()
                
                if webhook_data:
                    logger.info(f"Processing {len(webhook_data)} webhook notifications")
                    
                    for webhook in webhook_data:
                        if not self.is_running:
                            break
                        
                        await self._process_webhook(webhook)
                        
                        # Small delay between webhook processing
                        await asyncio.sleep(0.5)
                
                # Check for new webhooks every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in webhook processor worker: {e}")
                await asyncio.sleep(60)
    
    async def _conflict_resolver_worker(self):
        """Worker that resolves calendar synchronization conflicts"""
        logger.info("Started conflict resolver worker")
        
        while self.is_running:
            try:
                # Get users with unresolved conflicts
                users_with_conflicts = await self._get_users_with_conflicts()
                
                if users_with_conflicts:
                    logger.info(f"Found {len(users_with_conflicts)} users with calendar conflicts")
                    
                    for user_id in users_with_conflicts:
                        if not self.is_running:
                            break
                        
                        try:
                            conflict_results = await self.calendar_sync_service.detect_and_resolve_conflicts(user_id)
                            logger.info(f"Resolved {conflict_results['conflicts_resolved']} conflicts for user {user_id}")
                        except Exception as e:
                            logger.error(f"Error resolving conflicts for user {user_id}: {e}")
                
                # Run conflict resolution every 30 minutes
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"Error in conflict resolver worker: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_worker(self):
        """Worker that cleans up old sync data and logs"""
        logger.info("Started cleanup worker")
        
        while self.is_running:
            try:
                # Clean up old calendar events (older than 90 days)
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                
                await self.supabase.table("calendar_events").delete().lt(
                    "start_time", cutoff_date.isoformat()
                ).execute()
                
                # Clean up resolved conflicts (older than 30 days)
                conflict_cutoff = datetime.utcnow() - timedelta(days=30)
                
                await self.supabase.table("calendar_sync_conflicts").delete().match({
                    "resolution_status": "resolved"
                }).lt("resolved_at", conflict_cutoff.isoformat()).execute()
                
                # Clean up old sync status entries
                await self.supabase.table("calendar_sync_status").delete().lt(
                    "last_sync_at", (datetime.utcnow() - timedelta(days=30)).isoformat()
                ).execute()
                
                logger.info("Completed calendar data cleanup")
                
                # Run cleanup daily
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def _get_users_for_auto_sync(self) -> List[Dict[str, Any]]:
        """Get users who have auto-sync enabled and are due for sync"""
        try:
            # Get users with calendar preferences enabled
            response = await self.supabase.table("calendar_preferences").select(
                "user_id, sync_frequency_minutes, updated_at"
            ).eq("auto_sync_enabled", True).execute()
            
            users_for_sync = []
            current_time = datetime.utcnow()
            
            for user_pref in response.data:
                user_id = user_pref["user_id"]
                sync_frequency = user_pref.get("sync_frequency_minutes", 10)
                
                # Check if user is due for sync
                sync_status_response = await self.supabase.table("calendar_sync_status").select(
                    "last_sync_at"
                ).eq("user_id", user_id).single().execute()
                
                last_sync = None
                if sync_status_response.data and sync_status_response.data.get("last_sync_at"):
                    last_sync = datetime.fromisoformat(
                        sync_status_response.data["last_sync_at"].replace("Z", "+00:00")
                    )
                
                # Check if sync is due
                if not last_sync or (current_time - last_sync).total_seconds() >= (sync_frequency * 60):
                    users_for_sync.append({
                        "user_id": user_id,
                        "sync_frequency_minutes": sync_frequency,
                        "last_sync": last_sync
                    })
            
            return users_for_sync
            
        except Exception as e:
            logger.error(f"Error getting users for auto-sync: {e}")
            return []
    
    async def _sync_user_calendar(self, user_data: Dict[str, Any]) -> bool:
        """Sync calendar for a single user"""
        user_id = user_data["user_id"]
        
        try:
            # Perform calendar sync
            sync_results = await self.calendar_sync_service.sync_user_calendars(
                user_id=user_id,
                days_ahead=30,
                force_refresh=False
            )
            
            # Resolve any conflicts
            conflict_results = await self.calendar_sync_service.detect_and_resolve_conflicts(user_id)
            
            logger.info(f"Auto-sync completed for user {user_id}: {sync_results['total_events']} events, {conflict_results['conflicts_resolved']} conflicts resolved")
            return True
            
        except Exception as e:
            logger.error(f"Error during auto-sync for user {user_id}: {e}")
            return False
    
    async def _get_pending_webhooks(self) -> List[Dict[str, Any]]:
        """Get pending webhook notifications from Redis"""
        try:
            # Ensure Redis client is initialized
            if not self.redis_client.client:
                await self.redis_client.initialize()
            
            webhooks = []
            
            # Get Google webhook notifications
            google_webhooks = await self.redis_client.lrange("calendar_webhooks:google", 0, -1)
            for webhook_data in google_webhooks:
                try:
                    webhook = json.loads(webhook_data)
                    webhook["provider"] = "google"
                    webhooks.append(webhook)
                except json.JSONDecodeError:
                    logger.error(f"Invalid webhook data: {webhook_data}")
            
            # Get Microsoft webhook notifications
            microsoft_webhooks = await self.redis_client.lrange("calendar_webhooks:microsoft", 0, -1)
            for webhook_data in microsoft_webhooks:
                try:
                    webhook = json.loads(webhook_data)
                    webhook["provider"] = "microsoft"
                    webhooks.append(webhook)
                except json.JSONDecodeError:
                    logger.error(f"Invalid webhook data: {webhook_data}")
            
            # Clear processed webhooks
            if google_webhooks:
                await self.redis_client.delete("calendar_webhooks:google")
            if microsoft_webhooks:
                await self.redis_client.delete("calendar_webhooks:microsoft")
            
            return webhooks
            
        except Exception as e:
            logger.error(f"Error getting pending webhooks: {e}")
            return []
    
    async def _process_webhook(self, webhook: Dict[str, Any]):
        """Process a single webhook notification"""
        try:
            provider = webhook.get("provider")
            user_id = webhook.get("user_id")
            
            if not user_id or not provider:
                logger.warning(f"Invalid webhook data: missing user_id or provider: {webhook}")
                return
            
            if provider == "google":
                result = await self.webhook_service.handle_google_webhook(
                    user_id=user_id,
                    resource_id=webhook.get("resource_id", ""),
                    resource_state=webhook.get("resource_state", "sync")
                )
            elif provider == "microsoft":
                result = await self.webhook_service.handle_microsoft_webhook(
                    user_id=user_id,
                    subscription_id=webhook.get("subscription_id", ""),
                    change_type=webhook.get("change_type", "updated")
                )
            else:
                logger.warning(f"Unsupported webhook provider: {provider}")
                return
            
            if result.get("success"):
                logger.info(f"Successfully processed {provider} webhook for user {user_id}")
            else:
                logger.error(f"Failed to process {provider} webhook for user {user_id}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
    
    async def _get_users_with_conflicts(self) -> List[str]:
        """Get users with unresolved calendar conflicts"""
        try:
            response = await self.supabase.table("calendar_sync_conflicts").select(
                "user_id"
            ).eq("resolution_status", "unresolved").execute()
            
            # Get unique user IDs
            user_ids = list(set([conflict["user_id"] for conflict in response.data]))
            return user_ids
            
        except Exception as e:
            logger.error(f"Error getting users with conflicts: {e}")
            return []
    
    async def queue_webhook(self, provider: str, webhook_data: Dict[str, Any]) -> bool:
        """Queue a webhook notification for processing"""
        try:
            # Ensure Redis client is initialized
            if not self.redis_client.client:
                await self.redis_client.initialize()
            
            queue_key = f"calendar_webhooks:{provider}"
            webhook_json = json.dumps(webhook_data)
            
            await self.redis_client.lpush(queue_key, webhook_json)
            logger.info(f"Queued {provider} webhook for processing")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing webhook: {e}")
            return False


# Global background worker instance
_background_worker: Optional[CalendarBackgroundWorker] = None

def get_calendar_background_worker() -> CalendarBackgroundWorker:
    """Get global calendar background worker instance"""
    global _background_worker
    if _background_worker is None:
        _background_worker = CalendarBackgroundWorker()
    return _background_worker


class CalendarScheduler:
    """Scheduler for calendar-related operations"""
    
    def __init__(self):
        self.background_worker = get_calendar_background_worker()
    
    async def schedule_user_sync(self, user_id: str, sync_frequency_minutes: int = 10) -> bool:
        """Schedule periodic sync for a user"""
        try:
            from ..services.calendar_sync_service import get_calendar_sync_service
            
            calendar_service = get_calendar_sync_service()
            success = await calendar_service.schedule_background_sync(user_id, sync_frequency_minutes)
            
            logger.info(f"Scheduled calendar sync for user {user_id} every {sync_frequency_minutes} minutes")
            return success
            
        except Exception as e:
            logger.error(f"Error scheduling user sync: {e}")
            return False
    
    async def trigger_immediate_sync(self, user_id: str, force_refresh: bool = True) -> Dict[str, Any]:
        """Trigger immediate calendar sync for a user"""
        try:
            from ..services.calendar_sync_service import get_calendar_sync_service
            
            calendar_service = get_calendar_sync_service()
            sync_results = await calendar_service.sync_user_calendars(
                user_id=user_id,
                days_ahead=30,
                force_refresh=force_refresh
            )
            
            # Also resolve conflicts
            conflict_results = await calendar_service.detect_and_resolve_conflicts(user_id)
            
            return {
                "sync_results": sync_results,
                "conflict_results": conflict_results,
                "triggered_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error triggering immediate sync for user {user_id}: {e}")
            return {"error": str(e)}


# Global scheduler instance
def get_calendar_scheduler() -> CalendarScheduler:
    """Get calendar scheduler instance"""
    return CalendarScheduler()