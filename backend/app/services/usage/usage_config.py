"""
Global configuration for token costs, usage limits, and subscription tiers.

This module centralizes all token cost calculations and quota limits
to ensure consistent pricing across the application.
"""

from enum import Enum
from typing import Dict
from dataclasses import dataclass


class SubscriptionTier(str, Enum):
    """User subscription tiers with different token limits"""

    FREE = "free"
    PREMIUM = "premium"


class OperationType(str, Enum):
    """Types of operations that consume tokens"""

    # NLU Operations (fast, cheap)
    INTENT_CLASSIFICATION = "intent_classification"
    ENTITY_EXTRACTION = "entity_extraction"

    # Agent Operations (moderate cost)
    CONVERSATION = "conversation"
    TASK_ENRICHMENT = "task_enrichment"
    EMAIL_DRAFT = "email_draft"
    BRIEFING_GENERATION = "briefing_generation"

    # Premium Operations (expensive)
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    MULTI_TURN_CONVERSATION = "multi_turn_conversation"
    COMPLEX_REASONING = "complex_reasoning"


@dataclass
class ModelCost:
    """Token costs per model (cost per 1k tokens in USD)"""

    # OpenAI GPT-4o models (as of 2024)
    GPT_4O_INPUT = 0.0025  # $2.50 per 1M input tokens
    GPT_4O_OUTPUT = 0.01  # $10.00 per 1M output tokens

    # OpenAI GPT-4o-mini models (cost-efficient)
    GPT_4O_MINI_INPUT = 0.00015  # $0.15 per 1M input tokens
    GPT_4O_MINI_OUTPUT = 0.0006  # $0.60 per 1M output tokens

    # OpenAI GPT-3.5-turbo (legacy)
    GPT_35_TURBO_INPUT = 0.0005  # $0.50 per 1M input tokens
    GPT_35_TURBO_OUTPUT = 0.0015  # $1.50 per 1M output tokens

    @classmethod
    def get_cost_per_token(cls, model: str, token_type: str = "input") -> float:
        """
        Get cost per token for a specific model.

        Args:
            model: Model name (e.g., 'gpt-4o', 'gpt-4o-mini')
            token_type: 'input' or 'output'

        Returns:
            Cost per token in USD
        """
        model_lower = model.lower()
        token_type_lower = token_type.lower()

        # Map model names to costs
        if "gpt-4o-mini" in model_lower:
            return cls.GPT_4O_MINI_INPUT if token_type_lower == "input" else cls.GPT_4O_MINI_OUTPUT
        elif "gpt-4o" in model_lower:
            return cls.GPT_4O_INPUT if token_type_lower == "input" else cls.GPT_4O_OUTPUT
        elif "gpt-3.5-turbo" in model_lower:
            return cls.GPT_35_TURBO_INPUT if token_type_lower == "input" else cls.GPT_35_TURBO_OUTPUT
        else:
            # Default to GPT-4o pricing for unknown models (conservative estimate)
            return cls.GPT_4O_INPUT if token_type_lower == "input" else cls.GPT_4O_OUTPUT

    @classmethod
    def calculate_cost(
        cls, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Calculate total cost for a model call.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        input_cost = (input_tokens / 1000) * cls.get_cost_per_token(model, "input")
        output_cost = (output_tokens / 1000) * cls.get_cost_per_token(model, "output")
        return input_cost + output_cost


class UsageConfig:
    """Central configuration for usage limits and costs"""

    # =========================================================================
    # SUBSCRIPTION TIER LIMITS
    # =========================================================================

    # Monthly token limits per tier
    MONTHLY_LIMITS: Dict[SubscriptionTier, int] = {
        SubscriptionTier.FREE: 10_000,  # 10k tokens/month for free users
        SubscriptionTier.PREMIUM: 1_000_000,  # 1M tokens/month for premium users
    }

    # Daily token limits (for additional safety)
    DAILY_LIMITS: Dict[SubscriptionTier, int] = {
        SubscriptionTier.FREE: 1_000,  # 1k tokens/day for free users
        SubscriptionTier.PREMIUM: 100_000,  # 100k tokens/day for premium users
    }

    # =========================================================================
    # OPERATION COST ESTIMATES (in tokens)
    # =========================================================================

    # Estimated token costs per operation type
    # These are averages - actual costs will be tracked per LLM call
    OPERATION_TOKEN_ESTIMATES: Dict[OperationType, int] = {
        # Fast NLU operations (using GPT-4o-mini)
        OperationType.INTENT_CLASSIFICATION: 100,  # ~100 tokens for classification
        OperationType.ENTITY_EXTRACTION: 150,  # ~150 tokens for extraction
        # Moderate agent operations
        OperationType.CONVERSATION: 500,  # ~500 tokens per conversation turn
        OperationType.TASK_ENRICHMENT: 300,  # ~300 tokens to enrich task details
        OperationType.EMAIL_DRAFT: 800,  # ~800 tokens to draft email
        OperationType.BRIEFING_GENERATION: 1_000,  # ~1k tokens for daily briefing
        # Expensive premium operations
        OperationType.SCHEDULE_OPTIMIZATION: 2_000,  # ~2k tokens for scheduling
        OperationType.MULTI_TURN_CONVERSATION: 1_500,  # ~1.5k tokens for multi-turn
        OperationType.COMPLEX_REASONING: 3_000,  # ~3k tokens for complex reasoning
    }

    # =========================================================================
    # PREMIUM FEATURE GATES
    # =========================================================================

    # Operations that require premium subscription (regardless of token limits)
    PREMIUM_ONLY_OPERATIONS = {
        OperationType.EMAIL_DRAFT,  # LLM-based email drafting
        OperationType.SCHEDULE_OPTIMIZATION,  # Advanced scheduling
        OperationType.COMPLEX_REASONING,  # Complex reasoning tasks
    }

    # Operations that show upgrade prompts when quota is low
    UPGRADE_PROMPT_OPERATIONS = {
        OperationType.BRIEFING_GENERATION,
        OperationType.MULTI_TURN_CONVERSATION,
        OperationType.TASK_ENRICHMENT,
    }

    # =========================================================================
    # MODEL SELECTION POLICY
    # =========================================================================

    # Default models per operation type (for cost optimization)
    DEFAULT_MODELS: Dict[OperationType, str] = {
        # Use cheap models for fast operations
        OperationType.INTENT_CLASSIFICATION: "gpt-4o-mini",
        OperationType.ENTITY_EXTRACTION: "gpt-4o-mini",
        # Use standard models for quality-critical operations
        OperationType.CONVERSATION: "gpt-4o-mini",
        OperationType.TASK_ENRICHMENT: "gpt-4o-mini",
        OperationType.BRIEFING_GENERATION: "gpt-4o",
        # Use powerful models for premium operations
        OperationType.EMAIL_DRAFT: "gpt-4o",
        OperationType.SCHEDULE_OPTIMIZATION: "gpt-4o",
        OperationType.MULTI_TURN_CONVERSATION: "gpt-4o-mini",
        OperationType.COMPLEX_REASONING: "gpt-4o",
    }

    # =========================================================================
    # QUOTA WARNING THRESHOLDS
    # =========================================================================

    # Percentage thresholds for showing warnings
    QUOTA_WARNING_THRESHOLDS = {
        "warning": 0.75,  # Show warning at 75% usage
        "critical": 0.90,  # Show critical warning at 90% usage
        "exceeded": 1.0,  # Block at 100% usage
    }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @classmethod
    def get_monthly_limit(cls, tier: SubscriptionTier) -> int:
        """Get monthly token limit for a subscription tier"""
        return cls.MONTHLY_LIMITS[tier]

    @classmethod
    def get_daily_limit(cls, tier: SubscriptionTier) -> int:
        """Get daily token limit for a subscription tier"""
        return cls.DAILY_LIMITS[tier]

    @classmethod
    def get_operation_estimate(cls, operation: OperationType) -> int:
        """Get estimated token cost for an operation"""
        return cls.OPERATION_TOKEN_ESTIMATES[operation]

    @classmethod
    def is_premium_only(cls, operation: OperationType) -> bool:
        """Check if operation requires premium subscription"""
        return operation in cls.PREMIUM_ONLY_OPERATIONS

    @classmethod
    def should_show_upgrade_prompt(cls, operation: OperationType) -> bool:
        """Check if operation should show upgrade prompt when quota is low"""
        return operation in cls.UPGRADE_PROMPT_OPERATIONS

    @classmethod
    def get_default_model(cls, operation: OperationType) -> str:
        """Get default model for an operation type"""
        return cls.DEFAULT_MODELS.get(operation, "gpt-4o-mini")

    @classmethod
    def calculate_quota_percentage(cls, tokens_used: int, tier: SubscriptionTier) -> float:
        """Calculate percentage of monthly quota used"""
        limit = cls.get_monthly_limit(tier)
        return (tokens_used / limit) * 100 if limit > 0 else 0

    @classmethod
    def get_quota_status(cls, tokens_used: int, tier: SubscriptionTier) -> str:
        """
        Get quota status based on usage.

        Returns:
            'ok', 'warning', 'critical', or 'exceeded'
        """
        percentage = cls.calculate_quota_percentage(tokens_used, tier) / 100

        if percentage >= cls.QUOTA_WARNING_THRESHOLDS["exceeded"]:
            return "exceeded"
        elif percentage >= cls.QUOTA_WARNING_THRESHOLDS["critical"]:
            return "critical"
        elif percentage >= cls.QUOTA_WARNING_THRESHOLDS["warning"]:
            return "warning"
        else:
            return "ok"

    @classmethod
    def get_tokens_remaining(cls, tokens_used: int, tier: SubscriptionTier) -> int:
        """Calculate remaining tokens in quota"""
        limit = cls.get_monthly_limit(tier)
        return max(0, limit - tokens_used)
