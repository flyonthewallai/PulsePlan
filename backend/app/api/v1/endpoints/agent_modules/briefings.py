"""
Briefings API endpoints
Handles daily briefing retrieval and manual generation
"""
import logging
from datetime import date, datetime
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, CurrentUser
from app.database.repositories.integration_repositories import get_briefings_repository
from app.database.repositories.user_repositories.user_repository import get_user_repository
from app.agents.orchestrator import AgentOrchestrator
from app.agents.agent_models import WorkflowType
from app.workers.communication.email_service import get_email_service

logger = logging.getLogger(__name__)
router = APIRouter()


class BriefingResponse(BaseModel):
    """Briefing response model"""
    id: str
    user_id: str
    briefing_date: str
    content: Dict[str, Any]
    generated_at: str
    created_at: str


class TestBriefingRequest(BaseModel):
    """Request to send test briefing"""
    send_email: bool = Field(default=True, description="Whether to send email")
    send_notification: bool = Field(default=False, description="Whether to send iOS notification")


class TestBriefingResponse(BaseModel):
    """Response from test briefing"""
    success: bool
    briefing: Optional[Dict[str, Any]] = None
    email_sent: bool = False
    notification_sent: bool = False
    message: str


@router.get("/today", response_model=BriefingResponse)
async def get_todays_briefing(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get today's briefing for the current user
    Returns cached briefing if available, generates new one if not
    """
    try:
        user_id = UUID(current_user.user_id)
        repository = get_briefings_repository()

        # Try to get cached briefing
        briefing = await repository.get_todays_briefing(user_id)

        if briefing:
            logger.info(f"Returning cached briefing for user {user_id}")
            return BriefingResponse(**briefing)

        # Generate new briefing
        logger.info(f"No cached briefing found for user {user_id}, generating new one")
        orchestrator = AgentOrchestrator()

        workflow_result = await orchestrator.execute_workflow(
            workflow_type=WorkflowType.BRIEFING,
            user_id=str(user_id),
            input_data={"timeframe": "today"}
        )

        if not workflow_result or "error" in workflow_result:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate briefing: {workflow_result.get('error', 'Unknown error')}"
            )

        # Save briefing to database
        briefing_content = {
            "summary": workflow_result.get("summary", ""),
            "greeting": workflow_result.get("greeting", ""),
            "tasks": workflow_result.get("todays_tasks", []),
            "events": workflow_result.get("upcoming_events", []),
            "priorities": workflow_result.get("top_priorities", []),
            "recommendations": workflow_result.get("recommendations", []),
            "free_time_blocks": workflow_result.get("free_time_blocks", ""),
            "reschedule_summary": workflow_result.get("reschedule_summary", ""),
            "raw_result": workflow_result
        }

        saved_briefing = await repository.save_briefing(
            user_id=user_id,
            briefing_date=date.today(),
            content=briefing_content
        )

        logger.info(f"Generated and saved new briefing for user {user_id}")
        return BriefingResponse(**saved_briefing)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting today's briefing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get briefing: {str(e)}"
        )


@router.post("/send-test", response_model=TestBriefingResponse)
async def send_test_briefing(
    request: TestBriefingRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate and send a test briefing immediately
    Used for testing and manual triggers from settings
    """
    try:
        user_id = UUID(current_user.user_id)
        user_email = current_user.email
        
        # Get user's full name from database using repository
        user_repo = get_user_repository()
        user_name = await user_repo.get_full_name(str(user_id)) or "User"

        logger.info(f"Generating test briefing for user {user_id}")

        # Generate fresh briefing
        orchestrator = AgentOrchestrator()
        workflow_result = await orchestrator.execute_workflow(
            workflow_type=WorkflowType.BRIEFING,
            user_id=str(user_id),
            input_data={"timeframe": "today"}
        )

        if not workflow_result or "error" in workflow_result:
            return TestBriefingResponse(
                success=False,
                message=f"Failed to generate briefing: {workflow_result.get('error', 'Unknown error')}"
            )

        # Debug logging to see workflow result structure
        logger.info(f"Workflow result keys: {list(workflow_result.keys())}")
        if "result" in workflow_result:
            logger.info(f"Result keys: {list(workflow_result['result'].keys())}")
            if "briefing" in workflow_result["result"]:
                logger.info(f"Briefing keys: {list(workflow_result['result']['briefing'].keys())}")
                if "content_sections" in workflow_result["result"]["briefing"]:
                    logger.info(f"Content sections keys: {list(workflow_result['result']['briefing']['content_sections'].keys())}")
        
        # Prepare briefing content - use the correct workflow structure
        briefing_content = {
            "briefing": workflow_result.get("result", {}).get("briefing", {}),
            "raw_result": workflow_result
        }
        
        logger.info(f"Briefing content keys: {list(briefing_content.keys())}")
        logger.info(f"Briefing content briefing keys: {list(briefing_content['briefing'].keys())}")

        # Save to database
        repository = get_briefings_repository()
        await repository.save_briefing(
            user_id=user_id,
            briefing_date=date.today(),
            content=briefing_content
        )

        email_sent = False
        notification_sent = False

        # Send email if requested
        if request.send_email:
            try:
                email_service = get_email_service()
                email_result = await email_service.send_daily_briefing(
                    to=user_email,
                    user_name=user_name,
                    briefing_data=briefing_content
                )
                email_sent = email_result.get("success", False)
                # Log without PII (email addresses) for privacy compliance
                logger.info(f"Test briefing email sent to user {user_id}: {email_sent}")
            except Exception as e:
                logger.error(f"Failed to send test briefing email: {e}")

        # Send notification if requested
        if request.send_notification:
            try:
                from app.services.notifications.ios_notification_service import get_ios_notification_service
                ios_service = get_ios_notification_service()

                notification_result = await ios_service.send_notification(
                    user_id=str(user_id),
                    title="Your Daily Briefing",
                    body=briefing_content.get("summary", "Your briefing is ready!"),
                    data={
                        "type": "briefing",
                        "briefing_date": date.today().isoformat()
                    },
                    priority="normal"
                )
                notification_sent = notification_result.get("success", False)
                logger.info(f"Test briefing notification sent to user {user_id}: {notification_sent}")
            except Exception as e:
                logger.error(f"Failed to send test briefing notification: {e}")

        return TestBriefingResponse(
            success=True,
            briefing=briefing_content,
            email_sent=email_sent,
            notification_sent=notification_sent,
            message="Test briefing generated and sent successfully"
        )

    except Exception as e:
        logger.error(f"Error sending test briefing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test briefing: {str(e)}"
        )


@router.get("/history")
async def get_briefing_history(
    days: int = 7,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get recent briefing history for the current user

    Args:
        days: Number of days to look back (default: 7)
    """
    try:
        user_id = UUID(current_user.user_id)
        repository = get_briefings_repository()

        briefings = await repository.get_recent_briefings(user_id, days)

        return {
            "success": True,
            "count": len(briefings),
            "briefings": briefings
        }

    except Exception as e:
        logger.error(f"Error getting briefing history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get briefing history: {str(e)}"
        )

