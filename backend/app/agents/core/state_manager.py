"""
Workflow State Management System
Provides centralized, isolated state management with snapshots and recovery
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from copy import deepcopy
import hashlib

from ..graphs.base import WorkflowState, WorkflowType

logger = logging.getLogger(__name__)


class StateStatus(str, Enum):
    """State lifecycle status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"
    ARCHIVED = "archived"


class StatePersistenceLevel(str, Enum):
    """State persistence levels"""
    MEMORY_ONLY = "memory_only"
    REDIS_CACHED = "redis_cached"
    DATABASE_PERSISTED = "database_persisted"


@dataclass
class StateSnapshot:
    """Immutable snapshot of workflow state"""
    snapshot_id: str
    workflow_id: str
    timestamp: datetime
    state_data: Dict[str, Any]
    state_hash: str
    checkpoint_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateRecoveryPoint:
    """Recovery point for workflow state"""
    recovery_id: str
    workflow_id: str
    timestamp: datetime
    snapshot: StateSnapshot
    recovery_reason: str
    can_recover: bool = True
    recovery_metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowStateManager:
    """
    Centralized state management for workflow isolation with:
    - State snapshots and checkpointing
    - Recovery mechanisms
    - State persistence and cleanup
    - Isolation between workflow instances
    - Concurrent access protection
    """
    
    def __init__(self, persistence_level: StatePersistenceLevel = StatePersistenceLevel.MEMORY_ONLY):
        self.persistence_level = persistence_level
        
        # Active state storage
        self.active_states: Dict[str, WorkflowState] = {}
        self.state_metadata: Dict[str, Dict[str, Any]] = {}
        self.state_locks: Dict[str, asyncio.Lock] = {}
        
        # Snapshot storage
        self.snapshots: Dict[str, List[StateSnapshot]] = {}
        self.recovery_points: Dict[str, List[StateRecoveryPoint]] = {}
        
        # State lifecycle tracking
        self.state_status: Dict[str, StateStatus] = {}
        self.state_watchers: Dict[str, Set[Callable]] = {}
        
        # Cleanup configuration
        self.max_snapshots_per_workflow = 10
        self.snapshot_retention_hours = 24
        self.cleanup_interval = 3600  # 1 hour
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    async def create_isolated_state(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        user_id: str,
        initial_data: Dict[str, Any],
        persistence_level: Optional[StatePersistenceLevel] = None
    ) -> WorkflowState:
        """Create new isolated workflow state"""
        
        async with self._get_state_lock(workflow_id):
            if workflow_id in self.active_states:
                logger.warning(
                    f"Workflow state {workflow_id} already exists",
                    extra={"workflow_id": workflow_id}
                )
                return self.active_states[workflow_id]
            
            # Create initial state
            state = WorkflowState(
                user_id=user_id,
                request_id=initial_data.get("request_id", workflow_id),
                workflow_type=workflow_type.value,
                input_data=initial_data.get("input_data", {}),
                output_data=None,
                user_context=initial_data.get("user_context", {}),
                connected_accounts=initial_data.get("connected_accounts", {}),
                current_node="",
                visited_nodes=[],
                execution_start=datetime.utcnow(),
                error=None,
                retry_count=0,
                trace_id=workflow_id,
                metrics={},
                search_data=None,
                email_data=None,
                structured_output=None,
                requires_feedback=False,
                feedback_request=None,
                follow_up_context=None
            )
            
            # Store state
            self.active_states[workflow_id] = state
            self.state_status[workflow_id] = StateStatus.INITIALIZING
            
            # Initialize metadata
            self.state_metadata[workflow_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "workflow_type": workflow_type.value,
                "user_id": user_id,
                "persistence_level": (persistence_level or self.persistence_level).value,
                "snapshots_taken": 0,
                "last_accessed": datetime.utcnow().isoformat()
            }
            
            # Create initial snapshot
            await self._create_snapshot(workflow_id, "initial_state")
            
            logger.info(
                f"Created isolated state for workflow {workflow_id}",
                extra={
                    "workflow_type": workflow_type.value,
                    "user_id": user_id,
                    "persistence": (persistence_level or self.persistence_level).value
                }
            )
            
            return deepcopy(state)
    
    async def get_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state with isolation protection"""
        async with self._get_state_lock(workflow_id):
            if workflow_id not in self.active_states:
                logger.warning(f"Workflow state {workflow_id} not found")
                return None
            
            # Update access tracking
            self.state_metadata[workflow_id]["last_accessed"] = datetime.utcnow().isoformat()
            
            # Return deep copy to maintain isolation
            return deepcopy(self.active_states[workflow_id])
    
    async def update_state(
        self,
        workflow_id: str,
        state_updates: Dict[str, Any],
        checkpoint_name: Optional[str] = None
    ) -> bool:
        """Update workflow state with automatic snapshotting"""
        async with self._get_state_lock(workflow_id):
            if workflow_id not in self.active_states:
                logger.error(f"Cannot update non-existent workflow state {workflow_id}")
                return False
            
            # Get current state
            current_state = self.active_states[workflow_id]
            
            # Create pre-update snapshot if this is a significant update
            if checkpoint_name or self._is_significant_update(state_updates):
                await self._create_snapshot(
                    workflow_id,
                    checkpoint_name or f"pre_update_{datetime.utcnow().strftime('%H%M%S')}"
                )
            
            # Apply updates
            for key, value in state_updates.items():
                if key in current_state:
                    current_state[key] = value
                else:
                    logger.warning(
                        f"Attempting to update non-existent key '{key}' in state",
                        extra={"workflow_id": workflow_id}
                    )
            
            # Update metadata
            self.state_metadata[workflow_id]["last_updated"] = datetime.utcnow().isoformat()
            self.state_metadata[workflow_id]["last_accessed"] = datetime.utcnow().isoformat()
            
            # Update status if needed
            if "error" in state_updates and state_updates["error"]:
                self.state_status[workflow_id] = StateStatus.FAILED
            elif "output_data" in state_updates and state_updates["output_data"]:
                if current_state.get("current_node") == "response":
                    self.state_status[workflow_id] = StateStatus.COMPLETED
                else:
                    self.state_status[workflow_id] = StateStatus.ACTIVE
            
            # Notify watchers
            await self._notify_state_watchers(workflow_id, "updated", state_updates)
            
            logger.debug(
                f"Updated state for workflow {workflow_id}",
                extra={
                    "updated_keys": list(state_updates.keys()),
                    "checkpoint": checkpoint_name
                }
            )
            
            return True
    
    async def create_checkpoint(self, workflow_id: str, checkpoint_name: str) -> bool:
        """Create named checkpoint for state recovery"""
        async with self._get_state_lock(workflow_id):
            if workflow_id not in self.active_states:
                logger.error(f"Cannot checkpoint non-existent workflow state {workflow_id}")
                return False
            
            snapshot = await self._create_snapshot(workflow_id, checkpoint_name)
            
            if snapshot:
                # Create recovery point
                recovery_point = StateRecoveryPoint(
                    recovery_id=f"{workflow_id}_{checkpoint_name}_{datetime.utcnow().timestamp()}",
                    workflow_id=workflow_id,
                    timestamp=datetime.utcnow(),
                    snapshot=snapshot,
                    recovery_reason=f"Manual checkpoint: {checkpoint_name}"
                )
                
                if workflow_id not in self.recovery_points:
                    self.recovery_points[workflow_id] = []
                
                self.recovery_points[workflow_id].append(recovery_point)
                
                logger.info(
                    f"Created checkpoint '{checkpoint_name}' for workflow {workflow_id}",
                    extra={"workflow_id": workflow_id, "checkpoint": checkpoint_name}
                )
                
                return True
            
            return False
    
    async def recover_from_checkpoint(
        self,
        workflow_id: str,
        checkpoint_name: Optional[str] = None
    ) -> bool:
        """Recover workflow state from checkpoint"""
        async with self._get_state_lock(workflow_id):
            recovery_points = self.recovery_points.get(workflow_id, [])
            
            if not recovery_points:
                logger.error(
                    f"No recovery points available for workflow {workflow_id}",
                    extra={"workflow_id": workflow_id}
                )
                return False
            
            # Find recovery point
            recovery_point = None
            if checkpoint_name:
                # Look for specific checkpoint
                recovery_point = next(
                    (rp for rp in recovery_points 
                     if rp.snapshot.checkpoint_name == checkpoint_name),
                    None
                )
            else:
                # Use most recent recovery point
                recovery_point = max(recovery_points, key=lambda rp: rp.timestamp)
            
            if not recovery_point or not recovery_point.can_recover:
                logger.error(
                    f"No valid recovery point found for workflow {workflow_id}",
                    extra={
                        "workflow_id": workflow_id,
                        "checkpoint_name": checkpoint_name,
                        "available_checkpoints": [rp.snapshot.checkpoint_name for rp in recovery_points]
                    }
                )
                return False
            
            # Restore state from snapshot
            restored_state = deepcopy(recovery_point.snapshot.state_data)
            self.active_states[workflow_id] = restored_state
            self.state_status[workflow_id] = StateStatus.RECOVERED
            
            # Update metadata
            self.state_metadata[workflow_id].update({
                "recovered_at": datetime.utcnow().isoformat(),
                "recovered_from": recovery_point.snapshot.checkpoint_name or "latest",
                "recovery_reason": recovery_point.recovery_reason
            })
            
            # Notify watchers
            await self._notify_state_watchers(workflow_id, "recovered", {
                "recovery_point": recovery_point.recovery_id,
                "checkpoint": recovery_point.snapshot.checkpoint_name
            })
            
            logger.info(
                f"Recovered workflow {workflow_id} from checkpoint",
                extra={
                    "workflow_id": workflow_id,
                    "checkpoint": recovery_point.snapshot.checkpoint_name,
                    "recovery_time": recovery_point.timestamp.isoformat()
                }
            )
            
            return True
    
    async def suspend_state(self, workflow_id: str, reason: str = "Manual suspension") -> bool:
        """Suspend workflow state for later resumption"""
        async with self._get_state_lock(workflow_id):
            if workflow_id not in self.active_states:
                return False
            
            # Create suspension snapshot
            snapshot = await self._create_snapshot(workflow_id, f"suspension_{datetime.utcnow().timestamp()}")
            
            if snapshot:
                self.state_status[workflow_id] = StateStatus.SUSPENDED
                self.state_metadata[workflow_id].update({
                    "suspended_at": datetime.utcnow().isoformat(),
                    "suspension_reason": reason
                })
                
                # Notify watchers
                await self._notify_state_watchers(workflow_id, "suspended", {"reason": reason})
                
                logger.info(
                    f"Suspended workflow {workflow_id}: {reason}",
                    extra={"workflow_id": workflow_id}
                )
                
                return True
            
            return False
    
    async def resume_state(self, workflow_id: str) -> bool:
        """Resume suspended workflow state"""
        async with self._get_state_lock(workflow_id):
            if workflow_id not in self.active_states:
                return False
            
            if self.state_status[workflow_id] != StateStatus.SUSPENDED:
                logger.warning(
                    f"Cannot resume workflow {workflow_id} - not suspended (status: {self.state_status[workflow_id]})"
                )
                return False
            
            self.state_status[workflow_id] = StateStatus.ACTIVE
            self.state_metadata[workflow_id].update({
                "resumed_at": datetime.utcnow().isoformat()
            })
            
            # Notify watchers
            await self._notify_state_watchers(workflow_id, "resumed", {})
            
            logger.info(
                f"Resumed workflow {workflow_id}",
                extra={"workflow_id": workflow_id}
            )
            
            return True
    
    async def complete_state(self, workflow_id: str, final_output: Dict[str, Any]) -> bool:
        """Mark workflow state as completed"""
        async with self._get_state_lock(workflow_id):
            if workflow_id not in self.active_states:
                return False
            
            # Update state with final output
            self.active_states[workflow_id]["output_data"] = final_output
            self.state_status[workflow_id] = StateStatus.COMPLETED
            
            # Create completion snapshot
            await self._create_snapshot(workflow_id, "completion")
            
            # Update metadata
            self.state_metadata[workflow_id].update({
                "completed_at": datetime.utcnow().isoformat(),
                "execution_time": (
                    datetime.utcnow() - datetime.fromisoformat(
                        self.state_metadata[workflow_id]["created_at"]
                    )
                ).total_seconds()
            })
            
            # Notify watchers
            await self._notify_state_watchers(workflow_id, "completed", final_output)
            
            logger.info(
                f"Completed workflow {workflow_id}",
                extra={
                    "workflow_id": workflow_id,
                    "execution_time": self.state_metadata[workflow_id]["execution_time"]
                }
            )
            
            return True
    
    async def archive_state(self, workflow_id: str) -> bool:
        """Archive completed workflow state"""
        async with self._get_state_lock(workflow_id):
            if workflow_id not in self.active_states:
                return False
            
            # Create final snapshot before archiving
            await self._create_snapshot(workflow_id, "archive")
            
            # Update status and metadata
            self.state_status[workflow_id] = StateStatus.ARCHIVED
            self.state_metadata[workflow_id]["archived_at"] = datetime.utcnow().isoformat()
            
            # Remove from active states (keep metadata and snapshots)
            del self.active_states[workflow_id]
            
            # Notify watchers
            await self._notify_state_watchers(workflow_id, "archived", {})
            
            logger.info(f"Archived workflow {workflow_id}")
            return True
    
    def register_state_watcher(self, workflow_id: str, callback: Callable) -> bool:
        """Register callback for state change notifications"""
        if workflow_id not in self.state_watchers:
            self.state_watchers[workflow_id] = set()
        
        self.state_watchers[workflow_id].add(callback)
        return True
    
    def get_state_metrics(self) -> Dict[str, Any]:
        """Get state management metrics"""
        total_snapshots = sum(len(snapshots) for snapshots in self.snapshots.values())
        total_recovery_points = sum(len(points) for points in self.recovery_points.values())
        
        status_counts = {}
        for status in self.state_status.values():
            status_counts[status.value] = status_counts.get(status.value, 0) + 1
        
        return {
            "active_states": len(self.active_states),
            "total_workflows": len(self.state_metadata),
            "total_snapshots": total_snapshots,
            "total_recovery_points": total_recovery_points,
            "status_breakdown": status_counts,
            "memory_usage": {
                "states": len(self.active_states),
                "snapshots": total_snapshots,
                "locks": len(self.state_locks)
            }
        }
    
    def _get_state_lock(self, workflow_id: str) -> asyncio.Lock:
        """Get or create lock for workflow state"""
        if workflow_id not in self.state_locks:
            self.state_locks[workflow_id] = asyncio.Lock()
        return self.state_locks[workflow_id]
    
    async def _create_snapshot(
        self,
        workflow_id: str,
        checkpoint_name: Optional[str] = None
    ) -> Optional[StateSnapshot]:
        """Create state snapshot"""
        if workflow_id not in self.active_states:
            return None
        
        state_data = deepcopy(self.active_states[workflow_id])
        state_hash = self._compute_state_hash(state_data)
        
        snapshot = StateSnapshot(
            snapshot_id=f"{workflow_id}_{datetime.utcnow().timestamp()}",
            workflow_id=workflow_id,
            timestamp=datetime.utcnow(),
            state_data=state_data,
            state_hash=state_hash,
            checkpoint_name=checkpoint_name,
            metadata={
                "snapshot_reason": checkpoint_name or "automatic",
                "state_size": len(json.dumps(state_data, default=str))
            }
        )
        
        # Store snapshot
        if workflow_id not in self.snapshots:
            self.snapshots[workflow_id] = []
        
        self.snapshots[workflow_id].append(snapshot)
        
        # Limit snapshots per workflow
        if len(self.snapshots[workflow_id]) > self.max_snapshots_per_workflow:
            removed = self.snapshots[workflow_id].pop(0)
            logger.debug(f"Removed old snapshot {removed.snapshot_id}")
        
        # Update metadata
        self.state_metadata[workflow_id]["snapshots_taken"] += 1
        self.state_metadata[workflow_id]["last_snapshot"] = snapshot.timestamp.isoformat()
        
        return snapshot
    
    def _compute_state_hash(self, state_data: Dict[str, Any]) -> str:
        """Compute hash of state data for change detection"""
        state_json = json.dumps(state_data, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()
    
    def _is_significant_update(self, updates: Dict[str, Any]) -> bool:
        """Determine if state update is significant enough for snapshotting"""
        significant_keys = {
            "current_node",
            "output_data",
            "error",
            "structured_output"
        }
        
        return bool(set(updates.keys()) & significant_keys)
    
    async def _notify_state_watchers(
        self,
        workflow_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Notify registered state watchers"""
        watchers = self.state_watchers.get(workflow_id, set())
        
        for callback in watchers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(workflow_id, event_type, event_data)
                else:
                    callback(workflow_id, event_type, event_data)
            except Exception as e:
                logger.error(
                    f"Error in state watcher callback: {str(e)}",
                    extra={"workflow_id": workflow_id, "event_type": event_type}
                )
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old snapshots and states"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_data()
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")
    
    async def _cleanup_old_data(self):
        """Clean up old snapshots and archived states"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.snapshot_retention_hours)
        
        # Clean up old snapshots
        for workflow_id, snapshots in list(self.snapshots.items()):
            initial_count = len(snapshots)
            
            # Keep recent snapshots and named checkpoints
            self.snapshots[workflow_id] = [
                snapshot for snapshot in snapshots
                if (snapshot.timestamp > cutoff_time or 
                    snapshot.checkpoint_name and snapshot.checkpoint_name != "automatic")
            ]
            
            removed_count = initial_count - len(self.snapshots[workflow_id])
            if removed_count > 0:
                logger.debug(
                    f"Cleaned up {removed_count} old snapshots for workflow {workflow_id}"
                )
        
        # Clean up old recovery points
        for workflow_id, recovery_points in list(self.recovery_points.items()):
            initial_count = len(recovery_points)
            
            self.recovery_points[workflow_id] = [
                rp for rp in recovery_points
                if rp.timestamp > cutoff_time
            ]
            
            removed_count = initial_count - len(self.recovery_points[workflow_id])
            if removed_count > 0:
                logger.debug(
                    f"Cleaned up {removed_count} old recovery points for workflow {workflow_id}"
                )
        
        # Clean up archived state metadata
        archived_workflows = [
            workflow_id for workflow_id, status in self.state_status.items()
            if status == StateStatus.ARCHIVED
        ]
        
        for workflow_id in archived_workflows:
            created_at = datetime.fromisoformat(self.state_metadata[workflow_id]["created_at"])
            if created_at < cutoff_time:
                # Remove all data for old archived workflows
                self.state_metadata.pop(workflow_id, None)
                self.state_status.pop(workflow_id, None)
                self.snapshots.pop(workflow_id, None)
                self.recovery_points.pop(workflow_id, None)
                self.state_locks.pop(workflow_id, None)
                self.state_watchers.pop(workflow_id, None)
                
                logger.debug(f"Cleaned up archived workflow {workflow_id}")


# Global state manager instance
workflow_state_manager = WorkflowStateManager()