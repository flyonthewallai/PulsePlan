# LangGraph Agent Workflow Design

## Overview

This document outlines the design for migrating from N8N to LangGraph-based agent workflows in FastAPI. The system will maintain the same functionality while providing better security, observability, and control.

## Core Workflow Graphs

### 1. Natural Language Processing Workflow
**File:** `app/workflows/natural_language_workflow.py`

```mermaid
graph TD
    A[User Query] --> B[Intent Classification]
    B --> C{Intent Type}
    C -->|Calendar| D[Calendar Workflow]
    C -->|Task| E[Task Workflow]
    C -->|Briefing| F[Briefing Workflow]
    C -->|Chat| G[Chat Workflow]
    C -->|Unknown| H[Clarification Request]
    D --> I[Policy Gate]
    E --> I
    F --> I
    G --> I
    I --> J[Rate Limit Check]
    J --> K[Execute Tool]
    K --> L[Reconcile Results]
    L --> M[Generate Response]
    M --> N[Update Trace]
```

**Nodes:**
- `intent_classifier`: Analyzes user query to determine workflow type
- `policy_gate`: Validates permissions and scopes
- `rate_limiter`: Checks rate limits per integration
- `tool_executor`: Executes the appropriate tool
- `result_reconciler`: Handles conflicts and validates outputs
- `response_generator`: Formats final response
- `trace_updater`: Records decision trace with PII redaction

### 2. Calendar Integration Workflow
**File:** `app/workflows/calendar_workflow.py`

```mermaid
graph TD
    A[Calendar Request] --> B[Token Validation]
    B --> C[Provider Selection]
    C -->|Google| D[Google Calendar Tool]
    C -->|Microsoft| E[Microsoft Calendar Tool]
    D --> F[Idempotency Check]
    E --> F
    F --> G[Execute Operation]
    G --> H[Cache Update]
    H --> I[Webhook Notification]
```

**Nodes:**
- `token_validator`: Validates and refreshes OAuth tokens
- `provider_selector`: Routes to appropriate calendar provider
- `idempotency_checker`: Prevents duplicate operations
- `calendar_executor`: Performs calendar operations
- `cache_updater`: Updates Redis cache
- `webhook_notifier`: Sends real-time updates

### 3. Task Management Workflow
**File:** `app/workflows/task_workflow.py`

```mermaid
graph TD
    A[Task Request] --> B[Task Type Detection]
    B -->|Create| C[Task Creation]
    B -->|Update| D[Task Update]
    B -->|Delete| E[Task Deletion]
    B -->|List| F[Task Retrieval]
    C --> G[Validation Gate]
    D --> G
    E --> G
    F --> G
    G --> H[Database Operation]
    H --> I[Schedule Recalculation]
    I --> J[Notification Service]
```

**Nodes:**
- `task_type_detector`: Determines operation type
- `validation_gate`: Validates task data and permissions
- `database_executor`: Performs CRUD operations
- `schedule_recalculator`: Updates intelligent scheduling
- `notification_service`: Sends user notifications

### 4. Daily Briefing Workflow
**File:** `app/workflows/briefing_workflow.py`

```mermaid
graph TD
    A[Briefing Request] --> B[Data Aggregation]
    B --> C[Email Analysis]
    B --> D[Calendar Analysis]
    B --> E[Task Analysis]
    C --> F[Content Synthesis]
    D --> F
    E --> F
    F --> G[Template Generation]
    G --> H[Delivery Service]
```

**Nodes:**
- `data_aggregator`: Collects user data from multiple sources
- `email_analyzer`: Processes email data with connected accounts
- `calendar_analyzer`: Analyzes calendar events
- `task_analyzer`: Reviews pending tasks
- `content_synthesizer`: Combines analysis into briefing
- `template_generator`: Formats briefing content
- `delivery_service`: Sends briefing via email/notification

### 5. Intelligent Scheduling Workflow
**File:** `app/workflows/scheduling_workflow.py`

