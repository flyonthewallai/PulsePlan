"""
Unified Agent API Endpoint
Single endpoint for all agent interactions with optimized processing
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from app.core.auth import get_current_user, CurrentUser

from app.agents.core.orchestration.intent_processor import get_intent_processor, ActionType
from app.agents.core.conversation.conversation_manager import get_conversation_manager
from app.agents.core.conversation.conversation_state_manager import get_conversation_state_manager
from app.agents.core.conversation.websocket_notification_manager import get_websocket_manager
from app.agents.core.orchestration.agent_task_manager import get_agent_task_manager

# Import modular components
from .agent_modules.models import UnifiedAgentRequest, UnifiedAgentResponse, TaskStatusRequest, TaskCancelRequest
from .agent_modules.conversation import get_user_active_conversation, set_user_active_conversation
from .agent_modules.operations import execute_crud_operation_direct, execute_task_listing_direct
from .agent_modules.workflows import execute_workflow_background

logger = logging.getLogger(__name__)
router = APIRouter()




@router.post("/process", response_model=UnifiedAgentResponse)
async def process_unified_query(
    request: UnifiedAgentRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user)
):
    logger.info(f"🎯 [REQUEST] Starting process_unified_query for query: '{request.query}'")
    print(f"🎯 [REQUEST] Starting process_unified_query for query: '{request.query}'")
    """
    Process user query through unified agent pipeline
    """
    try:
        start_time = datetime.utcnow()
        user_id = current_user.user_id

        logger.info(f"🔍 [UNIFIED-AGENT] Processing query from user {user_id}")
        logger.info(f"📝 [UNIFIED-AGENT] Full request data: {request.dict()}")
        logger.info(f"💬 [UNIFIED-AGENT] User query: '{request.query}'")

        # Get services
        intent_processor = get_intent_processor()
        conversation_manager = get_conversation_manager()
        conversation_state_manager = get_conversation_state_manager()
        websocket_manager = get_websocket_manager()
        task_manager = get_agent_task_manager()

        # Get or create conversation with smart continuation logic
        print(f"🗨️ [UNIFIED-AGENT] Request conversation_id: {request.conversation_id}, force_new: {request.force_new_conversation}")

        # If no conversation_id provided and not forcing new, try to get user's most recent active conversation
        target_conversation_id = request.conversation_id
        if not target_conversation_id and not request.force_new_conversation:
            target_conversation_id = await get_user_active_conversation(user_id)
            print(f"🗨️ [UNIFIED-AGENT] Auto-retrieved active conversation: {target_conversation_id}")

        conversation = await conversation_manager.get_or_create_conversation(
            user_id=user_id,
            conversation_id=None if request.force_new_conversation else target_conversation_id
        )
        print(f"🗨️ [UNIFIED-AGENT] Using conversation_id: {conversation.id} (new: {'Yes' if conversation.id != request.conversation_id else 'No'})")

        # Mark this conversation as the user's active one
        await set_user_active_conversation(user_id, conversation.id)

        # Add user message to conversation
        await conversation_manager.add_message(
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=request.query,
            metadata=request.metadata
        )

        # Get conversation history if requested
        conversation_history = []
        if request.include_history:
            conversation_history = await conversation_manager.get_conversation_history(
                conversation_id=conversation.id,
                user_id=user_id,
                limit=10,
                include_summary=True
            )
            print(f"📚 [UNIFIED-AGENT] Retrieved conversation history: {len(conversation_history)} turns")
            for i, turn in enumerate(conversation_history):
                print(f"   Turn {i+1}: {turn.get('role', 'unknown')} - '{turn.get('content', '')[:100]}...'")
        else:
            print(f"📚 [UNIFIED-AGENT] Conversation history not included in request")

        # Get conversation state
        conversation_state = await conversation_state_manager.get_conversation_state(
            conversation_id=conversation.id,
            user_id=user_id
        )

        # Process intent with unified processor
        logger.info(f"🧠 [UNIFIED-AGENT] Processing intent for query: '{request.query}'")
        intent_result = await intent_processor.process_user_query(
            user_query=request.query,
            user_id=user_id,
            conversation_id=conversation.id,
            conversation_history=conversation_history
        )
        logger.info(f"🧠 [INTENT] Processed intent: action={intent_result.action}, workflow_type={intent_result.workflow_type}")
        logger.info(f"🎯 [UNIFIED-AGENT] Intent result: {intent_result}")

        # Phase 1: Send immediate response via WebSocket (skip for simple CRUD operations)
        simple_crud_actions = [ActionType.LIST_TASKS, ActionType.DELETE_TASK]
        if intent_result.action not in simple_crud_actions:
            immediate_message = intent_result.immediate_response or "I'm processing your request..."
            await websocket_manager.send_immediate_response(
                user_id=user_id,
                message=immediate_message,
                action=intent_result.action.value,
                requires_clarification=intent_result.requires_clarification,
                clarification_question=intent_result.clarification_question,
                can_switch=intent_result.can_switch_workflow,
                suggested_workflows=intent_result.suggested_workflows
            )

        # Handle clarification requests
        if intent_result.requires_clarification:
            clarification = await conversation_state_manager.add_clarification_request(
                conversation_id=conversation.id,
                user_id=user_id,
                question=intent_result.clarification_question,
                context={"intent": intent_result.intent, "action": intent_result.action.value}
            )
            
            await websocket_manager.send_clarification_request(
                user_id=user_id,
                clarification_id=clarification.id,
                question=clarification.question,
                context=clarification.context
            )

        # Create task card if needed (skip if clarification is required)
        task_id = None
        if intent_result.requires_task_card and not intent_result.requires_clarification:
            task_id = await intent_processor.create_task_card_if_needed(
                result=intent_result,
                user_id=user_id,
                conversation_id=conversation.id
            )
            
            # Add task to conversation state queue
            if task_id:
                task_card = await task_manager.get_task_card(task_id)
                if task_card:
                    await conversation_state_manager.add_task_to_queue(
                        conversation_id=conversation.id,
                        user_id=user_id,
                        task_card=task_card
                    )

        # Add immediate response to conversation if available (skip for CRUD operations that will show success cards)
        simple_crud_actions = [ActionType.LIST_TASKS, ActionType.DELETE_TASK, ActionType.CREATE_TASK, ActionType.UPDATE_TASK, ActionType.COMPLETE_TASK]
        if intent_result.immediate_response and intent_result.action not in simple_crud_actions:
            await conversation_manager.add_message(
                conversation_id=conversation.id,
                user_id=user_id,
                role="assistant",
                content=intent_result.immediate_response,
                metadata={"intent": intent_result.intent, "action": intent_result.action.value}
            )

        # Schedule background workflow execution if needed
        # Skip background tasks if clarification is required
        if not intent_result.requires_clarification:
            logger.info(f"🔀 [ROUTING] Action: {intent_result.action}, workflow_type: {intent_result.workflow_type}, task_id: {task_id}")
            # For LIST_TASKS, execute directly without creating a task card
            if intent_result.action == ActionType.LIST_TASKS:
                logger.info(f"🔀 [ROUTING] Taking LIST_TASKS direct execution path")
                background_tasks.add_task(
                    execute_task_listing_direct,
                    user_id=user_id,
                    conversation_id=conversation.id,
                    intent_result=intent_result,
                    original_query=request.query
                )
            # For simple CRUD operations, execute directly without workflow tasks
            elif intent_result.action in [ActionType.CREATE_TASK, ActionType.UPDATE_TASK, ActionType.DELETE_TASK, ActionType.COMPLETE_TASK]:
                logger.info(f"🔀 [ROUTING] Taking CRUD direct execution path for {intent_result.action}")
                background_tasks.add_task(
                    execute_crud_operation_direct,
                    user_id=user_id,
                    conversation_id=conversation.id,
                    intent_result=intent_result,
                    original_query=request.query
                )
            elif intent_result.workflow_type and task_id:
                logger.info(f"🔀 [ROUTING] Taking workflow execution path: {intent_result.workflow_type}")
                background_tasks.add_task(
                    execute_workflow_background,
                    user_id=user_id,
                    conversation_id=conversation.id,
                    task_id=task_id,
                    intent_result=intent_result,
                    original_query=request.query
                )

        # Build response
        # Determine immediate response based on action type
        simple_crud_actions = [ActionType.LIST_TASKS, ActionType.DELETE_TASK, ActionType.CREATE_TASK, ActionType.UPDATE_TASK, ActionType.COMPLETE_TASK]
        immediate_response = intent_result.immediate_response

        if intent_result.action == ActionType.CREATE_TASK and intent_result.task_info and not intent_result.requires_clarification:
            immediate_response = None  # Will be in success card
        elif intent_result.requires_clarification:
            immediate_response = intent_result.immediate_response  # Always send clarification
        elif intent_result.action not in simple_crud_actions:
            immediate_response = intent_result.immediate_response
        else:
            immediate_response = None
            
        response = UnifiedAgentResponse(
            success=True,
            conversation_id=conversation.id,
            task_id=task_id,
            immediate_response=immediate_response,
            intent=intent_result.intent,
            action=intent_result.action.value,
            confidence=intent_result.confidence,
            requires_followup=intent_result.requires_task_card,
            metadata={
                **intent_result.metadata,
                "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                "workflow_type": intent_result.workflow_type
            }
        )

        logger.info(f"✅ [UNIFIED-AGENT] Query processed successfully: {intent_result.intent} -> {intent_result.action.value}")
        logger.info(f"📤 [UNIFIED-AGENT] Final response being sent to frontend:")
        logger.info(f"📤 [UNIFIED-AGENT] - success: {response.success}")
        logger.info(f"📤 [UNIFIED-AGENT] - immediate_response: '{response.immediate_response}'")
        logger.info(f"📤 [UNIFIED-AGENT] - intent: {response.intent}")
        logger.info(f"📤 [UNIFIED-AGENT] - action: {response.action}")
        logger.info(f"📤 [UNIFIED-AGENT] - conversation_id: {response.conversation_id}")
        logger.info(f"📤 [UNIFIED-AGENT] - task_id: {response.task_id}")
        logger.info(f"📤 [UNIFIED-AGENT] - Full response dict: {response.dict()}")
        return response

    except Exception as e:
        logger.error(f"Failed to process unified query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.get("/task/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get status of an agent task
    """
    try:
        task_manager = get_agent_task_manager()
        task = await task_manager.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "success": True,
            "task": task.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.post("/task/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    request: TaskCancelRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Cancel a running agent task
    """
    try:
        task_manager = get_agent_task_manager()
        task = await task_manager.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await task_manager.cancel_task(task_id, request.reason)

        return {
            "success": success,
            "message": "Task cancelled successfully" if success else "Task could not be cancelled",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/conversations")
async def list_conversations(
    limit: int = 20,
    include_inactive: bool = False,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List user's conversations
    """
    try:
        conversation_manager = get_conversation_manager()
        conversations = await conversation_manager.list_user_conversations(
            user_id=current_user.user_id,
            limit=limit,
            include_inactive=include_inactive
        )

        return {
            "success": True,
            "conversations": [conv.dict() for conv in conversations],
            "total": len(conversations),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    include_turns: bool = True,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get conversation details and history
    """
    try:
        conversation_manager = get_conversation_manager()

        # Get conversation context
        context = await conversation_manager.get_conversation_context(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )

        if not context.get("conversation_id"):
            raise HTTPException(status_code=404, detail="Conversation not found")

        result = {
            "success": True,
            "conversation": context,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Include full turn history if requested
        if include_turns:
            history = await conversation_manager.get_conversation_history(
                conversation_id=conversation_id,
                user_id=current_user.user_id,
                limit=limit,
                include_summary=False
            )
            result["turns"] = history

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    hard_delete: bool = False,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete conversation
    """
    try:
        conversation_manager = get_conversation_manager()
        success = await conversation_manager.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id,
            soft_delete=not hard_delete
        )

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "success": True,
            "message": f"Conversation {'deleted' if hard_delete else 'archived'} successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


























