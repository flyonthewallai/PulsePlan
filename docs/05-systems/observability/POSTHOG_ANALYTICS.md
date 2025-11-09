# PostHog Analytics Implementation Guide

## Overview

PulsePlan uses PostHog for comprehensive analytics tracking across the entire application. This includes:

1. **Agent Operations Analytics** - Track AI agent performance, workflows, and LLM usage
2. **User Behavior Analytics** - Track clicks, page views, and user journeys across the app
3. **Premium & Monetization Analytics** - Track conversion funnels and subscription events
4. **Performance Monitoring** - Track latency, errors, and system health

## Architecture

### Backend Integration

**Location:** `backend/app/services/analytics/posthog_service.py`

The `PostHogService` class provides a centralized wrapper around the PostHog SDK with:
- Automatic PII sanitization
- Event batching for performance
- Feature flag support
- Error handling and fallbacks

**Key Components:**

```
backend/app/services/analytics/
├── __init__.py
├── posthog_service.py      # Core analytics service
└── README.md               # Detailed usage guide
```

### Frontend Integration (Future)

**Location:** `web/src/services/analytics/`

The frontend will integrate PostHog for client-side tracking:
- Page views and navigation
- Button clicks and user interactions
- Form submissions and conversions
- Client-side performance metrics

## Configuration

### Environment Variables

Add to `.env`:

```bash
# PostHog Configuration
POSTHOG_API_KEY=phc_your_api_key_here
POSTHOG_HOST=https://us.i.posthog.com  # or your self-hosted instance
POSTHOG_ENABLED=true                    # Set to false to disable
```

### Settings Integration

**File:** `backend/app/config/core/settings.py`

```python
class Settings(BaseSettings):
    # PostHog Analytics Configuration
    POSTHOG_API_KEY: str = Field(default="", description="PostHog API key")
    POSTHOG_HOST: str = Field(default="https://us.i.posthog.com")
    POSTHOG_ENABLED: bool = Field(default=True)
```

## Event Tracking Strategy

### 1. Agent Operations Events

Track AI agent performance and usage patterns:

| Event Name | Purpose | Key Properties |
|------------|---------|----------------|
| `agent_query_received` | User submits query to agent | `query_length`, `session_id` |
| `intent_classified` | NLU classifies user intent | `intent`, `confidence`, `method` |
| `workflow_started` | LangGraph workflow begins | `workflow_type`, `intent` |
| `workflow_completed` | Workflow finishes execution | `success`, `duration_ms`, `error_type` |
| `action_executed` | Agent executes an action | `action_type`, `success`, `duration_ms` |
| `llm_call_made` | OpenAI API call made | `model`, `tokens_used`, `operation` |

**Example:**

```python
from app.services.analytics.posthog_service import get_posthog_service

analytics = get_posthog_service()

analytics.track_workflow_started(
    user_id="user_123",
    workflow_type="tasks",
    intent="task_management",
    session_id="session_abc"
)
```

### 2. User Journey Events

Track user interactions and conversions:

| Event Name | Purpose | Key Properties |
|------------|---------|----------------|
| `conversation_started` | New conversation session | `session_id` |
| `conversation_turn` | Each turn in multi-turn dialog | `turn_index`, `intent` |
| `clarification_requested` | Agent asks for more info | `missing_slots`, `intent` |
| `task_created` | Task successfully created | `task_id`, `via_agent`, `llm_enriched` |
| `schedule_generated` | Schedule successfully created | `tasks_scheduled`, `conflicts_count` |
| `email_draft` | Email drafted | `is_premium`, `method`, `recipient_count` |

### 3. Premium & Monetization Events

Track upgrade prompts and conversions:

| Event Name | Purpose | Key Properties |
|------------|---------|----------------|
| `upgrade_prompt_shown` | Free user hits limit | `feature`, `tokens_needed`, `tokens_remaining` |
| `feature_gated` | Feature blocked for user | `feature`, `reason` |
| `premium_feature_used` | Premium feature accessed | `feature` |
| `subscription_status_changed` | User upgrades/downgrades | `old_status`, `new_status`, `plan_type` |

### 4. Performance Monitoring Events

Track system performance and latency:

| Event Name | Purpose | Key Properties |
|------------|---------|----------------|
| `query_latency` | End-to-end query time | `total_duration_ms`, `used_llm`, `intent` |
| `intent_classification_latency` | NLU processing speed | `duration_ms`, `method` |
| `workflow_execution_latency` | Workflow processing speed | `workflow_type`, `duration_ms` |

