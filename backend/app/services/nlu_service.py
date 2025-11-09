"""
NLU Service
Business logic layer for NLU (Natural Language Understanding) operations

Handles action records, gates, clarifications, and NLU monitoring.
Implements RULES.md Section 1.2 - Service layer pattern.
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from app.database.repositories.integration_repositories import (
    NLURepository,
    create_nlu_repository
)
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class NLUService:
    """
    Service for NLU operations

    Handles:
    - Action record creation and management
    - Policy gate creation and updates
    - Clarification handling
    - NLU monitoring and logging
    """

    def __init__(self, repository: NLURepository = None):
        """
        Initialize NLU service with optional repository injection

        Args:
            repository: NLU repository instance (injected for testing)
        """
        self.repo = repository or create_nlu_repository()

    async def create_action_record(
        self,
        user_id: UUID,
        session_id: UUID,
        turn_index: int,
        intent: str,
        params: Dict[str, Any],
        confidence: float
    ) -> UUID:
        """
        Create an action record from NLU extraction

        Args:
            user_id: User ID
            session_id: Conversation session ID
            turn_index: Turn index in conversation
            intent: Detected intent
            params: Extracted parameters
            confidence: NLU confidence score

        Returns:
            Created action ID

        Raises:
            ServiceError: If creation fails
        """
        try:
            action_id = await self.repo.create_action_record(
                user_id=user_id,
                session_id=session_id,
                turn_index=turn_index,
                intent=intent,
                params=params,
                confidence=confidence
            )

            logger.info(
                f"Created action record {action_id} for user {user_id}, "
                f"intent={intent}, confidence={confidence:.2f}"
            )

            return action_id

        except Exception as e:
            logger.error(f"Error creating action record: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to create action record",
                operation="create_action_record",
                details={
                    "user_id": str(user_id),
                    "intent": intent,
                    "confidence": confidence
                }
            )

    async def get_action_record(self, action_id: UUID) -> Dict[str, Any]:
        """
        Get an action record by ID

        Args:
            action_id: Action ID

        Returns:
            Action record dictionary

        Raises:
            ServiceError: If not found or fetch fails
        """
        try:
            action = await self.repo.get_action_record(action_id)

            if not action:
                raise ServiceError(
                    message=f"Action record not found",
                    operation="get_action_record",
                    details={"action_id": str(action_id)}
                )

            return action

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error fetching action record: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to fetch action record",
                operation="get_action_record",
                details={"action_id": str(action_id)}
            )

    async def get_action(self, action_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get an action by ID (alias for get_action_record, returns None if not found)

        Args:
            action_id: Action ID

        Returns:
            Action dictionary or None if not found
        """
        try:
            action = await self.repo.get_action(action_id)
            return action
        except Exception as e:
            logger.error(f"Error fetching action: {e}", exc_info=True)
            return None

    async def update_action_status(
        self,
        action_id: UUID,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update action status

        Args:
            action_id: Action ID
            status: New status (pending_confirmation, executing, completed, failed, draft)
            result: Optional result data

        Returns:
            True if updated successfully

        Raises:
            ServiceError: If update fails
        """
        try:
            updated = await self.repo.update_action_status(
                action_id=action_id,
                status=status,
                result=result
            )

            logger.info(f"Updated action {action_id} status to {status}")
            return updated

        except Exception as e:
            logger.error(f"Error updating action status: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to update action status",
                operation="update_action_status",
                details={"action_id": str(action_id), "status": status}
            )

    async def update_action_params(
        self,
        action_id: UUID,
        params: Dict[str, Any]
    ) -> bool:
        """
        Update action parameters (for slot filling)

        Args:
            action_id: Action ID
            params: New/updated parameters

        Returns:
            True if updated successfully

        Raises:
            ServiceError: If update fails
        """
        try:
            updated = await self.repo.update_action_params(action_id, params)

            logger.info(f"Updated action {action_id} params: {list(params.keys())}")
            return updated

        except Exception as e:
            logger.error(f"Error updating action params: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to update action params",
                operation="update_action_params",
                details={"action_id": str(action_id)}
            )

    async def create_pending_gate(
        self,
        action_id: UUID,
        gate_token: str,
        gate_type: str,
        clarification_message: Optional[str] = None,
        required_slots: Optional[List[str]] = None
    ) -> bool:
        """
        Create a pending gate for confirmation/clarification

        Args:
            action_id: Action ID
            gate_token: Unique gate token
            gate_type: Gate type (confirmation, clarification, permission)
            clarification_message: Message to show user
            required_slots: List of required slots for clarification

        Returns:
            True if created successfully

        Raises:
            ServiceError: If creation fails
        """
        try:
            created = await self.repo.create_pending_gate(
                action_id=action_id,
                gate_token=gate_token,
                gate_type=gate_type,
                clarification_message=clarification_message,
                required_slots=required_slots
            )

            logger.info(
                f"Created {gate_type} gate for action {action_id}, "
                f"token={gate_token}"
            )

            return created

        except Exception as e:
            logger.error(f"Error creating pending gate: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to create pending gate",
                operation="create_pending_gate",
                details={
                    "action_id": str(action_id),
                    "gate_type": gate_type
                }
            )

    async def get_pending_gate(self, gate_token: str) -> Optional[Dict[str, Any]]:
        """
        Get pending gate by token

        Args:
            gate_token: Gate token

        Returns:
            Gate dictionary or None if not found

        Raises:
            ServiceError: If fetch fails
        """
        try:
            gate = await self.repo.get_pending_gate(gate_token)
            return gate

        except Exception as e:
            logger.error(f"Error fetching pending gate: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to fetch pending gate",
                operation="get_pending_gate",
                details={"gate_token": gate_token}
            )

    async def resolve_gate(
        self,
        gate_token: str,
        approved: bool,
        resolution_slots: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve a pending gate (approve/deny)

        Args:
            gate_token: Gate token
            approved: Whether gate was approved
            resolution_slots: Slots provided during resolution

        Returns:
            Resolved gate data including action_id

        Raises:
            ServiceError: If resolution fails or gate not found
        """
        try:
            result = await self.repo.resolve_gate(
                gate_token=gate_token,
                approved=approved,
                resolution_slots=resolution_slots
            )

            logger.info(
                f"Resolved gate {gate_token}, approved={approved}"
            )

            return result

        except Exception as e:
            logger.error(f"Error resolving gate: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to resolve gate",
                operation="resolve_gate",
                details={"gate_token": gate_token, "approved": approved}
            )

    async def log_nlu_extraction(
        self,
        user_id: UUID,
        session_id: UUID,
        turn_index: int,
        raw_message: str,
        extracted_intent: str,
        extracted_params: Dict[str, Any],
        confidence: float,
        model_used: str
    ) -> None:
        """
        Log NLU extraction for monitoring

        Args:
            user_id: User ID
            session_id: Session ID
            turn_index: Turn index
            raw_message: Original user message
            extracted_intent: Extracted intent
            extracted_params: Extracted parameters
            confidence: Confidence score
            model_used: Model name/version
        """
        try:
            await self.repo.log_nlu_extraction(
                user_id=user_id,
                session_id=session_id,
                turn_index=turn_index,
                raw_message=raw_message,
                extracted_intent=extracted_intent,
                extracted_params=extracted_params,
                confidence=confidence,
                model_used=model_used
            )

            logger.debug(f"Logged NLU extraction for session {session_id}")

        except Exception as e:
            # Don't raise error for logging failures
            logger.warning(f"Failed to log NLU extraction: {e}")


def get_nlu_service() -> NLUService:
    """
    Factory function for NLU service

    Used for dependency injection in endpoints and services.
    """
    return NLUService()