```mermaid
graph TD
    A[Schedule Request] --> B[Constraint Analysis]
    B --> C[Availability Check]
    C --> D[Priority Optimization]
    D --> E[Time Block Generation]
    E --> F[Conflict Resolution]
    F --> G[Schedule Commit]
    G --> H[Calendar Sync]
```

**Nodes:**
- `constraint_analyzer`: Evaluates user preferences and limitations
- `availability_checker`: Checks calendar availability
- `priority_optimizer`: Applies priority-based scheduling algorithms
- `time_block_generator`: Creates optimal time blocks
- `conflict_resolver`: Handles scheduling conflicts
- `schedule_committer`: Saves schedule to database
- `calendar_syncer`: Syncs with external calendars

## Workflow Architecture Patterns

### Standard Workflow Structure
All workflows follow this pattern:
1. **Input Validation** → Validate and sanitize inputs
2. **Policy Gate** → Check permissions and scopes
3. **Rate Limiting** → Apply per-integration rate limits
4. **Business Logic** → Execute core functionality
5. **Idempotency** → Ensure exactly-once execution
6. **Result Processing** → Format and validate outputs
7. **Observability** → Record traces and metrics

### Error Handling Pattern
```python
class WorkflowError(Exception):
    """Base workflow error with context"""
    def __init__(self, message: str, context: dict, recoverable: bool = False):
        self.message = message
        self.context = context
        self.recoverable = recoverable
        super().__init__(message)

# Error recovery nodes
def error_handler_node(state: WorkflowState) -> WorkflowState:
    if state.error and state.error.recoverable:
        return retry_operation(state)
    else:
        return fail_gracefully(state)
```

### State Management
```python
from typing import TypedDict, Optional, Any, List
from datetime import datetime

class WorkflowState(TypedDict):
    # Core state
    user_id: str
    request_id: str
    workflow_type: str
    
    # Input/Output
    input_data: dict
    output_data: Optional[dict]
    
    # Context
    user_context: dict
    connected_accounts: dict
    
    # Execution tracking
    current_node: str
    visited_nodes: List[str]
    execution_start: datetime
    
    # Error handling
    error: Optional[WorkflowError]
    retry_count: int
    
    # Observability
    trace_id: str
    metrics: dict
```

## Integration Points

### Database Models
```python
# Decision traces table
class DecisionTrace(BaseModel):
    id: str
    job_id: str
    user_id: str
    workflow_type: str
    inputs: dict  # Redacted PII
    steps: List[dict]
    policy_checks: List[dict]
    summary: str
    model: str
    prompt_id: str
    prompt_version: str
    created_at: datetime

# Idempotency records table
class IdempotencyRecord(BaseModel):
    user_id: str
    effect_hash: str
    result: dict
    created_at: datetime
    ttl: int
```

### OAuth Token Management
```python
# Enhanced token storage with versioning
class OAuthToken(BaseModel):
    user_id: str
    provider: str
    encrypted_access_token: str
    encrypted_refresh_token: Optional[str]
    expires_at: datetime
    scopes: List[str]
    token_version: int
    created_at: datetime
    updated_at: datetime
```

### Rate Limiting Keys
```python
# Redis rate limiting structure
RATE_LIMIT_KEYS = {
    "user_global": "rate:user:{user_id}:global",
    "user_provider": "rate:user:{user_id}:{provider}",
    "provider_global": "rate:provider:{provider}:global",
    "workflow_type": "rate:workflow:{workflow_type}:{user_id}"
}
```

## Security Implementation

### Policy Engine
```python
class PolicyEngine:
    async def check_permissions(self, user_id: str, operation: str, resource: str) -> bool:
        # Check user permissions, scopes, time windows
        user_policies = await self.get_user_policies(user_id)
        return self.evaluate_policy(user_policies, operation, resource)
    
    async def log_policy_decision(self, decision: PolicyDecision):
        # Log all policy decisions for audit
        await self.audit_logger.log(decision)
```

