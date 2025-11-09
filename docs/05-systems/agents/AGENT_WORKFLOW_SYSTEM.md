# PulsePlan Agent Workflow System - Comprehensive Documentation

**Version:** 1.0  
**Last Updated:** 2025-01-28  
**Status:** Production

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Core Components](#core-components)
5. [Workflow Execution](#workflow-execution)
6. [Continuation & Conversation Management](#continuation--conversation-management)
7. [Current Issues & Gaps](#current-issues--gaps)
8. [Future Improvements](#future-improvements)
9. [Operational Runbook](#operational-runbook)

---

## Executive Summary

The PulsePlan Agent Workflow System is a **hybrid AI agent architecture** that combines deterministic rule-based NLU with LangGraph workflows for intelligent task automation. The system processes natural language queries, routes them to specialized workflows, and maintains conversation context for multi-turn interactions.

### Key Characteristics

- **LLM-Last Architecture**: Uses deterministic NLU (Rules → ONNX Classifier → Entity Extractors) with LLM only for conversation generation
- **Multi-Agent Workflows**: 6 specialized LangGraph workflows (Calendar, Task, Scheduling, Search, Briefing, Email)
- **Conversation Continuation**: Intelligent follow-up detection using cascading priority classification
- **Policy-Based Gating**: Automatic execution vs. confirmation gates based on action risk/impact
- **Isolation & Recovery**: Enhanced error boundaries, state management, and automatic recovery mechanisms

### System Metrics

- **Average Query Latency**: < 2s (without LLM), < 5s (with LLM)
- **Intent Classification Accuracy**: ~85% (target: >90%)
- **Continuation Detection Accuracy**: ~95% (with semantic similarity)
- **Workflow Success Rate**: ~98% (with recovery mechanisms)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                          │
│  POST /api/v1/agent/process                                      │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              Agent Orchestrator                                  │
│  - execute_natural_language_query()                             │
│  - execute_workflow()                                            │
│  - handle_follow_up_query()                                     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Unified      │ │ Workflow     │ │ Conversation │
│ Intent       │ │ Execution    │ │ Supervisor   │
│ Processor    │ │ Engine       │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                 │
       ▼                ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              NLU Pipeline (Deterministic)                      │
│  Rules → ONNX Classifier → Entity Extractors → Gates           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              Planning Handler                                    │
│  - Policy Evaluation                                            │
│  - Action Record Creation                                       │
│  - Gate Creation (if needed)                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              Action Executor                                    │
│  - CalendarActionExecutor                                       │
│  - TaskActionExecutor                                           │
│  - EmailActionExecutor                                          │
│  - SearchActionExecutor                                         │
│  - RescheduleActionExecutor                                     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph Workflows                                 │
│  CalendarGraph | TaskGraph | SchedulingGraph | SearchGraph      │
│  BriefingGraph | EmailGraph                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Layers

#### Layer 1: API Gateway

- **File**: `backend/app/api/v1/endpoints/agent.py`
- **Responsibility**: Request validation, authentication, response formatting
- **Key Features**: Rate limiting, request logging, error handling

#### Layer 2: Orchestration Layer

- **File**: `backend/app/agents/orchestrator.py`
- **Responsibility**: Central workflow coordination, isolation, error boundaries
- **Key Features**:
  - Workflow isolation containers
  - State management (Redis + PostgreSQL)
  - Automatic recovery mechanisms
  - Circuit breaker protection
  - PostHog analytics integration

#### Layer 3: Intent Processing Layer

- **Files**:
  - `backend/app/agents/core/orchestration/intent_processor.py`
  - `backend/app/agents/core/orchestration/intent_processing/`
- **Responsibility**: NLU classification, entity extraction, continuation detection
- **Key Features**:
  - Deterministic NLU pipeline (Rules → ONNX → Extractors)
  - Continuation classification (5 priority levels)
  - Semantic similarity (optional, async)
  - Conversation state management

#### Layer 4: Planning Layer

- **File**: `backend/app/agents/services/planning_handler.py`
- **Responsibility**: Policy evaluation, action record creation, gate management
- **Key Features**:
  - Policy-based decision making (AUTO/GATE/DRAFT)
  - Entity matching and resolution
  - Confirmation message generation
  - Slot filling and continuation handling

#### Layer 5: Execution Layer

- **File**: `backend/app/agents/services/action_executor.py`
- **Responsibility**: Action dispatch to specialized executors
- **Key Features**:
  - Intent → Executor mapping
  - Execution result tracking
  - Error handling and recovery
  - PostHog analytics

#### Layer 6: Workflow Layer

- **Files**: `backend/app/agents/graphs/*.py`
- **Responsibility**: Domain-specific workflow execution
- **Key Features**:
  - LangGraph state machines
  - Standard workflow nodes (validation, gates, rate limiting)
  - Structured output generation
  - Feedback loop support

---

## Data Flow

### End-to-End Query Processing Flow

```
1. User Query
   └─> POST /api/v1/agent/process
       {
         "query": "What's on my calendar today?",
         "conversation_id": "abc-123",
         "include_history": true
       }

2. Agent Orchestrator
   └─> execute_natural_language_query()
       └─> UnifiedIntentProcessor.process_user_query()

3. Intent Classification
   └─> IntentClassifier.classify_intent()
       ├─> Check pending gates (continuation logic)
       ├─> Run NLU pipeline (Rules → ONNX → Extractors)
       └─> Continuation classifier (5 priority levels)
           └─> Result: ("NEW_INTENT", None) or ("CONTINUATION", action_id)

4. Entity Extraction
   └─> EntityExtractor.extract_task_info()
       └─> Populate slots in NLU result

5. Planning Handler
   └─> PlanningHandler.handle_planning()
       ├─> Create action record
       ├─> Entity matching (if reschedule/calendar intent)
       ├─> Gather context (calendar, tasks, etc.)
       ├─> Build policy context
       ├─> Evaluate policy → Decision (AUTO/GATE/DRAFT)
       └─> If AUTO: Execute immediately
           If GATE: Create pending gate
           If DRAFT: Save as draft

6. Action Execution (if AUTO)
   └─> ActionExecutor.execute_action()
       └─> Route to specialized executor
           └─> CalendarActionExecutor.execute()
               └─> CalendarGraph workflow
                   └─> Execute calendar query
                       └─> Return results

7. Supervisor
   └─> WorkflowSupervisor.supervise_workflow_execution()
       └─> Wrap structured output in conversation response
           └─> Return to API

8. API Response
   └─> {
         "success": true,
         "conversation_id": "abc-123",
         "immediate_response": "Here's your schedule for today...",
         "workflow_output": {...}
       }
```

### Continuation Flow Example

```
Turn 1: "What's on my calendar next Friday?"
  └─> NLU: intent="calendar_query", slots={date: "next_friday"}
  └─> Continuation: NEW_INTENT (no previous action)
  └─> Planning: AUTO (safe query)
  └─> Execution: Calendar query → Return events
  └─> Action ID: abc-123 created

Turn 2: "What about today?"
  └─> NLU: intent="calendar_query", slots={date: "today"}
  └─> Continuation Classifier:
      ├─> Priority 1: No pending gate
      ├─> Priority 2: No temporal_slot_fill
      ├─> Priority 3: No adjustment keywords
      └─> Priority 4: Intent similarity check
          └─> calendar_query == calendar_query → CONTINUATION
  └─> Planning: handle_continuation(action_id=abc-123)
      └─> Merge slots: {date: "today"} (overrides "next_friday")
      └─> Keep intent: calendar_query
      └─> Re-plan with merged context
  └─> Execution: Calendar query for "today"
  └─> Response: "Here's your schedule for today..."
```

---

## Core Components

### 1. Agent Orchestrator

**File**: `backend/app/agents/orchestrator.py`

**Purpose**: Central coordinator for all workflow execution

**Key Methods**:

- `execute_natural_language_query()`: Process NL queries via unified intent processor
- `execute_workflow()`: Execute LangGraph workflows with isolation
- `execute_workflow_with_conversation_layer()`: Execute workflow + wrap in conversation response
- `handle_follow_up_query()`: Handle follow-up messages

**Architecture Features**:

- **Isolation**: Workflow containers with resource limits
- **Error Boundaries**: Comprehensive error handling and recovery
- **State Management**: Redis caching + PostgreSQL persistence
- **Recovery**: Automatic retry for recoverable errors
- **Analytics**: PostHog event tracking

**Configuration**:

```python
# Enable/disable isolation
orchestrator = AgentOrchestrator(enable_isolation=True)

# Toggle isolation at runtime
orchestrator.toggle_isolation(enabled=False)  # Fallback to legacy mode
```

### 2. Unified Intent Processor

**Files**:

- `backend/app/agents/core/orchestration/intent_processor.py`
- `backend/app/agents/core/orchestration/intent_processing/intent_processor.py`

**Purpose**: Single entry point for all user query processing

**Key Components**:

- `IntentClassifier`: Intent classification using NLU pipeline
- `EntityExtractor`: Entity extraction and slot filling
- `ActionRouter`: Intent → Action → Workflow routing
- `ConversationManager`: Conversation state and history management

**Processing Pipeline**:

1. **Intent Classification**: Rules → ONNX Classifier → Entity Extractors
2. **Continuation Detection**: 5 priority levels (pending gate → temporal → adjustment → intent similarity → semantic)
3. **Entity Extraction**: Task info, dates, participants, etc.
4. **Action Routing**: Map intent to action type and workflow
5. **Planning**: Pass to planning handler for policy evaluation

**Key Methods**:

- `process_user_query()`: Main entry point
- `_handle_slot_fill()`: Handle slot filling for pending actions
- `_handle_continuation()`: Handle continuation of previous actions
- `_handle_cancel_pending()`: Handle cancellation of pending actions

### 3. Continuation Classifier

**File**: `backend/app/agents/core/orchestration/continuation.py`

**Purpose**: Determine if user input is continuation, slot fill, or new intent

**Classification Categories**:

- `SLOT_FILL`: Filling missing information for pending action
- `CONTINUATION`: Adjusting/modifying last plan
- `CANCEL_PENDING`: Canceling pending action
- `NEW_INTENT`: Starting fresh conversation

**Priority Levels** (cascading):

1. **Priority 1: Pending Gate** (highest)

   - If user has pending confirmation/clarification
   - Checks for cancellation or slot-filling
   - Exception: `temporal_slot_fill` WITHOUT pending gate → Priority 2

2. **Priority 2: Temporal Slot Fill** (smart continuation)

   - Intent: `temporal_slot_fill`
   - Detected when user provides temporal references
   - If NO pending gate → treated as CONTINUATION

3. **Priority 3: Adjustment Keywords**

   - Keywords: "change", "modify", "adjust", "update", "reschedule"
   - Linguistic cues: "what about", "how about", "instead", "actually"

4. **Priority 4: Intent Similarity**

   - Checks if new intent matches previous intent
   - Intent families: calendar_family, task_family, email_family, search_family

5. **Priority 5: Semantic Similarity** (optional, async)
   - Uses OpenAI `text-embedding-3-small`
   - Cosine similarity threshold: 0.6
   - Adds ~100-200ms latency

**Configuration**:

```python
# Enable/disable semantic similarity
turn_type, action_id = await classify_turn_async(
    state=conversation_state,
    nlu=nlu_result.to_dict(),
    enable_semantic_similarity=True  # Set to False to disable
)

# Adjust similarity threshold
is_similar, score = await compute_semantic_similarity(
    text1, text2, threshold=0.6  # Increase for stricter matching
)
```

### 4. Planning Handler

**File**: `backend/app/agents/services/planning_handler.py`

**Purpose**: Policy-based decision making for action execution

**Policy Decisions**:

- `AUTO`: Execute immediately (safe operations)
- `GATE`: Require user confirmation (risky operations)
- `DRAFT`: Save as draft (missing required information)

**Policy Evaluation Factors**:

- Intent confidence
- Slot completeness
- Action metadata (is_external_write, is_destructive, is_bulk_operation)
- User preferences
- Estimated impact

**Key Methods**:

- `handle_planning()`: Main planning flow
- `handle_slot_fill()`: Update action with new slot values
- `handle_continuation()`: Handle continuation/modification of previous action
- `_format_confirmation_message()`: Generate user-friendly confirmation messages

**Entity Matching**:

- Pre-policy entity resolution for reschedule/calendar intents
- LLM extraction → DB entity matching
- Handles ambiguous matches with clarification requests

### 5. Action Executor

**File**: `backend/app/agents/services/action_executor.py`

**Purpose**: Dispatch actions to specialized executors

**Specialized Executors**:

- `CalendarActionExecutor`: Calendar operations
- `TaskActionExecutor`: Task management
- `EmailActionExecutor`: Email operations
- `SearchActionExecutor`: Search queries
- `QueryActionExecutor`: User data queries
- `BriefingActionExecutor`: Daily/weekly briefings
- `RescheduleActionExecutor`: Rescheduling operations
- `ConversationalActionExecutor`: Greetings, thanks, help

**Execution Flow**:

1. Route intent to appropriate executor
2. Execute action with specialized logic
3. Track execution metrics (duration, success/failure)
4. Return execution result

**Error Handling**:

- Comprehensive error tracking
- PostHog analytics for all executions
- Graceful degradation on failures

### 6. LangGraph Workflows

**Files**: `backend/app/agents/graphs/*.py`

**Purpose**: Domain-specific workflow execution

**Workflow Types**:

- `CalendarGraph`: Calendar queries and event management
- `TaskGraph`: Task CRUD operations
- `SchedulingGraph`: Intelligent scheduling with OR-Tools
- `SearchGraph`: Search across user data
- `BriefingGraph`: Daily/weekly briefings
- `EmailGraph`: Email operations

**Standard Workflow Nodes** (from BaseWorkflow):

1. `input_validator_node`: Validate and sanitize inputs
2. `policy_gate_node`: Check permissions and scopes
3. `rate_limiter_node`: Apply rate limiting
4. `idempotency_checker_node`: Ensure exactly-once execution
5. `result_processor_node`: Format and validate outputs
6. `trace_updater_node`: Record traces and metrics
7. `structured_output_node`: Generate structured machine-readable output
8. `feedback_loop_node`: Handle feedback collection
9. `response_node`: Prepare final output for conversation layer

**Workflow State**:

```python
class WorkflowState(TypedDict):
    user_id: str
    request_id: str
    workflow_type: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    user_context: Dict[str, Any]
    connected_accounts: Dict[str, Any]
    current_node: str
    visited_nodes: List[str]
    execution_start: datetime
    error: Optional[Dict[str, Any]]
    retry_count: int
    trace_id: str
    metrics: Dict[str, Any]
    structured_output: Optional[Dict[str, Any]]
    requires_feedback: bool
    feedback_request: Optional[Dict[str, Any]]
    follow_up_context: Optional[Dict[str, Any]]
```

### 7. Conversation Supervisor

**File**: `backend/app/agents/services/supervisor.py`

**Purpose**: Wrap workflow outputs in conversation-friendly responses

**Key Methods**:

- `supervise_workflow_execution()`: Convert workflow output to conversation response
- `handle_follow_up_message()`: Handle follow-up messages (minimal implementation)

**Current Status**: Minimal implementation - wraps outputs in simple messages

**Future Enhancement**: Advanced conversation generation, context-aware responses, proactive suggestions

---

## Workflow Execution

### Execution Modes

#### 1. Isolated Execution (Default)

- **Enabled**: `enable_isolation=True`
- **Features**:
  - Workflow containers with resource limits
  - State persistence (Redis + PostgreSQL)
  - Error boundaries and recovery
  - Circuit breaker protection
  - Checkpointing support

#### 2. Legacy Execution (Fallback)

- **Enabled**: `enable_isolation=False`
- **Features**:
  - Direct workflow execution
  - Basic error handling
  - No state persistence
  - No recovery mechanisms

### Execution Flow

```
1. Orchestrator receives request
   └─> Generate workflow_id (trace_id)

2. Create isolated state (if isolation enabled)
   └─> workflow_state_manager.create_isolated_state()
       └─> Persist to Redis + PostgreSQL

3. Create workflow container
   └─> WorkflowContainerFactory.create_container()
       └─> Set resource limits
       └─> Configure error boundaries

4. Execute workflow with error boundary
   └─> workflow_error_boundary.execute_with_boundary()
       └─> container.execute_with_boundaries()
           └─> Build LangGraph
           └─> Execute graph.ainvoke(state)

5. Update state with results
   └─> workflow_state_manager.complete_state()
       └─> Persist output_data

6. Trigger automatic recovery (if error)
   └─> workflow_recovery_service.schedule_recovery()
       └─> Retry after delay (30 seconds)

7. Cleanup (after delay)
   └─> Archive state
   └─> Remove from active tracking
```

### Error Handling & Recovery

**Error Types**:

- **Recoverable**: TimeoutError, ConnectionError, OSError
- **Non-Recoverable**: ValidationError, PermissionError, BusinessLogicError

**Recovery Mechanisms**:

- Automatic retry for recoverable errors (30s delay)
- Circuit breaker for repeated failures
- State checkpointing for resumption
- Manual recovery via `orchestrator.recover_workflow()`

**Recovery Triggers**:

- `AUTOMATIC`: Scheduled after error
- `MANUAL`: User-initiated recovery
- `SCHEDULED`: Time-based recovery

---

## Continuation & Conversation Management

### Conversation State Management

**Storage**:

- **PostgreSQL**: Full conversation history (`conversation_sessions`, `conversation_turns`)
- **Redis**: Active context cache (TTL: 1 hour)

**State Components**:

- `conversation_id`: Session identifier
- `last_action`: Previous action record
- `pending_gate`: Active confirmation/clarification gate
- `conversation_history`: Recent turns (last 10)

### Continuation Detection Algorithm

**Input**: User query + conversation state

**Output**: `(turn_type, action_id)`

**Algorithm**:

```python
def classify_turn(state, nlu):
    # Priority 1: Pending gate exists
    if state.pending_gate:
        if intent == "cancel":
            return ("CANCEL_PENDING", action_id)
        if state.is_terse or intent == pending_intent:
            return ("SLOT_FILL", action_id)

    # Priority 2: Temporal slot fill = continuation
    if state.last_action and intent == "temporal_slot_fill":
        return ("CONTINUATION", plan_id)

    # Priority 3: Adjustment keywords
    if state.last_action and intent in ADJUSTMENT_INTENTS:
        return ("NEW_INTENT", None)  # Explicit new action

    # Priority 4: Intent similarity
    if state.last_action and are_intents_similar(intent, last_intent):
        return ("CONTINUATION", plan_id)

    # Priority 5: Semantic similarity (async)
    if enable_semantic_similarity:
        is_similar, score = await compute_semantic_similarity(...)
        if is_similar:
            return ("CONTINUATION", plan_id)

    # Default: New intent
    return ("NEW_INTENT", None)
```

### Continuation Handling

**Slot Fill**:

- Merge new slots with existing action params
- Re-evaluate policy
- Execute if AUTO, create gate if GATE

**Continuation**:

- Retrieve previous action
- Merge slots (new overrides old)
- Keep original intent
- Re-plan with merged context

**Cancel Pending**:

- Mark action as cancelled
- Clear pending gate
- Return cancellation confirmation

---

## Current Issues & Gaps

### ✅ Architecture Compliance Issues - RESOLVED

#### **Direct Supabase Access in Agent Files** - ✅ FIXED (2025-01-28)

All critical agent files have been migrated to use the service layer:

- ✅ `events.py` - Uses `TimeblockService`, `TagService`, `CourseService`
- ✅ `intent_processor.py` - Uses `TodoService` and `TaskService`
- ✅ `planning_handler.py` - Uses `TodoService`, `TaskService`, `TimeblockService`
- ✅ `user_context_service.py` - Uses full service layer + repositories
- ✅ `query_actions.py` - Uses `CalendarEventService` and `TaskService`

**New Repositories Created:**

- `UserContextCacheRepository` - For user context cache operations

**Enhanced Repositories:**

- `ConversationRepository` - Added `list_by_user()` and `count_active_by_user()` methods

**Architecture Compliance:** ~90% (up from 80%) - Target achieved for critical files

### Critical Issues

#### 1. **Incomplete Checkpointing/Resume**

- **Issue**: `LangGraphDriver.resume()` is a stub
- **Impact**: Follow-up gates rely on external state rather than true graph checkpoint resume
- **Location**: `backend/app/agents/core/orchestration/driver.py:169-185`
- **Severity**: High (affects gate resumption)

#### 2. **Supervisor Implementation Minimal**

- **Issue**: `WorkflowSupervisor` only wraps outputs in simple messages
- **Impact**: No advanced conversation generation, context-aware responses, or proactive suggestions
- **Location**: `backend/app/agents/services/supervisor.py`
- **Severity**: Medium (affects user experience)

#### 3. **Continuation Configuration Scattered**

- **Issue**: Thresholds, keywords, intent families spread across classifier logic
- **Impact**: Hard to tune, no centralized config/telemetry for false-positive/negative analysis
- **Location**: `backend/app/agents/core/orchestration/continuation.py`
- **Severity**: Medium (affects maintainability)

#### 4. **Conversation Summarization Missing**

- **Issue**: No aging/summary window for long histories
- **Impact**: Token/latency risk for long conversations
- **Location**: Conversation management layer
- **Severity**: Medium (affects scalability)

#### 5. **Observability Gaps**

- **Issue**: Continuation decisions (priority hit, scores, action linkage) not standardized as metrics/spans
- **Impact**: Hard to debug continuation misdetections
- **Location**: Continuation classifier
- **Severity**: Medium (affects debugging)

### Moderate Issues

#### 6. **Cross-Session Persistence Not Formalized**

- **Issue**: TTL mentioned but not documented with user-facing/session semantics
- **Impact**: Unclear behavior across app sessions/devices
- **Severity**: Low-Medium

#### 7. **Test Coverage Gaps**

- **Issue**: Unit example exists but no explicit suite covering each priority path
- **Impact**: Risk of regressions
- **Severity**: Medium

#### 8. **Privacy Concerns**

- **Issue**: Semantic similarity uses embeddings; no PII redaction documented
- **Impact**: Potential privacy risk
- **Severity**: Medium

#### 9. **Frontend Contract Drift**

- **Issue**: Frontend reference path may drift from actual implementation
- **Impact**: Documentation may become outdated
- **Severity**: Low

### Minor Issues

#### 10. **Entity Matching Error Handling**

- **Issue**: Entity matching failures logged but not always handled gracefully
- **Impact**: User may see unclear error messages
- **Severity**: Low

#### 11. **Rate Limiting Not Fully Implemented**

- **Issue**: `rate_limiter_node` is a placeholder
- **Impact**: No hierarchical rate limiting
- **Severity**: Low-Medium

#### 12. **Idempotency Checking Not Implemented**

- **Issue**: `idempotency_checker_node` is a placeholder
- **Impact**: Potential duplicate executions
- **Severity**: Low-Medium

---

## Future Improvements

### High Priority Improvements

#### 1. **Implement True Checkpointing & Resume**

- **Goal**: Complete `LangGraphDriver.resume()` with checkpoint IDs from gates
- **Implementation**:
  - Persist checkpoints via `workflow_state_manager`
  - Include checkpoint IDs in `ConversationResponse`
  - Enable deterministic follow-ups
- **Estimated Effort**: 2-3 days
- **Dependencies**: LangGraph checkpointing support

#### 2. **Centralized Continuation Configuration**

- **Goal**: Extract thresholds, keywords, intent families into single config module
- **Implementation**:
  - Create `continuation_config.py` with runtime reload capability
  - Add safe defaults per domain
  - Support per-user experimentation flags
  - Environment-based overrides
- **Estimated Effort**: 1-2 days

#### 3. **Enhanced Observability**

- **Goal**: Structured logs and metrics for continuation decisions
- **Implementation**:
  - Add metrics for: priority hit order, similarity scores, winner decision, action linkage
  - Emit PostHog events: `continuation_classified`, `continuation_misdetection`, `gate_wait`, `gate_resolved`
  - Create dashboards for continuation accuracy
- **Estimated Effort**: 2-3 days

#### 4. **Conversation Summarization Policy**

- **Goal**: Rolling summaries when history exceeds token budget
- **Implementation**:
  - Semantic chunking + LLM summary with guardrails
  - Store summaries in Redis with provenance
  - Keep last N full turns + summary
- **Estimated Effort**: 3-4 days

#### 5. **Enhanced Supervisor**

- **Goal**: Advanced conversation generation and context-aware responses
- **Implementation**:
  - LLM-based response generation (with token tracking)
  - Context-aware suggestions
  - Proactive clarifications
  - Multi-turn conversation planning
- **Estimated Effort**: 5-7 days

### Medium Priority Improvements

#### 6. **Cross-Session Persistence Semantics**

- **Goal**: Document and implement explicit policy for conversation persistence
- **Implementation**:
  - Define how `conversation_id` persists across app sessions/devices
  - Implement expiry, revival, user controls
  - Add API to fetch/close conversations
  - Export conversation transcript for transparency
- **Estimated Effort**: 2-3 days

#### 7. **Privacy & Safety for Embeddings**

- **Goal**: Redact PII before computing embeddings
- **Implementation**:
  - Redact emails/URLs/tokens/PII before embedding
  - Add tests for redaction pipeline
  - Document redaction pipeline
  - Config to disable embeddings per user/plan
- **Estimated Effort**: 2-3 days

#### 8. **Test Coverage Expansion**

- **Goal**: Comprehensive test suite for continuation system
- **Implementation**:
  - Unit tests per continuation priority
  - Integration tests: 3-5 turn conversations
  - Error boundary + recovery tests
  - Property tests for temporal phrases
- **Estimated Effort**: 3-5 days

#### 9. **Frontend Contract Hardening**

- **Goal**: Typed client and zod schema for `conversation_id` contract
- **Implementation**:
  - Provide typed client
  - Add zod schema validation
  - Dev console warnings when missing
  - E2E test for `conversation_id` continuity
- **Estimated Effort**: 1-2 days

#### 10. **Cost & Latency Controls**

- **Goal**: Dynamic toggle of semantic similarity based on intent and historical accuracy
- **Implementation**:
  - Per-user accuracy tracking
  - Dynamic enable/disable based on confidence
  - Rate limits/quotas for expensive paths
  - Plan-gated feature flags
- **Estimated Effort**: 2-3 days

### Low Priority Improvements

#### 11. **Rate Limiting Implementation**

- **Goal**: Hierarchical rate limiting per user/workflow type
- **Implementation**:
  - Redis-based rate limiting
  - Per-user, per-workflow-type limits
  - Graceful degradation on limit exceeded
- **Estimated Effort**: 2-3 days

#### 12. **Idempotency Checking**

- **Goal**: Ensure exactly-once execution
- **Implementation**:
  - Redis-based idempotency keys
  - Request deduplication
  - Idempotency key generation
- **Estimated Effort**: 2-3 days

#### 13. **Multi-Turn Slot Filling**

- **Goal**: Track multiple missing slots across turns
- **Implementation**:
  - Slot tracking in conversation state
  - Progressive slot filling
  - Slot validation and completion checks
- **Estimated Effort**: 3-4 days

#### 14. **Proactive Context Suggestions**

- **Goal**: "Did you mean to ask about calendar?" suggestions
- **Implementation**:
  - Intent prediction based on context
  - Proactive clarification requests
  - Context-aware suggestions
- **Estimated Effort**: 4-5 days

#### 15. **Fine-Tuned Continuation Classifier**

- **Goal**: Train custom model on conversation data
- **Implementation**:
  - Collect conversation data
  - Train continuation classifier model
  - A/B test against rule-based classifier
- **Estimated Effort**: 1-2 weeks

---

## Operational Runbook

### Monitoring & Debugging

#### Key Metrics to Monitor

1. **Query Latency**

   - Target: < 2s (without LLM), < 5s (with LLM)
   - Alert threshold: > 5s (without LLM), > 10s (with LLM)
   - Dashboard: PostHog → Agent Performance

2. **Intent Classification Accuracy**

   - Target: > 85%
   - Alert threshold: < 80%
   - Dashboard: PostHog → NLU Accuracy

3. **Continuation Detection Accuracy**

   - Target: > 95%
   - Alert threshold: < 90%
   - Dashboard: PostHog → Continuation Accuracy

4. **Workflow Success Rate**

   - Target: > 98%
   - Alert threshold: < 95%
   - Dashboard: PostHog → Workflow Success Rate

5. **Gate Resolution Rate**
   - Target: > 80%
   - Alert threshold: < 70%
   - Dashboard: PostHog → Gate Resolution

#### Debugging Continuation Issues

**Symptom**: Follow-ups not working (every message treated as new intent)

**Diagnosis**:

1. Check browser console for `conversation_id` tracking
2. Verify `conversation_id` passed in API request
3. Check backend logs for continuation classification
4. Verify `action_records` table has `user_message` column

**Fix**:

```bash
# Check conversation_id in frontend
# Ensure ChatPage.tsx has conversation tracking

# Check backend logs
tail -f backend/logs/app.log | grep "continuation"

# Verify database schema
psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'action_records';"
```

**Symptom**: Wrong intent inferred from continuation

**Diagnosis**:

1. Check last action status (should not be "failed" or "cancelled")
2. Verify intent similarity logic
3. Check semantic similarity scores (if enabled)

**Fix**:

```python
# Check last action
action = await repo.get_last_action(user_id)
print(f"Last action: {action}")

# Check continuation classification
turn_type, action_id = classify_turn(state, nlu)
print(f"Turn type: {turn_type}, Action ID: {action_id}")
```

#### Performance Optimization

**If latency spikes**:

1. Disable semantic similarity for intents with high historical confidence
2. Enable conversation summaries sooner
3. Check Redis connection pool
4. Verify database query performance

**If costs increase**:

1. Gate semantic similarity to premium plans
2. Batch embeddings when feasible
3. Review LLM usage in supervisor
4. Check for unnecessary LLM calls

**If continuation accuracy regresses**:

1. Lower semantic threshold temporarily
2. Enable additional logging guard
3. Sample 1% of conversations for audit (without PII)
4. Review continuation configuration

### Common Operations

#### Enable/Disable Isolation

```python
# Disable isolation (fallback to legacy mode)
orchestrator.toggle_isolation(enabled=False)

# Re-enable isolation
orchestrator.toggle_isolation(enabled=True)
```

#### Manual Workflow Recovery

```python
# Recover failed workflow
success = await orchestrator.recover_workflow(
    workflow_id="abc-123",
    checkpoint_name="error_state"
)
```

#### Suspend/Resume Workflow

```python
# Suspend workflow
await orchestrator.suspend_workflow(
    workflow_id="abc-123",
    reason="Manual suspension"
)

# Resume workflow
await orchestrator.resume_workflow(workflow_id="abc-123")
```

#### Create Checkpoint

```python
# Create named checkpoint
await orchestrator.create_checkpoint(
    workflow_id="abc-123",
    checkpoint_name="before_external_api_call"
)
```

#### Batch Recovery

```python
# Recover multiple failed workflows
recovered_ids = await orchestrator.batch_recover_failed_workflows(max_workflows=10)
```

### Troubleshooting

#### Issue: Semantic similarity not working

**Symptom**: Logs show "OpenAI client not available"

**Fix**:

```bash
# Add to .env
OPENAI_API_KEY=sk-...
```

#### Issue: Continuation misdetection

**Symptom**: "What about today?" returns wrong results

**Fix**:

1. Check last action status
2. Verify intent similarity
3. Review continuation configuration
4. Check semantic similarity scores

#### Issue: Workflow execution fails

**Symptom**: Workflow errors with no recovery

**Fix**:

1. Check error type (recoverable vs non-recoverable)
2. Verify isolation enabled
3. Check state manager connection
4. Review error boundary logs

---

## Appendix

### Key Files Reference

- **Orchestrator**: `backend/app/agents/orchestrator.py`
- **Intent Processor**: `backend/app/agents/core/orchestration/intent_processor.py`
- **Continuation**: `backend/app/agents/core/orchestration/continuation.py`
- **Planning Handler**: `backend/app/agents/services/planning_handler.py`
- **Action Executor**: `backend/app/agents/services/action_executor.py`
- **Supervisor**: `backend/app/agents/services/supervisor.py`
- **Base Workflow**: `backend/app/agents/graphs/base.py`
- **Workflow Driver**: `backend/app/agents/core/orchestration/driver.py`

### Related Documentation

- [Conversation Continuation System](./CONVERSATION_CONTINUATION_SYSTEM.md)
- [Agent Implementation Roadmap](../08-plans/AGENT_IMPLEMENTATION.md)
- [Workflow Automation System](../08-plans/WORKFLOW.md)
- [Architecture Overview](../02-architecture/ARCHITECTURE.md)

### Glossary

- **NLU**: Natural Language Understanding
- **ONNX**: Open Neural Network Exchange (model format)
- **LangGraph**: Workflow orchestration framework
- **Gate**: User confirmation/clarification checkpoint
- **Continuation**: Follow-up query that modifies/continues previous action
- **Slot Fill**: Providing missing information for pending action
- **Action Record**: Database record tracking user intent and execution
- **Workflow Container**: Isolated execution environment for workflows
- **Checkpoint**: Saved state for workflow resumption

---

**Document Maintainer**: AI Agent System Team  
**Last Review Date**: 2025-01-28  
**Next Review Date**: 2025-02-28