### 5. General App Usage Events (Future - Frontend)

Track user clicks, navigation, and interactions:

| Event Name | Purpose | Key Properties |
|------------|---------|----------------|
| `page_viewed` | User navigates to page | `page_name`, `path`, `referrer` |
| `button_clicked` | User clicks button | `button_name`, `page`, `section` |
| `form_submitted` | User submits form | `form_name`, `success` |
| `modal_opened` | User opens modal | `modal_name`, `trigger` |
| `modal_closed` | User closes modal | `modal_name`, `duration_open_ms` |
| `calendar_event_created` | User creates calendar event | `event_type`, `duration_minutes` |
| `filter_applied` | User applies filter | `filter_type`, `filter_value` |
| `search_performed` | User searches | `query_length`, `results_count` |
| `task_completed_ui` | User completes task in UI | `task_id`, `time_to_complete_ms` |
| `settings_changed` | User changes settings | `setting_name`, `new_value` |

## Privacy & PII Protection

### Automatic PII Filtering

The PostHog service automatically removes PII before sending events:

**Filtered Fields:**
- `email`
- `name`
- `phone`
- `address`
- `ip_address`

**Implementation:**

```python
class PostHogService:
    def _sanitize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII from event properties"""
        pii_fields = {"email", "name", "phone", "address", "ip_address"}

        sanitized = {}
        for key, value in properties.items():
            if key.lower() in pii_fields:
                continue  # Skip PII
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_properties(value)
            else:
                sanitized[key] = value

        return sanitized
```

### Best Practices

1. **Never track sensitive data:**
   - ❌ Passwords
   - ❌ API keys or tokens
   - ❌ Credit card information
   - ❌ Full email addresses
   - ❌ Personal health information

2. **Use anonymized identifiers:**
   - ✅ User IDs (UUID)
   - ✅ Session IDs
   - ✅ Task IDs
   - ✅ Workflow IDs

3. **Track aggregate data:**
   - ✅ Query length (not query content for sensitive queries)
   - ✅ Token counts
   - ✅ Duration metrics
   - ✅ Success/failure rates

## Feature Flags

PostHog feature flags enable gradual rollouts and A/B testing.

### Common Use Cases

1. **New Feature Rollouts**
   ```python
   if analytics.is_feature_enabled(user_id, "enable_new_intent_classifier"):
       # Use new classifier
       result = new_classifier.predict(text)
   else:
       # Use old classifier
       result = old_classifier.predict(text)
   ```

2. **A/B Testing**
   ```python
   variant = analytics.get_feature_flag_payload(user_id, "scheduling_algorithm")
   if variant == "experimental":
       # Use experimental algorithm
   else:
       # Use production algorithm
   ```

3. **Premium Feature Gating**
   ```python
   if analytics.is_feature_enabled(user_id, "enable_advanced_scheduling"):
       # Show advanced scheduling options
   else:
       # Show upgrade prompt
   ```

### Recommended Feature Flags

| Flag Name | Purpose | Default |
|-----------|---------|---------|
| `enable_new_intent_classifier` | Roll out new NLU model | `false` |
| `enable_advanced_scheduling` | Premium scheduling features | `premium_only` |
| `enable_multi_turn_memory` | Conversation persistence | `false` |
| `enable_llm_enrichment` | LLM title enrichment | `false` |
| `enable_bulk_operations` | Bulk task operations | `premium_only` |
| `enable_email_llm_drafting` | LLM email drafting | `premium_only` |

## Dashboard Setup

### Agent Performance Dashboard

**Insights to Create:**

1. **Workflow Success Rate**
   - Event: `workflow_completed`
   - Filter: `success = true`
   - Group by: `workflow_type`
   - Visualization: Bar chart

2. **Average Query Latency**
   - Event: `query_latency`
   - Aggregation: Average `total_duration_ms`
   - Group by: `used_llm`
   - Visualization: Line chart over time

3. **LLM Token Usage**
   - Event: `llm_call_made`
   - Aggregation: Sum `tokens_used`
   - Group by: `user_id`, `operation`
   - Visualization: Bar chart

4. **Intent Classification Accuracy**
   - Event: `intent_classified`
   - Filter: `confidence >= 0.8`
   - Aggregation: Percentage
   - Visualization: Trend over time

