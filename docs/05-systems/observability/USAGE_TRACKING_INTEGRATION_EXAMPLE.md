# Usage Tracking Integration Example

This guide shows how to integrate the Phase 1 token tracking system into your LangGraph workflows and agent operations.

---

## 🎯 Integration Pattern

**Two-step process for every LLM operation:**

1. **Pre-flight**: Check quota before LLM call
2. **Post-flight**: Track actual tokens used after LLM call

---

## Example 1: Simple Agent Operation

```python
from uuid import UUID
from typing import Dict, Any
from app.services.usage import (
    get_usage_limiter,
    get_token_tracker,
    OperationType,
    QuotaExceededException
)

async def handle_conversation(
    user_id: UUID,
    user_message: str,
    session_id: UUID
) -> Dict[str, Any]:
    """
    Handle a conversation turn with token tracking.
    """
    limiter = get_usage_limiter()
    tracker = get_token_tracker()

    # STEP 1: Pre-flight quota check
    result = await limiter.check_operation_allowed(
        user_id=user_id,
        operation_type=OperationType.CONVERSATION
    )

    if not result.allowed:
        # User has exceeded quota
        return {
            "success": False,
            "error": "quota_exceeded",
            "message": result.reason,
            "requires_upgrade": result.requires_upgrade,
            "tokens_remaining": result.tokens_remaining,
            "upgrade_prompt": result.requires_upgrade
        }

    # STEP 2: Make LLM call
    import time
    start_time = time.time()

    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = await llm.ainvoke(user_message)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # STEP 3: Track the call
        await tracker.track_llm_call(
            user_id=user_id,
            operation_type=OperationType.CONVERSATION,
            model="gpt-4o-mini",
            input_tokens=response.response_metadata["token_usage"]["prompt_tokens"],
            output_tokens=response.response_metadata["token_usage"]["completion_tokens"],
            session_id=session_id,
            intent="conversation",
            metadata={
                "message_length": len(user_message),
                "response_length": len(response.content)
            },
            duration_ms=duration_ms
        )

        return {
            "success": True,
            "response": response.content,
            "tokens_used": (
                response.response_metadata["token_usage"]["total_tokens"]
            )
        }

    except Exception as e:
        # Track failed call
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"LLM call failed: {e}")

        return {
            "success": False,
            "error": "llm_error",
            "message": str(e)
        }
```

---

## Example 2: Premium Feature with Quota Enforcement

```python
from app.services.usage import (
    get_usage_limiter,
    get_token_tracker,
    OperationType,
    QuotaExceededException
)

async def draft_email_with_llm(
    user_id: UUID,
    email_context: Dict[str, Any],
    session_id: UUID
) -> Dict[str, Any]:
    """
    Premium feature: Draft email using LLM.
    Requires premium subscription AND sufficient quota.
    """
    limiter = get_usage_limiter()
    tracker = get_token_tracker()

    # STEP 1: Check if user can use premium feature
    try:
        await limiter.enforce_operation_quota(
            user_id=user_id,
            operation_type=OperationType.EMAIL_DRAFT  # Premium-only operation
        )
    except QuotaExceededException as e:
        # Automatically sends PostHog event for quota exceeded
        return {
            "success": False,
            "error": "quota_exceeded" if not e.result.requires_upgrade else "premium_required",
            "message": e.result.reason,
            "requires_upgrade": e.result.requires_upgrade,
            "tokens_remaining": e.result.tokens_remaining
        }

    # STEP 2: Make LLM call (premium feature)
    start_time = time.time()

    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)  # Use premium model

    prompt = f"""Draft a professional email with the following context:
    To: {email_context['recipient']}
    Subject: {email_context['subject']}
    Context: {email_context['context']}
    """

    response = await llm.ainvoke(prompt)
    duration_ms = (time.time() - start_time) * 1000

    # STEP 3: Track premium feature usage
    await tracker.track_llm_call(
        user_id=user_id,
        operation_type=OperationType.EMAIL_DRAFT,
        model="gpt-4o",
        input_tokens=response.response_metadata["token_usage"]["prompt_tokens"],
        output_tokens=response.response_metadata["token_usage"]["completion_tokens"],
        session_id=session_id,
        intent="email_draft",
        metadata={
            "recipient": email_context["recipient"],
            "subject": email_context["subject"],
            "premium_feature": True
        },
        duration_ms=duration_ms
    )

    # PostHog automatically tracks "premium_feature_used" event

    return {
        "success": True,
        "email_draft": response.content,
        "tokens_used": response.response_metadata["token_usage"]["total_tokens"]
    }
```

---

## Example 3: Integration with LangGraph Workflow

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
from app.services.usage import get_usage_limiter, get_token_tracker, OperationType

