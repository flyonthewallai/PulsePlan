# 🧭 Conversational Scheduling Confirmation System — Implementation Plan

**Goal:** Implement a context-aware, conversational scheduling confirmation system that never auto-executes high-impact scheduling operations without user permission, while leveraging rich user context from memory, hobbies, and preferences.

---

## 🎯 Guiding Principles

### ✅ Core Rules

1. **Never auto-execute scheduling without explicit user permission**
   - Scheduling is high-impact (affects multiple calendar events/timeblocks)
   - System must understand intent deeply before proceeding
   - Conversational confirmation is the default path

2. **Power users opt-in to automation via Workflows system**
   - Users who want auto-scheduling create a workflow (see `plans/WORKFLOW.md`)
   - Workflows system handles `confirmation_mode: 'silent'` for trusted automations
   - Separates one-off scheduling requests from recurring automation

3. **Rich context drives intelligent planning**
   - Retrieve user preferences from vector memory (see `plans/MEMORY.md`)
   - Query hobbies table for time preferences and constraints
   - Use scheduler_preferences for working hours and penalties
   - Access conversation history for learned preferences

4. **Graceful conversational flow**
   - Extract what we can from the query
   - Ask targeted clarifying questions for missing context
   - Summarize understanding before creating schedule
   - Present visual preview with rationale
   - Confirm before execution

---

## 🧩 System Architecture

### Layer 1: Intent Recognition + Slot Extraction

**Current State:**
- ✅ `schedule_period` intent with 0.95 confidence (high-precision rules)
- ✅ `timeframe` slot extractor (this week, next month, etc.)
- ✅ NLU service extracts slots even for rule matches

**Enhancement Needed:**
- Extract constraints from natural language (e.g., "I have football Saturday night")
- Identify preferences (e.g., "I want to study 12 hours Sunday")
- Recognize explicit confirmation signals (e.g., "yes, go ahead")

### Layer 2: Context Retrieval (Memory + Database)

**Retrieve from multiple sources:**

1. **Vector Memory (Semantic Search)**
   - Namespace: `profile_snapshot` - Weekly behavior stats, learned preferences
   - Namespace: `preferences` - Explicit user preferences stored from NLU
   - Namespace: `chat_summary` - Relevant past conversations about scheduling
   - Query: "user scheduling preferences, hobbies, working hours, constraints"

2. **Structured Database**
   - `user_hobbies` - Preferred times, days, duration ranges, flexibility
   - `scheduler_preferences` - Working hours, break intervals, deep work windows
   - `users.preferences` - Study/work preferences JSONB
   - `integration_settings.instructions` - Custom instructions per integration

3. **Ephemeral Conversation State**
   - Redis `ConversationState` - Current workflow context
   - Accumulated clarifications from multi-turn dialogue
   - Pending schedule drafts

**Implementation:**