### User Journey Funnel

**Funnel Steps:**

1. `conversation_started`
2. `intent_classified`
3. `workflow_started`
4. `workflow_completed` (success = true)
5. `task_created` or `schedule_generated`

**Purpose:** Identify drop-off points in agent conversations

### Premium Conversion Dashboard

**Insights to Create:**

1. **Upgrade Prompt Conversion Rate**
   - Funnel: `upgrade_prompt_shown` → `subscription_status_changed`
   - Group by: `feature`
   - Visualization: Conversion funnel

2. **Feature Gate Frequency**
   - Event: `feature_gated`
   - Group by: `feature`, `reason`
   - Visualization: Bar chart

3. **Premium Feature Usage**
   - Event: `premium_feature_used`
   - Group by: `feature`
   - Filter: User properties: `subscription_tier = premium`
   - Visualization: Line chart over time

### Performance Monitoring Dashboard

**Insights to Create:**

1. **P50/P95/P99 Latency**
   - Event: `query_latency`
   - Aggregation: Percentiles of `total_duration_ms`
   - Visualization: Multi-line chart

2. **Error Rate**
   - Event: `workflow_completed`
   - Filter: `success = false`
   - Group by: `error_type`, `workflow_type`
   - Visualization: Stacked bar chart

3. **LLM Call Latency**
   - Event: `llm_call_made`
   - Aggregation: Average `duration_ms`
   - Group by: `model`
   - Visualization: Line chart

### General App Usage Dashboard (Future)

**Insights to Create:**

1. **Most Clicked Features**
   - Event: `button_clicked`
   - Group by: `button_name`, `page`
   - Visualization: Bar chart

2. **Page View Analytics**
   - Event: `page_viewed`
   - Group by: `page_name`
   - Visualization: Sankey diagram (user flow)

3. **Modal Engagement**
   - Event: `modal_opened`
   - Aggregation: Count, Average `duration_open_ms`
   - Group by: `modal_name`
   - Visualization: Table

4. **Feature Adoption Rate**
   - Events: `task_completed_ui`, `calendar_event_created`, etc.
   - Aggregation: Unique users per feature
   - Visualization: Line chart over time

## Integration Points

### Backend Services

**1. Agent Orchestrator**

File: `backend/app/agents/orchestrator.py`

```python
from app.services.analytics.posthog_service import get_posthog_service

class AgentOrchestrator:
    def __init__(self):
        self.analytics = get_posthog_service()

    async def execute_workflow(self, workflow_type, user_id, input_data):
        start_time = time.time()

        # Track workflow start
        self.analytics.track_workflow_started(
            user_id=user_id,
            workflow_type=workflow_type.value,
            intent=input_data.get("intent")
        )

        try:
            result = await self._execute(...)

            # Track success
            duration_ms = (time.time() - start_time) * 1000
            self.analytics.track_workflow_completed(
                user_id=user_id,
                workflow_type=workflow_type.value,
                success=True,
                duration_ms=duration_ms
            )

            return result
        except Exception as e:
            # Track failure
            duration_ms = (time.time() - start_time) * 1000
            self.analytics.track_workflow_completed(
                user_id=user_id,
                workflow_type=workflow_type.value,
                success=False,
                duration_ms=duration_ms,
                error_type=e.__class__.__name__
            )
            raise
```

**2. Workflow Graphs**

File: `backend/app/agents/graphs/task_graph.py`

```python
from app.services.analytics.posthog_service import get_posthog_service

class TaskGraph(BaseWorkflow):
    def __init__(self):
        super().__init__(WorkflowType.TASK)
        self.analytics = get_posthog_service()

    async def database_executor_node(self, state):
        # Execute task operation
        result = await task_tool.execute(...)

        # Track task creation
        if operation == "create" and result.success:
            self.analytics.track_task_created(
                user_id=state["user_id"],
                task_id=result.data["id"],
                via_agent=True,
                llm_enriched=False
            )

        return state
```

**3. NLU Pipeline**

File: `backend/app/agents/nlu/classifier_onnx.py`

```python
from app.services.analytics.posthog_service import get_posthog_service

class IntentClassifier:
    def __init__(self):
        self.analytics = get_posthog_service()

    async def predict(self, text, user_id):
        start_time = time.time()

        intent, confidence = self._classify(text)

        duration_ms = (time.time() - start_time) * 1000

        # Track classification
        self.analytics.track_intent_classified(
            user_id=user_id,
            intent=intent,
            confidence=confidence,
            method="onnx_classifier"
        )

        self.analytics.track_intent_classification_latency(
            user_id=user_id,
            duration_ms=duration_ms,
            method="onnx_classifier"
        )

        return intent, confidence
```