class TaskWorkflowState(TypedDict):
    user_id: str
    session_id: str
    task_description: str
    enriched_task: dict
    error: str | None
    quota_check_passed: bool


async def check_quota_node(state: TaskWorkflowState) -> TaskWorkflowState:
    """
    First node: Check if user has quota for task enrichment.
    """
    limiter = get_usage_limiter()
    user_id = UUID(state["user_id"])

    result = await limiter.check_operation_allowed(
        user_id=user_id,
        operation_type=OperationType.TASK_ENRICHMENT
    )

    if not result.allowed:
        state["error"] = result.reason
        state["quota_check_passed"] = False
    else:
        state["quota_check_passed"] = True

    return state


async def enrich_task_node(state: TaskWorkflowState) -> TaskWorkflowState:
    """
    Second node: Use LLM to enrich task with deadlines, priorities, etc.
    """
    if not state["quota_check_passed"]:
        # Skip if quota check failed
        return state

    tracker = get_token_tracker()
    user_id = UUID(state["user_id"])
    session_id = UUID(state["session_id"])

    # Make LLM call
    start_time = time.time()
    llm = ChatOpenAI(model="gpt-4o-mini")

    prompt = f"Enrich this task: {state['task_description']}"
    response = await llm.ainvoke(prompt)

    duration_ms = (time.time() - start_time) * 1000

    # Track the call
    await tracker.track_llm_call(
        user_id=user_id,
        operation_type=OperationType.TASK_ENRICHMENT,
        model="gpt-4o-mini",
        input_tokens=response.response_metadata["token_usage"]["prompt_tokens"],
        output_tokens=response.response_metadata["token_usage"]["completion_tokens"],
        session_id=session_id,
        intent="enrich_task",
        metadata={"workflow": "task_graph"},
        duration_ms=duration_ms
    )

    state["enriched_task"] = {
        "original": state["task_description"],
        "enriched": response.content
    }

    return state


# Build LangGraph workflow
workflow = StateGraph(TaskWorkflowState)

# Add nodes
workflow.add_node("check_quota", check_quota_node)
workflow.add_node("enrich_task", enrich_task_node)

# Define edges
workflow.set_entry_point("check_quota")
workflow.add_edge("check_quota", "enrich_task")
workflow.add_edge("enrich_task", END)

# Compile
task_enrichment_workflow = workflow.compile()
```

---

## Example 4: Showing Quota Status to User

```python
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.services.usage import get_usage_limiter

router = APIRouter()

@router.get("/my-quota")
async def get_my_quota(current_user = Depends(get_current_user)):
    """
    Show user their current quota status (for dashboard UI).
    """
    limiter = get_usage_limiter()

    summary = await limiter.get_quota_summary(current_user.id)

    return {
        "subscription_tier": summary["subscription_tier"],
        "monthly_usage": {
            "used": summary["monthly"]["used"],
            "limit": summary["monthly"]["limit"],
            "remaining": summary["monthly"]["remaining"],
            "percentage": summary["monthly"]["percentage"],
            "status": summary["monthly"]["status"]  # ok/warning/critical/exceeded
        },
        "warnings": summary["warnings"],
        "top_operations": summary["operation_breakdown"],
        "last_reset": summary["last_reset_at"]
    }
```

**Example response:**

```json
{
  "subscription_tier": "free",
  "monthly_usage": {
    "used": 7500,
    "limit": 10000,
    "remaining": 2500,
    "percentage": 75.0,
    "status": "warning"
  },
  "warnings": [
    "You have used 75% of your monthly quota (2500 tokens remaining)."
  ],
  "top_operations": {
    "conversation": 4000,
    "task_enrichment": 2000,
    "briefing_generation": 1500
  },
  "last_reset_at": "2025-10-01T00:00:00Z"
}
```

---

## Example 5: Handling Subscription Upgrades

```python
from app.services.usage import get_usage_limiter, SubscriptionTier

async def handle_subscription_purchase(
    user_id: UUID,
    plan_type: str
) -> Dict[str, Any]:
    """
    Handle user upgrading to premium.
    """
    limiter = get_usage_limiter()

    # Determine new tier
    new_tier = (
        SubscriptionTier.PREMIUM
        if plan_type == "premium"
        else SubscriptionTier.FREE
    )

    # Update subscription (automatically sends PostHog event)
    updated_quota = await limiter.update_user_subscription(
        user_id=user_id,
        new_tier=new_tier
    )

    return {
        "success": True,
        "new_tier": new_tier.value,
        "new_monthly_limit": updated_quota["monthly_token_limit"],
        "message": f"Upgraded to {new_tier.value}! You now have {updated_quota['monthly_token_limit']:,} tokens per month."
    }
