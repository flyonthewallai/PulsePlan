"""
Workflow Manager
Central orchestrator for LangGraph workflows with error handling and observability
"""
from typing import Dict, Any, Optional, Type, List, Callable
from datetime import datetime
import asyncio
import logging
import uuid

from .graphs.base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError, create_initial_state
from .models.workflow_output import create_workflow_output, WorkflowStatus, ConversationResponse
from .services.supervisor import get_workflow_supervisor
# Removed ChatGraph - using unified system instead
from .graphs.calendar_graph import CalendarGraph  
from .graphs.task_graph import TaskGraph
from .graphs.briefing_graph import BriefingWorkflow as BriefingGraph
from .graphs.scheduling_graph import SchedulingWorkflow as SchedulingGraph
from .graphs.search_graph import SearchGraph

# Import new architecture components
from .core.state.workflow_container import WorkflowContainer, WorkflowContainerFactory, WorkflowResourceLimits
from .core.error.error_boundary import WorkflowErrorBoundary
from .core.state.state_manager import WorkflowStateManager, StatePersistenceLevel
from .core.error.recovery_service import WorkflowRecoveryService, RecoveryTrigger

# Import unified system services
from .core.orchestration.intent_processor import get_intent_processor

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Enhanced central workflow manager with:
    1. Isolated workflow execution containers
    2. Comprehensive error boundaries and recovery
    3. Advanced state management and persistence
    4. Resource monitoring and limits
    5. Automated failure recovery mechanisms
    6. Circuit breaker protection
    """
    
    def __init__(self, enable_isolation: bool = True):
        self.workflows: Dict[WorkflowType, Type[BaseWorkflow]] = {
            # WorkflowType.NATURAL_LANGUAGE now handled by unified system
            WorkflowType.CALENDAR: CalendarGraph,
            WorkflowType.TASK: TaskGraph,
            WorkflowType.BRIEFING: BriefingGraph,
            WorkflowType.SCHEDULING: SchedulingGraph,
            WorkflowType.SEARCH: SearchGraph
        }
        
        # Enhanced architecture configuration
        self.enable_isolation = enable_isolation
        self.container_factory = WorkflowContainerFactory()
        
        # Track active workflows for monitoring (legacy compatibility)
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Enhanced metrics and monitoring
        self.execution_metrics: Dict[str, Any] = {
            "total_executions": 0,
            "isolated_executions": 0,
            "recovery_attempts": 0,
            "circuit_breaker_activations": 0
        }
        
    async def execute_workflow(
        self,
        workflow_type: WorkflowType,
        user_id: str,
        input_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        resource_limits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with enhanced isolation, error boundaries, and recovery
        """
        workflow_class = self.workflows.get(workflow_type)
        if not workflow_class:
            raise WorkflowError(
                f"Unknown workflow type: {workflow_type}",
                {"workflow_type": workflow_type}
            )
        
        # Generate workflow ID
        workflow_id = trace_id or str(uuid.uuid4())
        
        # Update metrics
        self.execution_metrics["total_executions"] += 1

        # Log workflow execution start
        logger.info(f"🚀 [WORKFLOW START] {workflow_type.value} | ID: {workflow_id} | User: {user_id}")
        logger.info(f"📋 [WORKFLOW INPUT] {workflow_type.value} | Input: {input_data}")

        try:
            if self.enable_isolation:
                # Use enhanced isolation architecture
                return await self._execute_with_isolation(
                    workflow_type=workflow_type,
                    workflow_class=workflow_class,
                    workflow_id=workflow_id,
                    user_id=user_id,
                    input_data=input_data,
                    user_context=user_context,
                    connected_accounts=connected_accounts,
                    resource_limits=resource_limits
                )
            else:
                # Fall back to legacy execution
                return await self._execute_legacy(
                    workflow_type=workflow_type,
                    workflow_class=workflow_class,
                    workflow_id=workflow_id,
                    user_id=user_id,
                    input_data=input_data,
                    user_context=user_context,
                    connected_accounts=connected_accounts
                )
                
        except WorkflowError as e:
            # Log workflow error
            logger.error(f"❌ [WORKFLOW ERROR] {workflow_type.value} | ID: {workflow_id} | Error: {e.message}")
            # Handle workflow-specific errors
            await self._handle_workflow_error(workflow_id, workflow_type, e)
            # Don't re-raise to avoid duplicate error messages
            return self._create_error_response(workflow_id, workflow_type, e)
            
        except Exception as e:
            # Handle unexpected errors
            workflow_error = WorkflowError(
                f"Unexpected workflow error: {str(e)}",
                {"workflow_type": workflow_type.value, "user_id": user_id},
                recoverable=self._is_recoverable_error(e)
            )

            # Log unexpected error
            logger.error(f"💥 [WORKFLOW CRITICAL ERROR] {workflow_type.value} | ID: {workflow_id} | Error: {str(e)}")

            await self._handle_workflow_error(workflow_id, workflow_type, workflow_error)
            return self._create_error_response(workflow_id, workflow_type, workflow_error)
    
    def _create_error_response(self, workflow_id: str, workflow_type: WorkflowType, error: WorkflowError) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type.value,
            "status": "failed",
            "success": False,
            "error": error.message,
            "recoverable": error.recoverable,
            "context": error.context,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time": 0.0
        }
    
    async def execute_natural_language_query(
        self,
        user_id: str,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute natural language processing using unified system
        """
        try:
            # Use unified intent processor instead of ChatGraph workflow
            intent_processor = get_intent_processor()

            result = await intent_processor.process_user_query(
                user_id=user_id,
                query=query,
                conversation_id=user_context.get("conversation_id") if user_context else None,
                include_history=True
            )

            return {
                "status": "completed",
                "success": True,
                "result": result.dict(),
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id
            }

        except Exception as e:
            logger.error(f"Natural language query failed: {e}")
            return {
                "status": "failed",
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id
            }
    
    async def execute_workflow_with_conversation_layer(
        self,
        workflow_type: WorkflowType,
        user_id: str,
        user_query: str,
        input_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        trace_id: Optional[str] = None
    ) -> ConversationResponse:
        """
        Execute workflow with new structured output and conversation layer
        This is the new main entry point that separates workflow execution from conversation
        """
        
        # Execute the workflow to get structured output
        workflow_result = await self.execute_workflow(
            workflow_type=workflow_type,
            user_id=user_id,
            input_data=input_data,
            user_context=user_context,
            connected_accounts=connected_accounts,
            trace_id=trace_id
        )
        
        # Convert workflow result to structured output
        workflow_output = self._convert_to_structured_output(workflow_result, workflow_type.value)
        
        # Use supervisor to wrap in conversation layer
        supervisor = await get_workflow_supervisor()
        conversation_response = await supervisor.supervise_workflow_execution(
            user_query=user_query,
            workflow_output=workflow_output,
            user_context=user_context,
            conversation_history=conversation_history
        )
        
        return conversation_response
    
    async def handle_follow_up_query(
        self,
        user_message: str,
        trace_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationResponse]:
        """
        Handle follow-up messages that reference previous workflow executions
        """
        supervisor = await get_workflow_supervisor()
        return await supervisor.handle_follow_up_message(
            user_message=user_message,
            trace_id=trace_id,
            user_context=user_context
        )
    
    async def execute_calendar_operation(
        self,
        user_id: str,
        provider: str,
        operation: str,
        operation_data: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute calendar workflow directly
        """
        input_data = {
            "provider": provider,
            "operation": operation
        }
        
        if operation_data:
            input_data.update(operation_data)
        
        return await self.execute_workflow(
            workflow_type=WorkflowType.CALENDAR,
            user_id=user_id,
            input_data=input_data,
            user_context=user_context,
            connected_accounts=connected_accounts
        )
    
    async def execute_task_operation(
        self,
        user_id: str,
        operation: str,
        task_data: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute task workflow directly
        """
        input_data = {"operation": operation}
        
        if task_data:
            input_data["task_data"] = task_data
        if task_id:
            input_data["task_id"] = task_id
        
        return await self.execute_workflow(
            workflow_type=WorkflowType.TASK,
            user_id=user_id,
            input_data=input_data,
            user_context=user_context
        )
    
    async def generate_daily_briefing(
        self,
        user_id: str,
        briefing_date: Optional[str] = None,
        delivery_method: str = "api",
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate daily briefing workflow
        """
        input_data = {
            "delivery_method": delivery_method
        }
        
        if briefing_date:
            input_data["date"] = briefing_date
        
        return await self.execute_workflow(
            workflow_type=WorkflowType.BRIEFING,
            user_id=user_id,
            input_data=input_data,
            user_context=user_context,
            connected_accounts=connected_accounts
        )
    
    async def create_intelligent_schedule(
        self,
        user_id: str,
        scheduling_request: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute intelligent scheduling workflow
        """
        return await self.execute_workflow(
            workflow_type=WorkflowType.SCHEDULING,
            user_id=user_id,
            input_data={"scheduling_request": scheduling_request},
            user_context=user_context,
            connected_accounts=connected_accounts
        )
    
    async def execute_search_query(
        self,
        user_id: str,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute search workflow directly
        """
        return await self.execute_workflow(
            workflow_type=WorkflowType.SEARCH,
            user_id=user_id,
            input_data={"query": query},
            user_context=user_context,
            connected_accounts=connected_accounts
        )
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a running or completed workflow
        """
        return self.active_workflows.get(workflow_id)
    
    def get_active_workflows(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all active workflows, optionally filtered by user
        """
        if user_id:
            return {
                wf_id: wf_data for wf_id, wf_data in self.active_workflows.items()
                if wf_data.get("user_id") == user_id
            }
        
        return self.active_workflows.copy()
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive workflow execution metrics
        """
        # Legacy metrics (for compatibility)
        total_workflows = len(self.active_workflows)
        running_workflows = sum(1 for wf in self.active_workflows.values() if wf["status"] == "running")
        completed_workflows = sum(1 for wf in self.active_workflows.values() if wf["status"] == "completed")  
        failed_workflows = sum(1 for wf in self.active_workflows.values() if wf["status"] == "failed")
        
        # Calculate success rate
        finished_workflows = completed_workflows + failed_workflows
        success_rate = (completed_workflows / finished_workflows * 100) if finished_workflows > 0 else 0
        
        # Enhanced metrics
        base_metrics = {
            "orchestrator": {
                "total_workflows": total_workflows,
                "running_workflows": running_workflows,
                "completed_workflows": completed_workflows,
                "failed_workflows": failed_workflows,
                "success_rate": round(success_rate, 2),
                "workflow_types": self._get_workflow_type_metrics(),
                "execution_metrics": self.execution_metrics,
                "isolation_enabled": self.enable_isolation
            }
        }
        
        # Add enhanced architecture metrics if enabled
        if self.enable_isolation:
            try:
                base_metrics.update({
                    "state_manager": workflow_state_manager.get_state_metrics(),
                    "error_boundary": workflow_error_boundary.get_error_metrics(),
                    "recovery_service": workflow_recovery_service.get_recovery_metrics()
                })
            except Exception as e:
                logger.warning(f"Failed to get enhanced metrics: {str(e)}")
        
        return base_metrics
    
    # Enhanced architecture management methods
    
    async def recover_workflow(
        self,
        workflow_id: str,
        checkpoint_name: Optional[str] = None
    ) -> bool:
        """
        Manually trigger workflow recovery
        """
        if not self.enable_isolation:
            logger.warning("Recovery not available - isolation disabled")
            return False
        
        attempt = await workflow_recovery_service.attempt_recovery(
            workflow_id=workflow_id,
            trigger=RecoveryTrigger.MANUAL,
            specific_checkpoint=checkpoint_name
        )
        
        return attempt.status.value == "success"
    
    async def suspend_workflow(self, workflow_id: str, reason: str = "Manual suspension") -> bool:
        """
        Suspend a workflow for later resumption
        """
        if not self.enable_isolation:
            logger.warning("Suspend not available - isolation disabled")
            return False
        
        return await workflow_state_manager.suspend_state(workflow_id, reason)
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resume a suspended workflow
        """
        if not self.enable_isolation:
            logger.warning("Resume not available - isolation disabled")
            return False
        
        return await workflow_state_manager.resume_state(workflow_id)
    
    async def create_checkpoint(self, workflow_id: str, checkpoint_name: str) -> bool:
        """
        Create a named checkpoint for workflow recovery
        """
        if not self.enable_isolation:
            logger.warning("Checkpoints not available - isolation disabled")
            return False
        
        return await workflow_state_manager.create_checkpoint(workflow_id, checkpoint_name)
    
    def register_recovery_handler(
        self,
        workflow_type: str,
        handler: Callable[[str, Dict[str, Any]], bool]
    ):
        """
        Register custom recovery handler for workflow type
        """
        if self.enable_isolation:
            workflow_recovery_service.register_recovery_handler(workflow_type, handler)
        else:
            logger.warning("Recovery handlers not available - isolation disabled")
    
    def set_recovery_policy(self, workflow_type: str, policy: Dict[str, Any]):
        """
        Set recovery policy for workflow type
        """
        if self.enable_isolation:
            workflow_recovery_service.set_recovery_policy(workflow_type, policy)
        else:
            logger.warning("Recovery policies not available - isolation disabled")
    
    async def batch_recover_failed_workflows(self, max_workflows: int = 10) -> List[str]:
        """
        Batch recover multiple failed workflows
        """
        if not self.enable_isolation:
            logger.warning("Batch recovery not available - isolation disabled")
            return []
        
        attempts = await workflow_recovery_service.batch_recover_failed_workflows(max_workflows)
        return [attempt.workflow_id for attempt in attempts if attempt.status.value == "success"]
    
    def toggle_isolation(self, enabled: bool):
        """
        Toggle isolation mode on/off (for testing or emergency fallback)
        """
        if enabled and not self.enable_isolation:
            logger.info("Enabling enhanced isolation architecture")
            self.enable_isolation = True
        elif not enabled and self.enable_isolation:
            logger.warning("Disabling enhanced isolation architecture - falling back to legacy mode")
            self.enable_isolation = False
        
        self.execution_metrics["isolation_toggle"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "enabled": enabled
        }
    
    def _get_workflow_type_metrics(self) -> Dict[str, int]:
        """Get metrics by workflow type"""
        type_counts = {}
        
        for wf_data in self.active_workflows.values():
            wf_type = wf_data["workflow_type"]
            type_counts[wf_type] = type_counts.get(wf_type, 0) + 1
        
        return type_counts
    
    def _format_workflow_result(self, result_state: WorkflowState) -> Dict[str, Any]:
        """
        Format workflow result for API response
        """
        workflow_id = result_state["trace_id"]
        workflow_type = result_state["workflow_type"]
        execution_time = (datetime.utcnow() - result_state["execution_start"]).total_seconds()
        nodes_executed = len(result_state.get("visited_nodes", []))
        output_data = result_state.get("output_data", {})

        # Log workflow completion
        logger.info(f"✅ [WORKFLOW SUCCESS] {workflow_type} | ID: {workflow_id} | Time: {execution_time:.2f}s | Nodes: {nodes_executed}")
        logger.info(f"📤 [WORKFLOW OUTPUT] {workflow_type} | Output: {output_data}")

        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "user_id": result_state["user_id"],
            "status": "completed",
            "result": output_data,
            "execution_time": execution_time,
            "nodes_executed": nodes_executed,
            "metrics": result_state.get("metrics", {}),
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def _convert_to_structured_output(self, workflow_result: Dict[str, Any], workflow_type: str):
        """
        Convert orchestrator workflow result to structured WorkflowOutput
        """
        result_data = workflow_result.get("result", {})
        
        # Determine status
        if workflow_result.get("status") == "completed":
            if result_data.get("success", True):
                status = WorkflowStatus.SUCCESS
            else:
                if result_data.get("requires_feedback") or result_data.get("feedback_request"):
                    status = WorkflowStatus.NEEDS_INPUT
                else:
                    status = WorkflowStatus.PARTIAL_SUCCESS
        else:
            status = WorkflowStatus.FAILURE
        
        # Extract structured data from workflow result
        structured_data = result_data.get("structured_data", {})
        if not structured_data:
            # Fallback: use the entire result as structured data
            structured_data = result_data
        
        # Extract error information
        error = result_data.get("error")
        error_code = None
        if error and isinstance(error, dict):
            error_code = error.get("code")
            error = error.get("message", str(error))
        
        # Extract follow-up context
        follow_up_context = result_data.get("follow_up_context", {})
        
        # Extract suggested actions
        suggested_actions = result_data.get("suggested_actions", [])
        
        return create_workflow_output(
            workflow_type=workflow_type,
            status=status,
            execution_time=workflow_result.get("execution_time", 0.0),
            trace_id=workflow_result.get("workflow_id", "unknown"),
            data=structured_data,
            error=error,
            error_code=error_code,
            follow_up_context=follow_up_context,
            suggested_actions=suggested_actions
        )
    
    async def _execute_with_isolation(
        self,
        workflow_type: WorkflowType,
        workflow_class: Type[BaseWorkflow],
        workflow_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None,
        resource_limits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow with full isolation architecture
        """
        self.execution_metrics["isolated_executions"] += 1
        
        # Create isolated state
        await workflow_state_manager.create_isolated_state(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            user_id=user_id,
            initial_data={
                "input_data": input_data,
                "user_context": user_context or {},
                "connected_accounts": connected_accounts or {},
                "request_id": workflow_id
            },
            persistence_level=StatePersistenceLevel.REDIS_CACHED
        )
        
        # Create workflow container with resource limits
        container = self.container_factory.create_container(
            workflow_class=workflow_class,
            workflow_type=workflow_type,
            user_id=user_id,
            custom_limits=resource_limits
        )
        
        # Track workflow execution (legacy compatibility)
        self.active_workflows[workflow_id] = {
            "workflow_type": workflow_type.value,
            "user_id": user_id,
            "started_at": datetime.utcnow(),
            "status": "running",
            "isolated": True
        }
        
        try:
            # Get current state
            current_state = await workflow_state_manager.get_state(workflow_id)
            if not current_state:
                raise WorkflowError("Failed to create workflow state", {"workflow_id": workflow_id})
            
            # Execute with error boundary and container isolation
            result_state = await workflow_error_boundary.execute_with_boundary(
                workflow_func=container.execute_with_boundaries,
                state=current_state,
                workflow_type=workflow_type.value
            )
            
            # Update state with results
            if result_state.get("output_data"):
                await workflow_state_manager.complete_state(
                    workflow_id,
                    result_state["output_data"]
                )
            
            # Update tracking
            self.active_workflows[workflow_id].update({
                "status": "completed",
                "completed_at": datetime.utcnow()
            })
            
            # Format and return result
            return self._format_workflow_result(result_state)
            
        except Exception as e:
            # Update tracking
            self.active_workflows[workflow_id].update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow()
            })
            
            # Trigger automatic recovery if appropriate
            await self._trigger_automatic_recovery(workflow_id, workflow_type, e)
            
            raise e
        
        finally:
            # Schedule cleanup
            asyncio.create_task(self._cleanup_workflow_tracking(workflow_id, delay=300))
    
    async def _execute_legacy(
        self,
        workflow_type: WorkflowType,
        workflow_class: Type[BaseWorkflow],
        workflow_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        connected_accounts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Legacy workflow execution (for backward compatibility)
        """
        # Create initial state
        initial_state = create_initial_state(
            user_id=user_id,
            workflow_type=workflow_type,
            input_data=input_data,
            user_context=user_context,
            connected_accounts=connected_accounts,
            trace_id=workflow_id
        )
        
        # Track workflow execution
        self.active_workflows[workflow_id] = {
            "workflow_type": workflow_type.value,
            "user_id": user_id,
            "started_at": datetime.utcnow(),
            "status": "running",
            "isolated": False
        }
        
        # Create and execute workflow
        workflow_instance = workflow_class()
        result_state = await workflow_instance.execute(initial_state)
        
        # Update tracking
        self.active_workflows[workflow_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow()
        })
        
        return self._format_workflow_result(result_state)
    
    async def _handle_workflow_error(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        error: WorkflowError
    ):
        """
        Handle workflow errors with enhanced logging and recovery triggers
        """
        logger.error(
            f"Workflow error in {workflow_type.value}: {error.message}",
            extra={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type.value,
                "error_context": error.context,
                "recoverable": error.recoverable
            }
        )
        
        # Update legacy tracking
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].update({
                "status": "failed",
                "error": error.message,
                "failed_at": datetime.utcnow()
            })
        
        # Update state manager if using isolation
        if self.enable_isolation:
            await workflow_state_manager.update_state(
                workflow_id,
                {
                    "error": {
                        "message": error.message,
                        "type": type(error).__name__,
                        "recoverable": error.recoverable,
                        "context": error.context,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                checkpoint_name="error_state"
            )
    
    async def _trigger_automatic_recovery(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        error: Exception
    ):
        """
        Trigger automatic recovery for failed workflows
        """
        if not self.enable_isolation:
            return
        
        # Check if error is recoverable
        is_recoverable = getattr(error, 'recoverable', False) or self._is_recoverable_error(error)
        
        if is_recoverable:
            self.execution_metrics["recovery_attempts"] += 1
            
            # Schedule automatic recovery
            await workflow_recovery_service.schedule_recovery(
                workflow_id=workflow_id,
                delay_seconds=30,  # 30 second delay
                trigger=RecoveryTrigger.AUTOMATIC
            )
            
            logger.info(
                f"Scheduled automatic recovery for workflow {workflow_id}",
                extra={
                    "workflow_id": workflow_id,
                    "workflow_type": workflow_type.value,
                    "error": str(error)
                }
            )
    
    def _is_recoverable_error(self, error: Exception) -> bool:
        """
        Determine if an error is potentially recoverable
        """
        recoverable_errors = (
            asyncio.TimeoutError,
            ConnectionError,
            OSError,
        )
        
        if isinstance(error, recoverable_errors):
            return True
        
        # Check error message for recoverable patterns
        error_msg = str(error).lower()
        recoverable_patterns = [
            "timeout", "connection", "temporary", "rate limit",
            "service unavailable", "retry"
        ]
        
        return any(pattern in error_msg for pattern in recoverable_patterns)
    
    async def _cleanup_workflow_tracking(self, workflow_id: str, delay: int = 300):
        """
        Remove workflow from active tracking after delay
        """
        await asyncio.sleep(delay)
        self.active_workflows.pop(workflow_id, None)
        
        # Archive state if using isolation
        if self.enable_isolation:
            try:
                await workflow_state_manager.archive_state(workflow_id)
            except Exception as e:
                logger.warning(
                    f"Failed to archive workflow state {workflow_id}: {str(e)}"
                )


# Global agent orchestrator instance with enhanced architecture
agent_orchestrator = AgentOrchestrator(enable_isolation=True)


async def get_agent_orchestrator() -> AgentOrchestrator:
    """
    FastAPI dependency to get agent orchestrator
    """
    return agent_orchestrator