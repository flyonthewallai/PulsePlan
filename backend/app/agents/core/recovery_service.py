"""
Workflow Recovery Service
Provides automated recovery mechanisms for failed workflows using state snapshots and error analysis
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json

from .state_manager import workflow_state_manager, StateStatus, StateSnapshot
from .error_boundary import workflow_error_boundary, ErrorSeverity, RecoveryStrategy
from ..graphs.base import WorkflowState, WorkflowError, WorkflowType

logger = logging.getLogger(__name__)


class RecoveryTrigger(str, Enum):
    """Types of recovery triggers"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    ERROR_THRESHOLD = "error_threshold"
    TIMEOUT = "timeout"


class RecoveryStatus(str, Enum):
    """Recovery attempt status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt"""
    attempt_id: str
    workflow_id: str
    trigger: RecoveryTrigger
    strategy: RecoveryStrategy
    timestamp: datetime
    status: RecoveryStatus
    original_error: Optional[str] = None
    recovery_checkpoint: Optional[str] = None
    result_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class WorkflowRecoveryService:
    """
    Service for automated workflow recovery with:
    - Intelligent recovery strategy selection
    - Automated retry with state restoration
    - Recovery attempt tracking and metrics
    - Custom recovery handlers
    - Recovery scheduling and batching
    """
    
    def __init__(self):
        self.recovery_attempts: Dict[str, List[RecoveryAttempt]] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        self.recovery_policies: Dict[str, Dict[str, Any]] = {}
        self.active_recoveries: Set[str] = set()
        
        # Configuration
        self.max_recovery_attempts = 3
        self.recovery_timeout = 300  # 5 minutes
        self.batch_recovery_delay = 30  # 30 seconds
        self.error_analysis_window = 300  # 5 minutes
        
        # Recovery scheduling
        self.scheduled_recoveries: Dict[str, datetime] = {}
        self.recovery_scheduler_task = None
        
        # Start recovery scheduler
        self._start_recovery_scheduler()
    
    async def attempt_recovery(
        self,
        workflow_id: str,
        trigger: RecoveryTrigger = RecoveryTrigger.MANUAL,
        specific_checkpoint: Optional[str] = None,
        custom_strategy: Optional[RecoveryStrategy] = None
    ) -> RecoveryAttempt:
        """
        Attempt to recover a failed workflow
        """
        if workflow_id in self.active_recoveries:
            logger.warning(
                f"Recovery already in progress for workflow {workflow_id}",
                extra={"workflow_id": workflow_id}
            )
            # Return latest attempt
            return self.recovery_attempts[workflow_id][-1] if workflow_id in self.recovery_attempts else None
        
        # Create recovery attempt record
        attempt = RecoveryAttempt(
            attempt_id=f"{workflow_id}_recovery_{datetime.utcnow().timestamp()}",
            workflow_id=workflow_id,
            trigger=trigger,
            strategy=custom_strategy or await self._determine_recovery_strategy(workflow_id),
            timestamp=datetime.utcnow(),
            status=RecoveryStatus.PENDING,
            metadata={"specific_checkpoint": specific_checkpoint}
        )
        
        # Track attempt
        if workflow_id not in self.recovery_attempts:
            self.recovery_attempts[workflow_id] = []
        self.recovery_attempts[workflow_id].append(attempt)
        
        # Mark as active
        self.active_recoveries.add(workflow_id)
        
        try:
            logger.info(
                f"Starting recovery attempt for workflow {workflow_id}",
                extra={
                    "workflow_id": workflow_id,
                    "strategy": attempt.strategy.value,
                    "trigger": trigger.value,
                    "attempt_id": attempt.attempt_id
                }
            )
            
            attempt.status = RecoveryStatus.IN_PROGRESS
            
            # Execute recovery based on strategy
            success = await self._execute_recovery_strategy(
                attempt,
                specific_checkpoint
            )
            
            if success:
                attempt.status = RecoveryStatus.SUCCESS
                attempt.result_message = "Recovery completed successfully"
                
                logger.info(
                    f"Successfully recovered workflow {workflow_id}",
                    extra={
                        "workflow_id": workflow_id,
                        "attempt_id": attempt.attempt_id,
                        "strategy": attempt.strategy.value
                    }
                )
            else:
                attempt.status = RecoveryStatus.FAILURE
                attempt.result_message = "Recovery strategy failed to restore workflow"
                
                logger.error(
                    f"Failed to recover workflow {workflow_id}",
                    extra={
                        "workflow_id": workflow_id,
                        "attempt_id": attempt.attempt_id,
                        "strategy": attempt.strategy.value
                    }
                )
                
                # Schedule retry if applicable
                await self._schedule_retry_recovery(workflow_id, attempt)
            
        except Exception as e:
            attempt.status = RecoveryStatus.FAILURE
            attempt.result_message = f"Recovery attempt failed with error: {str(e)}"
            
            logger.error(
                f"Recovery attempt failed for workflow {workflow_id}: {str(e)}",
                extra={
                    "workflow_id": workflow_id,
                    "attempt_id": attempt.attempt_id,
                    "error": str(e)
                }
            )
        
        finally:
            # Remove from active recoveries
            self.active_recoveries.discard(workflow_id)
        
        return attempt
    
    async def schedule_recovery(
        self,
        workflow_id: str,
        delay_seconds: int,
        trigger: RecoveryTrigger = RecoveryTrigger.SCHEDULED
    ) -> bool:
        """Schedule workflow recovery for future execution"""
        
        recovery_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        self.scheduled_recoveries[workflow_id] = recovery_time
        
        logger.info(
            f"Scheduled recovery for workflow {workflow_id} at {recovery_time.isoformat()}",
            extra={
                "workflow_id": workflow_id,
                "delay_seconds": delay_seconds,
                "recovery_time": recovery_time.isoformat()
            }
        )
        
        return True
    
    async def batch_recover_failed_workflows(
        self,
        max_workflows: int = 10,
        error_threshold_minutes: int = 5
    ) -> List[RecoveryAttempt]:
        """Batch recover multiple failed workflows"""
        
        # Find failed workflows that haven't been recently attempted
        cutoff_time = datetime.utcnow() - timedelta(minutes=error_threshold_minutes)
        
        failed_workflows = []
        for workflow_id, status in workflow_state_manager.state_status.items():
            if status == StateStatus.FAILED and workflow_id not in self.active_recoveries:
                # Check if we haven't attempted recovery recently
                recent_attempts = [
                    attempt for attempt in self.recovery_attempts.get(workflow_id, [])
                    if attempt.timestamp > cutoff_time
                ]
                
                if not recent_attempts or len(recent_attempts) < self.max_recovery_attempts:
                    failed_workflows.append(workflow_id)
        
        # Limit to max workflows
        failed_workflows = failed_workflows[:max_workflows]
        
        if not failed_workflows:
            logger.info("No failed workflows found for batch recovery")
            return []
        
        logger.info(
            f"Starting batch recovery for {len(failed_workflows)} workflows",
            extra={"workflow_count": len(failed_workflows)}
        )
        
        # Execute recoveries with delays to prevent overwhelming
        recovery_attempts = []
        for i, workflow_id in enumerate(failed_workflows):
            if i > 0:
                await asyncio.sleep(self.batch_recovery_delay)
            
            attempt = await self.attempt_recovery(
                workflow_id,
                trigger=RecoveryTrigger.AUTOMATIC
            )
            recovery_attempts.append(attempt)
        
        return recovery_attempts
    
    async def analyze_recovery_patterns(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze recovery patterns and success rates"""
        
        if workflow_id:
            attempts = self.recovery_attempts.get(workflow_id, [])
        else:
            attempts = []
            for workflow_attempts in self.recovery_attempts.values():
                attempts.extend(workflow_attempts)
        
        if not attempts:
            return {"message": "No recovery attempts found"}
        
        # Analyze patterns
        total_attempts = len(attempts)
        successful_attempts = len([a for a in attempts if a.status == RecoveryStatus.SUCCESS])
        failed_attempts = len([a for a in attempts if a.status == RecoveryStatus.FAILURE])
        
        success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0
        
        # Strategy effectiveness
        strategy_stats = {}
        for attempt in attempts:
            strategy = attempt.strategy.value
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"total": 0, "successful": 0}
            
            strategy_stats[strategy]["total"] += 1
            if attempt.status == RecoveryStatus.SUCCESS:
                strategy_stats[strategy]["successful"] += 1
        
        # Calculate strategy success rates
        for strategy, stats in strategy_stats.items():
            stats["success_rate"] = (stats["successful"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        
        # Trigger analysis
        trigger_stats = {}
        for attempt in attempts:
            trigger = attempt.trigger.value
            trigger_stats[trigger] = trigger_stats.get(trigger, 0) + 1
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": round(success_rate, 2),
            "strategy_effectiveness": strategy_stats,
            "trigger_breakdown": trigger_stats,
            "analysis_period": {
                "start": min(attempts, key=lambda a: a.timestamp).timestamp.isoformat(),
                "end": max(attempts, key=lambda a: a.timestamp).timestamp.isoformat()
            }
        }
    
    def register_recovery_handler(
        self,
        workflow_type: str,
        handler: Callable[[str, Dict[str, Any]], bool]
    ):
        """Register custom recovery handler for workflow type"""
        
        self.recovery_handlers[workflow_type] = handler
        
        logger.info(
            f"Registered custom recovery handler for {workflow_type}",
            extra={"workflow_type": workflow_type}
        )
    
    def set_recovery_policy(
        self,
        workflow_type: str,
        policy: Dict[str, Any]
    ):
        """Set recovery policy for workflow type"""
        
        self.recovery_policies[workflow_type] = policy
        
        logger.info(
            f"Set recovery policy for {workflow_type}",
            extra={"workflow_type": workflow_type, "policy": policy}
        )
    
    async def _determine_recovery_strategy(self, workflow_id: str) -> RecoveryStrategy:
        """Determine appropriate recovery strategy for workflow"""
        
        # Get current state info
        state = await workflow_state_manager.get_state(workflow_id)
        if not state:
            return RecoveryStrategy.FAIL_FAST
        
        workflow_type = state.get("workflow_type", "unknown")
        
        # Check if we have a custom policy
        if workflow_type in self.recovery_policies:
            policy = self.recovery_policies[workflow_type]
            if "default_strategy" in policy:
                return RecoveryStrategy(policy["default_strategy"])
        
        # Analyze error history
        error_metrics = workflow_error_boundary.get_error_metrics()
        recent_errors = error_metrics.get("recent_errors", 0)
        
        # Get error info from state
        error_info = state.get("error", {})
        if error_info:
            if error_info.get("recoverable", False):
                # Check retry count
                retry_count = state.get("retry_count", 0)
                if retry_count < 2:
                    return RecoveryStrategy.RETRY
                else:
                    return RecoveryStrategy.FALLBACK
            else:
                # Non-recoverable error - try fallback or circuit break
                if recent_errors > 5:
                    return RecoveryStrategy.CIRCUIT_BREAK
                else:
                    return RecoveryStrategy.FALLBACK
        
        # Default strategy based on workflow type
        strategy_map = {
            "task": RecoveryStrategy.RETRY,
            "calendar": RecoveryStrategy.FALLBACK,
            "natural_language": RecoveryStrategy.RETRY,
            "scheduling": RecoveryStrategy.FALLBACK,
            "briefing": RecoveryStrategy.FALLBACK,
            "search": RecoveryStrategy.RETRY,
            "database": RecoveryStrategy.RETRY,
            "email": RecoveryStrategy.FALLBACK
        }
        
        return strategy_map.get(workflow_type, RecoveryStrategy.RETRY)
    
    async def _execute_recovery_strategy(
        self,
        attempt: RecoveryAttempt,
        specific_checkpoint: Optional[str] = None
    ) -> bool:
        """Execute the specific recovery strategy"""
        
        workflow_id = attempt.workflow_id
        strategy = attempt.strategy
        
        try:
            if strategy == RecoveryStrategy.RETRY:
                return await self._execute_retry_recovery(workflow_id, specific_checkpoint)
            
            elif strategy == RecoveryStrategy.FALLBACK:
                return await self._execute_fallback_recovery(workflow_id)
            
            elif strategy == RecoveryStrategy.CIRCUIT_BREAK:
                return await self._execute_circuit_break_recovery(workflow_id)
            
            elif strategy == RecoveryStrategy.ESCALATE:
                return await self._execute_escalation_recovery(workflow_id)
            
            else:
                logger.warning(
                    f"Unknown recovery strategy: {strategy}",
                    extra={"workflow_id": workflow_id, "strategy": strategy.value}
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Recovery strategy execution failed: {str(e)}",
                extra={
                    "workflow_id": workflow_id,
                    "strategy": strategy.value,
                    "error": str(e)
                }
            )
            return False
    
    async def _execute_retry_recovery(
        self,
        workflow_id: str,
        specific_checkpoint: Optional[str] = None
    ) -> bool:
        """Execute retry-based recovery"""
        
        # Try to recover from checkpoint
        if specific_checkpoint:
            success = await workflow_state_manager.recover_from_checkpoint(
                workflow_id, specific_checkpoint
            )
        else:
            # Try to recover from latest valid checkpoint
            success = await workflow_state_manager.recover_from_checkpoint(workflow_id)
        
        if success:
            # Resume the workflow
            await workflow_state_manager.resume_state(workflow_id)
            
            logger.info(
                f"Successfully restored workflow {workflow_id} from checkpoint",
                extra={"workflow_id": workflow_id, "checkpoint": specific_checkpoint}
            )
            
            return True
        
        return False
    
    async def _execute_fallback_recovery(self, workflow_id: str) -> bool:
        """Execute fallback-based recovery"""
        
        # Get workflow state and type
        state = await workflow_state_manager.get_state(workflow_id)
        if not state:
            return False
        
        workflow_type = state.get("workflow_type", "unknown")
        
        # Try custom recovery handler first
        if workflow_type in self.recovery_handlers:
            try:
                handler = self.recovery_handlers[workflow_type]
                result = await handler(workflow_id, state)
                
                if result:
                    logger.info(
                        f"Custom recovery handler succeeded for workflow {workflow_id}",
                        extra={"workflow_id": workflow_id, "workflow_type": workflow_type}
                    )
                    return True
                    
            except Exception as e:
                logger.error(
                    f"Custom recovery handler failed: {str(e)}",
                    extra={"workflow_id": workflow_id, "workflow_type": workflow_type}
                )
        
        # Default fallback: create minimal success state
        fallback_output = {
            "success": True,
            "recovered": True,
            "recovery_method": "fallback",
            "message": "Workflow recovered using fallback mechanism",
            "partial_results": state.get("output_data", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update state to completed with fallback results
        await workflow_state_manager.complete_state(workflow_id, fallback_output)
        
        logger.info(
            f"Applied fallback recovery for workflow {workflow_id}",
            extra={"workflow_id": workflow_id}
        )
        
        return True
    
    async def _execute_circuit_break_recovery(self, workflow_id: str) -> bool:
        """Execute circuit breaker recovery"""
        
        # Suspend the workflow to prevent further attempts
        await workflow_state_manager.suspend_state(
            workflow_id,
            "Circuit breaker activated - suspended for recovery"
        )
        
        # Schedule recovery for later when circuit might be closed
        await self.schedule_recovery(
            workflow_id,
            delay_seconds=300,  # 5 minutes
            trigger=RecoveryTrigger.SCHEDULED
        )
        
        logger.info(
            f"Applied circuit breaker recovery for workflow {workflow_id}",
            extra={"workflow_id": workflow_id}
        )
        
        return True
    
    async def _execute_escalation_recovery(self, workflow_id: str) -> bool:
        """Execute escalation recovery"""
        
        # Mark for manual intervention
        state = await workflow_state_manager.get_state(workflow_id)
        if not state:
            return False
        
        escalation_data = {
            "escalated": True,
            "escalation_reason": "Automated recovery failed multiple times",
            "requires_manual_intervention": True,
            "escalation_timestamp": datetime.utcnow().isoformat(),
            "original_error": state.get("error", {}),
            "recovery_attempts": len(self.recovery_attempts.get(workflow_id, []))
        }
        
        # Update state with escalation info
        await workflow_state_manager.update_state(workflow_id, {
            "output_data": escalation_data,
            "requires_feedback": True,
            "feedback_request": {
                "type": "manual_recovery",
                "message": "This workflow requires manual intervention to resolve",
                "escalation_info": escalation_data
            }
        })
        
        logger.warning(
            f"Escalated workflow {workflow_id} for manual intervention",
            extra={"workflow_id": workflow_id}
        )
        
        return True
    
    async def _schedule_retry_recovery(
        self,
        workflow_id: str,
        failed_attempt: RecoveryAttempt
    ):
        """Schedule retry recovery based on attempt history"""
        
        attempts = self.recovery_attempts.get(workflow_id, [])
        attempt_count = len(attempts)
        
        if attempt_count < self.max_recovery_attempts:
            # Calculate exponential backoff delay
            delay = min(30 * (2 ** attempt_count), 300)  # Cap at 5 minutes
            
            await self.schedule_recovery(
                workflow_id,
                delay_seconds=delay,
                trigger=RecoveryTrigger.AUTOMATIC
            )
            
            logger.info(
                f"Scheduled retry recovery for workflow {workflow_id} in {delay}s",
                extra={
                    "workflow_id": workflow_id,
                    "attempt_count": attempt_count,
                    "delay": delay
                }
            )
    
    def _start_recovery_scheduler(self):
        """Start the recovery scheduler task"""
        if self.recovery_scheduler_task is None:
            self.recovery_scheduler_task = asyncio.create_task(self._recovery_scheduler_loop())
    
    async def _recovery_scheduler_loop(self):
        """Main loop for scheduled recovery execution"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                current_time = datetime.utcnow()
                
                # Find workflows ready for recovery
                ready_recoveries = []
                for workflow_id, recovery_time in list(self.scheduled_recoveries.items()):
                    if current_time >= recovery_time:
                        ready_recoveries.append(workflow_id)
                        del self.scheduled_recoveries[workflow_id]
                
                # Execute scheduled recoveries
                for workflow_id in ready_recoveries:
                    if workflow_id not in self.active_recoveries:
                        asyncio.create_task(self.attempt_recovery(
                            workflow_id,
                            trigger=RecoveryTrigger.SCHEDULED
                        ))
                
            except Exception as e:
                logger.error(f"Error in recovery scheduler: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def get_recovery_metrics(self) -> Dict[str, Any]:
        """Get comprehensive recovery service metrics"""
        
        total_attempts = sum(len(attempts) for attempts in self.recovery_attempts.values())
        
        if total_attempts == 0:
            return {
                "total_attempts": 0,
                "active_recoveries": len(self.active_recoveries),
                "scheduled_recoveries": len(self.scheduled_recoveries)
            }
        
        # Calculate success rates
        all_attempts = []
        for attempts in self.recovery_attempts.values():
            all_attempts.extend(attempts)
        
        successful = len([a for a in all_attempts if a.status == RecoveryStatus.SUCCESS])
        success_rate = (successful / total_attempts) * 100
        
        return {
            "total_attempts": total_attempts,
            "successful_recoveries": successful,
            "success_rate": round(success_rate, 2),
            "active_recoveries": len(self.active_recoveries),
            "scheduled_recoveries": len(self.scheduled_recoveries),
            "registered_handlers": len(self.recovery_handlers),
            "recovery_policies": len(self.recovery_policies),
            "workflows_with_attempts": len(self.recovery_attempts)
        }


# Global recovery service instance
workflow_recovery_service = WorkflowRecoveryService()