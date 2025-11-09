# PulsePlan Agent Implementation Roadmap

## Executive Summary

Your current codebase has an excellent foundation for the hybrid AI agent architecture you described. You've already implemented:

- ✅ Deterministic NLU Pipeline (Rules → ONNX Classifier → Entity Extractors)
- ✅ LangGraph Multi-Agent System with specialized workflows
- ✅ Intent Processor with continuation/dialog management
- ✅ Planning Handler with policy-based gating
- ✅ Action Executor framework
- ✅ Subscription/Premium System (Apple Pay)
- ✅ **PostHog Analytics Integration** (Added for comprehensive agent tracking)

## Current Architecture Analysis

### What's Working Well

**NLU Pipeline** ([backend/app/agents/nlu/](../app/agents/nlu/)):

- ✅ Rule-based matching for high-precision intents
- ✅ ONNX classifier for intent classification
- ✅ Entity extractors for deterministic slot filling
- ✅ SLO gates for completeness checking

**Orchestration Layer** ([backend/app/agents/core/orchestration/](../app/agents/core/orchestration/)):

- ✅ Intent processor with continuation logic
- ✅ Planning handler with policy evaluation
- ✅ Driver interface for workflow execution
- ✅ Gates for confidence/completeness checks

**Workflow Layer** ([backend/app/agents/graphs/](../app/agents/graphs/)):

- ✅ 6 specialized LangGraph workflows:
  - TaskGraph, CalendarGraph, BriefingGraph
  - SchedulingGraph, SearchGraph, EmailGraph
- ✅ BaseWorkflow abstraction

**Premium System:**

- ✅ Subscription status tracking
- ✅ Apple Pay integration
- ✅ Premium gating infrastructure

**Analytics System (PostHog):**

- ✅ Event tracking for all agent operations
- ✅ User journey analytics
- ✅ Performance monitoring
- ✅ Feature flag support for gradual rollouts

### Critical Gaps to Address

**❌ Missing: Token-based usage tracking system**

- No token counter for free plan limits
- No LLM call tracking infrastructure
- No usage quota enforcement

**❌ Incomplete: Intent Classification Model**

- ONNX classifier exists but model file not trained/deployed
- Mock classifier used as fallback
- No training data pipeline

**❌ Incomplete: Action Executor Implementation**

- Service exists but action handlers not fully wired
- Missing execution logic for each intent type

**❌ Incomplete: Workflow-NLU Integration**

- NLU pipeline not fully connected to workflows
- Intent routing logic partially implemented

**❌ Missing: Multi-turn Conversation Memory**

- Conversation state tracking exists but not persistent
- No conversation history storage

## 📋 Phased Implementation Plan

### PHASE 1: Foundation & Token System (Week 1-2)

**Goal:** Establish token tracking and usage limits for free/premium plans

#### 1.1 Token Tracking Infrastructure

**Where:** `backend/app/services/usage/`

**Files to Create:**

- `backend/app/services/usage/token_tracker.py` - Core token tracking
- `backend/app/services/usage/usage_limiter.py` - Quota enforcement
- `backend/app/services/usage/usage_config.py` - **Global token costs & limits configuration**
- `backend/app/database/schemas/add_usage_tracking.sql` - DB schema

**Schema:**

```sql
-- Table: llm_usage
CREATE TABLE llm_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  session_id UUID,
  intent TEXT,
  tokens_used INTEGER,
  model TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  operation_type TEXT, -- 'classification', 'extraction', 'conversation'
  cost_usd DECIMAL(10,4), -- Calculated cost for billing
  metadata JSONB DEFAULT '{}'::jsonb -- Additional context
);

-- Table: usage_quotas
CREATE TABLE usage_quotas (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  monthly_token_limit INTEGER DEFAULT 10000,
  tokens_used_this_month INTEGER DEFAULT 0,
  last_reset_at TIMESTAMPTZ DEFAULT NOW(),
  subscription_tier TEXT DEFAULT 'free'
);

-- Table: usage_summary (monthly aggregated data for retention)
CREATE TABLE usage_summary (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  year INTEGER,
  month INTEGER,
  total_tokens INTEGER,
  total_cost_usd DECIMAL(10,4),
  operation_breakdown JSONB, -- {"email_draft_llm": 500, "schedule_optimization": 300}
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, year, month)
);

-- Indexes for performance
CREATE INDEX idx_llm_usage_user_timestamp ON llm_usage(user_id, timestamp DESC);
CREATE INDEX idx_llm_usage_timestamp ON llm_usage(timestamp DESC);
CREATE INDEX idx_usage_summary_user_period ON usage_summary(user_id, year, month);
```

#### 1.1.4 Data Retention Policy for llm_usage Table

**Critical for scalability:** The llm_usage table will grow fast - plan to archive or aggregate monthly totals to a summary table.

**Retention Strategy:**

```sql
-- Monthly aggregation job (run on 1st of each month)
CREATE OR REPLACE FUNCTION aggregate_monthly_usage()
RETURNS void AS $$
BEGIN
    -- Aggregate previous month's data
    INSERT INTO usage_summary (user_id, year, month, total_tokens, total_cost_usd, operation_breakdown)
    SELECT
        user_id,
        EXTRACT(YEAR FROM timestamp) as year,
        EXTRACT(MONTH FROM timestamp) as month,
        SUM(tokens_used) as total_tokens,
        SUM(cost_usd) as total_cost_usd,
        jsonb_object_agg(operation_type, tokens_used) as operation_breakdown
    FROM llm_usage
    WHERE timestamp >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
      AND timestamp < date_trunc('month', CURRENT_DATE)
    GROUP BY user_id, EXTRACT(YEAR FROM timestamp), EXTRACT(MONTH FROM timestamp)
    ON CONFLICT (user_id, year, month) DO UPDATE SET
        total_tokens = EXCLUDED.total_tokens,
        total_cost_usd = EXCLUDED.total_cost_usd,
        operation_breakdown = EXCLUDED.operation_breakdown;

    -- Archive old detailed records (keep last 3 months of detail)
    DELETE FROM llm_usage
    WHERE timestamp < CURRENT_DATE - INTERVAL '3 months';

    -- Log aggregation completion
    INSERT INTO system_logs (event, details)
    VALUES ('monthly_usage_aggregation', 'Completed aggregation for ' || to_char(CURRENT_DATE - INTERVAL '1 month', 'YYYY-MM'));
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly aggregation (via cron or background job)
-- 0 2 1 * * /path/to/aggregate_usage.sh
```

**Retention Timeline:**

