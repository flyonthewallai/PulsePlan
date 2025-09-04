"""
Intelligent Agent Integration Service
Integrates smart scheduling, intelligent prioritization, and enhanced NLP
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..models.workflow_output import ConversationResponse, WorkflowOutput, create_workflow_output, WorkflowStatus
from ...scheduler.smart_assistant import SmartSchedulingAssistant, TaskComplexityProfile
from ...scheduler.intelligent_prioritization import IntelligentPrioritizer, PriorityAdjustment
from .enhanced_nlp import EnhancedNLPProcessor, ParsedCommand, CommandType
from ...scheduler.service import SchedulerService, get_scheduler_service
from ...scheduler.domain import Task, Preferences

logger = logging.getLogger(__name__)


class IntelligentAgentService:
    """
    Unified service that combines smart scheduling, intelligent prioritization,
    and enhanced natural language processing for a comprehensive AI agent experience
    """
    
    def __init__(self):
        self.scheduler_service = get_scheduler_service()
        self.smart_assistant = SmartSchedulingAssistant(self.scheduler_service)
        self.intelligent_prioritizer = IntelligentPrioritizer()
        self.nlp_processor = EnhancedNLPProcessor()
    
    async def process_intelligent_request(
        self,
        user_id: str,
        user_query: str,
        user_context: Dict[str, Any],
        voice_input: bool = False
    ) -> ConversationResponse:
        """
        Main entry point for intelligent request processing with all features integrated
        """
        try:
            # 1. Process natural language command
            if voice_input:
                parsed_command = await self.nlp_processor.handle_voice_command(user_id, user_query)
            else:
                parsed_command = await self.nlp_processor.process_natural_language_command(
                    user_id, user_query, voice_input=False, conversation_context=user_context
                )
            
            # 2. Route to appropriate intelligent handler
            if parsed_command.workflow_type == "scheduling":
                return await self._handle_intelligent_scheduling(
                    user_id, parsed_command, user_context
                )
            elif parsed_command.command_type == CommandType.BATCH_OPERATION:
                return await self._handle_batch_operations(
                    user_id, parsed_command, user_context
                )
            elif parsed_command.workflow_type in ["task", "todo"]:
                return await self._handle_intelligent_task_management(
                    user_id, parsed_command, user_context
                )
            elif parsed_command.workflow_type == "calendar":
                return await self._handle_intelligent_calendar_operations(
                    user_id, parsed_command, user_context
                )
            else:
                # Fall back to regular processing for other workflows
                return await self._handle_regular_workflow(
                    user_id, parsed_command, user_context
                )
            
        except Exception as e:
            logger.error(f"Intelligent request processing failed: {e}")
            
            # Return error response
            error_output = create_workflow_output(
                workflow_type="chat",
                status=WorkflowStatus.FAILURE,
                execution_time=0.1,
                trace_id=f"error_{user_id}_{datetime.now().timestamp()}",
                error=f"I encountered an error processing your request: {str(e)}",
                suggested_actions=["Try rephrasing your request", "Contact support"]
            )
            
            from .conversation_layer import get_conversation_layer
            conversation_layer = get_conversation_layer()
            
            return await conversation_layer.wrap_workflow_output(
                user_query=user_query,
                workflow_output=error_output,
                user_context=user_context
            )
    
    async def _handle_intelligent_scheduling(
        self, user_id: str, parsed_command: ParsedCommand, user_context: Dict[str, Any]
    ) -> ConversationResponse:
        """Handle scheduling requests with smart assistant"""
        
        # Get user's tasks and preferences
        tasks = await self._load_user_tasks(user_id, days_ahead=7)
        preferences = await self._load_user_preferences(user_id)
        existing_events = await self._load_calendar_events(user_id, days_ahead=7)
        
        # Apply intelligent prioritization first
        prioritized_tasks, priority_adjustments = await self.intelligent_prioritizer.analyze_and_adjust_priorities(
            tasks, {}, user_context, time_horizon_days=7
        )
        
        # Create smart schedule
        smart_solution = await self.smart_assistant.create_smart_schedule(
            user_id=user_id,
            tasks=prioritized_tasks,
            preferences=preferences,
            existing_events=existing_events,
            context=parsed_command.parameters
        )
        
        # Format response data
        response_data = {
            "operation": "smart_scheduling",
            "schedule_created": smart_solution.feasible,
            "scheduled_tasks": [
                {
                    "task_id": block.task_id,
                    "start": block.start.isoformat(),
                    "end": block.end.isoformat(),
                    "utility_score": block.utility_score,
                    "completion_probability": block.estimated_completion_probability
                }
                for block in smart_solution.blocks
            ],
            "optimization_score": smart_solution.objective_value,
            "priority_adjustments": [
                {
                    "task_id": adj.task_id,
                    "reason": adj.reason.value,
                    "explanation": adj.explanation,
                    "confidence": adj.confidence
                }
                for adj in priority_adjustments
            ],
            "insights": {
                "energy_optimization": "applied" if smart_solution.diagnostics.get("energy_optimization") else "not_applied",
                "context_aware": "applied" if smart_solution.diagnostics.get("context_aware") else "not_applied",
                "smart_scheduling": "applied" if smart_solution.diagnostics.get("smart_scheduling") else "not_applied"
            }
        }
        
        # Create workflow output
        workflow_output = create_workflow_output(
            workflow_type="scheduling",
            status=WorkflowStatus.SUCCESS if smart_solution.feasible else WorkflowStatus.PARTIAL_SUCCESS,
            execution_time=1.5,  # Would be measured in practice
            trace_id=f"smart_schedule_{user_id}_{datetime.now().timestamp()}",
            data=response_data,
            suggested_actions=[
                "View your optimized schedule",
                "Make adjustments to the schedule",
                "Set up notifications for scheduled tasks"
            ] if smart_solution.feasible else [
                "Review conflicting commitments",
                "Adjust task priorities",
                "Extend scheduling horizon"
            ]
        )
        
        # Wrap in conversation layer
        from .conversation_layer import get_conversation_layer
        conversation_layer = get_conversation_layer()
        
        return await conversation_layer.wrap_workflow_output(
            user_query=f"Create intelligent schedule: {parsed_command.parameters}",
            workflow_output=workflow_output,
            user_context=user_context
        )
    
    async def _handle_batch_operations(
        self, user_id: str, parsed_command: ParsedCommand, user_context: Dict[str, Any]
    ) -> ConversationResponse:
        """Handle batch operations like 'cancel all meetings on Thursday'"""
        
        results = []
        
        for batch_op in parsed_command.batch_operations:
            operation = batch_op["operation"]
            scope = batch_op["scope"]
            parameters = batch_op["parameters"]
            
            if operation == "batch_cancel":
                result = await self._execute_batch_cancel(user_id, scope, parameters)
            elif operation == "batch_reschedule":
                result = await self._execute_batch_reschedule(user_id, scope, parameters)
            elif operation == "batch_delete":
                result = await self._execute_batch_delete(user_id, scope, parameters)
            else:
                result = {"operation": operation, "success": False, "error": "Unknown batch operation"}
            
            results.append(result)
        
        # Summarize results
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r.get("success", False))
        
        response_data = {
            "operation": "batch_operations",
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": total_operations - successful_operations,
            "results": results,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0
        }
        
        # Create workflow output
        workflow_output = create_workflow_output(
            workflow_type=parsed_command.workflow_type,
            status=WorkflowStatus.SUCCESS if successful_operations == total_operations else WorkflowStatus.PARTIAL_SUCCESS,
            execution_time=0.8,
            trace_id=f"batch_ops_{user_id}_{datetime.now().timestamp()}",
            data=response_data,
            suggested_actions=[
                "Review the changes made",
                "Undo specific operations if needed",
                "Confirm the updates look correct"
            ]
        )
        
        # Wrap in conversation layer
        from .conversation_layer import get_conversation_layer
        conversation_layer = get_conversation_layer()
        
        return await conversation_layer.wrap_workflow_output(
            user_query=f"Batch operation: {parsed_command.primary_action}",
            workflow_output=workflow_output,
            user_context=user_context
        )
    
    async def _handle_intelligent_task_management(
        self, user_id: str, parsed_command: ParsedCommand, user_context: Dict[str, Any]
    ) -> ConversationResponse:
        """Handle task management with intelligent prioritization"""
        
        # Get user's current tasks
        tasks = await self._load_user_tasks(user_id, days_ahead=14)
        
        # Apply intelligent prioritization
        prioritized_tasks, priority_adjustments = await self.intelligent_prioritizer.analyze_and_adjust_priorities(
            tasks, {}, user_context, time_horizon_days=14
        )
        
        # Detect overcommitment
        available_hours = user_context.get("available_hours_per_day", {"weekday": 8, "weekend": 6})
        overcommitment_analysis = await self.intelligent_prioritizer.detect_overcommitment(
            prioritized_tasks, available_hours, horizon_days=7
        )
        
        # Get workload distribution
        workload_distribution = self.intelligent_prioritizer.get_workload_distribution(
            prioritized_tasks, group_by="priority"
        )
        
        # Execute the requested task operation
        task_operation_result = await self._execute_task_operation(
            user_id, parsed_command.operation, parsed_command.parameters
        )
        
        # Format response data
        response_data = {
            "operation": parsed_command.operation,
            "task_operation_result": task_operation_result,
            "intelligent_insights": {
                "priority_adjustments": [
                    {
                        "task_id": adj.task_id,
                        "old_priority": adj.old_priority,
                        "new_priority": adj.new_priority,
                        "reason": adj.reason.value,
                        "explanation": adj.explanation,
                        "confidence": adj.confidence
                    }
                    for adj in priority_adjustments[:5]  # Top 5 adjustments
                ],
                "overcommitment_analysis": overcommitment_analysis,
                "workload_distribution": workload_distribution
            },
            "recommendations": self._generate_task_management_recommendations(
                prioritized_tasks, overcommitment_analysis, priority_adjustments
            )
        }
        
        # Create workflow output
        workflow_output = create_workflow_output(
            workflow_type="task",
            status=WorkflowStatus.SUCCESS if task_operation_result.get("success") else WorkflowStatus.PARTIAL_SUCCESS,
            execution_time=1.2,
            trace_id=f"intelligent_tasks_{user_id}_{datetime.now().timestamp()}",
            data=response_data,
            suggested_actions=response_data["recommendations"][:3]  # Top 3 recommendations as actions
        )
        
        # Wrap in conversation layer
        from .conversation_layer import get_conversation_layer
        conversation_layer = get_conversation_layer()
        
        return await conversation_layer.wrap_workflow_output(
            user_query=f"Intelligent task management: {parsed_command.operation}",
            workflow_output=workflow_output,
            user_context=user_context
        )
    
    async def _handle_intelligent_calendar_operations(
        self, user_id: str, parsed_command: ParsedCommand, user_context: Dict[str, Any]
    ) -> ConversationResponse:
        """Handle calendar operations with smart features"""
        
        # Execute calendar operation
        calendar_result = await self._execute_calendar_operation(
            user_id, parsed_command.operation, parsed_command.parameters
        )
        
        # If this was a scheduling operation, apply intelligent features
        if parsed_command.operation in ["create", "update", "reschedule"]:
            # Get tasks and apply smart scheduling
            tasks = await self._load_user_tasks(user_id, days_ahead=7)
            if tasks:
                preferences = await self._load_user_preferences(user_id)
                existing_events = await self._load_calendar_events(user_id, days_ahead=7)
                
                # Check for optimal scheduling opportunities
                scheduling_suggestions = await self._analyze_scheduling_opportunities(
                    user_id, tasks, existing_events, preferences, parsed_command.parameters
                )
                
                calendar_result["scheduling_suggestions"] = scheduling_suggestions
        
        # Create workflow output
        workflow_output = create_workflow_output(
            workflow_type="calendar",
            status=WorkflowStatus.SUCCESS if calendar_result.get("success") else WorkflowStatus.PARTIAL_SUCCESS,
            execution_time=0.9,
            trace_id=f"smart_calendar_{user_id}_{datetime.now().timestamp()}",
            data=calendar_result,
            suggested_actions=[
                "Review your updated calendar",
                "Check for scheduling conflicts",
                "Optimize your task schedule"
            ]
        )
        
        # Wrap in conversation layer
        from .conversation_layer import get_conversation_layer
        conversation_layer = get_conversation_layer()
        
        return await conversation_layer.wrap_workflow_output(
            user_query=f"Smart calendar operation: {parsed_command.operation}",
            workflow_output=workflow_output,
            user_context=user_context
        )
    
    async def _handle_regular_workflow(
        self, user_id: str, parsed_command: ParsedCommand, user_context: Dict[str, Any]
    ) -> ConversationResponse:
        """Handle regular workflows (non-intelligent) with enhanced NLP parsing"""
        
        # Use the enhanced parsing results to improve regular workflows
        enhanced_parameters = parsed_command.parameters.copy()
        
        # Add extracted entities as parameters
        for entity in parsed_command.entities:
            entity_key = f"extracted_{entity.type.value}"
            if entity_key not in enhanced_parameters:
                enhanced_parameters[entity_key] = []
            enhanced_parameters[entity_key].append({
                "value": entity.value,
                "text": entity.text,
                "confidence": entity.confidence
            })
        
        # Execute the workflow with enhanced parameters
        result = await self._execute_generic_workflow(
            user_id, parsed_command.workflow_type, parsed_command.operation, enhanced_parameters
        )
        
        # Create workflow output
        workflow_output = create_workflow_output(
            workflow_type=parsed_command.workflow_type,
            status=WorkflowStatus.SUCCESS if result.get("success") else WorkflowStatus.PARTIAL_SUCCESS,
            execution_time=0.5,
            trace_id=f"enhanced_{parsed_command.workflow_type}_{user_id}_{datetime.now().timestamp()}",
            data=result,
            suggested_actions=result.get("suggested_actions", [])
        )
        
        # Wrap in conversation layer
        from .conversation_layer import get_conversation_layer
        conversation_layer = get_conversation_layer()
        
        return await conversation_layer.wrap_workflow_output(
            user_query=f"Enhanced {parsed_command.workflow_type}: {parsed_command.operation}",
            workflow_output=workflow_output,
            user_context=user_context
        )
    
    async def handle_follow_up_with_intelligence(
        self, user_id: str, follow_up_message: str, previous_result: Dict[str, Any]
    ) -> ConversationResponse:
        """Handle follow-up messages with full intelligent context"""
        
        # Process follow-up with contextual understanding
        parsed_follow_up = await self.nlp_processor.handle_contextual_follow_up(
            user_id, follow_up_message, previous_result
        )
        
        # If this references scheduling or task data, apply intelligent features
        if parsed_follow_up.references_previous_query and parsed_follow_up.workflow_type in ["calendar", "task", "scheduling"]:
            return await self.process_intelligent_request(
                user_id, follow_up_message, {"previous_result": previous_result}
            )
        else:
            # Handle as regular follow-up
            return await self._handle_regular_workflow(
                user_id, parsed_follow_up, {"previous_result": previous_result}
            )
    
    async def _load_user_tasks(self, user_id: str, days_ahead: int = 7) -> List[Task]:
        """Load user's tasks (mock implementation)"""
        # In practice, this would load from database
        return []
    
    async def _load_user_preferences(self, user_id: str) -> Preferences:
        """Load user preferences (mock implementation)"""
        # In practice, this would load from database
        from ...scheduler.domain import Preferences
        return Preferences(timezone="America/New_York")
    
    async def _load_calendar_events(self, user_id: str, days_ahead: int = 7) -> List:
        """Load calendar events (mock implementation)"""
        # In practice, this would load from calendar service
        return []
    
    async def _execute_batch_cancel(self, user_id: str, scope: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute batch cancellation"""
        # Mock implementation
        return {"operation": "batch_cancel", "success": True, "affected_count": 3, "scope": scope}
    
    async def _execute_batch_reschedule(self, user_id: str, scope: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute batch rescheduling"""
        # Mock implementation
        return {"operation": "batch_reschedule", "success": True, "affected_count": 5, "scope": scope, "parameters": parameters}
    
    async def _execute_batch_delete(self, user_id: str, scope: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute batch deletion"""
        # Mock implementation
        return {"operation": "batch_delete", "success": True, "affected_count": 2, "scope": scope}
    
    async def _execute_task_operation(self, user_id: str, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task operation"""
        # Mock implementation
        return {"operation": operation, "success": True, "parameters": parameters}
    
    async def _execute_calendar_operation(self, user_id: str, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calendar operation"""
        # Mock implementation
        return {"operation": operation, "success": True, "parameters": parameters}
    
    async def _execute_generic_workflow(self, user_id: str, workflow_type: str, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic workflow"""
        # Mock implementation
        return {"workflow_type": workflow_type, "operation": operation, "success": True, "parameters": parameters}
    
    async def _analyze_scheduling_opportunities(
        self, user_id: str, tasks: List[Task], events: List, preferences: Preferences, context: Dict[str, Any]
    ) -> List[str]:
        """Analyze scheduling opportunities"""
        # Mock implementation
        return [
            "Consider scheduling high-focus tasks during your morning peak hours",
            "You have a 2-hour gap on Thursday that could fit your project work",
            "Group similar tasks together to reduce context switching"
        ]
    
    def _generate_task_management_recommendations(
        self, tasks: List[Task], overcommitment_analysis: Dict[str, Any], priority_adjustments: List[PriorityAdjustment]
    ) -> List[str]:
        """Generate intelligent task management recommendations"""
        recommendations = []
        
        if overcommitment_analysis.get("is_overcommitted"):
            recommendations.append(f"You're overcommitted by {overcommitment_analysis['excess_hours']:.1f} hours - consider deferring some tasks")
        
        if priority_adjustments:
            high_confidence_adjustments = [adj for adj in priority_adjustments if adj.confidence > 0.8]
            if high_confidence_adjustments:
                recommendations.append(f"I've identified {len(high_confidence_adjustments)} tasks that should be reprioritized")
        
        recommendations.extend([
            "Break large tasks into smaller, manageable chunks",
            "Schedule your most important work during peak energy hours",
            "Consider batching similar tasks to reduce context switching"
        ])
        
        return recommendations[:5]  # Limit to top 5


# Global service instance
intelligent_agent_service = IntelligentAgentService()


def get_intelligent_agent_service() -> IntelligentAgentService:
    """Get the global intelligent agent service instance"""
    return intelligent_agent_service