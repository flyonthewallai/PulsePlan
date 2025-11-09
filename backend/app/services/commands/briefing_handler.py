"""
Briefing Command Handler
Generates daily briefing using orchestrator
"""
from typing import Dict, Any
import logging
from datetime import datetime
from .base import BaseCommandHandler, CommandResult
from app.agents.orchestrator import AgentOrchestrator
from app.agents.graphs.base import WorkflowType

logger = logging.getLogger(__name__)


class BriefingCommandHandler(BaseCommandHandler):
    """Handler for /briefing command - shows daily overview"""

    def __init__(self):
        super().__init__()
        self.command_name = "briefing"

    async def execute(self, user_id: str, parameters: Dict[str, Any]) -> CommandResult:
        """
        Execute briefing command
        
        No parameters required - generates briefing for current day
        """
        try:
            # Use orchestrator to execute briefing workflow
            orchestrator = AgentOrchestrator()
            
            # Execute briefing workflow
            workflow_result = await orchestrator.execute_workflow(
                workflow_type=WorkflowType.BRIEFING,
                user_id=user_id,
                input_data={"timeframe": "today"}
            )

            # Check if workflow completed successfully  
            if workflow_result and workflow_result.get("status") == "completed":
                briefing_result = workflow_result.get("result", {})
                
                # Format briefing as markdown for chat display
                response_parts = [f"📰 **Daily Briefing** - {datetime.now().strftime('%A, %B %d')}\n"]
                
                # Summary
                if briefing_result.get("summary"):
                    response_parts.append(f"## Overview\n{briefing_result['summary']}\n")
                
                # Today's tasks
                if briefing_result.get("todays_tasks"):
                    response_parts.append("## 📋 Today's Tasks")
                    for task in briefing_result["todays_tasks"][:5]:
                        response_parts.append(f"- {task}")
                    response_parts.append("")
                
                # Upcoming events
                if briefing_result.get("upcoming_events"):
                    response_parts.append("## 📅 Upcoming Events")
                    for event in briefing_result["upcoming_events"][:5]:
                        response_parts.append(f"- {event}")
                    response_parts.append("")
                
                # Top priorities
                if briefing_result.get("top_priorities"):
                    response_parts.append("## 🔥 Top Priorities")
                    for priority in briefing_result["top_priorities"][:3]:
                        response_parts.append(f"- {priority}")
                    response_parts.append("")
                
                # Recommendations
                if briefing_result.get("recommendations"):
                    response_parts.append("## 💡 Recommendations")
                    for rec in briefing_result["recommendations"][:3]:
                        response_parts.append(f"- {rec}")
                    response_parts.append("")

                response_msg = "\n".join(response_parts) if len(response_parts) > 1 else "📰 Your daily briefing is ready!"

                return CommandResult(
                    success=True,
                    command=self.command_name,
                    result=briefing_result,
                    immediate_response=response_msg
                )
            else:
                error_msg = workflow_result.get("error") if isinstance(workflow_result, dict) else "Failed to generate briefing"
                return CommandResult(
                    success=False,
                    command=self.command_name,
                    immediate_response=f"Could not generate briefing: {error_msg}",
                    error=error_msg
                )

        except Exception as e:
            logger.error(f"Error in briefing command handler: {e}", exc_info=True)
            
            # Fallback response if briefing service fails
            fallback_msg = f"""📰 **Daily Briefing** - {datetime.now().strftime('%A, %B %d')}

Your daily briefing is currently unavailable. Please try again later or check your schedule manually.

💡 **Quick Tip**: Use `/todo` to add tasks and `/schedule` to plan your day!"""
            
            return CommandResult(
                success=False,
                command=self.command_name,
                immediate_response=fallback_msg,
                error=str(e)
            )