- ✅ **Raw Data (llm_usage):** Keep 3 months of detailed records
- ✅ **Aggregated Data (usage_summary):** Keep indefinitely for billing/analytics
- ✅ **Monthly Aggregation:** Run on 1st of each month
- ✅ **Archive Strategy:** Move old data to cold storage (optional)
- ✅ **Performance:** Indexes optimized for common queries

**Implementation:**

```python
# backend/app/jobs/usage_aggregation.py
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.services.analytics.posthog_service import PostHogService

class UsageAggregationJob:
    """Monthly job to aggregate and archive usage data"""

    async def run_monthly_aggregation(self):
        """Aggregate previous month's usage data"""
        try:
            # Run SQL aggregation function
            async with get_db() as db:
                await db.execute("SELECT aggregate_monthly_usage()")

            # Track aggregation completion
            await PostHogService().capture(
                "usage_aggregation_completed",
                {
                    # Use TimezoneManager for consistent reference times
                    "month": get_timezone_manager().convert_to_user_timezone(datetime.utcnow(), user.timezone).strftime("%Y-%m"),
                    "records_processed": await self._count_processed_records()
                },
                "system"
            )

        except Exception as e:
            # Track aggregation failure
            await PostHogService().capture(
                "usage_aggregation_failed",
                {
                    "error": str(e),
                    "month": get_timezone_manager().convert_to_user_timezone(datetime.utcnow(), user.timezone).strftime("%Y-%m")
                },
                "system"
            )
            raise

    async def _count_processed_records(self) -> int:
        """Count records processed in last aggregation"""
        # Implementation to count processed records
        pass
```

**Implementation:**

```python
# backend/app/services/usage/usage_config.py
"""
Global configuration for token costs and limits.
All token prices + limits centralized for easy tweaking without redeployment.
"""

from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class TokenLimits:
    """Token limits per subscription tier"""
    free: int = 10000
    premium: Optional[int] = None  # Unlimited

@dataclass
class FeatureCosts:
    """Token costs for premium features"""
    email_draft_llm: int = 500
    schedule_optimization: int = 300
    bulk_task_operations: int = 200
    advanced_search: int = 400
    title_enrichment: int = 150
    conflict_explanation: int = 200
    conversation_context: int = 100

# Global configuration - can be overridden via environment or Supabase config table
TOKEN_LIMITS = TokenLimits()
FEATURE_COSTS = FeatureCosts()

# Model-specific token costs (per 1K tokens)
MODEL_COSTS = {
    "gpt-4": 30,      # $0.03 per 1K tokens
    "gpt-3.5-turbo": 2,  # $0.002 per 1K tokens
    "claude-3": 15,   # $0.015 per 1K tokens
}

# Operation-specific base costs
OPERATION_BASE_COSTS = {
    "intent_classification": 50,
    "entity_extraction": 75,
    "conversation_turn": 200,
    "workflow_execution": 100,
}
```

```python
# backend/app/services/usage/token_tracker.py
from .usage_config import TOKEN_LIMITS, FEATURE_COSTS, MODEL_COSTS, OPERATION_BASE_COSTS

class TokenTracker:
    """Track LLM token usage per user with comprehensive analytics"""

    async def track_usage(
        self,
        user_id: str,
        tokens: int,
        operation: str,
        model: str = "gpt-3.5-turbo",
        metadata: Dict[str, Any] = None
    ):
        """Track token usage with comprehensive analytics"""
        # Store in llm_usage table
        await self._store_usage_record(user_id, tokens, operation, model, metadata)

        # Update usage_quotas counter
        await self._update_quota_counter(user_id, tokens)

        # Send event to PostHog for analytics
        await self._track_analytics_event(user_id, tokens, operation, model, metadata)

    async def check_quota(self, user_id: str, operation: str = None) -> Tuple[bool, str]:
        """Check if user has quota remaining for operation"""
        usage = await self.get_usage_stats(user_id)
        subscription = await self._get_subscription_tier(user_id)

        limit = TOKEN_LIMITS.free if subscription == "free" else TOKEN_LIMITS.premium

        if limit is None:  # Premium unlimited
            return True, "unlimited"

        if usage["tokens_used_this_month"] >= limit:
            return False, f"Monthly limit reached: {limit} tokens"

        # Check operation-specific costs
        if operation:
            cost = FEATURE_COSTS.__dict__.get(operation, 0)
            if usage["tokens_used_this_month"] + cost > limit:
                return False, f"Insufficient tokens for {operation}. Need {cost}, have {limit - usage['tokens_used_this_month']}"

        return True, "quota_available"

    async def get_usage_stats(
        self,
        user_id: str,
        period: str = "month"
    ):
        """Return comprehensive usage statistics"""
        # Implementation details...
        pass
```

**Deliverables:**

- ✅ Token tracking table created
- ✅ Usage quota system implemented
- ✅ **API-gateway middleware for comprehensive token tracking**
- ✅ Middleware decorator for LLM calls: `@track_tokens`
- ✅ Free plan: 10,000 tokens/month
- ✅ Premium plan: Unlimited tokens
- ✅ PostHog analytics events for all token usage

#### 1.1.1 API-Gateway Token Tracking Middleware

**Where:** `backend/app/core/middleware/token_middleware.py`

**Critical Implementation:** Wrap every LLM-calling function, not just agent queries, so side-features (summaries, onboarding assistants, etc.) are counted too.

