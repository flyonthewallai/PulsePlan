"""
Minimal workflow supervisor service

Provides a simple conversation layer wrapper so the orchestrator can run
even if advanced supervisor logic is not implemented yet.
"""
from typing import Any, Dict, List, Optional

from ..models.workflow_output import ConversationResponse, WorkflowOutput


class WorkflowSupervisor:
    """Basic supervisor that wraps workflow outputs into user-facing messages."""

    async def supervise_workflow_execution(
        self,
        user_query: str,
        workflow_output: WorkflowOutput,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> ConversationResponse:
        message = self._summarize_output(workflow_output)
        return ConversationResponse(
            message=message,
            workflow_output=workflow_output,
            supervision_context=None,
            requires_follow_up=False,
            suggested_replies=[],
        )

    async def handle_follow_up_message(
        self,
        user_message: str,
        trace_id: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConversationResponse]:
        # Minimal implementation: no stored supervision context
        return None

    def _summarize_output(self, workflow_output: WorkflowOutput) -> str:
        try:
            status = getattr(workflow_output, "status", "success")
            workflow = getattr(workflow_output, "workflow", "workflow")
            if status == status.SUCCESS:  # type: ignore[attr-defined]
                return f"{workflow.capitalize()} completed successfully."
            if status == status.NEEDS_INPUT:  # type: ignore[attr-defined]
                return f"{workflow.capitalize()} needs more information to proceed."
            if status == status.PARTIAL_SUCCESS:  # type: ignore[attr-defined]
                return f"{workflow.capitalize()} completed with partial success."
            if status == status.FAILURE:  # type: ignore[attr-defined]
                error = getattr(workflow_output, "error", None) or "Unknown error"
                return f"{workflow.capitalize()} failed: {error}."
        except Exception:
            pass
        return "Request processed."


_supervisor_instance: Optional[WorkflowSupervisor] = None


async def get_workflow_supervisor() -> WorkflowSupervisor:
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = WorkflowSupervisor()
    return _supervisor_instance