```python
# File: backend/app/agents/services/scheduling_context_builder.py

from app.memory.retrieval.retrieval import RetrievalService
from app.database.hobbies_repository import HobbiesRepository
from app.database.repository import get_scheduler_preferences

class SchedulingContextBuilder:
    """Builds rich context for scheduling operations"""

    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.hobbies_repo = HobbiesRepository()

    async def build_context(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Build comprehensive scheduling context from all sources.

        Returns:
            {
                "vector_memories": [...],      # Learned preferences from memory
                "hobbies": [...],               # Structured hobby constraints
                "scheduler_prefs": {...},       # Working hours, penalties
                "user_preferences": {...},      # Study/work preferences
                "conversation_history": [...],  # Relevant past conversations
                "confidence_score": 0.85        # How complete is this context?
            }
        """
        # 1. Semantic search in vector memory
        vector_context = await self.retrieval_service.search_similar_context(
            user_id=user_id,
            query=f"scheduling preferences, constraints, hobbies, working hours: {query}",
            namespaces=["profile_snapshot", "preferences", "chat_summary"],
            limit=10
        )

        # 2. Query hobbies table
        hobbies = await self.hobbies_repo.get_active_hobbies(user_id)

        # 3. Get scheduler preferences
        scheduler_prefs = await get_scheduler_preferences(user_id)

        # 4. Get user general preferences
        user = await get_user(user_id)
        user_preferences = {
            "study_preferences": user.study_preferences,
            "work_preferences": user.work_preferences,
            "working_hours": user.working_hours,
            "timezone": user.timezone
        }

        # 5. Calculate confidence score
        confidence = self._calculate_context_confidence(
            vector_context, hobbies, scheduler_prefs
        )

        return {
            "vector_memories": vector_context,
            "hobbies": hobbies,
            "scheduler_prefs": scheduler_prefs,
            "user_preferences": user_preferences,
            "confidence_score": confidence
        }

    def _calculate_context_confidence(
        self, vector_context, hobbies, scheduler_prefs
    ) -> float:
        """
        Calculate how confident we are in the context completeness.

        Scoring:
        - Has working hours: +0.3
        - Has hobbies: +0.2
        - Has vector memories: +0.3
        - Has scheduler prefs: +0.2
        """
        score = 0.0

        if scheduler_prefs and scheduler_prefs.get("workday_start"):
            score += 0.3

        if hobbies and len(hobbies) > 0:
            score += 0.2

        if vector_context and len(vector_context) > 0:
            score += 0.3

        if scheduler_prefs:
            score += 0.2

        return min(score, 1.0)
```

### Layer 3: Conversational Clarification Manager

**Purpose:** Orchestrate multi-turn dialogue to gather missing information

**Implementation:**

```python
# File: backend/app/agents/services/scheduling_clarification_manager.py

from app.core.llm.client import get_llm_client
from app.agents.core.conversation.conversation_state_manager import (
    ConversationStateManager,
    ClarificationRequest
)

class SchedulingClarificationManager:
    """Manages conversational clarification for scheduling"""

    def __init__(self):
        self.llm_client = get_llm_client()
        self.state_manager = ConversationStateManager()

    async def check_context_completeness(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        context: Dict[str, Any],
        extracted_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if we have enough context to proceed with scheduling.

        Returns:
            {
                "complete": bool,
                "missing_fields": [...],
                "clarification_question": str | None,
                "confidence": float
            }
        """
        # Build prompt for LLM to assess completeness
        system_prompt = """You are a scheduling assistant that determines if you have enough information to create a schedule.

Given:
- User's query
- Retrieved context (hobbies, preferences, past behavior)
- Extracted parameters

Determine:
1. Is the information complete enough to proceed?
2. What critical information is missing (if any)?
3. What ONE concise clarifying question should we ask?

Response format:
{
    "complete": true/false,
    "missing_fields": ["constraints", "study_hours"],
    "clarification_question": "Do you have any fixed events this week I should work around?",
    "reasoning": "We know working hours but not specific constraints"
}
"""

        user_prompt = f"""Query: {query}

Retrieved Context:
- Hobbies: {len(context.get('hobbies', []))} active hobbies
- Working Hours: {context.get('user_preferences', {}).get('working_hours')}
- Past Preferences: {len(context.get('vector_memories', []))} memory entries
- Context Confidence: {context.get('confidence_score', 0.0)}

Extracted Parameters:
- Timeframe: {extracted_params.get('timeframe')}
- Hard Constraints: {len(extracted_params.get('hard_constraints', []))}
- Soft Constraints: {len(extracted_params.get('soft_constraints', []))}

Assess completeness and suggest ONE clarifying question if needed."""

        response = await self.llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        result = json.loads(response["content"])

        # Store clarification in conversation state if incomplete
        if not result["complete"]:
            await self._store_pending_clarification(
                user_id=user_id,
                conversation_id=conversation_id,
                clarification=result
            )

        return result

    async def _store_pending_clarification(
        self,
        user_id: str,
        conversation_id: str,
        clarification: Dict[str, Any]
    ):
        """Store clarification request in conversation state"""
        state = await self.state_manager.get_state(user_id, conversation_id)

        clarification_request = ClarificationRequest(
            field=clarification["missing_fields"][0] if clarification["missing_fields"] else "general",
            question=clarification["clarification_question"],
            context=clarification
        )

        state.pending_clarifications.append(clarification_request)
        await self.state_manager.save_state(state)
```