**4. API Endpoints**

File: `backend/app/api/v1/endpoints/tasks.py`

```python
from app.services.analytics.posthog_service import get_posthog_service

@router.post("/tasks")
async def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    analytics = get_posthog_service()

    # Create task
    task = await task_service.create_task(current_user.id, task_data)

    # Track task creation (not via agent)
    analytics.track_task_created(
        user_id=current_user.id,
        task_id=task.id,
        via_agent=False  # Created via API, not agent
    )

    return task
```

### Frontend Integration (Future)

**1. React Context Provider**

File: `web/src/contexts/AnalyticsContext.tsx`

```typescript
import posthog from 'posthog-js';
import { createContext, useContext, useEffect } from 'react';

const AnalyticsContext = createContext(null);

export function AnalyticsProvider({ children }) {
  useEffect(() => {
    posthog.init(import.meta.env.VITE_POSTHOG_API_KEY, {
      api_host: import.meta.env.VITE_POSTHOG_HOST,
      loaded: (posthog) => {
        if (import.meta.env.MODE === 'development') posthog.opt_out_capturing();
      }
    });
  }, []);

  return (
    <AnalyticsContext.Provider value={posthog}>
      {children}
    </AnalyticsContext.Provider>
  );
}

export const useAnalytics = () => useContext(AnalyticsContext);
```

**2. Custom Hooks**

File: `web/src/hooks/useAnalytics.ts`

```typescript
import { useAnalytics } from '@/contexts/AnalyticsContext';

export function usePageView(pageName: string) {
  const analytics = useAnalytics();

  useEffect(() => {
    analytics.capture('page_viewed', {
      page_name: pageName,
      path: window.location.pathname
    });
  }, [pageName]);
}

export function useTrackClick(buttonName: string, page: string) {
  const analytics = useAnalytics();

  return () => {
    analytics.capture('button_clicked', {
      button_name: buttonName,
      page: page,
      section: getSectionFromContext()
    });
  };
}
```

**3. Component Integration**

File: `web/src/components/TaskItem.tsx`

```typescript
import { useTrackClick } from '@/hooks/useAnalytics';

export function TaskItem({ task }) {
  const trackClick = useTrackClick('complete_task', 'tasks_page');

  const handleComplete = () => {
    trackClick();

    // Complete task logic
    completeTask(task.id);
  };

  return (
    <div>
      <button onClick={handleComplete}>Complete</button>
    </div>
  );
}
```

**4. Automatic Page View Tracking**

File: `web/src/app/routes.tsx`

```typescript
import { usePageView } from '@/hooks/useAnalytics';
import { useLocation } from 'react-router-dom';

export function AppRoutes() {
  const location = useLocation();

  // Track page views automatically
  useEffect(() => {
    const pageName = getPageNameFromPath(location.pathname);
    analytics.capture('page_viewed', {
      page_name: pageName,
      path: location.pathname,
      referrer: document.referrer
    });
  }, [location]);

  return <Routes>...</Routes>;
}
```

## Testing

### Backend Testing

**Disable in Tests:**

File: `backend/tests/conftest.py`

```python
import os
os.environ["POSTHOG_ENABLED"] = "false"
```

**Verify Events (Optional):**

File: `backend/tests/services/test_posthog_service.py`

```python
from app.services.analytics.posthog_service import PostHogService
from unittest.mock import Mock, patch

class TestPostHogService:
    @patch('posthog.capture')
    def test_track_workflow_started(self, mock_capture):
        service = PostHogService()

        service.track_workflow_started(
            user_id="test_user",
            workflow_type="tasks",
            intent="task_management"
        )

        assert mock_capture.called
        assert mock_capture.call_args[1]["event"] == "workflow_started"
```

### Frontend Testing

**Mock PostHog:**

File: `web/src/tests/setupTests.ts`

```typescript
import { vi } from 'vitest';

vi.mock('posthog-js', () => ({
  default: {
    init: vi.fn(),
    capture: vi.fn(),
    identify: vi.fn(),
    isFeatureEnabled: vi.fn(() => false)
  }
}));
```

## Performance Considerations