```python
# backend/app/core/middleware/token_middleware.py
from functools import wraps
from typing import Callable, Any
import asyncio
from app.services.usage.token_tracker import TokenTracker
from app.services.analytics.posthog_service import PostHogService

class TokenTrackingMiddleware:
    """Middleware to track token usage at API-gateway level"""

    def __init__(self):
        self.token_tracker = TokenTracker()
        self.analytics = PostHogService()

    def track_tokens(self, operation: str, model: str = "gpt-3.5-turbo"):
        """Decorator to track token usage for any LLM-calling function"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user_id from request context
                user_id = self._extract_user_id_from_context()

                # Check quota before execution
                can_proceed, reason = await self.token_tracker.check_quota(user_id, operation)
                if not can_proceed:
                    # Track quota exceeded event
                    await self.analytics.capture("quota_exceeded", {
                        "user_id": user_id,
                        "operation": operation,
                        "reason": reason
                    })
                    raise QuotaExceededException(f"Token limit reached: {reason}")

                # Execute function and capture token usage
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)

                    # Extract token count from result (function should return tokens_used)
                    tokens_used = getattr(result, 'tokens_used', 0)

                    # Track successful usage
                    await self.token_tracker.track_usage(
                        user_id=user_id,
                        tokens=tokens_used,
                        operation=operation,
                        model=model,
                        metadata={
                            "function": func.__name__,
                            "duration": time.time() - start_time,
                            "success": True
                        }
                    )

                    return result

                except Exception as e:
                    # Track error with token usage (if any)
                    tokens_used = getattr(e, 'tokens_used', 0)

                    await self.token_tracker.track_usage(
                        user_id=user_id,
                        tokens=tokens_used,
                        operation=operation,
                        model=model,
                        metadata={
                            "function": func.__name__,
                            "duration": time.time() - start_time,
                            "success": False,
                            "error_type": str(e.__class__.__name__)
                        }
                    )

                    # Track error analytics
                    await self.analytics.capture("agent_error", {
                        "workflow": operation,
                        "error_type": str(e.__class__.__name__),
                        "function": func.__name__,
                        "user_id": user_id
                    })

                    raise

            return wrapper
        return decorator

    def _extract_user_id_from_context(self) -> str:
        """Extract user_id from FastAPI request context"""
        # Implementation to get user_id from request
        pass

# Usage examples:
@TokenTrackingMiddleware().track_tokens("email_draft_llm", "gpt-4")
async def draft_email_with_llm(recipient: str, subject: str) -> EmailDraft:
    """Draft email using LLM - token usage automatically tracked"""
    # LLM call here
    pass

@TokenTrackingMiddleware().track_tokens("schedule_optimization", "gpt-3.5-turbo")
async def optimize_schedule_with_llm(tasks: List[Task]) -> Schedule:
    """Optimize schedule using LLM - token usage automatically tracked"""
    # LLM call here
    pass
```

**Key Features:**

- ✅ **Comprehensive Coverage:** Tracks ALL LLM calls across the application
- ✅ **Pre-execution Quota Check:** Prevents unnecessary API calls when quota exceeded
- ✅ **Error Tracking:** Captures token usage even when operations fail
- ✅ **Performance Monitoring:** Tracks execution duration
- ✅ **Automatic Analytics:** PostHog events for all operations
- ✅ **Error-Path Analytics:** Comprehensive error tracking for debugging

#### 1.1.2 Error-Path Analytics Implementation

**Where:** `backend/app/services/analytics/error_tracker.py`

**Critical for debugging live user sessions:** Add comprehensive error tracking with PostHog events.

```python
# backend/app/services/analytics/error_tracker.py
from typing import Dict, Any, Optional
from app.services.analytics.posthog_service import PostHogService
import traceback
import logging

class ErrorTracker:
    """Comprehensive error tracking for agent operations"""

    def __init__(self):
        self.analytics = PostHogService()
        self.logger = logging.getLogger(__name__)

    async def track_agent_error(
        self,
        workflow: str,
        error: Exception,
        user_id: str,
        context: Dict[str, Any] = None
    ):
        """Track agent errors with comprehensive context"""

        error_data = {
            "workflow": workflow,
            "error_type": str(error.__class__.__name__),
            "error_message": str(error),
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {},
            "stack_trace": traceback.format_exc() if self._should_include_stack_trace(error) else None
        }

        # Send to PostHog for analytics
        await self.analytics.capture("agent_error", error_data)

        # Log for debugging (without PII)
        self.logger.error(f"Agent error in {workflow}: {error.__class__.__name__}",
                         extra={"error_data": self._sanitize_for_logs(error_data)})

    async def track_workflow_error(
        self,
        workflow_name: str,
        node_name: str,
        error: Exception,
        user_id: str,
        state: Dict[str, Any] = None
    ):
        """Track workflow-specific errors"""

        error_data = {
            "workflow_name": workflow_name,
            "node_name": node_name,
            "error_type": str(error.__class__.__name__),
            "error_message": str(error),
            "user_id": user_id,
            "state_summary": self._summarize_state(state) if state else None,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.analytics.capture("workflow_error", error_data)

    async def track_nlu_error(
        self,
        query: str,
        error: Exception,
        user_id: str,
        nlu_pipeline_stage: str
    ):
        """Track NLU pipeline errors"""

        error_data = {
            "nlu_pipeline_stage": nlu_pipeline_stage,
            "error_type": str(error.__class__.__name__),
            "error_message": str(error),
            "user_id": user_id,
            "query_length": len(query),
            "query_hash": hashlib.md5(query.encode()).hexdigest()[:8],  # Anonymized
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.analytics.capture("nlu_error", error_data)

    async def track_external_api_error(
        self,
        service: str,
        endpoint: str,
        error: Exception,
        user_id: str,
        request_data: Dict[str, Any] = None
    ):
        """Track external API errors (Canvas, Google Calendar, etc.)"""

        error_data = {
            "service": service,
            "endpoint": endpoint,
            "error_type": str(error.__class__.__name__),
            "error_message": str(error),
            "user_id": user_id,
            "request_summary": self._summarize_request(request_data) if request_data else None,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.analytics.capture("external_api_error", error_data)

    def _should_include_stack_trace(self, error: Exception) -> bool:
        """Determine if stack trace should be included (avoid sensitive data)"""
        sensitive_errors = ["AuthenticationError", "PermissionError", "ValidationError"]
        return str(error.__class__.__name__) not in sensitive_errors

    def _sanitize_for_logs(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII from error data for logging"""
        sanitized = error_data.copy()
        # Remove or hash sensitive fields
        if "user_id" in sanitized:
            sanitized["user_id"] = sanitized["user_id"][:8] + "..."
        return sanitized

    def _summarize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create safe summary of workflow state"""
        return {
            "keys": list(state.keys()) if state else [],
            "size": len(str(state)) if state else 0
        }

    def _summarize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create safe summary of request data"""
        return {
            "keys": list(request_data.keys()) if request_data else [],
            "size": len(str(request_data)) if request_data else 0
        }

# Usage in workflows:
async def example_workflow_node(state: WorkflowState):
    try:
        # Workflow logic here
        result = await some_operation()
        return {"output_data": result}
    except Exception as e:
        # Track error with context
        await ErrorTracker().track_workflow_error(
            workflow_name="task_management",
            node_name="create_task",
            error=e,
            user_id=state["user_id"],
            state=state
        )
        raise
```

**Key Error Events Tracked:**

- ✅ `agent_error` - General agent operation errors
- ✅ `workflow_error` - Workflow-specific errors with state context
- ✅ `nlu_error` - NLU pipeline errors with query context
- ✅ `external_api_error` - External service errors
- ✅ `quota_exceeded` - Token limit reached events
- ✅ `authentication_error` - Auth failures
- ✅ `validation_error` - Input validation failures

#### 1.1.3 PostHog Event Batching System

**Where:** `backend/app/services/analytics/event_batcher.py`

**Critical for performance:** Wrap posthog.capture in an async queue to avoid blocking I/O under load. Implement by Phase 1.5 if not day 1.