### Layer 4: Schedule Planning with Rationale

**Purpose:** Generate schedule plan with LLM reasoning

**Implementation:**

```python
# File: backend/app/agents/services/schedule_planner.py

class SchedulePlanner:
    """Creates schedule plans with explanatory rationale"""

    async def create_plan(
        self,
        user_id: str,
        timeframe: tuple,
        context: Dict[str, Any],
        tasks: List[Dict],
        availability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a schedule plan using OR-Tools + LLM rationale.

        Returns:
            {
                "timeblocks": [...],
                "rationale": "I scheduled your workout at 8 AM because...",
                "conflicts": [...],
                "alternatives": [...],
                "confidence": 0.9
            }
        """
        # 1. Run OR-Tools optimization
        from app.scheduler.core.service import SchedulerService

        scheduler = SchedulerService()
        schedule_response = await scheduler.schedule(
            user_id=user_id,
            horizon_days=(timeframe[1] - timeframe[0]).days,
            dry_run=True  # Don't persist yet
        )

        # 2. Generate LLM rationale
        rationale = await self._generate_rationale(
            context=context,
            schedule=schedule_response.blocks,
            tasks=tasks
        )

        return {
            "timeblocks": [block.dict() for block in schedule_response.blocks],
            "rationale": rationale,
            "conflicts": schedule_response.conflicts,
            "alternatives": schedule_response.alternatives,
            "confidence": schedule_response.confidence_score
        }

    async def _generate_rationale(
        self,
        context: Dict[str, Any],
        schedule: List,
        tasks: List[Dict]
    ) -> str:
        """Generate human-readable rationale for scheduling decisions"""

        system_prompt = """You are a scheduling assistant explaining your decisions.

Given:
- User preferences and hobbies
- Generated schedule
- Task list

Explain in 2-3 sentences WHY you made key scheduling decisions, referencing:
- User preferences ("I scheduled your workout at 8 AM because you prefer morning exercise")
- Task urgency ("Study session for Algorithms on Sunday due to Monday deadline")
- Optimization trade-offs ("I balanced deep work time with break intervals")

Be conversational and personal."""

        user_prompt = f"""User Context:
{json.dumps(context, indent=2)}

Generated Schedule:
{json.dumps([{
    'task': block.title,
    'start': block.start_time.isoformat(),
    'duration': block.duration_minutes
} for block in schedule[:5]], indent=2)}

Tasks to Schedule:
{json.dumps([{
    'title': t['title'],
    'due_date': t.get('due_date'),
    'priority': t.get('priority')
} for t in tasks[:5]], indent=2)}

Explain your scheduling decisions:"""

        response = await self.llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        return response["content"]
```

### Layer 5: Confirmation Gate with Visual Preview

**Purpose:** Present schedule for user confirmation before execution

**Current System:**
- ✅ `pending_gates` table with `required_confirmations` JSONB
- ✅ Gate endpoints: `POST /gates/{token}/confirm`, `POST /gates/{token}/cancel`
- ✅ Gate expiration (10 minute TTL)

**Enhancement:**

