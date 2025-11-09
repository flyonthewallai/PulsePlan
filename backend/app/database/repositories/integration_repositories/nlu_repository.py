"""
NLU Repository 

Database operations for NLU pipeline using Supabase client directly.
"""

from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NLURepository:
    """Repository for NLU pipeline database operations using Supabase."""

    def __init__(self, supabase_client=None):
        """
        Initialize repository.

        Args:
            supabase_client: Supabase client (if None, will get from config)
        """
        if supabase_client is None:
            from app.config.database.supabase import get_supabase_client
            self.supabase = get_supabase_client()
        else:
            self.supabase = supabase_client

    # Action Records

    async def create_action_record(
        self,
        user_id: UUID,
        intent: str,
        params: dict,
        status: str = "draft",
        idempotency_key: Optional[str] = None,
        user_message: Optional[str] = None
    ) -> UUID:
        """Create action record."""
        action_id = uuid4()

        data = {
            "id": str(action_id),
            "user_id": str(user_id),
            "intent": intent,
            "params": params,
            "status": status,
            "idempotency_key": idempotency_key,
            "user_message": user_message
        }

        response = self.supabase.table("action_records").insert(data).execute()

        if not response.data:
            raise Exception(f"Failed to create action record: {response}")

        logger.debug(f"Created action record {action_id} for user {user_id}")
        return action_id

    async def get_action(self, action_id: UUID) -> Optional[Dict[str, Any]]:
        """Get action record by ID."""
        response = self.supabase.table("action_records")\
            .select("*")\
            .eq("id", str(action_id))\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    # Backwards-compatible alias used by planning handler and docs
    async def get_action_record(self, action_id: UUID) -> Optional[Dict[str, Any]]:
        """Alias for get_action to maintain compatibility with callers."""
        return await self.get_action(action_id)

    async def get_last_action(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get last action for user."""
        response = self.supabase.table("action_records")\
            .select("id, intent, params, status, created_at, user_message")\
            .eq("user_id", str(user_id))\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    async def update_action_status(
        self,
        action_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        external_refs: Optional[Dict[str, Any]] = None
    ):
        """Update action status."""
        update_data = {
            "status": status,
            "error_message": error_message,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Include optional external references if provided
        if external_refs is not None:
            update_data["external_refs"] = external_refs

        self.supabase.table("action_records")\
            .update(update_data)\
            .eq("id", str(action_id))\
            .execute()

    async def update_action_params(self, action_id: UUID, params: dict):
        """Update action parameters."""
        update_data = {
            "params": params,
            "updated_at": datetime.utcnow().isoformat()
        }

        self.supabase.table("action_records")\
            .update(update_data)\
            .eq("id", str(action_id))\
            .execute()

    async def update_action_external_refs(self, action_id: UUID, external_refs: dict):
        """Update external references."""
        update_data = {
            "external_refs": external_refs,
            "updated_at": datetime.utcnow().isoformat()
        }

        self.supabase.table("action_records")\
            .update(update_data)\
            .eq("id", str(action_id))\
            .execute()

    # Pending Gates

    async def create_pending_gate(
        self,
        action_id: UUID,
        gate_token: str,
        intent: str,
        required_confirmations: dict,
        policy_reasons: list,
        expires_at: datetime
    ):
        """Create pending gate idempotently on action_id."""
        data = {
            "action_id": str(action_id),
            "gate_token": gate_token,
            "intent": intent,
            "required_confirmations": required_confirmations,
            "policy_reasons": policy_reasons,
            "expires_at": expires_at.isoformat()
        }

        # Use upsert to avoid duplicate key errors when the same action is processed twice
        self.supabase.table("pending_gates").upsert(data, on_conflict="action_id").execute()
        logger.debug(f"Ensured pending gate for action {action_id} (token={gate_token}) exists")

    async def get_pending_gate(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get active pending gate for user.

        Note: This requires a join which Supabase doesn't support directly.
        We'll query gates and then filter by user_id from action_records.
        """
        # Get all non-expired, non-confirmed gates
        now = datetime.utcnow().isoformat()
        response = self.supabase.table("pending_gates")\
            .select("*, action_records(user_id)")\
            .is_("confirmed_at", "null")\
            .is_("cancelled_at", "null")\
            .gt("expires_at", now)\
            .order("created_at", desc=True)\
            .execute()

        # Filter by user_id
        for gate in response.data:
            if gate.get("action_records", {}).get("user_id") == str(user_id):
                return gate

        return None

    async def get_gate_by_token(self, gate_token: str) -> Optional[Dict[str, Any]]:
        """Get gate by token with action record info."""
        response = self.supabase.table("pending_gates")\
            .select("*, action_records(*)")\
            .eq("gate_token", gate_token)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    async def confirm_gate(self, gate_token: str):
        """Mark gate as confirmed."""
        self.supabase.table("pending_gates")\
            .update({"confirmed_at": datetime.utcnow().isoformat()})\
            .eq("gate_token", gate_token)\
            .execute()

    async def cancel_gate(self, gate_token: str):
        """Mark gate as cancelled."""
        self.supabase.table("pending_gates")\
            .update({"cancelled_at": datetime.utcnow().isoformat()})\
            .eq("gate_token", gate_token)\
            .execute()

    async def cleanup_expired_gates(self) -> int:
        """Cleanup expired gates."""
        now = datetime.utcnow().isoformat()

        # Get expired gates
        response = self.supabase.table("pending_gates")\
            .select("gate_token")\
            .lt("expires_at", now)\
            .is_("confirmed_at", "null")\
            .is_("cancelled_at", "null")\
            .execute()

        count = len(response.data) if response.data else 0

        if count > 0:
            # Update them as cancelled
            for gate in response.data:
                await self.cancel_gate(gate["gate_token"])

            logger.info(f"Cleaned up {count} expired gates")

        return count

    # Idempotency Keys

    async def create_idempotency_key(
        self,
        idempotency_key: str,
        action_id: UUID,
        operation_type: str,
        last_result: dict,
        expires_at: datetime
    ):
        """Create or update idempotency key record."""
        data = {
            "idempotency_key": idempotency_key,
            "action_id": str(action_id),
            "operation_type": operation_type,
            "last_result": last_result,
            "expires_at": expires_at.isoformat()
        }

        # Supabase upsert
        self.supabase.table("idempotency_keys")\
            .upsert(data, on_conflict="idempotency_key")\
            .execute()

    async def get_idempotency_result(
        self,
        idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get result for idempotency key if exists and not expired."""
        now = datetime.utcnow().isoformat()

        response = self.supabase.table("idempotency_keys")\
            .select("*")\
            .eq("idempotency_key", idempotency_key)\
            .gt("expires_at", now)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    async def cleanup_expired_idempotency_keys(self) -> int:
        """Cleanup expired idempotency keys."""
        now = datetime.utcnow().isoformat()

        # Get count first
        response = self.supabase.table("idempotency_keys")\
            .select("idempotency_key", count="exact")\
            .lt("expires_at", now)\
            .execute()

        count = response.count if hasattr(response, 'count') else 0

        if count > 0:
            # Delete expired keys
            self.supabase.table("idempotency_keys")\
                .delete()\
                .lt("expires_at", now)\
                .execute()

            logger.info(f"Cleaned up {count} expired idempotency keys")

        return count

    # User Actions History

    async def get_user_actions(
        self,
        user_id: UUID,
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's action history."""
        query = self.supabase.table("action_records")\
            .select("id, intent, params, status, external_refs, error_message, created_at, updated_at")\
            .eq("user_id", str(user_id))

        if status_filter:
            query = query.eq("status", status_filter)

        response = query.order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        return response.data if response.data else []

    # NLU Prompt Logs - For Continuous Model Improvement

    async def log_prompt(
        self,
        user_id: UUID,
        prompt: str,
        predicted_intent: str,
        confidence: float,
        secondary_intents: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[UUID] = None,
        message_index: Optional[int] = None
    ) -> UUID:
        """
        Log a user prompt with intent prediction for model refinement.

        Args:
            user_id: User ID
            prompt: Raw user input
            predicted_intent: Model's predicted intent
            confidence: Prediction confidence score (0-1)
            secondary_intents: List of secondary intents with scores
            conversation_id: Conversation/session ID
            message_index: Message index in conversation

        Returns:
            Log entry ID
        """
        log_id = uuid4()

        data = {
            "id": str(log_id),
            "user_id": str(user_id),
            "prompt": prompt,
            "predicted_intent": predicted_intent,
            "confidence": confidence,
            "secondary_intents": secondary_intents or [],
            "conversation_id": str(conversation_id) if conversation_id else None,
            "message_index": message_index
        }

        response = self.supabase.table("nlu_prompt_logs").insert(data).execute()

        if not response.data:
            raise Exception(f"Failed to log prompt: {response}")

        logger.debug(f"Logged prompt for user {user_id}: intent={predicted_intent}, confidence={confidence:.2f}")
        return log_id

    async def update_prompt_log_outcome(
        self,
        log_id: UUID,
        was_successful: bool,
        workflow_type: Optional[str] = None,
        execution_error: Optional[str] = None
    ):
        """
        Update prompt log with workflow execution outcome.

        Args:
            log_id: Log entry ID
            was_successful: Whether workflow succeeded
            workflow_type: Type of workflow executed
            execution_error: Error message if failed
        """
        update_data = {
            "was_successful": was_successful,
            "workflow_type": workflow_type,
            "execution_error": execution_error,
            "updated_at": datetime.utcnow().isoformat()
        }

        self.supabase.table("nlu_prompt_logs")\
            .update(update_data)\
            .eq("id", str(log_id))\
            .execute()

        logger.debug(f"Updated prompt log {log_id}: success={was_successful}")

    async def add_prompt_correction(
        self,
        log_id: UUID,
        corrected_intent: str,
        correction_notes: Optional[str] = None
    ):
        """
        Add manual correction to a prompt log.

        Args:
            log_id: Log entry ID
            corrected_intent: Correct intent label
            correction_notes: Notes on why correction was needed
        """
        update_data = {
            "corrected_intent": corrected_intent,
            "correction_notes": correction_notes,
            "updated_at": datetime.utcnow().isoformat()
        }

        self.supabase.table("nlu_prompt_logs")\
            .update(update_data)\
            .eq("id", str(log_id))\
            .execute()

        logger.info(f"Added correction to prompt log {log_id}: {corrected_intent}")

    async def get_low_confidence_prompts(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get prompts with low confidence for review.

        Args:
            threshold: Confidence threshold (default 0.7)
            limit: Maximum results to return

        Returns:
            List of low-confidence prompt logs
        """
        response = self.supabase.table("nlu_prompt_logs")\
            .select("*")\
            .lt("confidence", threshold)\
            .is_("corrected_intent", "null")\
            .order("confidence", desc=False)\
            .limit(limit)\
            .execute()

        return response.data if response.data else []

    async def get_failed_workflow_prompts(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get prompts that led to failed workflows.

        Args:
            limit: Maximum results to return

        Returns:
            List of prompt logs with workflow failures
        """
        response = self.supabase.table("nlu_prompt_logs")\
            .select("*")\
            .eq("was_successful", False)\
            .is_("corrected_intent", "null")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        return response.data if response.data else []

    async def get_prompts_for_retraining(
        self,
        min_date: Optional[datetime] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Get prompts for model retraining.
        Returns prompts with corrections or high-confidence predictions.

        Args:
            min_date: Only include prompts after this date
            limit: Maximum results to return

        Returns:
            List of prompt logs suitable for retraining
        """
        query = self.supabase.table("nlu_prompt_logs")\
            .select("prompt, predicted_intent, corrected_intent, confidence")

        if min_date:
            query = query.gte("created_at", min_date.isoformat())

        # Get prompts with corrections OR high confidence (>0.85)
        # Note: Supabase doesn't support complex OR queries easily,
        # so we'll fetch and filter in Python
        response = query.order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        if not response.data:
            return []

        # Filter for corrected OR high-confidence prompts
        training_data = []
        for log in response.data:
            if log.get("corrected_intent") or log.get("confidence", 0) > 0.85:
                training_data.append(log)

        logger.info(f"Retrieved {len(training_data)} prompts for retraining")
        return training_data

    async def count_all_prompts(self) -> int:
        """
        Count all prompts in the database
        
        Returns:
            Total count of prompts
        """
        response = self.supabase.table("nlu_prompt_logs").select("*", count="exact").execute()
        return response.count if hasattr(response, 'count') else 0

    async def count_prompts_since(self, since: datetime) -> int:
        """
        Count prompts since a specific datetime
        
        Args:
            since: Datetime to count from
        
        Returns:
            Count of prompts since that datetime
        """
        response = self.supabase.table("nlu_prompt_logs")\
            .select("*", count="exact")\
            .gte("created_at", since.isoformat())\
            .execute()
        return response.count if hasattr(response, 'count') else 0

    async def get_prompts_since(self, since: datetime) -> List[Dict[str, Any]]:
        """
        Get all prompts since a specific datetime
        
        Args:
            since: Datetime to get prompts from
        
        Returns:
            List of prompt logs since that datetime
        """
        response = self.supabase.table("nlu_prompt_logs")\
            .select("*")\
            .gte("created_at", since.isoformat())\
            .execute()
        
        return response.data if response.data else []


def create_nlu_repository(supabase_client=None) -> NLURepository:
    """
    Factory function to create NLU repository.

    Args:
        supabase_client: Supabase client (optional)

    Returns:
        NLURepository instance
    """
    return NLURepository(supabase_client)