```python
# backend/app/services/analytics/event_batcher.py
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import posthog
from app.core.config import settings
import logging

@dataclass
class PostHogEvent:
    """Structured event for PostHog"""
    event_name: str
    properties: Dict[str, Any]
    user_id: str
    timestamp: datetime
    distinct_id: Optional[str] = None

class PostHogEventBatcher:
    """Async event batching system for PostHog to avoid blocking I/O"""

    def __init__(self, batch_size: int = 50, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.batch_buffer: List[PostHogEvent] = []
        self.last_flush = datetime.utcnow()
        self.logger = logging.getLogger(__name__)

        # Initialize PostHog client
        posthog.api_key = settings.POSTHOG_API_KEY
        posthog.host = settings.POSTHOG_HOST

        # Start background task
        self._background_task = asyncio.create_task(self._batch_processor())

    async def capture(
        self,
        event_name: str,
        properties: Dict[str, Any],
        user_id: str,
        distinct_id: Optional[str] = None
    ):
        """Add event to batch queue (non-blocking)"""
        try:
            event = PostHogEvent(
                event_name=event_name,
                properties=properties,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                distinct_id=distinct_id or user_id
            )

            # Non-blocking queue put
            await self.event_queue.put(event)

        except asyncio.QueueFull:
            # Queue is full, log warning but don't block
            self.logger.warning("PostHog event queue full, dropping event")
        except Exception as e:
            self.logger.error(f"Error adding event to queue: {e}")

    async def _batch_processor(self):
        """Background task to process event batches"""
        while True:
            try:
                # Wait for events or timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.flush_interval
                    )
                    self.batch_buffer.append(event)
                except asyncio.TimeoutError:
                    # Timeout reached, flush if we have events
                    if self.batch_buffer:
                        await self._flush_batch()
                    continue

                # Check if we should flush
                if (len(self.batch_buffer) >= self.batch_size or
                    datetime.utcnow() - self.last_flush >= timedelta(seconds=self.flush_interval)):
                    await self._flush_batch()

            except Exception as e:
                self.logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def _flush_batch(self):
        """Flush current batch to PostHog"""
        if not self.batch_buffer:
            return

        try:
            # Convert events to PostHog format
            posthog_events = []
            for event in self.batch_buffer:
                posthog_events.append({
                    "event": event.event_name,
                    "properties": {
                        **event.properties,
                        "$timestamp": event.timestamp.isoformat(),
                        "user_id": event.user_id
                    },
                    "distinct_id": event.distinct_id
                })

            # Send batch to PostHog (non-blocking)
            await asyncio.get_event_loop().run_in_executor(
                None,
                posthog.batch,
                posthog_events
            )

            self.logger.info(f"Flushed {len(posthog_events)} events to PostHog")

        except Exception as e:
            self.logger.error(f"Error flushing batch to PostHog: {e}")
            # Could implement retry logic or dead letter queue here

        finally:
            # Clear buffer and update timestamp
            self.batch_buffer.clear()
            self.last_flush = datetime.utcnow()

    async def flush_immediately(self):
        """Force immediate flush of all pending events"""
        await self._flush_batch()

    async def close(self):
        """Gracefully shutdown the batcher"""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

        # Flush any remaining events
        await self.flush_immediately()

# Global instance
event_batcher = PostHogEventBatcher()

# Updated PostHog service to use batcher
class PostHogService:
    """PostHog service with async batching"""

    def __init__(self):
        self.batcher = event_batcher

    async def capture(
        self,
        event_name: str,
        properties: Dict[str, Any],
        user_id: str,
        distinct_id: Optional[str] = None
    ):
        """Capture event using batcher (non-blocking)"""
        await self.batcher.capture(event_name, properties, user_id, distinct_id)

    async def identify(self, user_id: str, properties: Dict[str, Any]):
        """Identify user (non-blocking)"""
        await self.batcher.capture(
            "$identify",
            {"$set": properties},
            user_id,
            user_id
        )

    async def alias(self, previous_id: str, new_id: str):
        """Alias user (non-blocking)"""
        await self.batcher.capture(
            "$create_alias",
            {"alias": new_id},
            previous_id,
            previous_id
        )
```

**Key Features:**

- ✅ **Non-blocking I/O:** Events queued asynchronously, no blocking on PostHog API calls
- ✅ **Batch Processing:** Events batched for efficiency (50 events or 5-second intervals)
- ✅ **Queue Management:** Overflow protection with configurable queue size
- ✅ **Error Handling:** Graceful degradation if PostHog is unavailable
- ✅ **Performance:** Background processing doesn't impact user-facing operations
- ✅ **Graceful Shutdown:** Flushes remaining events on application shutdown

**Testable Outcomes:**

```bash
# Test: Create free user, make 10 LLM calls, verify token count
curl -X POST /api/v1/agent/query \
  -H "Authorization: Bearer $FREE_USER_TOKEN" \
  -d '{"query": "create task: finish homework"}'

# Check usage
curl -X GET /api/v1/users/usage
# Expected: {"tokens_used": 247, "limit": 10000, "remaining": 9753}
```

#### 1.2 Intent Classification Model Training

**Where:** `ml/intent_classification/`

**Files to Create:**

- `ml/intent_classification/train_classifier.py` - Training script
- `ml/intent_classification/data/intents.json` - Training data
- `ml/intent_classification/evaluate.py` - Model evaluation
- `backend/app/agents/nlu/models/intent_classifier.onnx` - Trained model

**Training Data Format:**

```json
{
  "intents": [
    {
      "intent": "task_management",
      "examples": [
        "create a task to finish my homework",
        "add a todo for grocery shopping",
        "make a task called study for exam"
      ]
    },
    {
      "intent": "scheduling",
      "examples": [
        "schedule a study session tomorrow at 3pm",
        "block time for the gym next week",
        "plan my week"
      ]
    }
  ]
}
```

**Implementation:**

```python
# ml/intent_classification/train_classifier.py
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import onnx

# Load training data
# Train classifier
# Export to ONNX
# Save labels mapping
```

**Deliverables:**

- ✅ 10+ intents with 20+ examples each
- ✅ ONNX model exported and deployed
- ✅ Model accuracy > 85% on test set
- ✅ Labels file matching model output

**Testable Outcomes:**

```python
# Test classifier
from app.agents.nlu.classifier_onnx import IntentClassifier

classifier = IntentClassifier(
    model_path="backend/app/agents/nlu/models/intent_classifier.onnx",
    labels=["task_management", "scheduling", "search", ...]
)

intent, conf = classifier.predict("create a task to study")
assert intent == "task_management"
assert conf > 0.7
```

