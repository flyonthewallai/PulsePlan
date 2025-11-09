"""
Token tracking service with PostHog integration.

This module provides centralized token tracking for all LLM calls,
integrating with both database storage and PostHog analytics.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.database.repositories.integration_repositories import UsageRepository, get_usage_repository
from app.services.analytics.posthog_service import PostHogService, get_posthog_service
from app.services.usage.usage_config import (
    UsageConfig,
    ModelCost,
    OperationType,
)

logger = logging.getLogger(__name__)


class TokenTracker:
    """
    Centralized token tracking service.

    Handles:
    - Recording LLM usage to database
    - Calculating token costs
    - Sending analytics events to PostHog
    - Usage trend analysis
    """

    def __init__(
        self,
        usage_repo: Optional[UsageRepository] = None,
        posthog: Optional[PostHogService] = None,
    ):
        self.usage_repo = usage_repo or get_usage_repository()
        self.posthog = posthog or get_posthog_service()

    async def track_llm_call(
        self,
        user_id: UUID,
        operation_type: OperationType,
        model: str,
        input_tokens: int,
        output_tokens: int,
        session_id: Optional[UUID] = None,
        intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
    ) -> UUID:
        """
        Track an LLM API call with full token and cost tracking.

        Args:
            user_id: User who made the call
            operation_type: Type of operation (from OperationType enum)
            model: LLM model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            session_id: Optional session/conversation ID
            intent: Optional classified intent
            metadata: Optional additional context
            duration_ms: Optional call duration for performance tracking

        Returns:
            UUID of created usage record
        """
        try:
            # Calculate total tokens and cost
            total_tokens = input_tokens + output_tokens
            cost_usd = ModelCost.calculate_cost(model, input_tokens, output_tokens)

            # Enhance metadata with token breakdown
            enhanced_metadata = metadata or {}
            enhanced_metadata.update(
                {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "duration_ms": duration_ms,
                }
            )

            # Record to database
            usage_id = await self.usage_repo.record_llm_usage(
                user_id=user_id,
                tokens_used=total_tokens,
                model=model,
                operation_type=operation_type.value,
                cost_usd=cost_usd,
                session_id=session_id,
                intent=intent,
                metadata=enhanced_metadata,
            )

            # Send analytics event to PostHog
            await self.posthog.track_llm_call_made(
                user_id=str(user_id),
                operation=operation_type.value,
                model=model,
                tokens_used=total_tokens,
                duration_ms=duration_ms or 0,
                success=True,
                session_id=str(session_id) if session_id else None,
            )

            logger.debug(
                f"Tracked LLM call: {total_tokens} tokens "
                f"(operation: {operation_type.value}, model: {model})"
            )

            return usage_id

        except Exception as e:
            logger.error(f"Error tracking LLM call: {e}")
            # Send error event to PostHog
            await self.posthog.track_llm_call_made(
                user_id=str(user_id),
                operation=operation_type.value,
                model=model,
                tokens_used=0,
                duration_ms=duration_ms or 0,
                success=False,
                session_id=str(session_id) if session_id else None,
            )
            raise

    async def estimate_operation_cost(
        self, operation_type: OperationType, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get estimated token cost for an operation.

        Args:
            operation_type: Type of operation
            model: Optional model (uses default if not provided)

        Returns:
            Dictionary with token estimate and cost
        """
        if model is None:
            model = UsageConfig.get_default_model(operation_type)

        estimated_tokens = UsageConfig.get_operation_estimate(operation_type)

        # Assume 70% input / 30% output split for estimation
        estimated_input = int(estimated_tokens * 0.7)
        estimated_output = int(estimated_tokens * 0.3)

        estimated_cost = ModelCost.calculate_cost(
            model, estimated_input, estimated_output
        )

        return {
            "operation_type": operation_type.value,
            "model": model,
            "estimated_total_tokens": estimated_tokens,
            "estimated_input_tokens": estimated_input,
            "estimated_output_tokens": estimated_output,
            "estimated_cost_usd": estimated_cost,
        }

    async def get_usage_stats(
        self, user_id: UUID, period: str = "month"
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a user.

        Args:
            user_id: User ID
            period: 'day', 'month', or 'all'

        Returns:
            Dictionary with usage stats
        """
        if period == "day":
            total_tokens = await self.usage_repo.get_user_usage_today(user_id)
        elif period == "month":
            total_tokens = await self.usage_repo.get_user_usage_this_month(user_id)
        else:
            total_tokens = await self.usage_repo.get_user_usage_this_month(user_id)

        # Get quota information
        quota = await self.usage_repo.get_user_quota(user_id)

        if not quota:
            # Create default quota
            quota = await self.usage_repo.create_user_quota(user_id)

        # Calculate usage percentage and status
        tier = quota["subscription_tier"]
        monthly_limit = quota["monthly_token_limit"]
        tokens_used = quota["tokens_used_this_month"]

        quota_percentage = UsageConfig.calculate_quota_percentage(
            tokens_used, tier
        )
        quota_status = UsageConfig.get_quota_status(tokens_used, tier)
        tokens_remaining = UsageConfig.get_tokens_remaining(tokens_used, tier)

        # Get breakdown by operation
        operation_breakdown = await self.usage_repo.get_usage_by_operation(user_id)

        return {
            "user_id": str(user_id),
            "period": period,
            "total_tokens_used": total_tokens if period == "day" else tokens_used,
            "monthly_limit": monthly_limit,
            "tokens_remaining": tokens_remaining,
            "quota_percentage": quota_percentage,
            "quota_status": quota_status,
            "subscription_tier": tier,
            "operation_breakdown": operation_breakdown,
            "last_reset_at": quota["last_reset_at"].isoformat(),
        }

    async def check_and_track_quota_warnings(
        self, user_id: UUID, operation_type: OperationType
    ) -> Optional[str]:
        """
        Check quota status and send analytics events for warnings.

        Args:
            user_id: User ID
            operation_type: Operation being attempted

        Returns:
            Warning level ('warning', 'critical', 'exceeded', or None)
        """
        quota = await self.usage_repo.get_user_quota(user_id)

        if not quota:
            return None

        tokens_used = quota["tokens_used_this_month"]
        tier = quota["subscription_tier"]
        quota_status = UsageConfig.get_quota_status(tokens_used, tier)

        # Send analytics events for quota warnings
        if quota_status == "exceeded":
            estimated_tokens = UsageConfig.get_operation_estimate(operation_type)
            tokens_remaining = UsageConfig.get_tokens_remaining(tokens_used, tier)

            await self.posthog.track_quota_exceeded(
                user_id=str(user_id),
                operation=operation_type.value,
                reason="monthly_limit_reached",
            )

            # Show upgrade prompt if applicable
            if UsageConfig.should_show_upgrade_prompt(operation_type):
                await self.posthog.track_upgrade_prompt_shown(
                    user_id=str(user_id),
                    feature=operation_type.value,
                    tokens_needed=estimated_tokens,
                    tokens_remaining=tokens_remaining,
                )

        elif quota_status == "critical":
            # Track when user enters critical zone
            self.posthog.track_event(
                user_id=str(user_id),
                event_name="quota_critical",
                properties={
                    "tokens_used": tokens_used,
                    "monthly_limit": quota["monthly_token_limit"],
                    "quota_percentage": UsageConfig.calculate_quota_percentage(
                        tokens_used, tier
                    ),
                },
            )

        return quota_status if quota_status in ["warning", "critical", "exceeded"] else None

    async def get_usage_trends(
        self, user_id: UUID, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage trends over time.

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Dictionary with trend analysis
        """
        history = await self.usage_repo.get_recent_usage_history(user_id, days)

        if not history:
            return {
                "user_id": str(user_id),
                "days_analyzed": days,
                "daily_average": 0,
                "total_usage": 0,
                "trend": "no_data",
            }

        # Calculate daily average
        total_tokens = sum(record["total_tokens"] for record in history)
        daily_average = total_tokens / days if days > 0 else 0

        # Simple trend analysis (comparing first half vs second half)
        mid_point = len(history) // 2
        if mid_point > 0:
            first_half = sum(
                record["total_tokens"] for record in history[mid_point:]
            )
            second_half = sum(
                record["total_tokens"] for record in history[:mid_point]
            )

            if second_half > first_half * 1.2:
                trend = "increasing"
            elif second_half < first_half * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "user_id": str(user_id),
            "days_analyzed": days,
            "daily_average": daily_average,
            "total_usage": total_tokens,
            "trend": trend,
            "usage_history": history,
        }


# Singleton instance
_token_tracker: Optional[TokenTracker] = None


def get_token_tracker() -> TokenTracker:
    """Get or create global token tracker instance"""
    global _token_tracker
    if _token_tracker is None:
        _token_tracker = TokenTracker()
    return _token_tracker