```python
# File: backend/app/agents/services/scheduling_gate_service.py

class SchedulingGateService:
    """Creates and manages scheduling confirmation gates"""

    async def create_scheduling_gate(
        self,
        user_id: str,
        action_id: str,
        schedule_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Create a scheduling confirmation gate.

        Args:
            schedule_plan: Output from SchedulePlanner.create_plan()
            context: Full user context from SchedulingContextBuilder

        Returns:
            gate_token: Unique token for confirmation
        """
        gate_token = generate_token()

        # Prepare confirmation data for frontend
        required_confirmations = {
            "schedule_preview": {
                "timeblocks": schedule_plan["timeblocks"],
                "rationale": schedule_plan["rationale"],
                "conflicts": schedule_plan.get("conflicts", []),
                "alternatives": schedule_plan.get("alternatives", [])
            },
            "context_used": {
                "hobbies": [h["name"] for h in context["hobbies"]],
                "working_hours": context["user_preferences"]["working_hours"],
                "preferences_count": len(context["vector_memories"])
            },
            "modification_allowed": True,
            "visualization_data": self._prepare_calendar_view(
                schedule_plan["timeblocks"]
            )
        }

        policy_reasons = [
            f"Scheduling {len(schedule_plan['timeblocks'])} timeblocks across multiple days",
            f"Using {len(context['hobbies'])} hobbies and {len(context['vector_memories'])} learned preferences",
            "High-impact operation requires confirmation"
        ]

        # Create gate record
        await gate_repo.create_pending_gate(
            action_id=action_id,
            gate_token=gate_token,
            intent="schedule_period",
            required_confirmations=required_confirmations,
            policy_reasons=policy_reasons,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )

        return gate_token

    def _prepare_calendar_view(self, timeblocks: List[Dict]) -> Dict[str, Any]:
        """
        Prepare data for frontend calendar visualization.

        Returns structured data for week/day grid rendering.
        """
        # Group by day
        days = {}
        for block in timeblocks:
            day = datetime.fromisoformat(block["start_time"]).date().isoformat()
            if day not in days:
                days[day] = []
            days[day].append({
                "title": block["title"],
                "start": block["start_time"],
                "end": block["end_time"],
                "duration": block["duration_minutes"],
                "color": block.get("color", "#3B82F6")
            })

        return {
            "days": days,
            "range": {
                "start": min(timeblocks, key=lambda x: x["start_time"])["start_time"],
                "end": max(timeblocks, key=lambda x: x["end_time"])["end_time"]
            }
        }
```

### Layer 6: Integration with Workflows System

**User Personas:**

1. **Manual Scheduler (Default)**
   - Makes one-off scheduling requests: "create my schedule for this week"
   - Always gets conversational confirmation
   - Flow: Intent → Context → Clarify → Plan → Gate → Confirm → Execute

2. **Power User (Workflow Automation)**
   - Creates workflow: "Every Sunday 6 PM → schedule next week"
   - Opts into `confirmation_mode: 'silent'` or `'summary'`
   - Flow: Workflow Trigger → Execute → Summary Notification

**Decision Logic:**

