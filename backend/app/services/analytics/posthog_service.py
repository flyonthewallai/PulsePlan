"""
PostHog Analytics Service for PulsePlan

Provides comprehensive event tracking for:
- Agent operations (queries, workflows, actions)
- User journey (conversations, task creation, scheduling)
- Premium features (upgrades, feature usage)
- Performance metrics (latency, success rates)

Privacy-first: All PII is anonymized before sending to PostHog.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
import posthog
from posthog import Posthog

from app.config.core.settings import get_settings

logger = logging.getLogger(__name__)


class PostHogService:
    """
    Service wrapper for PostHog analytics integration.

    Handles event tracking, user identification, and feature flags
    for the PulsePlan agent system.
    """

    def __init__(self):
        """Initialize PostHog client with configuration from settings."""
        self.settings = get_settings()
        self.enabled = self.settings.POSTHOG_ENABLED

        if self.enabled:
            posthog.api_key = self.settings.POSTHOG_API_KEY
            posthog.host = self.settings.POSTHOG_HOST
            posthog.disabled = False
            logger.info("PostHog analytics initialized")
        else:
            posthog.disabled = True
            logger.info("PostHog analytics disabled")

    def _sanitize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove PII from event properties before sending to PostHog.

        Args:
            properties: Raw event properties

        Returns:
            Sanitized properties with PII removed
        """
        # List of fields that might contain PII
        pii_fields = {"email", "name", "phone", "address", "ip_address"}

        sanitized = {}
        for key, value in properties.items():
            if key.lower() in pii_fields:
                # Skip PII fields
                continue
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self._sanitize_properties(value)
            else:
                sanitized[key] = value

        return sanitized

    def track_event(
        self,
        user_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track an event in PostHog.

        Args:
            user_id: Unique user identifier (anonymized)
            event_name: Name of the event
            properties: Additional event properties
        """
        if not self.enabled:
            return

        try:
            sanitized_props = self._sanitize_properties(properties or {})
            sanitized_props["timestamp"] = datetime.utcnow().isoformat()

            posthog.capture(
                distinct_id=user_id,
                event=event_name,
                properties=sanitized_props
            )
            logger.debug(f"Tracked event: {event_name} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to track event {event_name}: {str(e)}")

    # =========================================================================
    # AGENT OPERATIONS
    # =========================================================================

    def track_agent_query_received(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None
    ) -> None:
        """Track when a user query is received by the agent."""
        self.track_event(
            user_id=user_id,
            event_name="agent_query_received",
            properties={
                "query_length": len(query),
                "session_id": session_id,
                "has_session": session_id is not None
            }
        )

    def track_intent_classified(
        self,
        user_id: str,
        intent: str,
        confidence: float,
        method: str,  # "rule_based", "onnx_classifier", "llm_fallback"
        session_id: Optional[str] = None
    ) -> None:
        """Track intent classification results."""
        self.track_event(
            user_id=user_id,
            event_name="intent_classified",
            properties={
                "intent": intent,
                "confidence": confidence,
                "method": method,
                "session_id": session_id,
                "high_confidence": confidence >= 0.8
            }
        )

    def track_workflow_started(
        self,
        user_id: str,
        workflow_type: str,
        intent: str,
        session_id: Optional[str] = None
    ) -> None:
        """Track when a workflow begins execution."""
        self.track_event(
            user_id=user_id,
            event_name="workflow_started",
            properties={
                "workflow_type": workflow_type,
                "intent": intent,
                "session_id": session_id
            }
        )

    def track_workflow_completed(
        self,
        user_id: str,
        workflow_type: str,
        success: bool,
        duration_ms: float,
        error_type: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """Track workflow completion."""
        self.track_event(
            user_id=user_id,
            event_name="workflow_completed",
            properties={
                "workflow_type": workflow_type,
                "success": success,
                "duration_ms": duration_ms,
                "error_type": error_type,
                "session_id": session_id
            }
        )

    def track_action_executed(
        self,
        user_id: str,
        action_type: str,
        intent: str,
        success: bool,
        duration_ms: float,
        session_id: Optional[str] = None
    ) -> None:
        """Track action execution from planning decisions."""
        self.track_event(
            user_id=user_id,
            event_name="action_executed",
            properties={
                "action_type": action_type,
                "intent": intent,
                "success": success,
                "duration_ms": duration_ms,
                "session_id": session_id
            }
        )

    def track_llm_call_made(
        self,
        user_id: str,
        operation: str,  # "classification", "extraction", "conversation", "enrichment"
        model: str,
        tokens_used: int,
        duration_ms: float,
        success: bool,
        session_id: Optional[str] = None
    ) -> None:
        """Track LLM API calls for token usage monitoring."""
        self.track_event(
            user_id=user_id,
            event_name="llm_call_made",
            properties={
                "operation": operation,
                "model": model,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
                "success": success,
                "session_id": session_id
            }
        )

    # =========================================================================
    # USER JOURNEY
    # =========================================================================

    def track_conversation_started(
        self,
        user_id: str,
        session_id: str
    ) -> None:
        """Track new conversation session."""
        self.track_event(
            user_id=user_id,
            event_name="conversation_started",
            properties={"session_id": session_id}
        )

    def track_conversation_turn(
        self,
        user_id: str,
        session_id: str,
        turn_index: int,
        intent: str
    ) -> None:
        """Track each turn in a multi-turn conversation."""
        self.track_event(
            user_id=user_id,
            event_name="conversation_turn",
            properties={
                "session_id": session_id,
                "turn_index": turn_index,
                "intent": intent,
                "is_multi_turn": turn_index > 0
            }
        )

    def track_clarification_requested(
        self,
        user_id: str,
        intent: str,
        missing_slots: list,
        session_id: Optional[str] = None
    ) -> None:
        """Track when agent requests clarification from user."""
        self.track_event(
            user_id=user_id,
            event_name="clarification_requested",
            properties={
                "intent": intent,
                "missing_slots": missing_slots,
                "missing_count": len(missing_slots),
                "session_id": session_id
            }
        )

    def track_task_created(
        self,
        user_id: str,
        task_id: str,
        via_agent: bool = True,
        llm_enriched: bool = False,
        session_id: Optional[str] = None
    ) -> None:
        """Track task creation."""
        self.track_event(
            user_id=user_id,
            event_name="task_created",
            properties={
                "task_id": task_id,
                "via_agent": via_agent,
                "llm_enriched": llm_enriched,
                "session_id": session_id
            }
        )

    def track_schedule_generated(
        self,
        user_id: str,
        tasks_scheduled: int,
        conflicts_count: int,
        optimization_goal: str,
        duration_ms: float,
        session_id: Optional[str] = None
    ) -> None:
        """Track schedule generation."""
        self.track_event(
            user_id=user_id,
            event_name="schedule_generated",
            properties={
                "tasks_scheduled": tasks_scheduled,
                "conflicts_count": conflicts_count,
                "optimization_goal": optimization_goal,
                "duration_ms": duration_ms,
                "has_conflicts": conflicts_count > 0,
                "session_id": session_id
            }
        )

    def track_email_draft(
        self,
        user_id: str,
        is_premium: bool,
        method: str,  # "llm" or "template"
        recipient_count: int,
        session_id: Optional[str] = None
    ) -> None:
        """Track email drafting."""
        self.track_event(
            user_id=user_id,
            event_name="email_draft",
            properties={
                "is_premium": is_premium,
                "method": method,
                "recipient_count": recipient_count,
                "session_id": session_id
            }
        )

    # =========================================================================
    # PREMIUM & MONETIZATION
    # =========================================================================

    def track_upgrade_prompt_shown(
        self,
        user_id: str,
        feature: str,
        tokens_needed: int,
        tokens_remaining: int
    ) -> None:
        """Track when upgrade prompt is shown to free user."""
        self.track_event(
            user_id=user_id,
            event_name="upgrade_prompt_shown",
            properties={
                "feature": feature,
                "tokens_needed": tokens_needed,
                "tokens_remaining": tokens_remaining,
                "token_deficit": tokens_needed - tokens_remaining
            }
        )

    def track_feature_gated(
        self,
        user_id: str,
        feature: str,
        reason: str  # "insufficient_tokens", "premium_only"
    ) -> None:
        """Track when a feature is blocked for a user."""
        self.track_event(
            user_id=user_id,
            event_name="feature_gated",
            properties={
                "feature": feature,
                "reason": reason
            }
        )

    def track_premium_feature_used(
        self,
        user_id: str,
        feature: str,
        session_id: Optional[str] = None
    ) -> None:
        """Track premium feature usage."""
        self.track_event(
            user_id=user_id,
            event_name="premium_feature_used",
            properties={
                "feature": feature,
                "session_id": session_id
            }
        )

    def track_subscription_status_changed(
        self,
        user_id: str,
        old_status: str,
        new_status: str,
        plan_type: str  # "free", "premium"
    ) -> None:
        """Track subscription changes."""
        self.track_event(
            user_id=user_id,
            event_name="subscription_status_changed",
            properties={
                "old_status": old_status,
                "new_status": new_status,
                "plan_type": plan_type,
                "is_upgrade": new_status == "premium" and old_status == "free",
                "is_downgrade": new_status == "free" and old_status == "premium"
            }
        )

    # =========================================================================
    # PERFORMANCE METRICS
    # =========================================================================

    def track_query_latency(
        self,
        user_id: str,
        total_duration_ms: float,
        intent: str,
        used_llm: bool,
        session_id: Optional[str] = None
    ) -> None:
        """Track end-to-end query processing latency."""
        self.track_event(
            user_id=user_id,
            event_name="query_latency",
            properties={
                "total_duration_ms": total_duration_ms,
                "intent": intent,
                "used_llm": used_llm,
                "session_id": session_id,
                "performance_category": self._categorize_latency(total_duration_ms, used_llm)
            }
        )

    def track_intent_classification_latency(
        self,
        user_id: str,
        duration_ms: float,
        method: str
    ) -> None:
        """Track NLU intent classification speed."""
        self.track_event(
            user_id=user_id,
            event_name="intent_classification_latency",
            properties={
                "duration_ms": duration_ms,
                "method": method,
                "is_fast": duration_ms < 50  # Target: < 50ms
            }
        )

    def track_workflow_execution_latency(
        self,
        user_id: str,
        workflow_type: str,
        duration_ms: float,
        session_id: Optional[str] = None
    ) -> None:
        """Track workflow execution speed."""
        self.track_event(
            user_id=user_id,
            event_name="workflow_execution_latency",
            properties={
                "workflow_type": workflow_type,
                "duration_ms": duration_ms,
                "session_id": session_id
            }
        )

    # =========================================================================
    # FEATURE FLAGS
    # =========================================================================

    def is_feature_enabled(
        self,
        user_id: str,
        feature_flag: str,
        default: bool = False
    ) -> bool:
        """
        Check if a feature flag is enabled for a user.

        Args:
            user_id: User identifier
            feature_flag: Name of the feature flag
            default: Default value if flag lookup fails

        Returns:
            True if feature is enabled, False otherwise
        """
        if not self.enabled:
            return default

        try:
            return posthog.feature_enabled(feature_flag, user_id) or default
        except Exception as e:
            logger.error(f"Failed to check feature flag {feature_flag}: {str(e)}")
            return default

    def get_feature_flag_payload(
        self,
        user_id: str,
        feature_flag: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get feature flag payload for a user.

        Args:
            user_id: User identifier
            feature_flag: Name of the feature flag

        Returns:
            Feature flag payload or None
        """
        if not self.enabled:
            return None

        try:
            return posthog.get_feature_flag_payload(feature_flag, user_id)
        except Exception as e:
            logger.error(f"Failed to get feature flag payload {feature_flag}: {str(e)}")
            return None

    # =========================================================================
    # USER IDENTIFICATION
    # =========================================================================

    def identify_user(
        self,
        user_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Identify a user in PostHog with their properties.

        Args:
            user_id: Unique user identifier
            properties: User properties (PII will be sanitized)
        """
        if not self.enabled:
            return

        try:
            sanitized_props = self._sanitize_properties(properties or {})
            posthog.identify(
                distinct_id=user_id,
                properties=sanitized_props
            )
            logger.debug(f"Identified user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to identify user {user_id}: {str(e)}")

    def alias_user(
        self,
        previous_id: str,
        new_id: str
    ) -> None:
        """
        Create an alias linking two user identifiers.

        Args:
            previous_id: Previous user identifier
            new_id: New user identifier
        """
        if not self.enabled:
            return

        try:
            posthog.alias(
                previous_id=previous_id,
                distinct_id=new_id
            )
            logger.debug(f"Aliased user: {previous_id} -> {new_id}")
        except Exception as e:
            logger.error(f"Failed to alias user {previous_id} to {new_id}: {str(e)}")

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _categorize_latency(self, duration_ms: float, used_llm: bool) -> str:
        """Categorize query latency for performance analysis."""
        if used_llm:
            if duration_ms < 3000:
                return "excellent"
            elif duration_ms < 5000:
                return "good"
            elif duration_ms < 10000:
                return "acceptable"
            else:
                return "slow"
        else:
            if duration_ms < 500:
                return "excellent"
            elif duration_ms < 1000:
                return "good"
            elif duration_ms < 2000:
                return "acceptable"
            else:
                return "slow"

    def shutdown(self) -> None:
        """Shutdown PostHog client and flush remaining events."""
        if self.enabled:
            try:
                posthog.shutdown()
                logger.info("PostHog client shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down PostHog client: {str(e)}")


# Global singleton instance
_posthog_service: Optional[PostHogService] = None


def get_posthog_service() -> PostHogService:
    """Get or create the global PostHog service instance."""
    global _posthog_service
    if _posthog_service is None:
        _posthog_service = PostHogService()
    return _posthog_service
