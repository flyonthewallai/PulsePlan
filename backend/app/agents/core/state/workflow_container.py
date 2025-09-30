"""
Workflow Isolation Container
Provides isolated execution environment for workflows with error boundaries and resource management
"""
import asyncio
import logging
import traceback
from typing import Any, Dict, Optional, Callable, Type, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field

from ...graphs.base import BaseWorkflow, WorkflowState, WorkflowError, WorkflowType

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResourceLimits:
    """Resource limits for workflow execution"""
    max_execution_time: float = 300.0  # 5 minutes default
    max_memory_mb: int = 512
    max_concurrent_tools: int = 10
    max_retry_attempts: int = 3
    backoff_multiplier: float = 2.0


@dataclass
class WorkflowExecutionContext:
    """Execution context for workflow isolation"""
    workflow_id: str
    user_id: str
    workflow_type: WorkflowType
    resource_limits: WorkflowResourceLimits
    start_time: datetime = field(default_factory=datetime.utcnow)
    active_tools: List[str] = field(default_factory=list)
    memory_usage: int = 0
    execution_metrics: Dict[str, Any] = field(default_factory=dict)


class WorkflowIsolationError(Exception):
    """Error raised when workflow isolation is violated"""
    pass


class WorkflowTimeoutError(Exception):
    """Error raised when workflow execution times out"""
    pass