```python
# File: backend/app/agents/services/action_executor.py (enhanced)

async def _execute_period_scheduling(
    self,
    user_id: str,
    params: Dict[str, Any],
    action_id: Optional[str] = None,
    workflow_mode: bool = False,
    confirmation_mode: str = "require"  # 'require', 'summary', 'silent'
) -> ExecutionResult:
    """
    Execute period scheduling with configurable confirmation.

    Args:
        workflow_mode: True if triggered by user_workflows system
        confirmation_mode: How to handle confirmation
            - 'require': Create gate, wait for user confirmation (default)
            - 'summary': Execute then send summary with undo option
            - 'silent': Execute directly, no confirmation
    """
    # 1. Build rich context
    context_builder = SchedulingContextBuilder()
    context = await context_builder.build_context(user_id, params["original_query"])

    # 2. Extract scheduling parameters
    extractor = get_param_extractor()
    scheduling_params = await extractor(
        user_message=params["original_query"],
        entities=params,
        context=context  # Pass context to extractor
    )

    # 3. Check completeness (conversational flow)
    if not workflow_mode and confirmation_mode == "require":
        clarification_mgr = SchedulingClarificationManager()
        completeness = await clarification_mgr.check_context_completeness(
            user_id=user_id,
            conversation_id=params.get("conversation_id"),
            query=params["original_query"],
            context=context,
            extracted_params=scheduling_params.dict()
        )

        # If incomplete, return clarifying question
        if not completeness["complete"]:
            return ExecutionResult(
                success=False,
                message=completeness["clarification_question"],
                data={"pending_clarification": True},
                requires_followup=True
            )

    # 4. Create schedule plan with rationale
    planner = SchedulePlanner()
    schedule_plan = await planner.create_plan(
        user_id=user_id,
        timeframe=self._parse_timeframe(scheduling_params.timeframe, user_id),
        context=context,
        tasks=await get_user_tasks(user_id),
        availability=await get_availability(user_id)
    )

    # 5. Handle confirmation based on mode
    if confirmation_mode == "silent":
        # Workflow: auto-execute
        result = await self._commit_schedule(user_id, schedule_plan)
        return ExecutionResult(
            success=True,
            message=f"Scheduled {len(schedule_plan['timeblocks'])} blocks",
            data=result
        )

    elif confirmation_mode == "summary":
        # Workflow: execute then notify
        result = await self._commit_schedule(user_id, schedule_plan)
        await self._send_summary_notification(
            user_id=user_id,
            schedule_plan=schedule_plan,
            result=result
        )
        return ExecutionResult(
            success=True,
            message="Schedule created, summary sent",
            data=result
        )

    else:  # confirmation_mode == "require"
        # Manual: create gate for confirmation
        gate_service = SchedulingGateService()
        gate_token = await gate_service.create_scheduling_gate(
            user_id=user_id,
            action_id=action_id,
            schedule_plan=schedule_plan,
            context=context
        )

        return ExecutionResult(
            success=False,  # Not executed yet
            message=f"Schedule ready for review: {schedule_plan['rationale']}",
            data={
                "gate_token": gate_token,
                "preview": schedule_plan,
                "requires_confirmation": True
            }
        )
```

---

## 🔄 Complete User Flow Examples

### Example 1: First-Time Scheduler (Manual, Conversational)

**User:** "create my schedule for this week"

**System Flow:**

1. **Intent Recognition**
   - Match: `schedule_period` (0.95 confidence)
   - Extract: `timeframe = "this_week"`

2. **Context Retrieval**
   - Query vector memory → 0 entries (new user)
   - Query hobbies → 0 entries
   - Query scheduler_prefs → default working hours
   - Context confidence: 0.3 (low)

3. **Clarification**
   - LLM assesses: "Missing critical information"
   - Question: "I'll create your schedule for this week. First, do you have any fixed events or specific times I should avoid? (like classes, meetings, or workouts)"

4. **User Response:** "I have football practice Saturday 6-8 PM"

5. **Context Update**
   - Add hard constraint: `{"type": "event_block", "day": "Saturday", "time": "18:00-20:00"}`
   - Re-assess completeness

6. **Second Clarification**
   - Question: "Got it — football Saturday evening. How many hours per day would you like to dedicate to studying?"

7. **User Response:** "about 6 hours each day"

8. **Planning**
   - Run OR-Tools with constraints
   - Generate rationale: "I scheduled your study sessions in 2-hour blocks throughout the week, avoiding Saturday evening for your football practice. I prioritized mornings when possible based on typical productivity patterns."

9. **Gate Creation**
   - Create confirmation gate with visual calendar preview
   - Frontend displays week view with proposed timeblocks

10. **User Confirmation:** "looks good, confirm"

11. **Execution**
    - Commit timeblocks to database
    - Store preferences in vector memory
    - Return success

---

### Example 2: Power User (Workflow Automation)

**Setup:**

User creates workflow via UI:
- Name: "Sunday Weekly Planner"
- Trigger: Every Sunday 6:00 PM
- Action: `schedule_period` with `timeframe: "next_week"`
- Confirmation Mode: **Summary**
- Active: ✅ (Premium)

**System Flow:**

1. **Trigger Detection**
   - Background worker detects workflow is due
   - Extracts workflow actions

