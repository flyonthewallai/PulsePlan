"""
Email Management Endpoints
Handles email operations, draft approvals, and OAuth email management
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_user, CurrentUser
from app.agents.tools.email import EmailManagerTool, EmailVerificationRequired
from app.services.token_service import get_token_service
from app.config.redis import get_redis_client

logger = logging.getLogger(__name__)
router = APIRouter()


class EmailSendRequest(BaseModel):
    to: List[str]
    subject: str
    body: str
    preferred_provider: Optional[str] = None


class EmailDraftApproval(BaseModel):
    draft_id: str
    approved: bool


class EmailListRequest(BaseModel):
    query: Optional[str] = ""
    limit: Optional[int] = 50
    preferred_provider: Optional[str] = None


class EmailGetRequest(BaseModel):
    message_id: str
    preferred_provider: Optional[str] = None


@router.post("/send")
async def send_email(
    request: EmailSendRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Send email with mandatory user approval
    This endpoint will always return a draft that requires approval
    """
    try:
        email_tool = EmailManagerTool()
        
        # Create context for the email tool
        context = {
            "user_id": current_user.user_id,
            "user_context": {"email": current_user.email}
        }
        
        # Execute send operation (this will always require approval)
        result = await email_tool.execute({
            "operation": "send",
            "to": request.to,
            "subject": request.subject,
            "body": request.body,
            "preferred_provider": request.preferred_provider,
            "sender": "user"
        }, context)
        
        # This should always return requires_approval=True
        if result.metadata and result.metadata.get("verification_required"):
            return {
                "success": False,
                "requires_approval": True,
                "draft": result.data.get("draft"),
                "message": result.data.get("message", "Email requires approval")
            }
        elif result.success:
            # This shouldn't happen with our safety constraints
            logger.warning(f"Email sent without approval for user {current_user.user_id}")
            return {
                "success": True,
                "message_id": result.data.get("message_id"),
                "warning": "Email was sent directly - this should not happen"
            }
        else:
            return {
                "success": False,
                "error": result.error
            }
            
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email send request: {str(e)}"
        )


@router.post("/approve-draft")
async def approve_draft(
    request: EmailDraftApproval,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Approve and send a draft email
    """
    if not request.approved:
        # User rejected the draft - just return success
        return {
            "success": True,
            "message": "Email draft cancelled by user"
        }
    
    try:
        email_tool = EmailManagerTool()
        
        # Create context for the email tool
        context = {
            "user_id": current_user.user_id,
            "user_context": {"email": current_user.email}
        }
        
        # Execute approved send
        result = await email_tool.execute({
            "operation": "approve_send",
            "draft_id": request.draft_id
        }, context)
        
        if result.success:
            return {
                "success": True,
                "message_id": result.data.get("message_id"),
                "sent_at": result.data.get("sent_at"),
                "message": "Email sent successfully with user approval"
            }
        else:
            return {
                "success": False,
                "error": result.error
            }
            
    except Exception as e:
        logger.error(f"Error in approve_draft endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve and send email: {str(e)}"
        )


@router.post("/list")
async def list_emails(
    request: EmailListRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List emails from user's connected accounts
    """
    try:
        email_tool = EmailManagerTool()
        
        # Create context for the email tool
        context = {
            "user_id": current_user.user_id,
            "user_context": {"email": current_user.email}
        }
        
        # Execute list operation
        result = await email_tool.execute({
            "operation": "list",
            "query": request.query,
            "limit": request.limit,
            "preferred_provider": request.preferred_provider
        }, context)
        
        if result.success:
            return {
                "success": True,
                "messages": result.data.get("messages", []),
                "total": result.data.get("total", 0),
                "provider": result.data.get("provider")
            }
        else:
            return {
                "success": False,
                "error": result.error
            }
            
    except Exception as e:
        logger.error(f"Error in list_emails endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list emails: {str(e)}"
        )


@router.post("/get")
async def get_email(
    request: EmailGetRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a specific email message
    """
    try:
        email_tool = EmailManagerTool()
        
        # Create context for the email tool
        context = {
            "user_id": current_user.user_id,
            "user_context": {"email": current_user.email}
        }
        
        # Execute get operation
        result = await email_tool.execute({
            "operation": "get",
            "message_id": request.message_id,
            "preferred_provider": request.preferred_provider
        }, context)
        
        if result.success:
            return {
                "success": True,
                "message": result.data.get("message")
            }
        else:
            return {
                "success": False,
                "error": result.error
            }
            
    except Exception as e:
        logger.error(f"Error in get_email endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email: {str(e)}"
        )


@router.get("/connection-status")
async def get_email_connection_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get email connection status (reuses OAuth connection status)
    """
    try:
        token_service = get_token_service()
        connection_status = await token_service.get_user_connection_status(current_user.user_id)
        
        # Convert to email-specific format
        connections = []
        
        if connection_status.google:
            connections.append({
                "provider": "google",
                "connected": True,
                "user_email": None,  # Would need API call to get actual email
                "scopes": ["gmail.send", "gmail.readonly"]  # From OAuth scopes
            })
        else:
            connections.append({
                "provider": "google",
                "connected": False
            })
        
        if connection_status.microsoft:
            connections.append({
                "provider": "microsoft", 
                "connected": True,
                "user_email": None,  # Would need API call to get actual email
                "scopes": ["mail.send", "mail.read"]  # From OAuth scopes
            })
        else:
            connections.append({
                "provider": "microsoft",
                "connected": False
            })
        
        return connections
        
    except Exception as e:
        logger.error(f"Error getting email connection status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection status: {str(e)}"
        )


@router.post("/create-draft")
async def create_draft(
    request: EmailSendRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a draft email (doesn't send)
    """
    try:
        email_tool = EmailManagerTool()
        
        # Create context for the email tool
        context = {
            "user_id": current_user.user_id,
            "user_context": {"email": current_user.email}
        }
        
        # Execute draft operation
        result = await email_tool.execute({
            "operation": "draft",
            "to": request.to,
            "subject": request.subject,
            "body": request.body,
            "preferred_provider": request.preferred_provider
        }, context)
        
        if result.success:
            return {
                "success": True,
                "draft_id": result.data.get("draft_id"),
                "created_at": result.data.get("created_at")
            }
        else:
            return {
                "success": False,
                "error": result.error
            }
            
    except Exception as e:
        logger.error(f"Error in create_draft endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {str(e)}"
        )