### PHASE 2: NLU → Workflow Integration (Week 3-4)

**Goal:** Complete end-to-end flow from user query to workflow execution

#### 2.1 Action Executor Completion

**Where:** `backend/app/agents/services/action_executor.py`

**Current State:** Service exists but action handlers incomplete

**Implementation:**

```python
# backend/app/agents/services/action_executor.py
class ActionExecutor:
    """Execute actions from planning decisions"""

    async def execute_action(
        self,
        action_record: Dict[str, Any]
    ) -> ExecutionResult:
        intent = action_record["intent"]
        params = action_record["params"]

        # Route to appropriate handler
        handler = self.get_handler(intent)
        result = await handler(params)

        # Track in PostHog
        await self.analytics.track_action_execution(
            intent=intent,
            success=result.success,
            duration=result.duration
        )

        return result

    async def _handle_task_management(self, params):
        # Create/update/delete tasks via TaskGraph
        pass

    async def _handle_scheduling(self, params):
        # Execute scheduling via SchedulingGraph
        pass

    async def _handle_email(self, params):
        # Send/read emails via EmailGraph
        pass
```

**Deliverables:**

- ✅ Action handlers for all 10+ intents
- ✅ Workflow integration for each handler
- ✅ Error handling and rollback logic
- ✅ External API call wrappers
- ✅ PostHog tracking for all action executions

**Testable Outcomes:**

```python
# Test: Execute action from NLU result
result = await action_executor.execute_action({
    "intent": "task_management",
    "params": {"title": "Finish homework", "due_date": "2025-10-25"}
})

assert result.success == True
assert result.external_refs["task_id"] is not None
```

#### 2.2 Intent Processor → Workflow Router

**Where:** `backend/app/agents/core/orchestration/intent_processor.py`

**Current State:** Intent processor exists but routing incomplete

**Enhancement Needed:**

```python
# backend/app/agents/core/orchestration/intent_processor.py

def _convert_planning_result_to_intent_result(
    self,
    planning_result: PlanningResult,
    nlu_result,
    user_query: str
) -> IntentResult:
    """
    Convert planning result to IntentResult.

    Current Status: ❌ Incomplete
    Needed: Map planning decisions to workflow types
    """

    # Determine workflow from intent
    workflow_map = {
        "task_management": "tasks",
        "scheduling": "scheduling",
        "calendar_event": "calendar",
        "search": "search",
        "email": "email"
    }

    workflow_type = workflow_map.get(nlu_result.intent)

    # Track intent routing in PostHog
    await self.analytics.track_intent_routing(
        intent=nlu_result.intent,
        workflow_type=workflow_type,
        confidence=nlu_result.confidence
    )

    # Build IntentResult with proper routing
    return IntentResult(
        intent=nlu_result.intent,
        action=self._map_intent_to_action(nlu_result.intent),
        confidence=nlu_result.confidence,
        entities=nlu_result.slots,
        workflow_type=workflow_type,
        requires_task_card=self._should_create_task_card(nlu_result.intent),
        immediate_response=planning_result.message,
        workflow_params=planning_result.execution_result or {},
        metadata={
            "decision": planning_result.decision.value,
            "action_id": str(planning_result.action_id)
        }
    )
```

**Deliverables:**

- ✅ Complete intent → workflow mapping
- ✅ Action → ActionType mapping
- ✅ Workflow parameter extraction
- ✅ Task card creation logic
- ✅ PostHog tracking for routing decisions

**Testable Outcomes:**

```bash
# Test: End-to-end query processing
POST /api/v1/agent/query
{
  "query": "create a task to study physics",
  "user_id": "..."
}

# Expected Response:
{
  "intent": "task_management",
  "action": "create_task",
  "workflow_type": "tasks",
  "confidence": 0.92,
  "entities": {"title": "study physics"},
  "decision": "AUTO",
  "execution_result": {"task_id": "..."}
}
```

#### 2.3 Conversation State Persistence

**Where:** `backend/app/database/`

**Files to Create:**

- `backend/app/database/conversation_repository.py`
- `backend/app/database/schemas/add_conversations.sql`

**Schema:**

```sql
CREATE TABLE conversation_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  started_at TIMESTAMPTZ DEFAULT NOW(),
  last_activity_at TIMESTAMPTZ DEFAULT NOW(),
  context JSONB DEFAULT '{}'::jsonb,
  context_embedding VECTOR(1536) -- OpenAI embedding dimension
);

CREATE TABLE conversation_turns (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES conversation_sessions(id),
  turn_index INTEGER,
  user_message TEXT,
  user_message_embedding VECTOR(1536), -- For semantic search
  intent TEXT,
  intent_confidence FLOAT,
  slots JSONB,
  action_id UUID,
  response TEXT,
  response_embedding VECTOR(1536), -- For semantic search
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for semantic search
CREATE INDEX idx_conversation_turns_embedding ON conversation_turns
USING ivfflat (user_message_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_conversation_sessions_embedding ON conversation_sessions
USING ivfflat (context_embedding vector_cosine_ops) WITH (lists = 100);
```

**Deliverables:**

- ✅ Conversation session tracking
- ✅ Turn history storage
- ✅ **Context embeddings for semantic recall**
- ✅ Context retrieval for follow-up queries
- ✅ Session timeout and cleanup
- ✅ PostHog funnel tracking for multi-turn conversations

#### 2.3.1 Multi-Turn Memory with Context Embeddings

**Where:** `backend/app/services/memory/conversation_memory.py`

**Critical for Phase 2.3:** Store derived context embeddings alongside text so the conversation system can later support semantic recall.

