# PostHog Analytics Integration

Comprehensive analytics tracking for PulsePlan agent operations, user journeys, and system performance.

## Setup

### 1. Install Dependencies

```bash
pip install posthog==3.7.4
```

### 2. Environment Configuration

Add to your `.env` file:

```bash
# PostHog Configuration
POSTHOG_API_KEY=your_posthog_api_key_here
POSTHOG_HOST=https://us.i.posthog.com
POSTHOG_ENABLED=true  # Set to false to disable analytics
```

### 3. Get Your PostHog API Key

1. Sign up at [posthog.com](https://posthog.com)
2. Create a new project
3. Copy your API key from Project Settings
4. Add it to your `.env` file

## Usage

### Basic Event Tracking

```python
from app.services.analytics.posthog_service import get_posthog_service

analytics = get_posthog_service()

# Track a custom event
analytics.track_event(
    user_id="user_123",
    event_name="custom_event",
    properties={
        "property1": "value1",
        "property2": 123
    }
)
```

### Agent Operations Tracking

```python
# Track intent classification
analytics.track_intent_classified(
    user_id="user_123",
    intent="task_management",
    confidence=0.92,
    method="onnx_classifier",
    session_id="session_abc"
)

# Track workflow execution
analytics.track_workflow_started(
    user_id="user_123",
    workflow_type="tasks",
    intent="task_management",
    session_id="session_abc"
)

analytics.track_workflow_completed(
    user_id="user_123",
    workflow_type="tasks",
    success=True,
    duration_ms=1234.5,
    session_id="session_abc"
)

# Track LLM usage
analytics.track_llm_call_made(
    user_id="user_123",
    operation="conversation",
    model="gpt-4o-mini",
    tokens_used=247,
    duration_ms=823.4,
    success=True,
    session_id="session_abc"
)
```

### User Journey Tracking

```python
# Track conversation flow
analytics.track_conversation_started(
    user_id="user_123",
    session_id="session_abc"
)

analytics.track_conversation_turn(
    user_id="user_123",
    session_id="session_abc",
    turn_index=1,
    intent="task_management"
)

# Track task creation
analytics.track_task_created(
    user_id="user_123",
    task_id="task_xyz",
    via_agent=True,
    llm_enriched=False,
    session_id="session_abc"
)

# Track scheduling
analytics.track_schedule_generated(
    user_id="user_123",
    tasks_scheduled=5,
    conflicts_count=1,
    optimization_goal="deadline_priority",
    duration_ms=456.7,
    session_id="session_abc"
)
```

### Premium Feature Tracking

```python
# Track upgrade prompts
analytics.track_upgrade_prompt_shown(
    user_id="user_123",
    feature="email_draft_llm",
    tokens_needed=500,
    tokens_remaining=100
)

# Track feature gating
analytics.track_feature_gated(
    user_id="user_123",
    feature="advanced_scheduling",
    reason="insufficient_tokens"
)

# Track premium feature usage
analytics.track_premium_feature_used(
    user_id="user_123",
    feature="bulk_task_operations",
    session_id="session_abc"
)

# Track subscription changes
analytics.track_subscription_status_changed(
    user_id="user_123",
    old_status="free",
    new_status="premium",
    plan_type="premium"
)
```

### Performance Monitoring

```python
# Track query latency
analytics.track_query_latency(
    user_id="user_123",
    total_duration_ms=1500.5,
    intent="task_management",
    used_llm=True,
    session_id="session_abc"
)

# Track NLU performance
analytics.track_intent_classification_latency(
    user_id="user_123",
    duration_ms=45.2,
    method="onnx_classifier"
)

# Track workflow performance
analytics.track_workflow_execution_latency(
    user_id="user_123",
    workflow_type="scheduling",
    duration_ms=2345.6,
    session_id="session_abc"
)
```

### Feature Flags

```python
# Check if a feature is enabled
is_enabled = analytics.is_feature_enabled(
    user_id="user_123",
    feature_flag="enable_new_intent_classifier",
    default=False
)

if is_enabled:
    # Use new classifier
    pass
else:
    # Use old classifier
    pass

# Get feature flag payload
payload = analytics.get_feature_flag_payload(
    user_id="user_123",
    feature_flag="scheduling_config"
)
# payload might contain: {"max_tasks": 10, "optimization_level": "high"}
```

### User Identification

```python
# Identify user with properties
analytics.identify_user(
    user_id="user_123",
    properties={
        "subscription_tier": "premium",
        "signup_date": "2025-01-15",
        "timezone": "America/New_York"
        # Note: PII like email is automatically filtered out
    }
)

# Create alias for user (e.g., after authentication)
analytics.alias_user(
    previous_id="anonymous_456",
    new_id="user_123"
)
```

## Privacy & PII Protection

The PostHog service automatically sanitizes PII (Personally Identifiable Information) before sending events:

**Automatically filtered fields:**
- `email`
- `name`
- `phone`
- `address`
- `ip_address`

**Example:**

```python
# These PII fields will be automatically removed
analytics.track_event(
    user_id="user_123",
    event_name="profile_updated",
    properties={
        "email": "user@example.com",  # ❌ FILTERED OUT
        "name": "John Doe",            # ❌ FILTERED OUT
        "timezone": "America/Denver",  # ✅ KEPT
        "subscription": "premium"       # ✅ KEPT
    }
)
```

## Integration Points

### 1. Agent Orchestrator

Already integrated in `backend/app/agents/orchestrator.py`:

- Tracks workflow start/completion
- Tracks success/failure with error types
- Tracks execution duration

### 2. Workflow Graphs

Add tracking to individual workflow implementations:

```python
# Example: backend/app/agents/graphs/task_graph.py
from app.services.analytics.posthog_service import get_posthog_service

class TaskGraph(BaseWorkflow):
    def __init__(self):
        super().__init__()
        self.analytics = get_posthog_service()

    async def _create_task_node(self, state: WorkflowState):
        # Your task creation logic
        task = await self.task_service.create_task(...)

        # Track task creation
        self.analytics.track_task_created(
            user_id=state["user_id"],
            task_id=task.id,
            via_agent=True,
            llm_enriched=False
        )

        return {"output_data": {"task": task}}
```

### 3. NLU Pipeline

Add to `backend/app/agents/nlu/` components:

```python
from app.services.analytics.posthog_service import get_posthog_service

analytics = get_posthog_service()

# Track intent classification
intent, confidence = classifier.predict(text)
analytics.track_intent_classified(
    user_id=user_id,
    intent=intent,
    confidence=confidence,
    method="onnx_classifier"
)
```

### 4. API Endpoints

Add to API endpoints for user actions:

```python
from app.services.analytics.posthog_service import get_posthog_service

@router.post("/tasks")
async def create_task(...):
    analytics = get_posthog_service()

    # Your task creation logic
    task = await create_task_service(...)

    # Track task creation
    analytics.track_task_created(
        user_id=current_user.id,
        task_id=task.id,
        via_agent=False  # Created via API, not agent
    )

    return task
```

## PostHog Dashboard Setup

### Recommended Dashboards

1. **Agent Performance Dashboard**
   - Workflow success rate by type
   - Average workflow duration
   - LLM usage and token consumption
   - Intent classification accuracy

2. **User Journey Funnel**
   - Conversation started → Intent classified → Workflow completed → Task created
   - Multi-turn conversation success rate
   - Clarification request rate

3. **Premium Conversion Dashboard**
   - Upgrade prompts shown
   - Feature gating events
   - Subscription conversions
   - Premium feature usage

4. **Performance Monitoring**
   - P50/P95/P99 query latency
   - Intent classification latency
   - Workflow execution latency by type
   - LLM call latency

### Creating Insights

1. **Workflow Success Rate:**
   ```
   Event: workflow_completed
   Filter: success = true
   Group by: workflow_type
   ```

2. **Average Tokens Per User:**
   ```
   Event: llm_call_made
   Aggregation: Sum(tokens_used)
   Group by: user_id
   ```

3. **Conversion Funnel:**
   ```
   1. upgrade_prompt_shown
   2. subscription_status_changed (new_status = premium)
   ```

## Feature Flags for Gradual Rollouts

Use PostHog feature flags to safely roll out new features:

### Example: Rolling out new intent classifier

1. Create feature flag in PostHog dashboard: `enable_new_intent_classifier`
2. Set rollout percentage (e.g., 10% of users)
3. Use in code:

```python
analytics = get_posthog_service()

if analytics.is_feature_enabled(user_id, "enable_new_intent_classifier"):
    # Use new classifier
    intent = new_classifier.predict(text)
else:
    # Use old classifier
    intent = old_classifier.predict(text)
```

4. Monitor performance in PostHog
5. Gradually increase rollout percentage
6. Eventually make it default for all users

## Testing

Disable PostHog in tests by setting `POSTHOG_ENABLED=false` in your test environment.

```python
# In test configuration
POSTHOG_ENABLED = False
```

## Troubleshooting

### Events not appearing in PostHog

1. Check `POSTHOG_ENABLED=true` in `.env`
2. Verify `POSTHOG_API_KEY` is correct
3. Check logs for PostHog errors
4. Ensure network connectivity to PostHog host

### PII being sent accidentally

The service automatically filters common PII fields. If you need to add more:

1. Edit `_sanitize_properties()` in `posthog_service.py`
2. Add field names to `pii_fields` set

## Best Practices

1. **Always include session_id** for multi-turn conversations
2. **Track both success and failure** cases
3. **Include duration_ms** for performance monitoring
4. **Use consistent event naming** (snake_case)
5. **Don't track sensitive data** (passwords, tokens, etc.)
6. **Batch events** when possible for performance
7. **Test with PostHog disabled** in development

## Resources

- [PostHog Documentation](https://posthog.com/docs)
- [PostHog Python SDK](https://posthog.com/docs/libraries/python)
- [Feature Flags Guide](https://posthog.com/docs/feature-flags)
- [Funnels & Insights](https://posthog.com/docs/user-guides/funnels)