### Encryption Service
```python
class EncryptionService:
    def encrypt_token(self, token: str, user_id: str) -> str:
        # Use libsodium or AWS KMS for encryption
        key = self.derive_user_key(user_id)
        return self.encrypt_with_key(token, key)
    
    def decrypt_token(self, encrypted_token: str, user_id: str) -> str:
        key = self.derive_user_key(user_id)
        return self.decrypt_with_key(encrypted_token, key)
```

## Observability Integration

### OpenTelemetry Traces
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("workflow_execution")
async def execute_workflow(workflow_state: WorkflowState):
    with tracer.start_as_current_span("policy_check"):
        await check_policies(workflow_state)
    
    with tracer.start_as_current_span("business_logic"):
        await execute_business_logic(workflow_state)
```

### Sentry Error Tracking
```python
import sentry_sdk

@sentry_sdk.capture_exceptions
async def workflow_error_handler(error: WorkflowError):
    sentry_sdk.set_context("workflow", {
        "user_id": error.context.get("user_id"),
        "workflow_type": error.context.get("workflow_type"),
        "current_node": error.context.get("current_node")
    })
    raise error
```

## Migration Strategy

### Phase 1: Core Infrastructure
1. Set up FastAPI with LangGraph
2. Implement policy engine and rate limiting
3. Set up encrypted token storage
4. Implement basic observability

### Phase 2: Workflow Migration
1. Implement natural language processing workflow
2. Migrate calendar integration workflow
3. Migrate task management workflow
4. Add comprehensive testing

### Phase 3: Advanced Features
1. Implement briefing workflow
2. Implement intelligent scheduling workflow
3. Add advanced monitoring and alerting
4. Performance optimization

### Phase 4: Cutover
1. Feature flag rollout by cohort
2. Monitor metrics and error rates
3. Complete migration from N8N
4. Remove legacy code

## Performance Considerations

### Caching Strategy
- User context: 15-minute TTL
- Connected accounts: 5-minute TTL
- Calendar data: 2-minute TTL with ETag support
- Task data: Real-time with cache invalidation

### Resource Limits
- Concurrent workflows per user: 3
- Maximum workflow execution time: 30 seconds
- Rate limits: 100 requests/hour per integration
- Token refresh: Async background job with jittered backoff

### Scaling
- Horizontal scaling with Redis for state management
- Dramatiq for background job processing
- Connection pooling for external APIs
- Circuit breakers for upstream service protection

## Testing Strategy

### Contract Tests
- OpenAPI snapshot testing
- Schema validation for all endpoints
- Error response validation

### Integration Tests
- Mock external services with respx/VCR
- Test workflow execution paths
- Test error handling and recovery

### Property-Based Tests
- Scheduler constraint satisfaction
- Rate limiting behavior
- Token encryption/decryption

### Chaos Testing
- Provider 429/5xx responses
- Token expiry mid-workflow
- Redis outage scenarios
- Network partitions

## Deployment Configuration

### Environment Variables
```bash
# Core settings
FASTAPI_ENV=production
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/db

# Security
ENCRYPTION_KEY_VERSION=1
TOKEN_ROTATION_INTERVAL=86400  # 24 hours
POLICY_REFRESH_INTERVAL=300    # 5 minutes

# Rate limiting
GLOBAL_RATE_LIMIT=1000
PROVIDER_RATE_LIMIT=100
USER_RATE_LIMIT=50

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
SENTRY_DSN=https://...
LOG_LEVEL=INFO

# Feature flags
ENABLE_ADVANCED_SCHEDULING=true
ENABLE_EMAIL_BRIEFINGS=true
ENABLE_WEBHOOK_NOTIFICATIONS=true
```

This design provides a robust, secure, and observable replacement for the N8N workflows while maintaining all existing functionality and improving upon security and monitoring capabilities.