```python
# backend/app/services/memory/conversation_memory.py
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from app.database.conversation_repository import ConversationRepository
from app.services.analytics.posthog_service import PostHogService

class ConversationMemory:
    """Multi-turn conversation memory with semantic search capabilities"""

    def __init__(self):
        self.repository = ConversationRepository()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model
        self.analytics = PostHogService()

    async def store_conversation_turn(
        self,
        session_id: str,
        user_message: str,
        intent: str,
        slots: Dict[str, Any],
        response: str,
        turn_index: int
    ):
        """Store conversation turn with embeddings"""

        # Generate embeddings
        user_embedding = await self._generate_embedding(user_message)
        response_embedding = await self._generate_embedding(response)

        # Store in database
        turn_id = await self.repository.create_conversation_turn(
            session_id=session_id,
            turn_index=turn_index,
            user_message=user_message,
            user_message_embedding=user_embedding,
            intent=intent,
            slots=slots,
            response=response,
            response_embedding=response_embedding
        )

        # Update session context embedding
        await self._update_session_context_embedding(session_id)

        # Track in PostHog
        await self.analytics.capture("conversation_turn_stored", {
            "session_id": session_id,
            "turn_index": turn_index,
            "intent": intent,
            "message_length": len(user_message),
            "response_length": len(response)
        }, session_id)

        return turn_id

    async def find_semantic_context(
        self,
        session_id: str,
        current_query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find semantically similar previous turns for context"""

        # Generate embedding for current query
        query_embedding = await self._generate_embedding(current_query)

        # Search for similar turns
        similar_turns = await self.repository.find_similar_turns(
            session_id=session_id,
            query_embedding=query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold
        )

        # Track semantic search usage
        await self.analytics.capture("semantic_context_search", {
            "session_id": session_id,
            "query_length": len(current_query),
            "results_found": len(similar_turns),
            "similarity_threshold": similarity_threshold
        }, session_id)

        return similar_turns

    async def get_conversation_context(
        self,
        session_id: str,
        current_query: str,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """Get comprehensive conversation context for current query"""

        # Get recent turns
        recent_turns = await self.repository.get_recent_turns(
            session_id=session_id,
            limit=max_turns
        )

        # Find semantically relevant turns
        semantic_turns = await self.find_semantic_context(
            session_id=session_id,
            current_query=current_query,
            limit=3
        )

        # Combine and deduplicate
        all_turns = recent_turns + semantic_turns
        unique_turns = self._deduplicate_turns(all_turns)

        # Build context summary
        context = {
            "recent_turns": recent_turns,
            "semantic_turns": semantic_turns,
            "context_summary": await self._build_context_summary(unique_turns),
            "session_metadata": await self.repository.get_session_metadata(session_id)
        }

        return context

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            # Use lightweight model for embeddings
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            # Fallback to simple hash-based embedding if model fails
            await self.analytics.capture("embedding_generation_failed", {
                "error": str(e),
                "text_length": len(text)
            }, "system")
            return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback embedding using text features"""
        # Simple feature-based embedding
        features = [
            len(text),
            text.count(' '),
            text.count('?'),
            text.count('!'),
            len(text.split()),
        ]
        # Pad to 1536 dimensions
        embedding = features + [0.0] * (1536 - len(features))
        return embedding[:1536]

    async def _update_session_context_embedding(self, session_id: str):
        """Update session-level context embedding"""
        # Get recent turns for session
        recent_turns = await self.repository.get_recent_turns(session_id, limit=5)

        # Combine recent context
        context_text = " ".join([
            f"User: {turn['user_message']} Assistant: {turn['response']}"
            for turn in recent_turns
        ])

        # Generate context embedding
        context_embedding = await self._generate_embedding(context_text)

        # Update session
        await self.repository.update_session_context_embedding(
            session_id=session_id,
            context_embedding=context_embedding
        )

    def _deduplicate_turns(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate turns from combined list"""
        seen_ids = set()
        unique_turns = []
        for turn in turns:
            if turn['id'] not in seen_ids:
                unique_turns.append(turn)
                seen_ids.add(turn['id'])
        return unique_turns

    async def _build_context_summary(self, turns: List[Dict[str, Any]]) -> str:
        """Build text summary of conversation context"""
        if not turns:
            return "No previous context"

        summary_parts = []
        for turn in turns[-3:]:  # Last 3 turns
            summary_parts.append(f"User: {turn['user_message'][:100]}...")
            summary_parts.append(f"Assistant: {turn['response'][:100]}...")

        return "\n".join(summary_parts)
```

**Key Features:**

- ✅ **Semantic Search:** Find relevant previous turns using vector similarity
- ✅ **Context Embeddings:** Store embeddings for both user messages and responses
- ✅ **Hybrid Context:** Combine recent turns with semantically relevant ones
- ✅ **Fallback Embeddings:** Graceful degradation if embedding model fails
- ✅ **Performance:** Lightweight embedding model for production use
- ✅ **Analytics:** Track semantic search usage and performance

**Testable Outcomes:**

```python
# Test: Multi-turn conversation
# Turn 1
response1 = await agent.process_query(
    "create a task to study",
    session_id=session_id
)
# Expected: Clarification request

# Turn 2
response2 = await agent.process_query(
    "for my physics exam next week",
    session_id=session_id
)
# Expected: Task created with combined context
```

### PHASE 3: Workflow Enhancements (Week 5-6)

**Goal:** Enhance each workflow with rule-based logic and minimal LLM usage

#### 3.1 Task Management Workflow Enhancement

**Where:** `backend/app/agents/graphs/task_graph.py`

**Enhancement Strategy:**

```python
# backend/app/agents/graphs/task_graph.py
class TaskGraph(BaseWorkflow):
    """
    Enhanced task workflow with deterministic logic
    """

    def _create_task_node(self, state: WorkflowState):
        """
        Create task using rule-based logic

        LLM Usage: ❌ None (unless title is ambiguous)
        Rule-Based: ✅ All CRUD operations
        """
        slots = state["nlu_result"]["slots"]

        # Deterministic task creation
        task_data = {
            "title": slots["title"],
            "due_date": slots.get("due_date"),
            "priority": slots.get("priority", "medium"),
            "duration": slots.get("duration")
        }

        # Only use LLM if title needs enrichment
        if self._is_title_too_vague(task_data["title"]):
            task_data["title"] = await self._enrich_title_with_llm(
                task_data["title"],
                user_context=state["user_context"]
            )

        # Create task deterministically
        task = await self.task_service.create_task(state["user_id"], task_data)

        # Track in PostHog
        await self.analytics.track_task_created(
            task_id=task.id,
            llm_enriched=self._is_title_too_vague(slots["title"])
        )

        return {"output_data": {"task_id": task.id, "task": task}}
```

**Deliverables:**

- ✅ Deterministic task CRUD
- ✅ LLM only for ambiguous inputs
- ✅ Batch task operations
- ✅ Task filtering and querying
- ✅ PostHog tracking for task operations

#### 3.2 Scheduling Workflow Enhancement

**Where:** `backend/app/agents/graphs/scheduling_graph.py`

**Enhancement Strategy:**

