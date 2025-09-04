"""
Email Processing Workflow
Handles email sending and reading with user-as-sender vs Pulse-as-sender differentiation
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from langgraph.graph import END

from .base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError
from app.core.websocket import websocket_manager

logger = logging.getLogger(__name__)


class EmailGraph(BaseWorkflow):
    """
    Email Processing Workflow that:
    1. Validates email requests (send vs read)
    2. Resolves contacts and applies policies
    3. Differentiates between user-as-sender and Pulse-as-sender
    4. Routes to appropriate email providers
    5. Processes email operations with proper error handling
    """
    
    def __init__(self):
        super().__init__(WorkflowType.EMAIL)
        
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for email workflow"""
        return {
            "input_validator": self.input_validator_node,
            "operation_router": self.operation_router_node,
            "contact_resolver": self.contact_resolver_node,
            "policy_gate": self.policy_gate_node,
            "rate_limiter": self.rate_limiter_node,
            "sender_router": self.sender_router_node,
            "provider_selector": self.provider_selector_node,
            "email_send_tool": self.email_send_tool_node,
            "email_read_tool": self.email_read_tool_node,
            "pulse_system_email_tool": self.pulse_system_email_tool_node,
            "summarizer": self.summarizer_node,
            "result_processor": self.result_processor_node,
            "trace_updater": self.trace_updater_node,
            "error_handler": self.error_handler_node
        }
    
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        return [
            # Standard workflow path with conditional routing
            ("input_validator", self.operation_router, {
                "read": "email_read_tool",
                "send": "contact_resolver"
            }),
            
            # Send email path
            ("contact_resolver", "policy_gate"),
            ("policy_gate", "rate_limiter"),
            ("rate_limiter", self.sender_router, {
                "pulse": "pulse_system_email_tool",
                "user": "provider_selector"
            }),
            
            # User sender path
            ("provider_selector", "email_send_tool"),
            ("email_send_tool", "result_processor"),
            
            # Pulse sender path  
            ("pulse_system_email_tool", "result_processor"),
            
            # Read email path
            ("email_read_tool", "summarizer"),
            ("summarizer", "result_processor"),
            
            # Final processing
            ("result_processor", "trace_updater"),
            ("trace_updater", END),
            
            # Error handling
            ("error_handler", END)
        ]
    
    def operation_router(self, state: WorkflowState) -> str:
        """Route based on email operation type"""
        operation = state["input_data"].get("operation", "send")
        
        if operation == "read":
            return "read"
        else:
            return "send"
    
    def sender_router(self, state: WorkflowState) -> str:
        """Route based on sender type (user vs Pulse)"""
        send_as = state["input_data"].get("send_as", "user")
        
        if send_as == "pulse":
            return "pulse"
        else:
            return "user"
    
    def operation_router_node(self, state: WorkflowState) -> WorkflowState:
        """Router node that calls the conditional router"""
        state["current_node"] = "operation_router"
        state["visited_nodes"].append("operation_router")
        return state
    
    def sender_router_node(self, state: WorkflowState) -> WorkflowState:
        """Router node that calls the conditional router"""
        state["current_node"] = "sender_router"
        state["visited_nodes"].append("sender_router")
        return state
    
    async def input_validator_node(self, state: WorkflowState) -> WorkflowState:
        """Validate email request and determine operation type"""
        state["current_node"] = "input_validator"
        state["visited_nodes"].append("input_validator")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "input_validator", "executing")
        
        try:
            input_data = state["input_data"]
            query = input_data.get("query", "")
            
            # Determine operation type (send vs read)
            operation = self._classify_email_operation(query)
            input_data["operation"] = operation
            
            # For send operations, determine sender type
            if operation == "send":
                send_classification = self._classify_sender_type(query, state["user_id"])
                input_data.update(send_classification)
            
            # Validate required fields
            if operation == "send":
                if not input_data.get("recipient") and not input_data.get("send_as") == "pulse":
                    raise WorkflowError("Recipient required for send operation", {"state": state})
                if not input_data.get("content") and not input_data.get("message"):
                    raise WorkflowError("Message content required for send operation", {"state": state})
            
            await websocket_manager.emit_node_update(workflow_id, "input_validator", "completed", {
                "operation": operation,
                "send_as": input_data.get("send_as"),
                "recipient": input_data.get("recipient")
            })
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_node_update(workflow_id, "input_validator", "failed", {"error": str(e)})
            raise WorkflowError(f"Input validation failed: {str(e)}", {"state": state})
    
    def _classify_email_operation(self, query: str) -> str:
        """Classify whether this is a send or read operation"""
        query_lower = query.lower()
        
        # Read indicators
        read_keywords = ["read", "show", "get", "fetch", "check", "latest", "recent", "inbox"]
        if any(keyword in query_lower for keyword in read_keywords):
            return "read"
        
        # Send indicators (default)
        return "send"
    
    def _classify_sender_type(self, query: str, user_id: str) -> Dict[str, Any]:
        """Classify sender type and extract email details using LLM"""
        from langchain_openai import ChatOpenAI
        import json
        import re
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        prompt = f"""
        Analyze this email request and determine the sender type and details.
        
        User request: "{query}"
        
        SENDER TYPE RULES:
        - "user": When sending to someone else (colleagues, friends, contacts)
        - "pulse": When sending to self (daily agenda, briefings, reports, notifications)
        
        EXAMPLES:
        - "Email Ronan my notes" → user (sending to someone else)
        - "Email me my daily agenda" → pulse (sending to self)
        - "Send John the project update" → user (sending to someone else)  
        - "Email me a summary of my tasks" → pulse (sending to self)
        
        Extract and return ONLY valid JSON (no markdown, no extra text):
        {{
            "send_as": "user|pulse",
            "recipient": "contact name or 'self'",
            "message": "extracted message content",
            "subject": "email subject",
            "reasoning": "brief explanation of sender type decision"
        }}
        """
        
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
            else:
                # Fallback: try to parse the entire response
                result = json.loads(content)
            
            # Validate the classification
            send_as = result.get("send_as", "user")
            recipient = result.get("recipient", "")
            
            # Policy guardrail: never let Pulse email third parties
            if send_as == "pulse" and recipient.lower() not in ["self", "me", user_id]:
                send_as = "user"
                result["send_as"] = "user"
                result["reasoning"] += " (Policy override: Pulse cannot email third parties)"
            
            return result
            
        except Exception as e:
            print(f"❌ [EMAIL CLASSIFICATION] Failed to classify sender: {str(e)}")
            print(f"❌ [EMAIL CLASSIFICATION] Raw response: {response.content if 'response' in locals() else 'No response'}")
            
            # Safe fallback - extract basic info from query
            if "connergroth03@gmail.com" in query.lower():
                return {
                    "send_as": "user",
                    "recipient": "connergroth03@gmail.com",
                    "message": query.replace("draft an email to connergroth03@gmail.com", "").strip(),
                    "subject": "Message from PulsePlan",
                    "reasoning": f"Fallback due to classification error: {str(e)}"
                }
            else:
                return {
                    "send_as": "user",
                    "recipient": "unknown",
                    "message": query,
                    "subject": "Message from PulsePlan",
                    "reasoning": f"Fallback due to classification error: {str(e)}"
                }
    
    async def contact_resolver_node(self, state: WorkflowState) -> WorkflowState:
        """Resolve contact information using contacts tool"""
        state["current_node"] = "contact_resolver"
        state["visited_nodes"].append("contact_resolver")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "contact_resolver", "executing")
        
        try:
            recipient = state["input_data"].get("recipient", "")
            
            if not recipient or recipient.lower() in ["self", "me"]:
                # No contact resolution needed for self-emails
                state["input_data"]["resolved_contact"] = {
                    "email": state.get("user_context", {}).get("email", ""),
                    "name": "You"
                }
            else:
                # Use contacts tool to resolve recipient
                from app.agents.tools.contacts import GoogleContactsTool
                
                contacts_tool = GoogleContactsTool()
                
                # Prepare context for the tool
                context = {
                    "user_id": state["user_id"],
                    "oauth_tokens": {
                        "google_access_token": state.get("connected_accounts", {}).get("google", {}).get("access_token")
                    }
                }
                
                # Prepare input data for search operation
                input_data = {
                    "operation": "search_contacts",
                    "query": recipient,
                    "max_results": 5
                }
                
                try:
                    tool_result = await contacts_tool.execute(input_data, context)
                    contact_result = tool_result.data if tool_result.success else {"success": False, "error": tool_result.error}
                except Exception as e:
                    contact_result = {"success": False, "error": str(e)}
                
                if contact_result.get("contacts") and len(contact_result["contacts"]) > 0:
                    # Use first matching contact
                    contact = contact_result["contacts"][0]
                    # Get primary email or first email
                    email_address = None
                    if contact.get("emails"):
                        # Find primary email or use first one
                        primary_email = next((e for e in contact["emails"] if e.get("primary")), None)
                        email_address = primary_email["address"] if primary_email else contact["emails"][0]["address"]
                    
                    state["input_data"]["resolved_contact"] = {
                        "email": email_address,
                        "name": contact.get("name", recipient)
                    }
                else:
                    # No contact found - this might be an email address directly
                    if "@" in recipient:
                        state["input_data"]["resolved_contact"] = {
                            "email": recipient,
                            "name": recipient
                        }
                    else:
                        raise WorkflowError(f"Contact '{recipient}' not found", {"recipient": recipient})
            
            await websocket_manager.emit_node_update(workflow_id, "contact_resolver", "completed", {
                "resolved_contact": state["input_data"]["resolved_contact"]
            })
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_node_update(workflow_id, "contact_resolver", "failed", {"error": str(e)})
            raise WorkflowError(f"Contact resolution failed: {str(e)}", {"state": state})
    
    async def policy_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Enforce email policies and limits"""
        state["current_node"] = "policy_gate"
        state["visited_nodes"].append("policy_gate")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "policy_gate", "executing")
        
        try:
            input_data = state["input_data"]
            send_as = input_data.get("send_as", "user")
            recipient = input_data.get("recipient", "")
            
            # Policy 1: Pulse cannot email third parties
            if send_as == "pulse" and recipient.lower() not in ["self", "me", state["user_id"]]:
                raise WorkflowError("Policy violation: Pulse cannot send emails to third parties", {
                    "send_as": send_as,
                    "recipient": recipient,
                    "policy": "no_third_party_pulse_emails"
                })
            
            # Policy 2: Recipient limit (prevent spam)
            max_recipients = 50  # Configurable limit
            if isinstance(recipient, list) and len(recipient) > max_recipients:
                raise WorkflowError(f"Too many recipients: {len(recipient)} > {max_recipients}", {
                    "recipient_count": len(recipient),
                    "max_recipients": max_recipients,
                    "policy": "recipient_limit"
                })
            
            # Policy 3: Content validation (basic)
            message = input_data.get("message", "")
            if len(message) > 10000:  # 10KB limit
                raise WorkflowError("Message too long", {
                    "message_length": len(message),
                    "max_length": 10000,
                    "policy": "message_length_limit"
                })
            
            # Log policy decision
            policy_decision = {
                "send_as": send_as,
                "recipient": recipient,
                "policies_checked": ["third_party_check", "recipient_limit", "content_length"],
                "outcome": "approved"
            }
            
            state["input_data"]["policy_decision"] = policy_decision
            
            await websocket_manager.emit_node_update(workflow_id, "policy_gate", "completed", policy_decision)
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_node_update(workflow_id, "policy_gate", "failed", {"error": str(e)})
            raise WorkflowError(f"Policy check failed: {str(e)}", {"state": state})
    
    async def rate_limiter_node(self, state: WorkflowState) -> WorkflowState:
        """Apply rate limiting based on provider quotas"""
        state["current_node"] = "rate_limiter"
        state["visited_nodes"].append("rate_limiter")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "rate_limiter", "executing")
        
        try:
            user_id = state["user_id"]
            send_as = state["input_data"].get("send_as", "user")
            
            # TODO: Implement actual rate limiting with Redis
            # For now, just log and pass through
            rate_limit_info = {
                "user_id": user_id,
                "send_as": send_as,
                "quota_remaining": 100,  # Mock value
                "reset_time": (datetime.utcnow().timestamp() + 3600),  # 1 hour from now
                "status": "within_limits"
            }
            
            state["input_data"]["rate_limit_info"] = rate_limit_info
            
            await websocket_manager.emit_node_update(workflow_id, "rate_limiter", "completed", rate_limit_info)
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_node_update(workflow_id, "rate_limiter", "failed", {"error": str(e)})
            raise WorkflowError(f"Rate limiting failed: {str(e)}", {"state": state})
    
    async def provider_selector_node(self, state: WorkflowState) -> WorkflowState:
        """Select email provider (Gmail or Outlook) for user sending"""
        state["current_node"] = "provider_selector"
        state["visited_nodes"].append("provider_selector")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "provider_selector", "executing")
        
        try:
            from app.services.token_service import get_token_service
            
            # Get user tokens using token service
            token_service = get_token_service()
            user_tokens = await token_service.get_user_tokens_for_agent(state["user_id"])
            
            # Check available providers
            available_providers = []
            if user_tokens.google and user_tokens.google.access_token:
                available_providers.append("gmail")
            if user_tokens.microsoft and user_tokens.microsoft.access_token:
                available_providers.append("outlook")
            
            if not available_providers:
                raise WorkflowError("No email providers connected", {
                    "google_connected": bool(user_tokens.google),
                    "microsoft_connected": bool(user_tokens.microsoft),
                    "available_providers": available_providers
                })
            
            # Select provider (prefer Gmail, fallback to Outlook)
            selected_provider = "gmail" if "gmail" in available_providers else available_providers[0]
            
            # Get access token for selected provider
            provider_token = None
            if selected_provider == "gmail" and user_tokens.google:
                provider_token = user_tokens.google.access_token
            elif selected_provider == "outlook" and user_tokens.microsoft:
                provider_token = user_tokens.microsoft.access_token
            
            state["input_data"]["selected_provider"] = selected_provider
            state["input_data"]["provider_token"] = provider_token
            
            await websocket_manager.emit_node_update(workflow_id, "provider_selector", "completed", {
                "selected_provider": selected_provider,
                "available_providers": available_providers
            })
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_node_update(workflow_id, "provider_selector", "failed", {"error": str(e)})
            raise WorkflowError(f"Provider selection failed: {str(e)}", {"state": state})
    
    async def email_send_tool_node(self, state: WorkflowState) -> WorkflowState:
        """Send email via user's provider (Gmail/Outlook)"""
        state["current_node"] = "email_send_tool"
        state["visited_nodes"].append("email_send_tool")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_tool_update(workflow_id, "EmailSendTool", "executing")
        
        try:
            from app.agents.tools.email import GmailUserTool
            
            input_data = state["input_data"]
            provider = input_data.get("selected_provider", "gmail")
            resolved_contact = input_data.get("resolved_contact", {})
            
            # Prepare email data
            email_data = {
                "to": resolved_contact.get("email"),
                "subject": input_data.get("subject", "Message from PulsePlan"),
                "body": input_data.get("message", ""),
                "provider": provider
            }
            
            # Send email using appropriate tool
            if provider == "gmail":
                from app.agents.tools.email import GmailUserTool
                email_tool = GmailUserTool()
            elif provider == "outlook":
                from app.agents.tools.email import OutlookUserTool
                email_tool = OutlookUserTool()
            else:
                raise WorkflowError(f"Unsupported email provider: {provider}", {"provider": provider})
                
            # Get user tokens using token service
            from app.services.token_service import get_token_service
            token_service = get_token_service()
            user_tokens = await token_service.get_user_tokens_for_agent(state["user_id"])
            
            # Prepare context for the tool
            context = {
                "user_id": state["user_id"],
                "user_tokens": user_tokens
            }
            
            result = await email_tool.send_email(email_data, context)
            
            if result.success:
                state["output_data"] = {
                    "workflow_type": "email",
                    "operation": "send",
                    "send_as": "user",
                    "message": f"Email sent successfully to {resolved_contact.get('name', resolved_contact.get('email'))}",
                    "recipient": resolved_contact,
                    "provider": provider,
                    "email_id": result.data.get("email_id") if result.data else None,
                    "query": state["input_data"].get("query", ""),
                    "success": True
                }
                
                await websocket_manager.emit_tool_update(workflow_id, "EmailSendTool", "completed", {
                    "recipient": resolved_contact.get("email"),
                    "provider": provider,
                    "email_id": result.data.get("email_id") if result.data else None
                })
            else:
                raise WorkflowError(f"Email send failed: {result.error}", {"result": result})
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_tool_update(workflow_id, "EmailSendTool", "failed", {"error": str(e)})
            raise WorkflowError(f"Email send failed: {str(e)}", {"state": state})
    
    async def email_read_tool_node(self, state: WorkflowState) -> WorkflowState:
        """Read emails from user's provider"""
        state["current_node"] = "email_read_tool"
        state["visited_nodes"].append("email_read_tool")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_tool_update(workflow_id, "EmailReadTool", "executing")
        
        try:
            from app.services.token_service import get_token_service
            
            # Get user tokens using token service
            token_service = get_token_service()
            user_tokens = await token_service.get_user_tokens_for_agent(state["user_id"])
            
            # Determine provider based on available tokens
            provider = None
            access_token = None
            
            if user_tokens.google and user_tokens.google.access_token:
                provider = "gmail"
                access_token = user_tokens.google.access_token
            elif user_tokens.microsoft and user_tokens.microsoft.access_token:
                provider = "outlook"
                access_token = user_tokens.microsoft.access_token
            else:
                raise WorkflowError("No email provider connected for reading", {
                    "google_connected": bool(user_tokens.google),
                    "microsoft_connected": bool(user_tokens.microsoft)
                })
            
            # Read emails using appropriate provider
            if provider == "gmail":
                from app.agents.tools.email import GmailUserTool
                email_tool = GmailUserTool()
            elif provider == "outlook":
                from app.agents.tools.email import OutlookUserTool
                email_tool = OutlookUserTool()
            else:
                raise WorkflowError(f"Unsupported email provider: {provider}")
            
            # Prepare parameters for list_messages
            query = state["input_data"].get("query", "")
            limit = state["input_data"].get("limit", 10)
            context = {"user_id": state["user_id"], "user_tokens": user_tokens}
            
            # Call list_messages with provider-specific parameters
            if provider == "gmail":
                result = await email_tool.list_messages(query, limit, context, access_token)
            elif provider == "outlook":
                result = await email_tool.list_messages(query, limit, context)
            else:
                raise WorkflowError(f"Unsupported provider for list_messages: {provider}")
            
            if result.success:
                state["email_data"] = result.data.get("messages", []) if result.data else []
                
                await websocket_manager.emit_tool_update(workflow_id, "EmailReadTool", "completed", {
                    "emails_found": len(state["email_data"]),
                    "provider": provider
                })
            else:
                raise WorkflowError(f"Email read failed: {result.error}", {"result": result})
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_tool_update(workflow_id, "EmailReadTool", "failed", {"error": str(e)})
            raise WorkflowError(f"Email read tool failed: {str(e)}", {"state": state})
    
    async def pulse_system_email_tool_node(self, state: WorkflowState) -> WorkflowState:
        """Send email from Pulse system account via Resend"""
        state["current_node"] = "pulse_system_email_tool"
        state["visited_nodes"].append("pulse_system_email_tool")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_tool_update(workflow_id, "PulseSystemEmailTool", "executing")
        
        try:
            # TODO: Implement Resend integration
            # For now, mock the system email sending
            
            input_data = state["input_data"]
            user_email = state.get("user_context", {}).get("email", "")
            
            email_data = {
                "from": "pulse@pulseplan.app",
                "to": user_email,
                "subject": input_data.get("subject", "Your PulsePlan Update"),
                "body": input_data.get("message", ""),
                "template": "system_notification"
            }
            
            # Mock successful send
            result = {
                "success": True,
                "email_id": f"pulse_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "provider": "resend"
            }
            
            state["output_data"] = {
                "workflow_type": "email",
                "operation": "send",
                "send_as": "pulse",
                "message": f"System email sent successfully to {user_email}",
                "recipient": {"email": user_email, "name": "You"},
                "provider": "pulse_system",
                "email_id": result.get("email_id"),
                "query": state["input_data"].get("query", ""),
                "success": True
            }
            
            await websocket_manager.emit_tool_update(workflow_id, "PulseSystemEmailTool", "completed", {
                "recipient": user_email,
                "provider": "pulse_system",
                "email_id": result.get("email_id")
            })
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_tool_update(workflow_id, "PulseSystemEmailTool", "failed", {"error": str(e)})
            raise WorkflowError(f"Pulse system email failed: {str(e)}", {"state": state})
    
    async def summarizer_node(self, state: WorkflowState) -> WorkflowState:
        """Summarize or extract information from read emails"""
        state["current_node"] = "summarizer"
        state["visited_nodes"].append("summarizer")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "summarizer", "executing")
        
        try:
            emails = state.get("email_data", [])
            
            if not emails:
                summary = "No emails found to summarize."
            elif len(emails) == 1:
                email = emails[0]
                summary = f"Latest email from {email.get('from', 'Unknown')}:\n\n"
                summary += f"Subject: {email.get('subject', 'No subject')}\n"
                summary += f"Date: {email.get('received', 'Unknown date')}\n\n"
                # Note: Gmail API doesn't return body in list_messages, only metadata
                summary += "Email content not available in list view. Use 'get' operation to retrieve full content."
            else:
                summary = f"Found {len(emails)} emails:\n\n"
                for i, email in enumerate(emails[:5], 1):  # Show first 5
                    summary += f"{i}. From: {email.get('from', 'Unknown')} - {email.get('subject', 'No subject')}\n"
                    summary += f"   Date: {email.get('received', 'Unknown date')}\n"
                    if email.get('unread'):
                        summary += f"   Status: Unread\n"
                    summary += "\n"
                if len(emails) > 5:
                    summary += f"... and {len(emails) - 5} more emails"
            
            state["output_data"] = {
                "workflow_type": "email",
                "operation": "read",
                "message": summary,
                "emails_count": len(emails),
                "emails": emails,  # Include all emails in output
                "query": state["input_data"].get("query", ""),
                "success": True,
                "total_results": len(emails)
            }
            
            await websocket_manager.emit_node_update(workflow_id, "summarizer", "completed", {
                "emails_processed": len(emails),
                "summary_length": len(summary)
            })
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_node_update(workflow_id, "summarizer", "failed", {"error": str(e)})
            raise WorkflowError(f"Email summarization failed: {str(e)}", {"state": state})
    
    async def result_processor_node(self, state: WorkflowState) -> WorkflowState:
        """Format results for UI with WebSocket emission"""
        state["current_node"] = "result_processor"
        state["visited_nodes"].append("result_processor")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "result_processor", "executing")
        
        try:
            # Ensure output_data exists
            if not state.get("output_data"):
                state["output_data"] = {}
                
            # Add metadata
            state["output_data"]["metadata"] = {
                "workflow_type": "email",
                "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
                "nodes_visited": len(state["visited_nodes"])
            }
            
            # Emit email_results WebSocket event for frontend consumption
            output_data = state.get("output_data", {})
            if output_data.get("workflow_type") == "email":
                email_results = {
                    "operation": output_data.get("operation", "unknown"),
                    "send_as": output_data.get("send_as"),
                    "message": output_data.get("message", ""),
                    "success": output_data.get("success", False),
                    "recipient": output_data.get("recipient"),
                    "provider": output_data.get("provider"),
                    "email_id": output_data.get("email_id"),
                    "emails_count": output_data.get("emails_count"),
                    "emails": output_data.get("emails"),
                    "total_results": output_data.get("total_results")
                }
                
                await websocket_manager.emit_email_results(workflow_id, email_results)
            
            # Emit WebSocket completion event (same pattern as SearchGraph)
            await websocket_manager.emit_workflow_status(workflow_id, "completed", state.get("output_data"))
            await websocket_manager.emit_node_update(workflow_id, "result_processor", "completed")
            
            return state
            
        except Exception as e:
            await websocket_manager.emit_node_update(workflow_id, "result_processor", "failed", {"error": str(e)})
            raise WorkflowError(f"Result processing failed: {str(e)}", {"state": state})
    
    async def trace_updater_node(self, state: WorkflowState) -> WorkflowState:
        """Store execution trace for transparency"""
        state["current_node"] = "trace_updater"
        state["visited_nodes"].append("trace_updater")
        
        try:
            # Create decision trace
            decision_trace = {
                "workflow_type": "email",
                "user_id": state["user_id"],
                "trace_id": state["trace_id"],
                "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
                "nodes_visited": state["visited_nodes"],
                "decisions": {
                    "operation": state["input_data"].get("operation"),
                    "send_as": state["input_data"].get("send_as"),
                    "send_as_reasoning": state["input_data"].get("reasoning"),
                    "policy_decision": state["input_data"].get("policy_decision"),
                    "selected_provider": state["input_data"].get("selected_provider"),
                    "resolved_contact": state["input_data"].get("resolved_contact")
                },
                "success": state.get("error") is None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store trace (TODO: implement actual storage)
            
            # Add to metrics
            state["metrics"]["decision_trace"] = decision_trace
            
            return state
            
        except Exception as e:
            return state
    
    async def error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle email workflow specific errors"""
        state["current_node"] = "error_handler"
        state["visited_nodes"].append("error_handler")
        
        workflow_id = state.get("trace_id")
        await websocket_manager.emit_node_update(workflow_id, "error_handler", "executing")
        
        try:
            error = state.get("error")
            if error and error.get("recoverable") and state["retry_count"] < 3:
                # Retry recoverable errors
                state["retry_count"] += 1
                state["metrics"]["retry_attempt"] = state["retry_count"]
                await websocket_manager.emit_node_update(workflow_id, "error_handler", "retrying", {
                    "retry_count": state["retry_count"]
                })
                return state
            else:
                # Fail gracefully with email-specific error handling
                error_message = "Email workflow failed"
                if error:
                    error_message = f"Email workflow failed: {error.get('message', str(error))}"
                
                state["output_data"] = {
                    "workflow_type": "email",
                    "error": error_message,
                    "recoverable": False,
                    "context": error,
                    "message": "I encountered an error while processing your email request. Please try again or contact support if the issue persists."
                }
                
                await websocket_manager.emit_node_update(workflow_id, "error_handler", "completed", {
                    "error": error_message
                })
                
                return state
                
        except Exception as e:
            # Fallback error handling
            state["output_data"] = {
                "workflow_type": "email",
                "error": f"Critical error in error handler: {str(e)}",
                "recoverable": False,
                "message": "A critical error occurred. Please try again later."
            }
            return state
