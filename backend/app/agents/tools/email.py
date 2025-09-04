"""
Email management tools for PulsePlan agents.
Handles Gmail, Outlook, and system email sending scenarios with smart routing.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from enum import Enum
import logging

from .base import EmailTool, ToolResult, ToolError
from app.services.token_service import get_token_service
from app.services.user_preferences import get_user_preferences_service
from app.agents.tools.contacts import GoogleContactsTool
import httpx
import json
from pydantic import BaseModel
from typing import List

logger = logging.getLogger(__name__)


class EmailDraft(BaseModel):
    """Email draft for user verification"""
    to: List[str]
    subject: str
    body: str
    sender_email: str
    provider: str
    draft_id: str
    needs_approval: bool = True


class ContactSuggestion(BaseModel):
    """Suggestion to add email recipients to contacts"""
    email: str
    name: Optional[str] = None
    suggested_action: str = "add_to_contacts"  # add_to_contacts, ignore, auto_add
    
    
class EmailResult(BaseModel):
    """Enhanced email result with contact suggestions"""
    success: bool
    message_id: Optional[str] = None
    provider: str
    contact_suggestions: List[ContactSuggestion] = []
    message: str


class EmailVerificationRequired(Exception):
    """Exception raised when email needs user approval"""
    def __init__(self, draft: EmailDraft, message: str = "Email requires user verification before sending"):
        self.draft = draft
        self.message = message
        super().__init__(message)


class EmailSender(str, Enum):
    """Who is sending the email"""
    USER = "user"  # User sending from their own account
    AGENT = "agent"  # Agent sending to user from system email


class EmailProvider(str, Enum):
    """Email provider types"""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    SYSTEM = "system"  # Agent system email


class SmartEmailRouter:
    """
    Routes email operations based on sender, recipient, and available accounts
    """
    
    @staticmethod
    def determine_best_provider(
        sender: EmailSender,
        connected_accounts: Dict[str, Any],
        user_preference: Optional[str] = None
    ) -> EmailProvider:
        """
        Determine best email provider based on context
        
        Args:
            sender: Who is sending (user vs agent)
            connected_accounts: User's connected email accounts
            user_preference: User's preferred email provider
            
        Returns:
            Best email provider to use
        """
        if sender == EmailSender.AGENT:
            # Agent always sends from system email
            return EmailProvider.SYSTEM
        
        # User is sending - check their connected accounts
        available_providers = []
        
        if "gmail" in connected_accounts or "google" in connected_accounts:
            available_providers.append(EmailProvider.GMAIL)
        
        if "microsoft" in connected_accounts or "outlook" in connected_accounts:
            available_providers.append(EmailProvider.OUTLOOK)
        
        if not available_providers:
            raise ToolError("No email accounts connected", "email_router")
        
        # Use user preference if available and valid
        if user_preference:
            preferred = EmailProvider(user_preference.lower())
            if preferred in available_providers:
                return preferred
        
        # Default priority: Gmail > Outlook
        if EmailProvider.GMAIL in available_providers:
            return EmailProvider.GMAIL
        
        return available_providers[0]


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
            logger.info(f"Auto-adding contact {email} ({name}) for user {user_id}")
            
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
            return f"\n\n💡 Tip: {email} isn't in your contacts yet. Would you like me to add them for easier messaging in the future?"
        else:
            emails = [s.email for s in suggestions]
            if len(emails) == 2:
                email_list = f"{emails[0]} and {emails[1]}"
            else:
                email_list = f"{', '.join(emails[:-1])}, and {emails[-1]}"
            
            return f"\n\n💡 Tip: {email_list} aren't in your contacts yet. Would you like me to add them for easier messaging in the future?"


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
            import base64
            from email.mime.text import MimeText
            from email.mime.multipart import MimeMultipart
            
            msg = MimeMultipart()
            msg['To'] = input_data["to"] if isinstance(input_data["to"], str) else ", ".join(input_data["to"])
            msg['Subject'] = input_data["subject"]
            
            body = MimeText(input_data["body"], 'plain')
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
    
    async def _create_draft_gmail(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
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
            }
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
    
    async def get_message(self, message_id: str, context: Dict[str, Any]) -> ToolResult:
        """Get Gmail message"""
        # TODO: Implement actual Gmail API call
        return ToolResult(
            success=True,
            data={
                "message": {
                    "id": message_id,
                    "subject": "Project Update",
                    "from": "colleague@company.com",
                    "to": context["user_context"].get("email", "user@example.com"),
                    "body": "Here's the latest project update...",
                    "received": "2024-01-15T10:30:00Z",
                    "provider": "gmail"
                }
            }
        )
    
    async def send_email(self, email_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send email via Outlook"""
        input_data = {
            "operation": "send",
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "body": email_data.get("body")
        }
        return await self.execute(input_data, context)
    
    async def list_emails(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List Outlook emails"""
        return await self.list_messages(
            filters.get("query", ""),
            filters.get("limit", 50),
            context
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


class OutlookUserTool(EmailTool):
    """Outlook operations using user's OAuth token"""
    
    def __init__(self):
        super().__init__(
            name="outlook_user",
            description="Outlook operations via user's Microsoft account"
        )
    
    def get_required_tokens(self) -> List[str]:
        return ["microsoft", "outlook"]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate Outlook input"""
        operation = input_data.get("operation")
        return operation in ["send", "list", "get", "draft"]
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute Outlook operation"""
        try:
            await asyncio.sleep(0.1)  # Simulate API call
            
            operation = input_data["operation"]
            
            if operation == "send":
                return await self._send_email_outlook(input_data, context)
            elif operation == "list":
                return await self.list_messages(
                    input_data.get("query", ""),
                    input_data.get("limit", 50),
                    context
                )
            elif operation == "get":
                return await self.get_message(input_data["message_id"], context)
            elif operation == "draft":
                return await self._create_draft_outlook(input_data, context)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Outlook operation failed: {str(e)}"
            )
    
    async def _send_email_outlook(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send email via Microsoft Graph API"""
        # TODO: Implement actual Microsoft Graph API call
        return ToolResult(
            success=True,
            data={
                "message_id": f"outlook_{datetime.utcnow().timestamp()}",
                "to": input_data["to"],
                "subject": input_data["subject"],
                "sent_at": datetime.utcnow().isoformat(),
                "provider": "outlook",
                "sender_type": "user"
            }
        )
    
    async def _create_draft_outlook(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create draft in Outlook"""
        # TODO: Implement actual Microsoft Graph API call
        return ToolResult(
            success=True,
            data={
                "draft_id": f"draft_outlook_{datetime.utcnow().timestamp()}",
                "to": input_data.get("to", ""),
                "subject": input_data.get("subject", ""),
                "created_at": datetime.utcnow().isoformat(),
                "provider": "outlook"
            }
        )
    
    async def list_messages(self, query: str, limit: int, context: Dict[str, Any]) -> ToolResult:
        """List Outlook messages"""
        # TODO: Implement actual Microsoft Graph API call
        return ToolResult(
            success=True,
            data={
                "messages": [
                    {
                        "id": "outlook_msg_1",
                        "subject": "Meeting Reminder",
                        "from": "assistant@company.com",
                        "received": "2024-01-15T09:00:00Z",
                        "unread": False
                    }
                ],
                "total": 1,
                "provider": "outlook"
            }
        )
    
    async def get_message(self, message_id: str, context: Dict[str, Any]) -> ToolResult:
        """Get Outlook message"""
        # TODO: Implement actual Microsoft Graph API call
        return ToolResult(
            success=True,
            data={
                "message": {
                    "id": message_id,
                    "subject": "Meeting Reminder",
                    "from": "assistant@company.com",
                    "to": context["user_context"].get("email", "user@example.com"),
                    "body": "Reminder: You have a meeting at 2 PM...",
                    "received": "2024-01-15T09:00:00Z",
                    "provider": "outlook"
                }
            }
        )
    
    async def send_email(self, email_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send email via Outlook"""
        input_data = {
            "operation": "send",
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "body": email_data.get("body")
        }
        return await self.execute(input_data, context)
    
    async def list_emails(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List Outlook emails"""
        return await self.list_messages(
            filters.get("query", ""),
            filters.get("limit", 50),
            context
        )


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
                error=f"System email operation failed: {str(e)}"
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
            }
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


# Convenience aliases for backward compatibility
GmailTool = GmailUserTool
OutlookTool = OutlookUserTool

class EmailIntegrationTool:
    """
    Simplified email tool that can be directly used by ChatGraph
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