class WorkflowContainer:
    """
    Isolated container for workflow execution with:
    - Resource limits and monitoring
    - Error boundaries and recovery
    - Timeout and cancellation handling
    - State isolation and cleanup
    """
    
    def __init__(
        self,
        workflow_class: Type[BaseWorkflow],
        resource_limits: Optional[WorkflowResourceLimits] = None
    ):
        self.workflow_class = workflow_class
        self.resource_limits = resource_limits or WorkflowResourceLimits()
        self.execution_context: Optional[WorkflowExecutionContext] = None
        self.task: Optional[asyncio.Task] = None
        self.cancelled = False
        
    @asynccontextmanager
    async def isolated_execution(self, state: WorkflowState):
        """Context manager for isolated workflow execution"""
        # Create execution context
        self.execution_context = WorkflowExecutionContext(
            workflow_id=state.get("trace_id", "unknown"),
            user_id=state.get("user_id", "unknown"),
            workflow_type=WorkflowType(state.get("workflow_type", "unknown")),
            resource_limits=self.resource_limits
        )
        
        logger.info(
            f"Starting isolated execution for workflow {self.execution_context.workflow_id}",
            extra={
                "workflow_type": self.execution_context.workflow_type.value,
                "user_id": self.execution_context.user_id,
                "limits": {
                    "max_time": self.resource_limits.max_execution_time,
                    "max_memory": self.resource_limits.max_memory_mb
                }
            }
        )
        
        try:
            # Set up resource monitoring
            await self._setup_resource_monitoring()
            
            # Initialize workflow instance in isolated context
            workflow_instance = self.workflow_class()
            
            yield workflow_instance
            
        except Exception as e:
            logger.error(
                f"Error in isolated execution context: {str(e)}",
                extra={
                    "workflow_id": self.execution_context.workflow_id,
                    "traceback": traceback.format_exc()
                }
            )
            # Add detailed debugging for len() errors
            if "object of type 'NoneType' has no len()" in str(e):
                logger.error(f"NoneType len() error - Full stack trace: {traceback.format_exc()}")
            raise
        finally:
            # Clean up resources
            await self._cleanup_resources()
            
            # Log execution metrics
            if self.execution_context:
                execution_time = (datetime.utcnow() - self.execution_context.start_time).total_seconds()
                logger.info(
                    f"Workflow execution completed in {execution_time:.2f}s",
                    extra={
                        "workflow_id": self.execution_context.workflow_id,
                        "execution_time": execution_time,
                        "memory_peak": self.execution_context.memory_usage,
                        "tools_used": len(self.execution_context.active_tools) if self.execution_context.active_tools else 0
                    }
                )
    
    async def execute_with_boundaries(self, initial_state: WorkflowState) -> WorkflowState:
        """
        Execute workflow with comprehensive error boundaries and isolation
        """
        try:
            async with self.isolated_execution(initial_state) as workflow:
                # Execute with timeout protection
                result = await asyncio.wait_for(
                    self._execute_with_monitoring(workflow, initial_state),
                    timeout=self.resource_limits.max_execution_time
                )
                return result
                
        except asyncio.TimeoutError:
            error_msg = f"Workflow timed out after {self.resource_limits.max_execution_time}s"
            logger.error(error_msg, extra={"workflow_id": initial_state.get("trace_id")})
            
            # Create timeout error state
            return self._create_error_state(
                initial_state,
                WorkflowTimeoutError(error_msg),
                recoverable=False
            )
            
        except WorkflowError as e:
            # Handle known workflow errors
            logger.warning(
                f"Workflow error: {e.message}",
                extra={
                    "workflow_id": initial_state.get("trace_id"),
                    "recoverable": e.recoverable,
                    "context": e.context
                }
            )
            return self._create_error_state(initial_state, e, recoverable=e.recoverable)
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected workflow error: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "workflow_id": initial_state.get("trace_id"),
                    "traceback": traceback.format_exc()
                }
            )
            
            workflow_error = WorkflowError(
                message=error_msg,
                context={"original_error": str(e), "type": type(e).__name__},
                recoverable=False
            )
            
            return self._create_error_state(initial_state, workflow_error, recoverable=False)
    
    async def _execute_with_monitoring(
        self, 
        workflow: BaseWorkflow, 
        initial_state: WorkflowState
    ) -> WorkflowState:
        """Execute workflow with resource monitoring"""
        
        # Create monitoring task
        monitor_task = asyncio.create_task(self._monitor_resources())
        
        try:
            # Execute workflow
            self.task = asyncio.create_task(workflow.execute(initial_state))
            result = await self.task
            
            # Cancel monitoring
            monitor_task.cancel()
            
            return result
            
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            logger.info(
                f"Workflow execution cancelled",
                extra={"workflow_id": initial_state.get("trace_id")}
            )
            
            # Cancel monitoring
            monitor_task.cancel()
            
            # Create cancelled state
            return self._create_error_state(
                initial_state,
                WorkflowError("Workflow cancelled", {}),
                recoverable=False
            )
        finally:
            # Ensure monitoring is cancelled
            if not monitor_task.done():
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
    
    async def _monitor_resources(self):
        """Monitor resource usage during workflow execution"""
        while not self.cancelled:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                if self.execution_context:
                    # Check execution time
                    elapsed = (datetime.utcnow() - self.execution_context.start_time).total_seconds()
                    if elapsed > self.resource_limits.max_execution_time * 0.9:  # 90% warning
                        logger.warning(
                            f"Workflow approaching timeout limit",
                            extra={
                                "workflow_id": self.execution_context.workflow_id,
                                "elapsed": elapsed,
                                "limit": self.resource_limits.max_execution_time
                            }
                        )
                    
                    # Check tool limits
                    active_tools = self.execution_context.active_tools if self.execution_context.active_tools else []
                    if len(active_tools) > self.resource_limits.max_concurrent_tools:
                        logger.warning(
                            f"Workflow exceeding concurrent tool limit",
                            extra={
                                "workflow_id": self.execution_context.workflow_id,
                                "active_tools": len(active_tools),
                                "limit": self.resource_limits.max_concurrent_tools
                            }
                        )
                        
                        # Cancel workflow if severely over limit
                        if len(active_tools) > self.resource_limits.max_concurrent_tools * 1.5:
                            await self.cancel()
                            break
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {str(e)}")
    
    async def cancel(self, reason: str = "User requested"):
        """Cancel workflow execution"""
        self.cancelled = True
        
        if self.task and not self.task.done():
            logger.info(
                f"Cancelling workflow execution: {reason}",
                extra={"workflow_id": getattr(self.execution_context, "workflow_id", "unknown")}
            )
            self.task.cancel()
    
    async def _setup_resource_monitoring(self):
        """Set up resource monitoring for the workflow"""
        # Initialize resource tracking
        if self.execution_context:
            self.execution_context.execution_metrics = {
                "start_time": datetime.utcnow().isoformat(),
                "resource_limits": {
                    "max_execution_time": self.resource_limits.max_execution_time,
                    "max_memory_mb": self.resource_limits.max_memory_mb,
                    "max_concurrent_tools": self.resource_limits.max_concurrent_tools
                }
            }
    
    async def _cleanup_resources(self):
        """Clean up workflow resources"""
        if self.execution_context:
            # Clear active tools
            if self.execution_context.active_tools:
                self.execution_context.active_tools.clear()
            
            # Record final metrics
            end_time = datetime.utcnow()
            execution_time = (end_time - self.execution_context.start_time).total_seconds()
            
            self.execution_context.execution_metrics.update({
                "end_time": end_time.isoformat(),
                "total_execution_time": execution_time,
                "peak_memory_usage": self.execution_context.memory_usage
            })
    
    def _create_error_state(
        self, 
        initial_state: WorkflowState, 
        error: Exception, 
        recoverable: bool = False
    ) -> WorkflowState:
        """Create error state for workflow failures"""
        
        error_state = initial_state.copy()
        error_state.update({
            "error": {
                "message": str(error),
                "type": type(error).__name__,
                "recoverable": recoverable,
                "timestamp": datetime.utcnow().isoformat(),
                "context": getattr(error, "context", {})
            },
            "output_data": {
                "success": False,
                "error": str(error),
                "recoverable": recoverable,
                "execution_time": (
                    datetime.utcnow() - initial_state.get("execution_start", datetime.utcnow())
                ).total_seconds()
            },
            "current_node": "error_handler",
            "visited_nodes": initial_state.get("visited_nodes", []) + ["error_handler"]
        })
        
        return error_state


