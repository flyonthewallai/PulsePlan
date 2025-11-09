"""
Usage limiter service for quota enforcement and feature gating.

This module handles pre-flight checks before LLM operations to ensure
users have sufficient quota and proper subscription tier.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from dataclasses import dataclass

from app.database.repositories.integration_repositories import UsageRepository, get_usage_repository
from app.services.analytics.posthog_service import PostHogService, get_posthog_service
from app.services.usage.usage_config import (
    UsageConfig,
    SubscriptionTier,
    OperationType,
)

logger = logging.getLogger(__name__)


@dataclass
class QuotaCheckResult:
    """Result of quota check operation"""

    allowed: bool
    reason: Optional[str] = None
    tokens_remaining: int = 0
    tokens_needed: int = 0
    subscription_tier: str = "free"
    requires_upgrade: bool = False
    quota_status: str = "ok"  # 'ok', 'warning', 'critical', 'exceeded'


class UsageLimiter:
    """
    Service for enforcing usage quotas and feature gates.

    Performs pre-flight checks before LLM operations to:
    - Verify subscription tier requirements
    - Check token quota availability
    - Send analytics events for blocked operations
    - Provide upgrade prompts when appropriate
    """

    def __init__(
        self,
        usage_repo: Optional[UsageRepository] = None,
        posthog: Optional[PostHogService] = None,
    ):
        self.usage_repo = usage_repo or get_usage_repository()
        self.posthog = posthog or get_posthog_service()

    async def check_operation_allowed(
        self, user_id: UUID, operation_type: OperationType, custom_token_estimate: Optional[int] = None
    ) -> QuotaCheckResult:
        """
        Check if user is allowed to perform an operation.

        This is the main entry point for quota enforcement.

        Args:
            user_id: User attempting the operation
            operation_type: Type of operation to check
            custom_token_estimate: Optional custom token estimate (uses default if not provided)

        Returns:
            QuotaCheckResult with decision and metadata
        """
        # Get user quota info
        quota = await self.usage_repo.get_user_quota(user_id)

        if not quota:
            # Create default quota for new user
            quota = await self.usage_repo.create_user_quota(user_id)

        subscription_tier = SubscriptionTier(quota["subscription_tier"])
        tokens_used = quota["tokens_used_this_month"]
        monthly_limit = quota["monthly_token_limit"]

        # 1. Check if operation requires premium subscription
        if UsageConfig.is_premium_only(operation_type):
            if subscription_tier != SubscriptionTier.PREMIUM:
                # Track feature gate event
                await self.posthog.track_feature_gated(
                    user_id=str(user_id),
                    feature=operation_type.value,
                    reason="premium_only",
                )

                return QuotaCheckResult(
                    allowed=False,
                    reason="This feature requires a premium subscription",
                    tokens_remaining=monthly_limit - tokens_used,
                    tokens_needed=0,
                    subscription_tier=subscription_tier.value,
                    requires_upgrade=True,
                    quota_status="premium_required",
                )

        # 2. Get token estimate for operation
        if custom_token_estimate:
            tokens_needed = custom_token_estimate
        else:
            tokens_needed = UsageConfig.get_operation_estimate(operation_type)

        # 3. Check token quota
        has_quota, tokens_remaining = await self.usage_repo.check_quota_available(
            user_id, tokens_needed
        )

        quota_status = UsageConfig.get_quota_status(tokens_used, subscription_tier)

        if not has_quota:
            # Track quota exceeded event
            await self.posthog.track_quota_exceeded(
                user_id=str(user_id),
                operation=operation_type.value,
                reason="insufficient_tokens",
            )

            # Show upgrade prompt for applicable operations
            if UsageConfig.should_show_upgrade_prompt(operation_type):
                await self.posthog.track_upgrade_prompt_shown(
                    user_id=str(user_id),
                    feature=operation_type.value,
                    tokens_needed=tokens_needed,
                    tokens_remaining=tokens_remaining,
                )

            return QuotaCheckResult(
                allowed=False,
                reason=f"Insufficient token quota. Need {tokens_needed} tokens, have {tokens_remaining} remaining.",
                tokens_remaining=tokens_remaining,
                tokens_needed=tokens_needed,
                subscription_tier=subscription_tier.value,
                requires_upgrade=subscription_tier == SubscriptionTier.FREE,
                quota_status="exceeded",
            )

        # 4. Operation allowed - return success with quota status
        return QuotaCheckResult(
            allowed=True,
            reason=None,
            tokens_remaining=tokens_remaining,
            tokens_needed=tokens_needed,
            subscription_tier=subscription_tier.value,
            requires_upgrade=False,
            quota_status=quota_status,
        )

    async def enforce_operation_quota(
        self, user_id: UUID, operation_type: OperationType
    ) -> QuotaCheckResult:
        """
        Enforce quota check and raise exception if not allowed.

        Convenience method for operations that should fail fast.

        Args:
            user_id: User attempting the operation
            operation_type: Type of operation

        Returns:
            QuotaCheckResult if allowed

        Raises:
            QuotaExceededException: If operation not allowed
        """
        result = await self.check_operation_allowed(user_id, operation_type)

        if not result.allowed:
            raise QuotaExceededException(result)

        return result

    async def get_quota_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive quota summary for user.

        Useful for displaying quota status in UI.

        Args:
            user_id: User ID

        Returns:
            Dictionary with quota details and status
        """
        quota = await self.usage_repo.get_user_quota(user_id)

        if not quota:
            quota = await self.usage_repo.create_user_quota(user_id)

        subscription_tier = SubscriptionTier(quota["subscription_tier"])
        tokens_used = quota["tokens_used_this_month"]
        monthly_limit = quota["monthly_token_limit"]
        tokens_remaining = monthly_limit - tokens_used

        quota_percentage = UsageConfig.calculate_quota_percentage(
            tokens_used, subscription_tier
        )
        quota_status = UsageConfig.get_quota_status(tokens_used, subscription_tier)

        # Get today's usage
        tokens_used_today = await self.usage_repo.get_user_usage_today(user_id)
        daily_limit = UsageConfig.get_daily_limit(subscription_tier)

        # Get operation breakdown
        operation_breakdown = await self.usage_repo.get_usage_by_operation(user_id)

        return {
            "user_id": str(user_id),
            "subscription_tier": subscription_tier.value,
            "monthly": {
                "limit": monthly_limit,
                "used": tokens_used,
                "remaining": tokens_remaining,
                "percentage": quota_percentage,
                "status": quota_status,
            },
            "daily": {
                "limit": daily_limit,
                "used": tokens_used_today,
                "remaining": max(0, daily_limit - tokens_used_today),
            },
            "operation_breakdown": operation_breakdown,
            "last_reset_at": quota["last_reset_at"].isoformat(),
            "warnings": self._get_quota_warnings(quota_status, tokens_remaining),
        }

    def _get_quota_warnings(
        self, quota_status: str, tokens_remaining: int
    ) -> list[str]:
        """Generate user-friendly quota warnings"""
        warnings = []

        if quota_status == "exceeded":
            warnings.append("You have exceeded your monthly token quota.")
            warnings.append("Upgrade to Premium for unlimited access.")
        elif quota_status == "critical":
            warnings.append(
                f"You are running low on tokens ({tokens_remaining} remaining)."
            )
            warnings.append("Consider upgrading to avoid interruptions.")
        elif quota_status == "warning":
            warnings.append(
                f"You have used 75% of your monthly quota ({tokens_remaining} tokens remaining)."
            )

        return warnings

    async def can_use_premium_feature(
        self, user_id: UUID, feature_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can use a premium feature.

        Args:
            user_id: User ID
            feature_name: Name of the feature

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        quota = await self.usage_repo.get_user_quota(user_id)

        if not quota:
            quota = await self.usage_repo.create_user_quota(user_id)

        subscription_tier = SubscriptionTier(quota["subscription_tier"])

        if subscription_tier != SubscriptionTier.PREMIUM:
            # Track feature gate event
            await self.posthog.track_feature_gated(
                user_id=str(user_id), feature=feature_name, reason="premium_only"
            )

            return False, "This feature requires a premium subscription"

        # Track premium feature usage
        await self.posthog.track_premium_feature_used(
            user_id=str(user_id), feature=feature_name
        )

        return True, None

    async def update_user_subscription(
        self, user_id: UUID, new_tier: SubscriptionTier
    ) -> Dict[str, Any]:
        """
        Update user's subscription tier.

        Args:
            user_id: User ID
            new_tier: New subscription tier

        Returns:
            Updated quota information
        """
        # Get old tier for analytics
        old_quota = await self.usage_repo.get_user_quota(user_id)
        old_tier = old_quota["subscription_tier"] if old_quota else "free"

        # Update subscription tier
        updated_quota = await self.usage_repo.update_subscription_tier(
            user_id, new_tier
        )

        # Track subscription change in PostHog
        await self.posthog.track_subscription_status_changed(
            user_id=str(user_id),
            old_status=old_tier,
            new_status=new_tier.value,
            plan_type=new_tier.value,
        )

        logger.info(
            f"Updated subscription for user {user_id}: {old_tier} -> {new_tier.value}"
        )

        return updated_quota


class QuotaExceededException(Exception):
    """Exception raised when user exceeds quota"""

    def __init__(self, result: QuotaCheckResult):
        self.result = result
        super().__init__(result.reason)


# Singleton instance
_usage_limiter: Optional[UsageLimiter] = None


def get_usage_limiter() -> UsageLimiter:
    """Get or create global usage limiter instance"""
    global _usage_limiter
    if _usage_limiter is None:
        _usage_limiter = UsageLimiter()
    return _usage_limiter
