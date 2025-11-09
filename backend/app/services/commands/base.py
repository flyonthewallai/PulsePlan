"""
Base Command Handler
Abstract interface for all command handlers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class CommandResult(BaseModel):
    """Result from command execution"""
    success: bool
    command: str
    result: Optional[Any] = None
    immediate_response: str
    error: Optional[str] = None
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None


class BaseCommandHandler(ABC):
    """
    Base class for all command handlers
    Each handler implements the execute method to process its specific command
    """

    def __init__(self):
        self.command_name = self.__class__.__name__.replace('CommandHandler', '').lower()

    @abstractmethod
    async def execute(self, user_id: str, parameters: Dict[str, Any]) -> CommandResult:
        """
        Execute the command with given parameters
        
        Args:
            user_id: ID of the user executing the command
            parameters: Parsed parameters from the command
            
        Returns:
            CommandResult with success status and response message
        """
        pass

    def validate_required_parameters(
        self,
        parameters: Dict[str, Any],
        required: list[str]
    ) -> Optional[CommandResult]:
        """
        Validate that required parameters are present
        
        Args:
            parameters: Parameters to validate
            required: List of required parameter names
            
        Returns:
            CommandResult with error if validation fails, None if valid
        """
        missing = [param for param in required if not parameters.get(param)]
        
        if missing:
            return CommandResult(
                success=False,
                command=self.command_name,
                immediate_response=f"Missing required parameter(s): {', '.join(missing)}",
                error=f"Missing required parameters: {missing}",
                requires_clarification=True,
                clarification_prompt=f"Please provide: {', '.join(missing)}"
            )
        
        return None

    def log_execution(self, user_id: str, parameters: Dict[str, Any], result: CommandResult):
        """Log command execution for observability"""
        logger.info(
            f"Command executed: {self.command_name}",
            extra={
                "user_id": user_id,
                "command": self.command_name,
                "parameters": parameters,
                "success": result.success,
            }
        )