class WorkflowContainerFactory:
    """Factory for creating workflow containers with appropriate isolation"""
    
    @staticmethod
    def create_container(
        workflow_class: Type[BaseWorkflow],
        workflow_type: WorkflowType,
        user_id: str,
        custom_limits: Optional[Dict[str, Any]] = None
    ) -> WorkflowContainer:
        """Create appropriately configured workflow container"""
        
        # Define workflow-specific resource limits
        limits_map = {
            WorkflowType.NATURAL_LANGUAGE: WorkflowResourceLimits(
                max_execution_time=180.0,  # 3 minutes for chat
                max_memory_mb=256,
                max_concurrent_tools=5
            ),
            WorkflowType.TASK: WorkflowResourceLimits(
                max_execution_time=120.0,  # 2 minutes for task operations
                max_memory_mb=128,
                max_concurrent_tools=3
            ),
            WorkflowType.CALENDAR: WorkflowResourceLimits(
                max_execution_time=240.0,  # 4 minutes for calendar sync
                max_memory_mb=256,
                max_concurrent_tools=5
            ),
            WorkflowType.BRIEFING: WorkflowResourceLimits(
                max_execution_time=600.0,  # 10 minutes for briefing generation
                max_memory_mb=512,
                max_concurrent_tools=8
            ),
            WorkflowType.SCHEDULING: WorkflowResourceLimits(
                max_execution_time=300.0,  # 5 minutes for scheduling
                max_memory_mb=512,
                max_concurrent_tools=6
            ),
            WorkflowType.SEARCH: WorkflowResourceLimits(
                max_execution_time=60.0,  # 1 minute for search
                max_memory_mb=128,
                max_concurrent_tools=2
            ),
            WorkflowType.EMAIL: WorkflowResourceLimits(
                max_execution_time=180.0,  # 3 minutes for email
                max_memory_mb=256,
                max_concurrent_tools=4
            )
        }
        
        # Get base limits for workflow type
        base_limits = limits_map.get(workflow_type, WorkflowResourceLimits())
        
        # Apply custom limits if provided
        if custom_limits:
            if "max_execution_time" in custom_limits:
                base_limits.max_execution_time = custom_limits["max_execution_time"]
            if "max_memory_mb" in custom_limits:
                base_limits.max_memory_mb = custom_limits["max_memory_mb"]
            if "max_concurrent_tools" in custom_limits:
                base_limits.max_concurrent_tools = custom_limits["max_concurrent_tools"]
        
        return WorkflowContainer(workflow_class, base_limits)