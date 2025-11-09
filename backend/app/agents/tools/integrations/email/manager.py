"""
Email Manager Tool
Smart email routing and management with contact suggestions
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.agents.tools.core.base import EmailTool, ToolResult
from .models import (
    EmailDraft, ContactSuggestion, EmailSender, EmailProvider,
    EmailVerificationRequired
)
from .router import SmartEmailRouter
from .gmail_provider import GmailUserTool
from .outlook_provider import OutlookUserTool
from .system_provider import SystemEmailTool
from app.services.auth.token_service import get_token_service
from app.services.infrastructure.user_preferences import get_user_preferences_service
from app.agents.tools.data.contacts import GoogleContactsTool

logger = logging.getLogger(__name__)


class EmailManagerTool(EmailTool):
    """
    Smart email manager that routes to appropriate provider
    """

    def __init__(self):
        super().__init__(
            name="email_manager",
            description="Smart email routing for user and agent sending"
        )

        # Initialize provider tools
        self.gmail_tool = GmailUserTool()
        self.outlook_tool = OutlookUserTool()
        self.system_tool = SystemEmailTool()

    def get_required_tokens(self) -> List[str]:
        """Get required tokens for email manager"""
        return ["google", "microsoft"]  # Can work with either

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate email manager input"""
        operation = input_data.get("operation")
        if operation not in ["send", "list", "get", "draft"]:
            return False

        if operation == "send":
            if not input_data.get("to") or not input_data.get("subject"):
                return False

        return True

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute email operation with mandatory user verification for sends"""
        try:
            operation = input_data["operation"]
            sender = EmailSender(input_data.get("sender", "user"))
            user_id = context.get("user_id")

            if not user_id:
                return ToolResult(
                    success=False,
                    data={},
                    error="User ID required for email operations",
                    metadata={"tool": "email_manager"}
                )

            # For send operations, ALWAYS require user approval
            if operation == "send":
                return await self._handle_send_with_verification(input_data, context, sender, user_id)

            # For read operations, proceed normally
            elif operation in ["list", "get"]:
                return await self._handle_read_operation(input_data, context, sender, user_id)

            elif operation == "draft":
                return await self._handle_draft_operation(input_data, context, sender, user_id)

            elif operation == "approve_send":
                return await self._handle_approved_send(input_data, context, user_id)

            else:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Unsupported operation: {operation}",
                    metadata={"tool": "email_manager"}
                )

        except EmailVerificationRequired as e:
            # This is expected for send operations - return draft for user approval
            return ToolResult(
                success=False,
                data={
                    "requires_approval": True,
                    "draft": e.draft.dict(),
                    "message": e.message
                },
                error="USER_APPROVAL_REQUIRED",
                metadata={"tool": "email_manager", "verification_required": True}
            )

        except Exception as e:
            logger.error(f"Email tool execution error: {str(e)}")
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                metadata={"tool": "email_manager"}
            )

    async def _handle_send_with_verification(
        self, input_data: Dict[str, Any], context: Dict[str, Any],
        sender: EmailSender, user_id: str
    ) -> ToolResult:
        """Handle send operation with mandatory user verification"""
        # Get user's connected accounts securely
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(user_id)

        # Determine best provider
        connected_accounts = {}
        if user_tokens.google:
            connected_accounts["google"] = user_tokens.google.dict()
        if user_tokens.microsoft:
            connected_accounts["microsoft"] = user_tokens.microsoft.dict()

        provider = SmartEmailRouter.determine_best_provider(
            sender=sender,
            connected_accounts=connected_accounts,
            user_preference=input_data.get("preferred_provider")
        )

        # Create draft for user verification
        draft_id = f"draft_{user_id}_{datetime.utcnow().timestamp()}"

        # Determine sender email
        sender_email = "noreply@pulseplan.ai"
        if provider == EmailProvider.GOOGLE and user_tokens.google:
            # Get user email from Google token (would need API call)
            sender_email = context.get("user_email", "user@gmail.com")
        elif provider == EmailProvider.OUTLOOK and user_tokens.microsoft:
            # Get user email from Microsoft token (would need API call)
            sender_email = context.get("user_email", "user@outlook.com")

        # Convert recipients to list if string
        recipients = input_data.get("to", [])
        if isinstance(recipients, str):
            recipients = [recipients]

        draft = EmailDraft(
            to=recipients,
            subject=input_data.get("subject", ""),
            body=input_data.get("body", ""),
            sender_email=sender_email,
            provider=provider.value,
            draft_id=draft_id
        )

        # ALWAYS require user approval for email sends
        raise EmailVerificationRequired(
            draft=draft,
            message=f"PulsePlan needs your approval to send this email to {', '.join(recipients)}"
        )

    async def _handle_read_operation(
        self, input_data: Dict[str, Any], context: Dict[str, Any],
        sender: EmailSender, user_id: str
    ) -> ToolResult:
        """Handle read operations (list, get)"""
        # Get user's tokens securely
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(user_id)

        connected_accounts = {}
        if user_tokens.google:
            connected_accounts["google"] = user_tokens.google.dict()
        if user_tokens.microsoft:
            connected_accounts["microsoft"] = user_tokens.microsoft.dict()

        if not connected_accounts:
            return ToolResult(
                success=False,
                data={},
                error="No email accounts connected. Please connect Gmail or Outlook first.",
                metadata={"tool": "email_manager"}
            )

        provider = SmartEmailRouter.determine_best_provider(
            sender=sender,
            connected_accounts=connected_accounts,
            user_preference=input_data.get("preferred_provider")
        )

        # Route to appropriate tool with tokens
        if provider == EmailProvider.GMAIL:
            tool = self.gmail_tool
        elif provider == EmailProvider.OUTLOOK:
            tool = self.outlook_tool
        else:
            return ToolResult(
                success=False,
                data={},
                error="System email doesn't support reading operations",
                metadata={"tool": "email_manager"}
            )

        # Add token to context
        context_with_tokens = {**context, "user_tokens": user_tokens}
        tool_input = {**input_data, "provider": provider.value}

        return await tool.execute(tool_input, context_with_tokens)

    async def _handle_draft_operation(
        self, input_data: Dict[str, Any], context: Dict[str, Any],
        sender: EmailSender, user_id: str
    ) -> ToolResult:
        """Handle draft creation"""
        # Get user's tokens securely
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(user_id)

        connected_accounts = {}
        if user_tokens.google:
            connected_accounts["google"] = user_tokens.google.dict()
        if user_tokens.microsoft:
            connected_accounts["microsoft"] = user_tokens.microsoft.dict()

        if not connected_accounts:
            return ToolResult(
                success=False,
                data={},
                error="No email accounts connected. Please connect Gmail or Outlook first.",
                metadata={"tool": "email_manager"}
            )

        provider = SmartEmailRouter.determine_best_provider(
            sender=sender,
            connected_accounts=connected_accounts,
            user_preference=input_data.get("preferred_provider")
        )

        # Route to appropriate tool
        if provider == EmailProvider.GMAIL:
            tool = self.gmail_tool
        elif provider == EmailProvider.OUTLOOK:
            tool = self.outlook_tool
        else:
            return ToolResult(
                success=False,
                data={},
                error="System email doesn't support draft creation",
                metadata={"tool": "email_manager"}
            )

        # Add token to context
        context_with_tokens = {**context, "user_tokens": user_tokens}
        tool_input = {**input_data, "provider": provider.value}

        return await tool.execute(tool_input, context_with_tokens)

    async def _handle_approved_send(
        self, input_data: Dict[str, Any], context: Dict[str, Any], user_id: str
    ) -> ToolResult:
        """Handle sending after user approval with contact suggestions"""
        draft_id = input_data.get("draft_id")
        if not draft_id:
            return ToolResult(
                success=False,
                data={},
                error="Draft ID required for approved send",
                metadata={"tool": "email_manager"}
            )

        # TODO: Retrieve draft from cache/database and send
        # For now, simulate successful send

        # Extract recipients from draft (for now, get from input_data)
        recipients = input_data.get("to", [])
        if isinstance(recipients, str):
            recipients = [recipients]

        # Check for contact suggestions after successful send
        contact_suggestions = await self._check_recipients_in_contacts(
            recipients, user_id, context
        )

        # Format success message with contact suggestions
        base_message = "Email sent successfully!"
        suggestion_message = await self._format_contact_suggestions_message(contact_suggestions)
        full_message = base_message + suggestion_message

        return ToolResult(
            success=True,
            data={
                "message_id": f"approved_{draft_id}",
                "sent_at": datetime.utcnow().isoformat(),
                "status": "sent_with_approval",
                "contact_suggestions": [s.dict() for s in contact_suggestions],
                "message": full_message
            },
            metadata={"tool": "email_manager", "approved_send": True}
        )

    # Implement abstract methods from EmailTool
    async def send_email(self, email_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send email using best available provider (with mandatory user verification)"""
        input_data = {
            "operation": "send",
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "body": email_data.get("body"),
            "sender": email_data.get("sender", "user")
        }
        return await self.execute(input_data, context)

    async def list_emails(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List emails using best available provider"""
        input_data = {
            "operation": "list",
            "query": filters.get("query", ""),
            "limit": filters.get("limit", 50),
            "sender": "user"  # Only user can list their messages
        }
        return await self.execute(input_data, context)

    async def _check_recipients_in_contacts(
        self, recipients: List[str], user_id: str, context: Dict[str, Any]
    ) -> List[ContactSuggestion]:
        """Check which recipients are not in user's contacts and suggest adding them"""
        try:
            # Check user preferences first
            preferences_service = get_user_preferences_service()
            if not await preferences_service.should_suggest_contacts(user_id):
                logger.info(f"User {user_id} has contact suggestions disabled")
                return []

            # Get user's tokens to check if they have contacts access
            token_service = get_token_service()
            user_tokens = await token_service.get_user_tokens_for_agent(user_id)

            if not user_tokens or not user_tokens.google:
                # No contacts access available
                return []

            # Check if contacts scope is available
            if not await token_service.has_contacts_access(user_id, "google"):
                logger.info(f"User {user_id} doesn't have contacts access, skipping contact suggestions")
                return []

            # Initialize contacts tool
            contacts_tool = GoogleContactsTool()
            contact_suggestions = []

            # Check each recipient
            for email in recipients:
                if isinstance(email, str) and "@" in email:
                    email_domain = email.split("@")[1] if "@" in email else None

                    # Check if this email should be auto-added
                    should_auto_add = await preferences_service.should_auto_add_contacts(user_id, email_domain)

                    # Search for this email in contacts
                    search_result = await contacts_tool.execute(
                        {
                            "operation": "search_contacts",
                            "query": email,
                            "max_results": 1
                        },
                        {
                            "user_id": user_id,
                            "oauth_tokens": {
                                "google_access_token": user_tokens.google.access_token
                            }
                        }
                    )

                    # If not found in contacts, suggest adding
                    if search_result.success and search_result.data.get("contacts_found", 0) == 0:
                        # Extract name from email if possible
                        name = email.split("@")[0].replace(".", " ").title() if "." in email.split("@")[0] else None

                        suggested_action = "auto_add" if should_auto_add else "add_to_contacts"

                        contact_suggestions.append(ContactSuggestion(
                            email=email,
                            name=name,
                            suggested_action=suggested_action
                        ))

                        # If auto-add is enabled, add the contact immediately
                        if should_auto_add:
                            await self._auto_add_contact(email, name, user_id, user_tokens.google.access_token)

            return contact_suggestions

        except Exception as e:
            logger.warning(f"Error checking contacts for user {user_id}: {str(e)}")
            return []  # Fail gracefully, don't block email sending

    async def _auto_add_contact(self, email: str, name: Optional[str], user_id: str, access_token: str) -> bool:
        """Automatically add a contact to user's Google Contacts"""
        try:
            # TODO: Implement actual contact creation via Google People API
            # For now, just log the action
            # Log without PII (email addresses) for privacy compliance
            logger.info(f"Auto-adding contact for user {user_id}")

            # This would be implemented with the Google People API:
            # headers = {"Authorization": f"Bearer {access_token}"}
            # contact_data = {
            #     "names": [{"givenName": name or email.split("@")[0]}],
            #     "emailAddresses": [{"value": email, "type": "other"}]
            # }
            # response = requests.post(
            #     "https://people.googleapis.com/v1/people:createContact",
            #     headers=headers,
            #     json=contact_data
            # )

            return True

        except Exception as e:
            logger.error(f"Error auto-adding contact {email} for user {user_id}: {str(e)}")
            return False

    async def _format_contact_suggestions_message(self, suggestions: List[ContactSuggestion]) -> str:
        """Format contact suggestions into a user-friendly message"""
        if not suggestions:
            return ""

        if len(suggestions) == 1:
            email = suggestions[0].email
            return f"\n\nTip: {email} isn't in your contacts yet. Would you like me to add them for easier messaging in the future?"
        else:
            emails = [s.email for s in suggestions]
            if len(emails) == 2:
                email_list = f"{emails[0]} and {emails[1]}"
            else:
                email_list = f"{', '.join(emails[:-1])}, and {emails[-1]}"

            return f"\n\nTip: {email_list} aren't in your contacts yet. Would you like me to add them for easier messaging in the future?"


class EmailIntegrationTool:
    """
    Simplified email tool for agent workflows
    Handles natural language email requests and routes to appropriate tools
    """

    def __init__(self):
        self.manager = EmailManagerTool()

    async def _execute(self, user_id: str, query: str, user_context: dict = None, connected_accounts: dict = None) -> dict:
        """
        Execute email operation from natural language query

        Args:
            user_id: User ID
            query: Natural language query (e.g., "read my past 5 emails", "send email to john")
            user_context: User context
            connected_accounts: Connected accounts info

        Returns:
            Dict with operation result
        """
        try:
            # Parse natural language query to determine operation
            query_lower = query.lower().strip()

            # Determine operation from query
            if any(word in query_lower for word in ["send", "email to", "compose", "write"]):
                operation = "send"
                # Extract recipient, subject, body from query
                # For now, simulate extraction
                result = await self._handle_send_request(query, user_id, user_context or {})
            elif any(word in query_lower for word in ["read", "show", "list", "check", "inbox", "emails"]):
                operation = "list"
                # Extract filters from query (e.g., "past 5 emails" -> limit: 5)
                limit = self._extract_limit(query)
                result = await self._handle_list_request(query, user_id, limit, user_context or {})
            else:
                return {
                    "success": False,
                    "error": "I'm not sure what email operation you'd like me to perform. You can ask me to read your emails or compose a new email.",
                    "message": "Please specify if you'd like to read emails or send an email."
                }

            return result

        except Exception as e:
            logger.error(f"Email integration error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"I encountered an error processing your email request: {str(e)}"
            }

    def _extract_limit(self, query: str) -> int:
        """Extract number limit from query"""
        import re

        # Look for numbers in the query
        numbers = re.findall(r'\d+', query)
        if numbers:
            try:
                return min(int(numbers[0]), 50)  # Cap at 50 for performance
            except (ValueError, IndexError):
                pass

        # Default limits based on context
        if "recent" in query.lower() or "latest" in query.lower():
            return 10

        return 20  # Default

    async def _handle_send_request(self, query: str, user_id: str, user_context: dict) -> dict:
        """Handle email sending requests"""
        try:
            # For send requests, we need to extract recipient, subject, body
            # This is a simplified version - in production you'd use NLP

            # For now, return error asking for more specific information
            return {
                "success": False,
                "error": "EMAIL_COMPOSE_NOT_IMPLEMENTED",
                "message": "Email composition from natural language is not yet implemented. Please use the email compose feature in the app.",
                "requires_compose_ui": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process send request: {str(e)}"
            }

    async def _handle_list_request(self, query: str, user_id: str, limit: int, user_context: dict) -> dict:
        """Handle email listing requests"""
        try:
            # Prepare input for email manager
            input_data = {
                "operation": "list",
                "query": "",  # Could extract search terms from query
                "limit": limit,
                "sender": "user"
            }

            context = {
                "user_id": user_id,
                "user_context": user_context
            }

            # Execute via email manager
            result = await self.manager.execute(input_data, context)

            if result.success:
                messages = result.data.get("messages", [])
                provider = result.data.get("provider", "unknown")

                # Format response for natural language
                if messages:
                    message_summaries = []
                    for i, msg in enumerate(messages, 1):
                        summary = f"{i}. **{msg.get('subject', 'No Subject')}**\n   From: {msg.get('from', 'Unknown')}\n   {msg.get('received', 'No date')}"
                        if msg.get('unread'):
                            summary += " *(unread)*"
                        message_summaries.append(summary)

                    response_message = f"Here are your {len(messages)} most recent emails from {provider.title()}:\n\n" + "\n\n".join(message_summaries)

                    return {
                        "success": True,
                        "message": response_message,
                        "data": result.data,
                        "email_count": len(messages),
                        "provider": provider
                    }
                else:
                    return {
                        "success": True,
                        "message": f"No emails found in your {provider.title()} inbox.",
                        "data": result.data,
                        "email_count": 0,
                        "provider": provider
                    }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": f"Failed to retrieve emails: {result.error}"
                }

        except Exception as e:
            logger.error(f"Email list request error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list emails: {str(e)}"
            }