### Event Batching

PostHog automatically batches events. For high-volume applications:

```python
# Configure batch size and flush interval
posthog.batch_size = 100  # Default: 100
posthog.flush_at = 100     # Default: 100
posthog.flush_interval = 0.5  # Seconds, Default: 0.5
```

### Async Event Tracking

For backend services, consider async event tracking:

```python
import asyncio

async def track_event_async(user_id, event_name, properties):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        analytics.track_event,
        user_id,
        event_name,
        properties
    )
```

### Redis Caching for Feature Flags

Cache feature flag results to reduce API calls:

```python
import redis
from functools import lru_cache

class PostHogService:
    @lru_cache(maxsize=1000)
    def is_feature_enabled(self, user_id: str, feature_flag: str) -> bool:
        # Cache for 5 minutes
        cache_key = f"feature_flag:{user_id}:{feature_flag}"
        cached = redis.get(cache_key)

        if cached:
            return cached == "true"

        enabled = posthog.feature_enabled(feature_flag, user_id)
        redis.setex(cache_key, 300, "true" if enabled else "false")

        return enabled
```

## Troubleshooting

### Events Not Appearing

1. **Check PostHog is enabled:**
   ```bash
   echo $POSTHOG_ENABLED  # Should be "true"
   ```

2. **Verify API key:**
   ```bash
   echo $POSTHOG_API_KEY  # Should start with "phc_"
   ```

3. **Check logs:**
   ```bash
   grep "PostHog" backend/logs/app.log
   ```

4. **Test connection:**
   ```python
   from app.services.analytics.posthog_service import get_posthog_service

   analytics = get_posthog_service()
   analytics.track_event("test_user", "test_event", {"test": True})
   ```

### PII Leaking

If PII is accidentally sent:

1. **Add to filter list:**
   ```python
   # In posthog_service.py
   pii_fields = {"email", "name", "phone", "address", "ip_address", "your_new_field"}
   ```

2. **Delete from PostHog:**
   - Go to PostHog dashboard
   - Settings → Data Management → Delete Personal Data
   - Enter user ID and field to delete

### Performance Issues

If PostHog is causing slowdowns:

1. **Disable in development:**
   ```bash
   POSTHOG_ENABLED=false
   ```

2. **Use async tracking:**
   ```python
   # Run tracking in background thread
   ```

3. **Reduce event frequency:**
   ```python
   # Sample high-frequency events
   if random.random() < 0.1:  # Track 10% of events
       analytics.track_event(...)
   ```

## Migration Plan

### Phase 1: Agent Analytics (Current)

- ✅ Install PostHog SDK
- ✅ Create PostHogService wrapper
- ✅ Integrate with agent orchestrator
- ✅ Track workflow events
- ✅ Track LLM usage
- ✅ Create agent performance dashboard

### Phase 2: Premium & Monetization (Weeks 1-2)

- ☐ Track upgrade prompts
- ☐ Track feature gating
- ☐ Track subscription changes
- ☐ Create conversion funnel dashboard
- ☐ Set up automated alerts for conversion drop-offs

### Phase 3: Frontend Integration (Weeks 3-4)

- ☐ Install PostHog JS SDK
- ☐ Create AnalyticsContext provider
- ☐ Track page views
- ☐ Track button clicks
- ☐ Track form submissions
- ☐ Create user behavior dashboard

### Phase 4: Advanced Features (Weeks 5-6)

- ☐ Implement feature flags
- ☐ Set up A/B tests
- ☐ Create cohort analysis
- ☐ Set up automated insights
- ☐ Implement session recordings (if needed)

## Resources

- [PostHog Documentation](https://posthog.com/docs)
- [PostHog Python SDK](https://posthog.com/docs/libraries/python)
- [PostHog JavaScript SDK](https://posthog.com/docs/libraries/js)
- [Feature Flags Guide](https://posthog.com/docs/feature-flags)
- [Funnel Analysis](https://posthog.com/docs/user-guides/funnels)
- [Session Recordings](https://posthog.com/docs/session-replay)

## Support

For issues or questions:

1. Check backend logs: `backend/logs/app.log`
2. Review PostHog dashboard: [https://app.posthog.com](https://app.posthog.com)
3. Consult service README: `backend/app/services/analytics/README.md`
4. Check PostHog status: [https://status.posthog.com](https://status.posthog.com)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-23
**Next Review:** After Phase 2 completion
