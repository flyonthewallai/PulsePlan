"""
Commands API Endpoints
Handles deterministic command execution
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.commands import get_handler, initialize_handlers
from app.services.commands.base import CommandResult

logger = logging.getLogger(__name__)

router = APIRouter()

# Ensure handlers are initialized
initialize_handlers()


class CommandExecuteRequest(BaseModel):
    """Request model for command execution"""
    command: str = Field(..., description="Command name (e.g., 'todo', 'schedule')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    raw_text: str = Field(..., description="Original user input text")


class CommandExecuteResponse(BaseModel):
    """Response model for command execution"""
    success: bool
    command: str
    result: Optional[Any] = None
    immediate_response: str
    error: Optional[str] = None
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None


class CommandDefinition(BaseModel):
    """Command metadata for frontend"""
    id: str
    name: str
    description: str
    examples: List[str]


@router.post("/execute", response_model=CommandExecuteResponse)
async def execute_command(
    request: CommandExecuteRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Execute a command with given parameters
    
    Commands bypass the LLM intent classification system and directly
    execute deterministic actions.
    """
    try:
        logger.info(
            f"Command execution request: {request.command}",
            extra={
                "user_id": current_user.user_id,
                "command": request.command,
                "parameters": request.parameters
            }
        )

        # Get handler for the command
        handler = get_handler(request.command)
        
        if not handler:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown command: {request.command}. Use /help to see available commands."
            )

        # Execute the command
        result: CommandResult = await handler.execute(
            user_id=current_user.user_id,
            parameters=request.parameters
        )

        # Log execution result
        handler.log_execution(current_user.user_id, request.parameters, result)

        return CommandExecuteResponse(
            success=result.success,
            command=result.command,
            result=result.result,
            immediate_response=result.immediate_response,
            error=result.error,
            requires_clarification=result.requires_clarification,
            clarification_prompt=result.clarification_prompt
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute command: {str(e)}"
        )


@router.get("/list", response_model=List[CommandDefinition])
async def list_commands(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all available commands
    
    Returns command metadata for frontend to build UI
    """
    # Static list of commands (matches frontend definitions)
    commands = [
        CommandDefinition(
            id="todo",
            name="todo",
            description="Create a new task",
            examples=[
                "/todo Finish essay tomorrow at 5pm",
                "/todo Buy groceries #personal"
            ]
        ),
        CommandDefinition(
            id="schedule",
            name="schedule",
            description="Schedule an event",
            examples=[
                "/schedule Team meeting tomorrow at 2pm",
                "/schedule Study session Friday 3pm for 90 minutes"
            ]
        ),
        CommandDefinition(
            id="reschedule",
            name="reschedule",
            description="Reschedule a task or event",
            examples=[
                "/reschedule essay to tomorrow",
                "/reschedule team meeting to 3pm"
            ]
        ),
        CommandDefinition(
            id="focus",
            name="focus",
            description="Start a focus/Pomodoro timer",
            examples=[
                "/focus",
                "/focus 50 minutes on essay writing"
            ]
        ),
        CommandDefinition(
            id="briefing",
            name="briefing",
            description="Show today's briefing",
            examples=["/briefing"]
        ),
        CommandDefinition(
            id="help",
            name="help",
            description="List available commands",
            examples=["/help"]
        ),
    ]
    
    return commands

