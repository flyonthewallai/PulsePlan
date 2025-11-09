"""
Gate Service
Business logic for gate (confirmation/cancellation) operations
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.database.repositories.integration_repositories import NLURepository, create_nlu_repository
from app.agents.services.action_executor import ActionExecutor, get_action_executor
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class GateService:
    """
    Service layer for gate operations
    
    Handles business logic for action confirmation/cancellation gates including:
    - Confirming pending gates
    - Cancelling pending gates
    - Getting gate status
    - Retrieving action traces
    """

    def __init__(
        self,
        nlu_repo: NLURepository = None,
        action_executor: ActionExecutor = None
    ):
        """
        Initialize GateService
        
        Args:
            nlu_repo: Optional NLURepository instance (for dependency injection/testing)
            action_executor: Optional ActionExecutor instance (for dependency injection/testing)
        """
        self.nlu_repo = nlu_repo or create_nlu_repository()
        self.action_executor = action_executor or get_action_executor()

    async def confirm_gate(
        self,
        token: str,
        user_id: UUID,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Confirm a pending gate and execute the action
        
        Args:
            token: Gate token
            user_id: User ID for authorization
            modifications: Optional modifications to action parameters
        
        Returns:
            Dict with gate_token, action_id, status, message, and execution_result
            
        Raises:
            ValueError: If gate not found, unauthorized, expired, or already processed
            ServiceError: If operation fails
        """
        try:
            # Get gate from database
            gate = await self.nlu_repo.get_gate_by_token(token)
            
            if not gate:
                raise ValueError(f"Gate {token} not found")
            
            # Extract action record info from joined data
            action_record = gate.get("action_records", {})
            action_id = gate.get("action_id")
            gate_user_id = action_record.get("user_id")
            
            # Check authorization
            if gate_user_id != str(user_id):
                raise ValueError("Not authorized to confirm this gate")
            
            # Check expiration
            expires_at = datetime.fromisoformat(gate["expires_at"].replace("Z", "+00:00"))
            if datetime.utcnow() > expires_at:
                raise ValueError("Gate has expired")
            
            # Check if already processed
            if gate.get("confirmed_at"):
                raise ValueError("Gate already confirmed")
            if gate.get("cancelled_at"):
                raise ValueError("Gate was cancelled")
            
            # Apply modifications to params if provided
            if modifications:
                current_params = action_record.get("params", {})
                final_params = {**current_params, **modifications}
                await self.nlu_repo.update_action_params(UUID(action_id), final_params)
            
            # Mark gate as confirmed
            await self.nlu_repo.confirm_gate(token)
            
            # Update action status to executing
            await self.nlu_repo.update_action_status(UUID(action_id), "executing")
            
            # Execute the action
            try:
                # Get the full action record
                full_action_record = await self.nlu_repo.get_action_record(UUID(action_id))
                
                # Apply modifications to params if provided
                if modifications:
                    full_action_record["params"] = {
                        **full_action_record["params"],
                        **modifications
                    }
                
                # Execute the action
                logger.info(f"Executing action {action_id} after gate confirmation")
                execution_result = await self.action_executor.execute_action(full_action_record)
                
                # Update action status based on execution result
                if execution_result.success:
                    await self.nlu_repo.update_action_status(
                        UUID(action_id),
                        "completed",
                        external_refs=execution_result.external_refs
                    )
                    logger.info(f"Action {action_id} completed successfully")
                else:
                    await self.nlu_repo.update_action_status(
                        UUID(action_id),
                        "failed",
                        error=execution_result.error
                    )
                    logger.error(f"Action {action_id} failed: {execution_result.error}")
                
                logger.info(f"Gate {token} confirmed and action executed")
                
                return {
                    "gate_token": token,
                    "action_id": UUID(action_id),
                    "status": "completed" if execution_result.success else "failed",
                    "message": execution_result.message,
                    "execution_result": execution_result.dict()
                }
            
            except Exception as e:
                # If execution fails, mark action as failed
                logger.error(f"Action execution failed for {action_id}: {e}", exc_info=True)
                await self.nlu_repo.update_action_status(
                    UUID(action_id),
                    "failed",
                    error=str(e)
                )
                
                return {
                    "gate_token": token,
                    "action_id": UUID(action_id),
                    "status": "failed",
                    "message": f"Execution failed: {str(e)}",
                    "execution_result": {"error": str(e)}
                }
        
        except ValueError:
            # Re-raise ValueError as-is (these are expected validation errors)
            raise
        except Exception as e:
            logger.error(f"Failed to confirm gate {token}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to confirm gate: {str(e)}",
                service="GateService",
                operation="confirm_gate",
                details={"token": token, "user_id": str(user_id)}
            )

    async def cancel_gate(
        self,
        token: str,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a pending gate
        
        Args:
            token: Gate token
            user_id: User ID for authorization
            reason: Optional cancellation reason
        
        Returns:
            Dict with gate_token, action_id, status, and message
            
        Raises:
            ValueError: If gate not found, unauthorized, or already processed
            ServiceError: If operation fails
        """
        try:
            # Get gate from database
            gate = await self.nlu_repo.get_gate_by_token(token)
            
            if not gate:
                raise ValueError(f"Gate {token} not found")
            
            # Extract action record info
            action_record = gate.get("action_records", {})
            action_id = gate.get("action_id")
            gate_user_id = action_record.get("user_id")
            action_status = action_record.get("status")
            
            # Check authorization
            if gate_user_id != str(user_id):
                raise ValueError("Not authorized to cancel this gate")
            
            # Check if already processed
            if action_status in ["completed", "failed"]:
                raise ValueError(f"Action already {action_status}")
            
            # Mark gate as cancelled
            await self.nlu_repo.cancel_gate(token)
            
            # Update action status
            await self.nlu_repo.update_action_status(
                UUID(action_id),
                "failed",
                reason or "User cancelled"
            )
            
            logger.info(f"Gate {token} cancelled successfully")
            
            return {
                "gate_token": token,
                "action_id": UUID(action_id),
                "status": "cancelled",
                "message": "Gate cancelled by user"
            }
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to cancel gate {token}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to cancel gate: {str(e)}",
                service="GateService",
                operation="cancel_gate",
                details={"token": token, "user_id": str(user_id)}
            )

    async def get_gate_status(
        self,
        token: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get status of a pending gate
        
        Args:
            token: Gate token
            user_id: User ID for authorization
        
        Returns:
            Dict with gate details and status
            
        Raises:
            ValueError: If gate not found or unauthorized
            ServiceError: If operation fails
        """
        try:
            gate = await self.nlu_repo.get_gate_by_token(token)
            
            if not gate:
                raise ValueError(f"Gate {token} not found")
            
            # Extract action record info
            action_record = gate.get("action_records", {})
            gate_user_id = action_record.get("user_id")
            
            # Check authorization
            if gate_user_id != str(user_id):
                raise ValueError("Not authorized to view this gate")
            
            # Determine status
            if gate.get("cancelled_at"):
                gate_status = "cancelled"
            elif gate.get("confirmed_at"):
                gate_status = "confirmed"
            else:
                expires_at = datetime.fromisoformat(gate["expires_at"].replace("Z", "+00:00"))
                if datetime.utcnow() > expires_at:
                    gate_status = "expired"
                else:
                    gate_status = "pending"
            
            return {
                "gate_token": gate["gate_token"],
                "action_id": UUID(gate["action_id"]),
                "status": gate_status,
                "intent": gate["intent"],
                "required_confirmations": gate["required_confirmations"],
                "policy_reasons": gate["policy_reasons"],
                "created_at": datetime.fromisoformat(gate["created_at"].replace("Z", "+00:00")),
                "expires_at": datetime.fromisoformat(gate["expires_at"].replace("Z", "+00:00")),
                "confirmed_at": datetime.fromisoformat(gate["confirmed_at"].replace("Z", "+00:00")) if gate.get("confirmed_at") else None,
                "cancelled_at": datetime.fromisoformat(gate["cancelled_at"].replace("Z", "+00:00")) if gate.get("cancelled_at") else None
            }
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to get gate status {token}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get gate status: {str(e)}",
                service="GateService",
                operation="get_gate_status",
                details={"token": token, "user_id": str(user_id)}
            )

    async def get_action_trace(
        self,
        action_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get ordered execution trace for an action
        
        Args:
            action_id: Action record ID
            user_id: User ID for authorization
        
        Returns:
            Dict with action details and ordered trace steps
            
        Raises:
            ValueError: If action not found or unauthorized
            ServiceError: If operation fails
        """
        try:
            from app.observability.prompt_logs import get_action_trace as get_trace
            
            # Check authorization
            action = await self.nlu_repo.get_action(action_id)
            
            if not action:
                raise ValueError(f"Action {action_id} not found")
            
            if action["user_id"] != str(user_id):
                raise ValueError("Not authorized to view this action")
            
            # Get full trace
            trace = await get_trace(self.nlu_repo.supabase, action_id)
            
            if "error" in trace:
                raise ValueError(trace["error"])
            
            return trace
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to get action trace {action_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get action trace: {str(e)}",
                service="GateService",
                operation="get_action_trace",
                details={"action_id": str(action_id), "user_id": str(user_id)}
            )


def get_gate_service() -> GateService:
    """
    Dependency injection function for GateService
    
    Returns:
        GateService instance with default dependencies
    """
    return GateService(
        nlu_repo=create_nlu_repository(),
        action_executor=get_action_executor()
    )