```python
# backend/app/agents/graphs/scheduling_graph.py
class SchedulingWorkflow(BaseWorkflow):
    """
    Enhanced scheduling with OR-Tools scheduler

    LLM Usage: ❌ Minimal (only for time resolution)
    Rule-Based: ✅ Constraint solving, optimization
    """

    def _schedule_node(self, state: WorkflowState):
        """
        Schedule using deterministic OR-Tools solver
        """
        # 1. Gather context (deterministic)
        calendar_events = await self._get_calendar_events(state["user_id"])
        tasks = await self._get_pending_tasks(state["user_id"])
        constraints = await self._get_user_constraints(state["user_id"])

        # 2. Use scheduler (deterministic, no LLM)
        from app.scheduler.scheduling.scheduler import TaskScheduler

        scheduler = TaskScheduler()
        schedule_result = scheduler.schedule_tasks(
            tasks=tasks,
            existing_events=calendar_events,
            constraints=constraints,
            optimization_goal="deadline_priority"  # Rule-based
        )

        # 3. LLM only for explaining conflicts (optional)
        if schedule_result.has_conflicts:
            explanation = await self._explain_conflicts_with_llm(
                schedule_result.conflicts
            )

        # Track in PostHog
        await self.analytics.track_scheduling_run(
            tasks_scheduled=len(tasks),
            conflicts=schedule_result.conflicts_count,
            optimization_goal=schedule_result.optimization_goal
        )

        return {"output_data": {"schedule": schedule_result}}
```

**Deliverables:**

- ✅ OR-Tools integration for optimal scheduling
- ✅ Constraint-based time allocation
- ✅ Conflict detection and resolution
- ✅ LLM only for explanations, not decisions
- ✅ PostHog tracking for scheduling performance

#### 3.3 Email Workflow Enhancement

**Where:** `backend/app/agents/graphs/email_graph.py`

**Enhancement Strategy:**

```python
# backend/app/agents/graphs/email_graph.py
class EmailGraph(BaseWorkflow):
    """
    Email workflow with template-based drafting

    LLM Usage: ✅ For drafting (premium feature)
    Rule-Based: ✅ Filtering, searching, sending
    """

    def _draft_email_node(self, state: WorkflowState):
        """
        Draft email using templates or LLM
        """
        # Check if premium user
        is_premium = await self._check_premium_status(state["user_id"])

        if is_premium:
            # Use LLM for drafting (premium feature)
            draft = await self._draft_with_llm(
                recipient=state["slots"]["participant"],
                subject=state["slots"]["title"],
                context=state["user_context"]
            )
            method = "llm"
        else:
            # Use template for free users
            draft = self._draft_with_template(
                template_type=state["slots"].get("email_type", "general"),
                recipient=state["slots"]["participant"],
                subject=state["slots"]["title"]
            )
            method = "template"

        # Track in PostHog
        await self.analytics.track_email_draft(
            is_premium=is_premium,
            method=method,
            recipient_count=len(state["slots"].get("participant", []))
        )

        return {"output_data": {"draft": draft}}
```

**Deliverables:**

- ✅ Email templates for common scenarios
- ✅ LLM drafting for premium users only
- ✅ Rule-based email filtering and search
- ✅ Token tracking for email operations
- ✅ PostHog tracking for email operations

### PHASE 4: Premium Features & Token Gating (Week 7-8)

**Goal:** Implement token-based premium features

#### 4.1 Premium Feature Gating

**Where:** `backend/app/services/premium/`

**Files to Create:**

- `backend/app/services/premium/feature_gate.py`
- `backend/app/services/premium/tier_config.py`

**Implementation:**

```python
# backend/app/services/premium/feature_gate.py
class FeatureGate:
    """Gate premium features based on subscription"""

    FEATURE_COSTS = {
        "email_draft_llm": 500,  # tokens
        "schedule_optimization": 300,
        "bulk_task_operations": 200,
        "advanced_search": 400
    }

    async def check_feature_access(
        self,
        user_id: str,
        feature: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can access feature

        Returns: (can_access, denial_reason)
        """
        # Check subscription
        subscription = await self.get_subscription(user_id)

        if subscription["status"] == "premium":
            # Track premium feature usage in PostHog
            await self.analytics.track_premium_feature_used(
                user_id=user_id,
                feature=feature
            )
            return True, None

        # Free user - check token quota
        usage = await self.token_tracker.get_usage(user_id)
        cost = self.FEATURE_COSTS.get(feature, 0)

        if usage["remaining"] >= cost:
            return True, None

        # Track upgrade prompt in PostHog
        await self.analytics.track_upgrade_prompt_shown(
            user_id=user_id,
            feature=feature,
            tokens_needed=cost,
            tokens_remaining=usage["remaining"]
        )

        return False, f"Insufficient tokens. Need {cost}, have {usage['remaining']}"
```

**Deliverables:**

- ✅ Feature cost definitions
- ✅ Subscription-based gating
- ✅ Token-based gating for free users
- ✅ Upgrade prompts
- ✅ PostHog conversion funnel tracking

**Testable Outcomes:**

```python
# Test: Free user hits token limit
for i in range(20):  # Exhaust free quota
    await agent.process_query(f"draft email to professor #{i}")

# Next request should be denied
response = await agent.process_query("draft another email")
assert response["error"] == "Token limit reached. Upgrade to premium."
```

#### 4.2 Usage Analytics Dashboard

**Where:** `backend/app/api/v1/endpoints/analytics.py`

**Endpoints to Create:**

```python
@router.get("/usage/summary")
async def get_usage_summary(user_id: str):
    """
    Get user's usage summary

    Returns:
      - tokens_used_today
      - tokens_used_this_month
      - quota_remaining
      - subscription_tier
      - top_operations
    """

@router.get("/usage/history")
async def get_usage_history(
    user_id: str,
    start_date: datetime,
    end_date: datetime
):
    """
    Get detailed usage history

    Returns list of operations with token counts
    """
```

**Deliverables:**

- ✅ Usage summary endpoint
- ✅ Usage history endpoint
- ✅ Operation breakdown
- ✅ Monthly reset tracking
- ✅ PostHog dashboard integration

### PHASE 5: Testing & Optimization (Week 9-10)

**Goal:** Comprehensive testing and performance optimization

#### 5.1 Integration Tests

**Where:** `backend/tests/integration/`

**Test Suites to Create:**

```python
# tests/integration/test_agent_workflows.py
class TestAgentWorkflows:

    async def test_task_creation_flow(self):
        """Test: NLU → Planning → Action → Task Created"""

    async def test_scheduling_flow(self):
        """Test: NLU → Scheduler → Calendar Update"""

    async def test_multi_turn_conversation(self):
        """Test: Follow-up queries use context"""

    async def test_token_limit_enforcement(self):
        """Test: Free user blocked after limit"""

    async def test_premium_feature_access(self):
        """Test: Premium user bypasses token limits"""

    async def test_analytics_tracking(self):
        """Test: PostHog events sent correctly"""
```

**Deliverables:**

- ✅ 50+ integration tests
- ✅ End-to-end workflow coverage
- ✅ Error case handling tests
- ✅ Performance benchmarks
- ✅ Analytics verification tests