```

---

## Example 6: Cost Estimation Before Operation

```python
from app.services.usage import get_token_tracker, OperationType

async def estimate_email_draft_cost() -> Dict[str, Any]:
    """
    Show user estimated cost before they use a feature.
    """
    tracker = get_token_tracker()

    estimate = await tracker.estimate_operation_cost(
        operation_type=OperationType.EMAIL_DRAFT,
        model="gpt-4o"  # Optional - uses default if not specified
    )

    return {
        "feature": "Email Draft",
        "estimated_tokens": estimate["estimated_total_tokens"],
        "estimated_cost_usd": estimate["estimated_cost_usd"],
        "model": estimate["model"],
        "breakdown": {
            "input_tokens": estimate["estimated_input_tokens"],
            "output_tokens": estimate["estimated_output_tokens"]
        }
    }
```

**Example response:**

```json
{
  "feature": "Email Draft",
  "estimated_tokens": 800,
  "estimated_cost_usd": 0.0092,
  "model": "gpt-4o",
  "breakdown": {
    "input_tokens": 560,
    "output_tokens": 240
  }
}
```

---

## Example 7: Monitoring Usage Trends (Admin)

```python
from app.database.usage_repository import get_usage_repository
from datetime import datetime, timedelta

async def get_platform_analytics() -> Dict[str, Any]:
    """
    Admin endpoint: Get platform-wide usage statistics.
    """
    repo = get_usage_repository()

    # Last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    stats = await repo.get_platform_usage_stats(start_date, end_date)
    top_users = await repo.get_top_users_by_usage(limit=10, days=30)

    return {
        "period": "last_30_days",
        "platform_stats": {
            "active_users": stats["active_users"],
            "total_tokens": stats["total_tokens"],
            "total_cost_usd": stats["total_cost"],
            "total_calls": stats["total_calls"],
            "avg_tokens_per_call": stats["avg_tokens_per_call"]
        },
        "top_users": [
            {
                "user_id": str(user["user_id"]),
                "total_tokens": user["total_tokens"],
                "total_cost": user["total_cost"],
                "call_count": user["call_count"]
            }
            for user in top_users
        ]
    }
```

---

## 🎯 Integration Checklist

When adding token tracking to a new operation:

- [ ] Determine `OperationType` (conversation, email_draft, etc.)
- [ ] Add pre-flight quota check with `check_operation_allowed()`
- [ ] Make LLM call and capture usage metadata
- [ ] Track call with `track_llm_call()`
- [ ] Handle `QuotaExceededException` gracefully
- [ ] Show upgrade prompts for premium features
- [ ] Test both free and premium tier scenarios

---

## 📊 PostHog Analytics Events

The following events are **automatically sent** when using the tracking system:

| Event | Triggered When | Properties |
|-------|---------------|------------|
| `llm_call_made` | LLM call tracked | operation, model, tokens_used, duration_ms, success |
| `quota_exceeded` | User exceeds quota | operation, reason |
| `quota_critical` | User hits 90% quota | tokens_used, monthly_limit, percentage |
| `upgrade_prompt_shown` | Free user shown upgrade | feature, tokens_needed, tokens_remaining |
| `feature_gated` | Premium feature blocked | feature, reason |
| `premium_feature_used` | Premium feature used | feature |
| `subscription_status_changed` | Subscription upgraded/downgraded | old_status, new_status, plan_type |

---

## 🚀 Quick Start

```python
# 1. Import services
from app.services.usage import (
    get_usage_limiter,
    get_token_tracker,
    OperationType,
    QuotaExceededException
)

# 2. Check quota before LLM call
limiter = get_usage_limiter()
result = await limiter.check_operation_allowed(user_id, OperationType.CONVERSATION)

if not result.allowed:
    # Handle quota exceeded
    pass

# 3. Make LLM call
# ... your LLM logic ...

# 4. Track the call
tracker = get_token_tracker()
await tracker.track_llm_call(
    user_id=user_id,
    operation_type=OperationType.CONVERSATION,
    model="gpt-4o-mini",
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    session_id=session_id
)
```

That's it! Token tracking is now integrated.

---

## 📝 Notes

- **All analytics events are non-blocking** - Won't slow down your operations
- **Quota checks are fast** - Simple database query (~5ms)
- **Token tracking is async** - Won't block LLM response
- **PostHog batching** - Events are batched for efficiency
- **Automatic cost calculation** - No need to manually calculate USD cost

---

## 🎉 Benefits

✅ **Monetization ready** - Track and enforce usage limits
✅ **Observable** - See which features consume most tokens
✅ **User-friendly** - Show quota status and warnings
✅ **Flexible** - Easy to adjust limits and costs
✅ **Scalable** - Efficient data retention strategy
