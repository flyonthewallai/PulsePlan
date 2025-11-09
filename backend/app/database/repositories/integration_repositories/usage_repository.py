"""
Usage tracking repository for token usage and quota management.

This module handles all database operations related to LLM usage tracking,
quota management, and usage analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.services.usage.usage_config import SubscriptionTier, OperationType
from supabase import Client

logger = logging.getLogger(__name__)


class UsageRepository:
    """Repository for usage tracking database operations"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    # =========================================================================
    # LLM USAGE TRACKING
    # =========================================================================

    async def record_llm_usage(
        self,
        user_id: UUID,
        tokens_used: int,
        model: str,
        operation_type: str,
        cost_usd: float,
        session_id: Optional[UUID] = None,
        intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Record LLM token usage.

        Args:
            user_id: User who made the LLM call
            tokens_used: Number of tokens consumed
            model: LLM model used
            operation_type: Type of operation (from OperationType enum)
            cost_usd: Calculated cost in USD
            session_id: Optional session/conversation ID
            intent: Optional intent classification
            metadata: Optional additional context

        Returns:
            UUID of created usage record
        """
        query = """
            INSERT INTO llm_usage (
                user_id, session_id, intent, tokens_used, model,
                operation_type, cost_usd, metadata, timestamp
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """

        try:
            result = await self.db.fetchval(
                query,
                user_id,
                session_id,
                intent,
                tokens_used,
                model,
                operation_type,
                cost_usd,
                metadata or {},
                datetime.utcnow(),
            )

            # Also update usage_quotas
            await self._increment_monthly_usage(user_id, tokens_used)

            logger.debug(
                f"Recorded {tokens_used} tokens for user {user_id} "
                f"(operation: {operation_type}, model: {model})"
            )

            return result

        except Exception as e:
            logger.error(f"Error recording LLM usage: {e}")
            raise

    async def _increment_monthly_usage(self, user_id: UUID, tokens: int):
        """Increment user's monthly token usage"""
        query = """
            INSERT INTO usage_quotas (user_id, tokens_used_this_month)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
            SET tokens_used_this_month = usage_quotas.tokens_used_this_month + $2
        """
        await self.db.execute(query, user_id, tokens)

    async def get_user_usage_today(self, user_id: UUID) -> int:
        """Get total tokens used by user today"""
        query = """
            SELECT COALESCE(SUM(tokens_used), 0) as total
            FROM llm_usage
            WHERE user_id = $1
            AND timestamp >= date_trunc('day', NOW())
        """
        result = await self.db.fetchval(query, user_id)
        return result or 0

    async def get_user_usage_this_month(self, user_id: UUID) -> int:
        """Get total tokens used by user this month"""
        query = """
            SELECT tokens_used_this_month
            FROM usage_quotas
            WHERE user_id = $1
        """
        result = await self.db.fetchval(query, user_id)
        return result or 0

    async def get_usage_by_operation(
        self, user_id: UUID, start_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get usage breakdown by operation type.

        Args:
            user_id: User ID
            start_date: Optional start date (default: current month)

        Returns:
            Dictionary mapping operation_type to token count
        """
        if start_date is None:
            start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = """
            SELECT operation_type, SUM(tokens_used) as total
            FROM llm_usage
            WHERE user_id = $1 AND timestamp >= $2
            GROUP BY operation_type
        """

        results = await self.db.fetch(query, user_id, start_date)
        return {row["operation_type"]: row["total"] for row in results}

    async def get_recent_usage_history(
        self, user_id: UUID, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get recent usage history for analytics.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of usage records
        """
        query = """
            SELECT
                DATE(timestamp) as date,
                operation_type,
                SUM(tokens_used) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as call_count
            FROM llm_usage
            WHERE user_id = $1
            AND timestamp >= NOW() - INTERVAL '{} days'
            GROUP BY DATE(timestamp), operation_type
            ORDER BY date DESC, operation_type
        """.format(days)

        results = await self.db.fetch(query, user_id)
        return [dict(row) for row in results]

    # =========================================================================
    # QUOTA MANAGEMENT
    # =========================================================================

    async def get_user_quota(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user's quota information.

        Returns:
            Dictionary with quota details or None if not found
        """
        query = """
            SELECT
                user_id,
                monthly_token_limit,
                tokens_used_this_month,
                last_reset_at,
                subscription_tier
            FROM usage_quotas
            WHERE user_id = $1
        """

        result = await self.db.fetchrow(query, user_id)
        return dict(result) if result else None

    async def create_user_quota(
        self,
        user_id: UUID,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        monthly_limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create quota record for new user.

        Args:
            user_id: User ID
            subscription_tier: Subscription tier
            monthly_limit: Optional custom limit (uses tier default if not provided)

        Returns:
            Created quota record
        """
        from app.services.usage.usage_config import UsageConfig

        if monthly_limit is None:
            monthly_limit = UsageConfig.get_monthly_limit(subscription_tier)

        query = """
            INSERT INTO usage_quotas (
                user_id, subscription_tier, monthly_token_limit,
                tokens_used_this_month, last_reset_at
            )
            VALUES ($1, $2, $3, 0, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET subscription_tier = $2, monthly_token_limit = $3
            RETURNING *
        """

        result = await self.db.fetchrow(
            query, user_id, subscription_tier.value, monthly_limit
        )
        return dict(result)

    async def update_subscription_tier(
        self, user_id: UUID, new_tier: SubscriptionTier
    ) -> Dict[str, Any]:
        """
        Update user's subscription tier and adjust quota.

        Args:
            user_id: User ID
            new_tier: New subscription tier

        Returns:
            Updated quota record
        """
        from app.services.usage.usage_config import UsageConfig

        new_limit = UsageConfig.get_monthly_limit(new_tier)

        query = """
            UPDATE usage_quotas
            SET subscription_tier = $1, monthly_token_limit = $2
            WHERE user_id = $3
            RETURNING *
        """

        result = await self.db.fetchrow(query, new_tier.value, new_limit, user_id)

        if result:
            logger.info(
                f"Updated user {user_id} to tier {new_tier.value} "
                f"with limit {new_limit}"
            )
            return dict(result)

        # Create quota if doesn't exist
        return await self.create_user_quota(user_id, new_tier, new_limit)

    async def reset_monthly_quota(self, user_id: UUID):
        """Reset user's monthly quota (called on month rollover)"""
        query = """
            UPDATE usage_quotas
            SET tokens_used_this_month = 0, last_reset_at = NOW()
            WHERE user_id = $1
        """
        await self.db.execute(query, user_id)
        logger.info(f"Reset monthly quota for user {user_id}")

    async def check_quota_available(
        self, user_id: UUID, tokens_needed: int
    ) -> tuple[bool, int]:
        """
        Check if user has enough quota for operation.

        Args:
            user_id: User ID
            tokens_needed: Tokens needed for operation

        Returns:
            Tuple of (has_quota: bool, tokens_remaining: int)
        """
        quota = await self.get_user_quota(user_id)

        if not quota:
            # Create default quota for new user
            quota = await self.create_user_quota(user_id)

        tokens_used = quota["tokens_used_this_month"]
        limit = quota["monthly_token_limit"]
        tokens_remaining = limit - tokens_used

        has_quota = tokens_remaining >= tokens_needed

        return has_quota, tokens_remaining

    # =========================================================================
    # USAGE ANALYTICS & SUMMARIES
    # =========================================================================

    async def get_usage_summary(
        self, user_id: UUID, year: int, month: int
    ) -> Optional[Dict[str, Any]]:
        """Get aggregated usage summary for a specific month"""
        query = """
            SELECT *
            FROM usage_summary
            WHERE user_id = $1 AND year = $2 AND month = $3
        """

        result = await self.db.fetchrow(query, user_id, year, month)
        return dict(result) if result else None

    async def create_usage_summary(
        self,
        user_id: UUID,
        year: int,
        month: int,
        total_tokens: int,
        total_cost_usd: float,
        operation_breakdown: Dict[str, int],
    ) -> Dict[str, Any]:
        """Create or update monthly usage summary"""
        query = """
            INSERT INTO usage_summary (
                user_id, year, month, total_tokens,
                total_cost_usd, operation_breakdown
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id, year, month) DO UPDATE
            SET total_tokens = $4,
                total_cost_usd = $5,
                operation_breakdown = $6
            RETURNING *
        """

        result = await self.db.fetchrow(
            query,
            user_id,
            year,
            month,
            total_tokens,
            total_cost_usd,
            operation_breakdown,
        )
        return dict(result)

    async def aggregate_monthly_usage(self):
        """
        Run monthly aggregation job to summarize usage and clean old data.

        This should be called at the beginning of each month via a scheduled job.
        """
        try:
            # Call the database function
            await self.db.execute("SELECT aggregate_monthly_usage()")
            logger.info("Monthly usage aggregation completed successfully")
        except Exception as e:
            logger.error(f"Error during monthly aggregation: {e}")
            raise

    async def reset_all_monthly_quotas(self):
        """
        Reset all users' monthly quotas.

        This should be called at the beginning of each month via a scheduled job.
        """
        try:
            await self.db.execute("SELECT reset_monthly_quotas()")
            logger.info("Monthly quota reset completed successfully")
        except Exception as e:
            logger.error(f"Error resetting monthly quotas: {e}")
            raise

    # =========================================================================
    # ADMIN & ANALYTICS
    # =========================================================================

    async def get_platform_usage_stats(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get platform-wide usage statistics (admin only).

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Dictionary with platform stats
        """
        query = """
            SELECT
                COUNT(DISTINCT user_id) as active_users,
                SUM(tokens_used) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as total_calls,
                AVG(tokens_used) as avg_tokens_per_call
            FROM llm_usage
            WHERE timestamp BETWEEN $1 AND $2
        """

        result = await self.db.fetchrow(query, start_date, end_date)
        return dict(result) if result else {}

    async def get_top_users_by_usage(
        self, limit: int = 10, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get top users by token usage"""
        query = """
            SELECT
                user_id,
                SUM(tokens_used) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as call_count
            FROM llm_usage
            WHERE timestamp >= NOW() - INTERVAL '{} days'
            GROUP BY user_id
            ORDER BY total_tokens DESC
            LIMIT $1
        """.format(days)

        results = await self.db.fetch(query, limit)
        return [dict(row) for row in results]


# Singleton instance
_usage_repository: Optional[UsageRepository] = None


def get_usage_repository() -> UsageRepository:
    """Get or create global usage repository instance"""
    global _usage_repository
    if _usage_repository is None:
        from app.config.database.supabase import get_supabase_client

        _usage_repository = UsageRepository(get_supabase_client())
    return _usage_repository