#### 5.2 Performance Optimization

**Targets:**

- ✅ Intent classification: < 50ms
- ✅ Entity extraction: < 100ms
- ✅ End-to-end query: < 2s (without LLM)
- ✅ End-to-end query: < 5s (with LLM)

**Optimizations:**

- Cache ONNX model in memory
- Redis caching for user context
- Batch entity extraction
- Async workflow execution
- PostHog event batching

## 🎯 Recommended Starting Point

### Start with Phase 1.1: Token Tracking System + PostHog Integration

**Why Start Here?**

1. **Foundation for everything:** Token limits affect all workflows
2. **Clear deliverables:** Database tables + tracking service + analytics
3. **Immediate value:** Can gate features right away
4. **Low risk:** Doesn't affect existing functionality
5. **Analytics baseline:** Establishes tracking from day one

### Detailed First Steps

**Step 1: Set up PostHog (Day 1)**

- Install PostHog SDK: `pip install posthog`
- Configure PostHog client
- Create analytics service wrapper
- Set up environment variables

**Step 2: Create Database Schema (Day 1)**

- File: `backend/app/database/schemas/add_usage_tracking.sql`

**Step 3: Implement TokenTracker Service (Day 2-3)**

- File: `backend/app/services/usage/token_tracker.py`
- Integrate PostHog event tracking

**Step 4: Add Tracking Middleware (Day 4)**

- File: `backend/app/core/middleware/token_middleware.py`
- Add PostHog context enrichment

**Step 5: Test Token Tracking (Day 5)**

- File: `backend/tests/services/test_token_tracker.py`
- Verify PostHog events

**Step 6: Add Usage Endpoints (Day 6-7)**

- File: `backend/app/api/v1/endpoints/infrastructure_modules/usage.py`
- Create PostHog dashboard

## 📊 Success Metrics

### Phase 1 Success Criteria:

- ☐ Free users limited to 10,000 tokens/month
- ☐ Premium users have unlimited tokens
- ☐ Token usage tracked per operation
- ☐ Usage API returns accurate counts
- ☐ PostHog events firing for all operations

### Overall Success Criteria:

- ☐ 90%+ queries handled by rule-based logic
- ☐ < 10% queries require LLM fallback
- ☐ Average query latency < 2 seconds
- ☐ Free users can complete 100+ queries/month
- ☐ Premium users have seamless experience
- ☐ Intent classification accuracy > 85%
- ☐ Zero duplicate logic across workflows
- ☐ Comprehensive analytics dashboards in PostHog

## 🚨 Critical Notes

1. **Don't over-LLM:** Your architecture is designed for LLM-last, stick to it
2. **Token tracking first:** Without this, you can't gate features properly
3. **Train the classifier:** Mock classifier won't scale - need real model
4. **Test incrementally:** Each phase has testable outcomes - use them
5. **Follow RULES.md:** Your architecture is well-defined - don't deviate
6. **Analytics from day one:** PostHog tracking ensures data-driven decisions
7. **Privacy first:** Anonymize PII in PostHog events

## 📈 PostHog Integration Details

### Key Events to Track

**Agent Operations:**

- `agent_query_received` - User query entered
- `intent_classified` - NLU classification result
- `workflow_started` - Workflow execution begins
- `workflow_completed` - Workflow execution ends
- `action_executed` - Action handler called
- `llm_call_made` - LLM API call (track tokens)

**User Journey:**

- `conversation_started` - New conversation session
- `conversation_turn` - Each turn in conversation
- `clarification_requested` - Agent asks for clarification
- `task_created` - Task successfully created
- `schedule_generated` - Schedule successfully generated

**Premium & Monetization:**

- `upgrade_prompt_shown` - Free user hits limit
- `feature_gated` - Premium feature blocked
- `premium_feature_used` - Premium user accesses feature
- `subscription_status_changed` - User upgrades/downgrades

**Performance:**

- `query_latency` - End-to-end query time
- `intent_classification_latency` - NLU speed
- `workflow_execution_latency` - Workflow speed

### PostHog Feature Flags

Use for gradual rollouts:

- `enable_new_intent_classifier` - A/B test new model
- `enable_advanced_scheduling` - Premium feature flag
- `enable_multi_turn_memory` - Conversation persistence
- `enable_llm_enrichment` - LLM title enrichment

## Next Actions After Approval

1. ✅ Install PostHog: `pip install posthog`
2. ✅ Create `backend/app/services/analytics/posthog_service.py`
3. ✅ Create `backend/app/database/schemas/add_usage_tracking.sql`
4. ✅ Create `backend/app/services/usage/token_tracker.py`
5. ✅ Update `backend/app/database/models.py` with UsageQuota model
6. ✅ Create migration script
7. ✅ Add unit tests
8. ✅ Set up PostHog dashboards

---

## 🔧 Refinement Implementation Summary

The following refinements have been implemented to enhance the agent system:

### ✅ 1. Global Token Cost Configuration

- **File:** `backend/app/services/usage/usage_config.py`
- **Features:** Centralized token costs, model pricing, operation costs
- **Benefits:** Easy tweaking without redeployment, consistent pricing across features

### ✅ 2. API-Gateway Token Tracking

- **File:** `backend/app/core/middleware/token_middleware.py`
- **Features:** Comprehensive LLM call tracking, pre-execution quota checks, error tracking
- **Benefits:** Tracks ALL LLM calls, not just agent queries, prevents unnecessary API calls

### ✅ 3. Error-Path Analytics

- **File:** `backend/app/services/analytics/error_tracker.py`
- **Features:** Comprehensive error tracking, workflow-specific errors, external API errors
- **Benefits:** Invaluable for debugging live user sessions, structured error context

### ✅ 4. PostHog Event Batching

- **File:** `backend/app/services/analytics/event_batcher.py`
- **Features:** Async event queuing, batch processing, non-blocking I/O
- **Benefits:** Avoids blocking I/O under load, improves performance, graceful degradation

### ✅ 5. Data Retention Policy

- **Enhancement:** Monthly aggregation system, 3-month raw data retention
- **Features:** Automated aggregation, usage_summary table, performance optimization
- **Benefits:** Scalable data management, cost-effective storage, historical analytics

### ✅ 6. Multi-Turn Memory with Embeddings

- **File:** `backend/app/services/memory/conversation_memory.py`
- **Features:** Semantic search, context embeddings, hybrid context retrieval
- **Benefits:** Advanced conversation memory, semantic recall, improved context understanding

---

**Document Version:** 2.1 (with PostHog integration + Refinements)
**Last Updated:** 2025-10-23
**Next Review:** After Phase 1 completion