2. **Context Retrieval**
   - Query vector memory → 15 entries (learned preferences over time)
   - Query hobbies → 3 active hobbies (gym, reading, cooking)
   - Query scheduler_prefs → custom working hours, penalties
   - Context confidence: 0.9 (high)

3. **Planning (No Clarification)**
   - Skip clarification (workflow mode + summary mode)
   - Run OR-Tools with full context
   - Generate rationale

4. **Auto-Execute**
   - Commit schedule directly to database
   - No gate created

5. **Summary Notification**
   - Send push notification: "✅ Your schedule for next week is ready"
   - Include summary: "Scheduled 7 study sessions, 3 gym blocks, and 2 cooking sessions based on your preferences"
   - Provide undo link (expires in 1 hour)

---

## 🧩 Database Schema Updates

### 1. Add `custom_instructions` to Users

```sql
-- Migration: add_custom_instructions_to_users.sql

ALTER TABLE users
ADD COLUMN custom_instructions TEXT;

COMMENT ON COLUMN users.custom_instructions IS
'Freeform user profile for AI context (e.g., "I''m a morning person, prefer workouts before 10 AM")';
```

### 2. Extend `action_records` for Context Tracking

```sql
-- Migration: extend_action_records_for_context.sql

ALTER TABLE action_records
ADD COLUMN context_snapshot JSONB DEFAULT '{}';

COMMENT ON COLUMN action_records.context_snapshot IS
'Snapshot of context used for this action (hobbies, preferences, memory entries)';
```

---

## 🧠 Memory Integration Plan (from plans/MEMORY.md)

### Phase 1: Auto-Ingest User Preferences into Vector Memory

**Trigger Points:**

1. **After successful scheduling** → Store learned preferences
2. **User updates hobbies** → Embed hobby preferences
3. **Weekly profile snapshot** → Aggregate weekly behavior

**Implementation:**

```python
# File: backend/app/agents/hooks/post_scheduling_hook.py

async def post_scheduling_hook(
    user_id: str,
    action_id: str,
    schedule_plan: Dict[str, Any],
    user_feedback: Optional[str] = None
):
    """
    Hook that runs after successful scheduling to learn preferences.

    Stores:
    - Time preferences ("user prefers morning study sessions")
    - Constraint patterns ("user always has football Saturday evenings")
    - Feedback insights ("user adjusted workout from 8 AM to 10 AM → prefers later workouts")
    """
    from app.memory.retrieval.vector_memory import VectorMemoryService

    vector_memory = VectorMemoryService()

    # Extract preference statements from schedule
    preferences = _extract_preference_statements(schedule_plan, user_feedback)

    for pref in preferences:
        await vector_memory.upsert_memory(
            user_id=user_id,
            namespace="preferences",
            doc_id=f"pref:scheduling:{action_id}:{uuid4()}",
            content=pref["statement"],
            metadata={
                "source": "scheduling_action",
                "confidence": pref["confidence"],
                "action_id": action_id,
                "category": pref["category"]  # time_preference, constraint, habit
            }
        )

def _extract_preference_statements(
    schedule_plan: Dict,
    user_feedback: Optional[str]
) -> List[Dict]:
    """
    Extract learnable preference statements from schedule and feedback.

    Examples:
    - "User prefers study sessions in morning hours (8 AM - 12 PM)"
    - "User has recurring football practice Saturday 6-8 PM"
    - "User adjusted workout from 8 AM to 10 AM, prefers later morning exercise"
    """
    statements = []

    # Analyze time distribution
    morning_blocks = [b for b in schedule_plan["timeblocks"]
                     if 6 <= datetime.fromisoformat(b["start_time"]).hour < 12]

    if len(morning_blocks) > len(schedule_plan["timeblocks"]) * 0.6:
        statements.append({
            "statement": "User prefers morning study sessions (6 AM - 12 PM)",
            "confidence": 0.8,
            "category": "time_preference"
        })

    # Analyze recurring constraints
    hard_constraints = schedule_plan.get("hard_constraints", [])
    for constraint in hard_constraints:
        if constraint.get("type") == "event_block":
            statements.append({
                "statement": f"User has recurring {constraint['name']} on {constraint['day']} at {constraint['time_range']}",
                "confidence": 0.95,
                "category": "constraint"
            })

    # Parse user feedback
    if user_feedback and "adjusted" in user_feedback.lower():
        # LLM-based extraction of adjustment preferences
        statements.append({
            "statement": f"User feedback: {user_feedback}",
            "confidence": 0.9,
            "category": "feedback"
        })

    return statements
```

