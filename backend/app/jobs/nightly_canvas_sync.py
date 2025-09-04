"""
Automated nightly Canvas sync job for PulsePlan.
Runs every night to sync Canvas data for all active users.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.config.supabase import get_supabase_client
from app.services.cache_service import get_cache_service
from app.jobs.canvas_sync import get_canvas_sync

logger = logging.getLogger(__name__)


class NightlyCanvasSync:
    """Automated nightly Canvas synchronization job"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.cache_service = get_cache_service()
        self.canvas_sync = get_canvas_sync()
    
    async def run_nightly_sync(self, batch_size: int = 50, max_concurrent: int = 10) -> Dict[str, Any]:
        """
        Run nightly Canvas sync for all active users
        
        Args:
            batch_size: Number of users to process in each batch
            max_concurrent: Maximum concurrent sync operations
        
        Returns:
            Dict with sync results and statistics
        """
        start_time = datetime.utcnow()
        logger.info("Starting nightly Canvas sync job")
        
        try:
            # Get all users with active Canvas integrations
            active_users = await self._get_active_canvas_users()
            
            if not active_users:
                logger.info("No active Canvas users found - skipping sync")
                return {
                    "job": "nightly_canvas_sync",
                    "started_at": start_time.isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "total_users": 0,
                    "synced_users": 0,
                    "failed_users": 0,
                    "skipped_users": 0,
                    "errors": []
                }
            
            logger.info(f"Found {len(active_users)} active Canvas users to sync")
            
            sync_stats = {
                "job": "nightly_canvas_sync",
                "started_at": start_time.isoformat(),
                "total_users": len(active_users),
                "synced_users": 0,
                "failed_users": 0,
                "skipped_users": 0,
                "errors": [],
                "user_results": []
            }
            
            # Process users in batches with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)
            
            for i in range(0, len(active_users), batch_size):
                batch = active_users[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} users")
                
                # Process batch concurrently
                batch_tasks = []
                for user in batch:
                    task = asyncio.create_task(
                        self._sync_user_with_semaphore(semaphore, user, sync_stats)
                    )
                    batch_tasks.append(task)
                
                # Wait for batch to complete
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch task failed: {result}")
                        sync_stats["errors"].append(f"Batch task error: {str(result)}")
                
                # Small delay between batches to avoid overwhelming the system
                await asyncio.sleep(1)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            sync_stats["completed_at"] = datetime.utcnow().isoformat()
            sync_stats["execution_time_seconds"] = execution_time
            sync_stats["success"] = True
            
            logger.info(
                f"Nightly Canvas sync completed in {execution_time:.2f}s. "
                f"Synced: {sync_stats['synced_users']}, "
                f"Failed: {sync_stats['failed_users']}, "
                f"Skipped: {sync_stats['skipped_users']}"
            )
            
            # Cache job results for monitoring
            await self._cache_job_results(sync_stats)
            
            return sync_stats
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Nightly Canvas sync job failed: {e}"
            logger.error(error_msg)
            
            return {
                "job": "nightly_canvas_sync",
                "started_at": start_time.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "execution_time_seconds": execution_time,
                "success": False,
                "error": str(e),
                "total_users": 0,
                "synced_users": 0,
                "failed_users": 0,
                "skipped_users": 0,
                "errors": [error_msg]
            }
    
    async def _sync_user_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        user: Dict[str, Any], 
        sync_stats: Dict[str, Any]
    ):
        """Sync a single user with semaphore protection"""
        async with semaphore:
            return await self._sync_single_user(user, sync_stats)
    
    async def _sync_single_user(self, user: Dict[str, Any], sync_stats: Dict[str, Any]):
        """Sync Canvas data for a single user"""
        user_id = user["user_id"]
        
        try:
            # Check if user was synced recently (within last 20 hours)
            # This prevents double-syncing if the job runs multiple times
            if await self._was_recently_synced(user_id, hours=20):
                logger.debug(f"User {user_id} was recently synced - skipping")
                sync_stats["skipped_users"] += 1
                sync_stats["user_results"].append({
                    "user_id": user_id,
                    "status": "skipped",
                    "reason": "recently_synced",
                    "synced_at": datetime.utcnow().isoformat()
                })
                return
            
            # Perform Canvas sync
            sync_result = await self.canvas_sync.sync_user_canvas_data(
                user_id=user_id,
                canvas_api_key=user.get("canvas_api_key"),
                canvas_url=user.get("canvas_url"),
                force_refresh=False,  # Don't force refresh for nightly sync
                include_grades=True   # Include grades in nightly sync
            )
            
            if sync_result.get("success", False):
                sync_stats["synced_users"] += 1
                sync_stats["user_results"].append({
                    "user_id": user_id,
                    "status": "synced",
                    "assignments_synced": sync_result["totals"]["assignments"],
                    "courses_synced": sync_result["totals"]["courses"],
                    "execution_time": sync_result.get("execution_time_seconds", 0),
                    "synced_at": sync_result.get("sync_completed_at")
                })
                logger.debug(f"Successfully synced Canvas data for user {user_id}")
            else:
                sync_stats["failed_users"] += 1
                error_msg = sync_result.get("error", "Unknown error")
                sync_stats["errors"].append(f"User {user_id}: {error_msg}")
                sync_stats["user_results"].append({
                    "user_id": user_id,
                    "status": "failed",
                    "error": error_msg,
                    "synced_at": datetime.utcnow().isoformat()
                })
                logger.warning(f"Failed to sync Canvas data for user {user_id}: {error_msg}")
                
        except Exception as e:
            sync_stats["failed_users"] += 1
            error_msg = f"Exception during sync: {str(e)}"
            sync_stats["errors"].append(f"User {user_id}: {error_msg}")
            sync_stats["user_results"].append({
                "user_id": user_id,
                "status": "failed",
                "error": error_msg,
                "synced_at": datetime.utcnow().isoformat()
            })
            logger.error(f"Exception syncing Canvas data for user {user_id}: {e}")
    
    async def _get_active_canvas_users(self) -> List[Dict[str, Any]]:
        """Get all users with active Canvas integrations"""
        try:
            # Get users from canvas_integrations table
            response = await self.supabase.table("canvas_integrations").select(
                "user_id, canvas_url, canvas_api_key, last_sync, is_active"
            ).eq("is_active", True).execute()
            
            active_users = []
            
            if response.data:
                for integration in response.data:
                    # Only include users with valid credentials
                    if integration.get("canvas_url") and integration.get("canvas_api_key"):
                        active_users.append({
                            "user_id": integration["user_id"],
                            "canvas_url": integration["canvas_url"],
                            "canvas_api_key": integration["canvas_api_key"],
                            "last_sync": integration.get("last_sync")
                        })
            
            return active_users
            
        except Exception as e:
            logger.error(f"Error getting active Canvas users: {e}")
            return []
    
    async def _was_recently_synced(self, user_id: str, hours: int = 20) -> bool:
        """Check if user was synced within the specified hours"""
        try:
            # Check integration status
            response = await self.supabase.table("canvas_integrations").select(
                "last_sync"
            ).eq("user_id", user_id).single().execute()
            
            if response.data and response.data.get("last_sync"):
                last_sync = datetime.fromisoformat(response.data["last_sync"])
                time_threshold = datetime.utcnow() - timedelta(hours=hours)
                return last_sync > time_threshold
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking recent sync for user {user_id}: {e}")
            return False
    
    async def _cache_job_results(self, results: Dict[str, Any]):
        """Cache job results for monitoring and debugging"""
        try:
            cache_key = f"nightly_canvas_sync:{datetime.utcnow().strftime('%Y-%m-%d')}"
            
            # Cache for 7 days
            await self.cache_service.set(cache_key, results, 604800)
            
            # Also cache as "latest" for easy access
            await self.cache_service.set("nightly_canvas_sync:latest", results, 604800)
            
        except Exception as e:
            logger.warning(f"Error caching job results: {e}")
    
    async def get_last_sync_results(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get results from last nightly sync job"""
        try:
            if date:
                cache_key = f"nightly_canvas_sync:{date}"
            else:
                cache_key = "nightly_canvas_sync:latest"
            
            return await self.cache_service.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting sync results: {e}")
            return None


# Global nightly sync instance
_nightly_canvas_sync: Optional[NightlyCanvasSync] = None

def get_nightly_canvas_sync() -> NightlyCanvasSync:
    """Get global nightly Canvas sync instance"""
    global _nightly_canvas_sync
    if _nightly_canvas_sync is None:
        _nightly_canvas_sync = NightlyCanvasSync()
    return _nightly_canvas_sync


# Main function for running the job
async def run_nightly_canvas_sync() -> Dict[str, Any]:
    """Run the nightly Canvas sync job - entry point for scheduler"""
    nightly_sync = get_nightly_canvas_sync()
    return await nightly_sync.run_nightly_sync()