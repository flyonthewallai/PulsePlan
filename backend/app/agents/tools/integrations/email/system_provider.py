"""
System Email Provider Tool
Handles system email sending for agent-initiated communications
"""
from typing import Dict, Any, List
from datetime import datetime
import asyncio
import logging

from app.agents.tools.core.base import EmailTool, ToolResult, ToolError

logger = logging.getLogger(__name__)


class SystemEmailTool(EmailTool):
    """
    System email tool for agent-initiated communications
    Uses PulsePlan's own email service
    """

    def __init__(self):
        super().__init__(
            name="system_email",
            description="System email service for agent notifications"
        )

    def get_required_tokens(self) -> List[str]:
        return []  # No OAuth needed, uses system credentials

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate system email input"""
        operation = input_data.get("operation")
        if operation == "send":
            return bool(input_data.get("to") and input_data.get("subject"))
        return operation in ["send"]  # System only sends, doesn't read

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute system email operation"""
        try:
            await asyncio.sleep(0.1)  # Simulate email service call

            operation = input_data["operation"]

            if operation == "send":
                return await self._send_system_email(input_data, context)
            else:
                raise ToolError(f"Operation {operation} not supported by system email", "system_email")

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=f"System email operation failed: {str(e)}",
                metadata={"tool": "system_email"}
            )

    async def _send_system_email(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send email via system email service"""
        # TODO: Implement actual email service (SendGrid, AWS SES, etc.)

        # Add agent branding to emails
        subject = input_data["subject"]
        if not subject.startswith("[PulsePlan]"):
            subject = f"[PulsePlan] {subject}"

        return ToolResult(
            success=True,
            data={
                "message_id": f"system_{datetime.utcnow().timestamp()}",
                "to": input_data["to"],
                "subject": subject,
                "from": "noreply@pulseplan.ai",  # System email address
                "sent_at": datetime.utcnow().isoformat(),
                "provider": "system",
                "sender_type": "agent"
            },
            metadata={"tool": "system_email"}
        )

    async def list_messages(self, query: str, limit: int, context: Dict[str, Any]) -> ToolResult:
        """System email doesn't support listing"""
        raise ToolError("System email doesn't support listing messages", "system_email")

    async def get_message(self, message_id: str, context: Dict[str, Any]) -> ToolResult:
        """System email doesn't support getting messages"""
        raise ToolError("System email doesn't support getting messages", "system_email")

    async def send_email(self, email_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send email via system email service"""
        input_data = {
            "operation": "send",
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "body": email_data.get("body")
        }
        return await self.execute(input_data, context)

    async def list_emails(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """System email doesn't support listing emails"""
        raise ToolError("System email doesn't support listing emails", "system_email")