### Phase 2: Hobby Ingestion Worker

```python
# File: backend/app/workers/memory_ingestion_worker.py

from app.database.hobbies_repository import HobbiesRepository
from app.memory.retrieval.vector_memory import VectorMemoryService

async def ingest_user_hobbies(user_id: str):
    """
    Background worker that embeds user hobbies into vector memory.

    Runs:
    - On hobby create/update
    - Daily at midnight (full sync)
    """
    hobbies_repo = HobbiesRepository()
    vector_memory = VectorMemoryService()

    hobbies = await hobbies_repo.get_active_hobbies(user_id)

    for hobby in hobbies:
        # Convert hobby to natural language statement
        statement = _hobby_to_statement(hobby)

        await vector_memory.upsert_memory(
            user_id=user_id,
            namespace="profile_snapshot",
            doc_id=f"hobby:{hobby['id']}",
            content=statement,
            metadata={
                "source": "hobby_table",
                "hobby_id": hobby["id"],
                "category": "habit"
            }
        )

def _hobby_to_statement(hobby: Dict) -> str:
    """
    Convert hobby record to natural language.

    Example:
    {
        "name": "Gym",
        "preferred_time": "morning",
        "days": ["Monday", "Wednesday", "Friday"],
        "duration_min": 60,
        "duration_max": 90
    }

    → "User has gym habit on Monday, Wednesday, Friday mornings, typically 60-90 minutes"
    """
    days_str = ", ".join(hobby.get("days", []))
    time_str = hobby.get("preferred_time", "any time")
    duration_str = f"{hobby.get('duration_min')}-{hobby.get('duration_max')} minutes"

    return (
        f"User has {hobby['name']} habit on {days_str} {time_str}, "
        f"typically {duration_str}"
    )
```

---

## 📋 Implementation Checklist

### Phase 1: Core Infrastructure (2-3 days)

- [ ] Create `SchedulingContextBuilder` service
- [ ] Create `SchedulingClarificationManager` service
- [ ] Create `SchedulePlanner` service with rationale generation
- [ ] Create `SchedulingGateService` for confirmation gates
- [ ] Add `custom_instructions` field to users table
- [ ] Extend `action_records` with `context_snapshot`

### Phase 2: Memory Integration (1-2 days)

- [ ] Implement `post_scheduling_hook` for preference learning
- [ ] Create `memory_ingestion_worker` for hobby embedding
- [ ] Add background job for daily hobby ingestion
- [ ] Implement preference extraction from feedback

### Phase 3: Action Executor Enhancement (1-2 days)

- [ ] Update `_execute_period_scheduling` with confirmation modes
- [ ] Add workflow integration (`workflow_mode`, `confirmation_mode`)
- [ ] Implement context-aware parameter extraction
- [ ] Add rationale generation to schedule planning

### Phase 4: API Endpoints (1 day)

- [ ] Create `POST /api/v1/scheduling/preview` - Generate schedule preview without execution
- [ ] Enhance `POST /gates/{token}/confirm` - Support schedule modifications
- [ ] Create `POST /api/v1/scheduling/feedback` - Collect user feedback for learning

### Phase 5: Frontend Integration (3-4 days)

- [ ] Create `SchedulePreviewModal.tsx` - Visual calendar preview
- [ ] Enhance `GateConfirmationModal.tsx` - Support schedule visualization
- [ ] Add schedule modification UI (drag timeblocks to adjust)
- [ ] Implement feedback collection after scheduling
- [ ] Add custom instructions field to settings page

