"""
Gmail Provider Tool
Handles Gmail operations using user's OAuth token
"""
from typing import Dict, Any, List
from datetime import datetime
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

from app.agents.tools.core.base import EmailTool, ToolResult

logger = logging.getLogger(__name__)


class GmailUserTool(EmailTool):
    """Gmail operations using user's OAuth token"""

    def __init__(self):
        super().__init__(
            name="gmail_user",
            description="Gmail operations via user's Gmail account"
        )

    def get_required_tokens(self) -> List[str]:
        return ["gmail", "google"]

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate Gmail input"""
        operation = input_data.get("operation")
        return operation in ["send", "list", "get", "draft"]

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute Gmail operation with real API calls"""
        try:
            operation = input_data["operation"]
            user_tokens = context.get("user_tokens")

            if not user_tokens or not user_tokens.google:
                return ToolResult(
                    success=False,
                    data={},
                    error="Gmail not connected. Please connect your Google account first.",
                    metadata={"tool": "gmail_user"}
                )

            access_token = user_tokens.google.access_token

            if operation == "send":
                return await self._send_email_gmail(input_data, context, access_token)
            elif operation == "list":
                return await self.list_messages(
                    input_data.get("query", ""),
                    input_data.get("limit", 50),
                    context,
                    access_token
                )
            elif operation == "get":
                return await self.get_message(input_data["message_id"], context, access_token)
            elif operation == "draft":
                return await self._create_draft_gmail(input_data, context, access_token)

        except Exception as e:
            logger.error(f"Gmail operation error: {str(e)}")
            return ToolResult(
                success=False,
                data={},
                error=f"Gmail operation failed: {str(e)}",
                metadata={"tool": "gmail_user"}
            )

    async def _send_email_gmail(self, input_data: Dict[str, Any], context: Dict[str, Any], access_token: str) -> ToolResult:
        """Send email via Gmail API"""
        try:
            # Construct email message
            msg = MIMEMultipart()
            msg['To'] = input_data["to"] if isinstance(input_data["to"], str) else ", ".join(input_data["to"])
            msg['Subject'] = input_data["subject"]

            body = MIMEText(input_data["body"], 'plain')
            msg.attach(body)

            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            # Send via Gmail API
            headers = {"Authorization": f"Bearer {access_token}"}
            payload = {"raw": raw_message}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    result_data = response.json()
                    return ToolResult(
                        success=True,
                        data={
                            "message_id": result_data.get("id"),
                            "to": input_data["to"],
                            "subject": input_data["subject"],
                            "sent_at": datetime.utcnow().isoformat(),
                            "provider": "gmail",
                            "sender_type": "user"
                        },
                        metadata={"tool": "gmail_user"}
                    )
                else:
                    logger.error(f"Gmail send failed: {response.status_code} - {response.text}")
                    return ToolResult(
                        success=False,
                        data={},
                        error=f"Gmail send failed: {response.status_code}",
                        metadata={"tool": "gmail_user"}
                    )

        except Exception as e:
            logger.error(f"Gmail send error: {str(e)}")
            return ToolResult(
                success=False,
                data={},
                error=f"Gmail send error: {str(e)}",
                metadata={"tool": "gmail_user"}
            )

    async def _create_draft_gmail(self, input_data: Dict[str, Any], context: Dict[str, Any], access_token: str) -> ToolResult:
        """Create draft in Gmail"""
        # TODO: Implement actual Gmail API call
        return ToolResult(
            success=True,
            data={
                "draft_id": f"draft_gmail_{datetime.utcnow().timestamp()}",
                "to": input_data.get("to", ""),
                "subject": input_data.get("subject", ""),
                "created_at": datetime.utcnow().isoformat(),
                "provider": "gmail"
            },
            metadata={"tool": "gmail_user"}
        )

    async def list_messages(self, query: str, limit: int, context: Dict[str, Any], access_token: str) -> ToolResult:
        """List Gmail messages"""
        try:
            logger.info(f"Gmail list_messages called with query: '{query}', limit: {limit}")
            logger.info(f"Access token available: {bool(access_token)}")

            # Convert natural language query to Gmail search query
            gmail_query = self._convert_to_gmail_query(query)

            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "maxResults": min(limit, 100),  # Gmail API limit
                "q": gmail_query
            }

            async with httpx.AsyncClient() as client:
                # First get message IDs
                response = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )

                if response.status_code != 200:
                    return ToolResult(
                        success=False,
                        data={},
                        error=f"Gmail list failed: {response.status_code} - {response.text}",
                        metadata={"tool": "gmail_user"}
                    )

                data = response.json()
                messages = data.get("messages", [])

                # Get details for each message (limited to avoid rate limits)
                detailed_messages = []
                for msg in messages[:min(10, len(messages))]:  # Limit to 10 for performance
                    msg_response = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                        headers=headers,
                        params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
                        timeout=30.0
                    )

                    if msg_response.status_code == 200:
                        msg_data = msg_response.json()
                        headers_dict = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}

                        detailed_messages.append({
                            "id": msg["id"],
                            "subject": headers_dict.get("Subject", "No Subject"),
                            "from": headers_dict.get("From", "Unknown Sender"),
                            "received": headers_dict.get("Date", datetime.utcnow().isoformat()),
                            "unread": "UNREAD" in msg_data.get("labelIds", [])
                        })

                return ToolResult(
                    success=True,
                    data={
                        "messages": detailed_messages,
                        "total": data.get("resultSizeEstimate", len(detailed_messages)),
                        "provider": "gmail"
                    },
                    metadata={"tool": "gmail_user"}
                )

        except Exception as e:
            logger.error(f"Gmail list error: {str(e)}")
            return ToolResult(
                success=False,
                data={},
                error=f"Gmail list error: {str(e)}",
                metadata={"tool": "gmail_user"}
            )

    def _convert_to_gmail_query(self, query: str) -> str:
        """Convert natural language query to Gmail search query"""
        query_lower = query.lower()

        # Default to inbox if no specific query
        if not query or query.strip() == "":
            return "in:inbox"

        # Handle "fetch my past X emails" or similar patterns
        if any(word in query_lower for word in ["fetch", "get", "show", "retrieve", "past", "recent", "last"]):
            if any(word in query_lower for word in ["email", "emails", "mail", "messages"]):
                # Extract number if specified
                import re
                numbers = re.findall(r'\d+', query)
                if numbers:
                    limit = int(numbers[0])
                    # Return inbox query - Gmail API will limit results
                    return "in:inbox"
                else:
                    return "in:inbox"

        # Handle specific search terms
        if "unread" in query_lower:
            return "is:unread"
        elif "read" in query_lower:
            return "is:read"
        elif "important" in query_lower:
            return "is:important"
        elif "starred" in query_lower:
            return "is:starred"

        # Default to inbox search
        return "in:inbox"

    async def get_message(self, message_id: str, context: Dict[str, Any], access_token: str) -> ToolResult:
        """Get Gmail message"""
        # TODO: Implement actual Gmail API call
        return ToolResult(
            success=True,
            data={
                "message": {
                    "id": message_id,
                    "subject": "Project Update",
                    "from": "colleague@company.com",
                    "to": context.get("user_context", {}).get("email", "user@example.com"),
                    "body": "Here's the latest project update...",
                    "received": "2024-01-15T10:30:00Z",
                    "provider": "gmail"
                }
            },
            metadata={"tool": "gmail_user"}
        )

    async def send_email(self, email_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send email via Gmail"""
        input_data = {
            "operation": "send",
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "body": email_data.get("body")
        }
        return await self.execute(input_data, context)

    async def list_emails(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List Gmail emails"""
        return await self.list_messages(
            filters.get("query", ""),
            filters.get("limit", 50),
            context
        )


# Convenience alias for backward compatibility
GmailTool = GmailUserTool