### Phase 6: Testing & Refinement (2 days)

- [ ] Test conversational flow with clarifications
- [ ] Test workflow automation (silent/summary modes)
- [ ] Test memory learning and retrieval
- [ ] Test context confidence scoring
- [ ] Load testing for OR-Tools performance

---

## 🧪 Testing Scenarios

### Scenario 1: New User, No Context

**Given:** User has no hobbies, no preferences, no history
**When:** User says "create my schedule for this week"
**Then:**
1. System asks for constraints
2. System asks for study hours preference
3. System generates basic schedule
4. System stores learned preferences in vector memory

**Assertions:**
- `context_confidence` < 0.4
- At least 2 clarifying questions asked
- After confirmation, 2+ preference entries in vector memory

---

### Scenario 2: Power User, Rich Context

**Given:** User has 3 hobbies, 10+ vector memory entries, scheduler prefs
**When:** User says "plan my next week"
**Then:**
1. System retrieves full context
2. System generates schedule immediately (no clarification)
3. System creates gate with rationale referencing hobbies/prefs
4. Rationale mentions specific user preferences

**Assertions:**
- `context_confidence` > 0.8
- Zero clarifying questions
- Rationale length > 100 chars
- Rationale mentions at least 1 hobby or preference

---

### Scenario 3: Workflow Automation (Silent Mode)

**Given:** User has active workflow with `confirmation_mode: 'silent'`
**When:** Workflow trigger fires (Sunday 6 PM)
**Then:**
1. System retrieves context
2. System generates schedule
3. System commits to database immediately
4. No gate created
5. User receives notification

**Assertions:**
- No gate record created
- Timeblocks inserted within 10 seconds of trigger
- Notification sent to user
- Action record status = `completed`

---

## 🚀 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Confirmation Rate** | > 80% | % of gates confirmed vs. cancelled |
| **Clarification Efficiency** | < 3 questions avg | Avg. clarifying questions before confirmation |
| **Context Confidence** | > 0.7 after 1 week | Avg. context confidence for users with 7+ days activity |
| **Workflow Adoption** | 30% of premium users | % premium users with at least 1 active workflow |
| **Memory Accuracy** | > 85% | % of retrieved memories relevant to scheduling (manual eval) |
| **Execution Time** | < 5 seconds | Time from "confirm" to schedule committed |

---

## 🔮 Future Enhancements

### Phase 2: Advanced Context

- **Multi-week optimization** - Plan 2-4 weeks ahead with semester-aware scheduling
- **Conditional constraints** - "If I have >3 tasks on Monday, reschedule low-priority to Tuesday"
- **Collaboration context** - "Schedule study group sessions when John and Sarah are available"

### Phase 3: Workflow Intelligence

- **AI-triggered workflows** - "If user falls behind on tasks → auto-reschedule weekend"
- **Adaptive confirmation** - Learn when user prefers confirmation vs. auto-execution
- **Workflow templates** - Community-shared workflow patterns

### Phase 4: Memory Evolution

- **Conversation summaries** - Auto-summarize scheduling discussions into `chat_summary` namespace
- **Preference drift detection** - Detect when user behavior changes and update preferences
- **Cross-session learning** - "You usually study algorithms on Sundays, should I prioritize that?"

---

## 📚 References

- **Workflow System**: `/plans/WORKFLOW.md`
- **Memory Architecture**: `/plans/MEMORY.md`
- **Current Conversation State**: `/backend/app/agents/core/conversation/conversation_state_manager.py`
- **Existing Gate System**: `/backend/app/api/v1/endpoints/agent_modules/gates.py`
- **OR-Tools Scheduler**: `/backend/app/scheduler/core/service.py`
- **Vector Memory Service**: `/backend/app/memory/retrieval/vector_memory.py`

---

**End of Implementation Plan**
