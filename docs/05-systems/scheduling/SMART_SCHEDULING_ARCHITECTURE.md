# PulsePlan Smart Scheduling Architecture

**Version:** 1.0.0
**Last Updated:** October 29, 2025
**Authors:** PulsePlan Engineering Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Two-Tier Architecture](#two-tier-architecture)
4. [Decision Flow](#decision-flow)
5. [Tier 1: Smart Slot Finder](#tier-1-smart-slot-finder)
6. [Tier 2: Main Constraint Scheduler](#tier-2-main-constraint-scheduler)
7. [Integration Guide](#integration-guide)
8. [API Reference](#api-reference)
9. [Performance Metrics](#performance-metrics)
10. [Future Enhancements](#future-enhancements)

---

## Executive Summary

PulsePlan employs a **two-tier scheduling architecture** designed to optimize both user experience and computational efficiency:

- **Tier 1 (Smart Slot Finder)**: Fast, heuristic-based scheduling for single events with short time horizons (≤1 day ahead)
- **Tier 2 (Main Scheduler)**: Constraint-based optimization for bulk scheduling and long-term planning (>1 day ahead)

This architecture ensures sub-second response times for immediate scheduling requests while maintaining sophisticated constraint satisfaction for complex, multi-event optimization scenarios.

**Key Benefits:**

- ⚡️ **Sub-500ms response time** for single-event scheduling
- 🎯 **High accuracy** through hybrid rule-based + LLM approach
- 🧠 **Adaptive intelligence** with confidence-based decision making
- 📊 **Explainability** via detailed rationale for all scheduling decisions
- 🔄 **Unified interface** for both new scheduling and rescheduling operations

---

## System Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Intent (NLU)                        │
│         "Schedule bio study for Friday afternoon"           │
│           "Move team meeting to tomorrow 2pm"               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Scheduling Router                          │
│                                                             │
│  Decision Logic:                                            │
│  • Days ahead ≤ 1 → Tier 1 (Smart Slot Finder)            │
│  • Days ahead > 1 → Tier 2 (Main Scheduler)               │
│  • Bulk operations → Tier 2                                │
└────────────┬──────────────────────────┬─────────────────────┘
             │                          │
             ▼                          ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│   Tier 1: Smart Slot   │  │  Tier 2: Main Scheduler     │
│       Finder            │  │   (OR-Tools CP-SAT)          │
│                         │  │                              │
│  • Rule-based          │  │  • Constraint programming    │
│  • Heuristic scoring   │  │  • Multi-objective optim.    │
│  • LLM fallback        │  │  • Bulk operations           │
│  • <500ms latency      │  │  • 2-10s latency            │
└─────────────────────────┘  └──────────────────────────────┘
             │                          │
             └──────────┬───────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              SchedulingResult + Rationale                   │
│                                                             │
│  • Chosen time slot                                         │
│  • Confidence score                                         │
│  • Decision rationale                                       │
│  • Alternative options (if applicable)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Two-Tier Architecture

### Design Philosophy

The two-tier design optimizes for different use cases:

| Aspect                 | Tier 1 (Smart Slot Finder)               | Tier 2 (Main Scheduler)          |
| ---------------------- | ---------------------------------------- | -------------------------------- |
| **Time Horizon**       | ≤ 1 day ahead                            | > 1 day ahead                    |
| **Scope**              | Single event                             | Multiple events                  |
| **Method**             | Heuristics + LLM                         | Constraint programming           |
| **Latency**            | < 500ms                                  | 2-10 seconds                     |
| **Optimization Depth** | Local (nearby slots)                     | Global (entire schedule)         |
| **Use Cases**          | Quick rescheduling, immediate scheduling | Weekly planning, bulk scheduling |

### When to Use Each Tier

#### Use Tier 1 (Smart Slot Finder) When:

✅ User wants to schedule/reschedule a **single event**
✅ Target time is **within 1 day** from now
✅ **Speed is critical** (real-time user interaction)
✅ Simple conflict resolution is sufficient

**Examples:**

- "Move bio study block to this afternoon"
- "Schedule team meeting for tomorrow at 2pm"
- "Reschedule lunch to 1pm today"

#### Use Tier 2 (Main Scheduler) When:

✅ User wants to schedule **multiple events** at once
✅ Target time is **>1 day ahead**
✅ **Optimization quality** is more important than speed
✅ Complex constraints need to be satisfied (priorities, dependencies, etc.)

**Examples:**

- "Schedule all my assignments for next week"
- "Plan my study sessions for the entire semester"
- "Optimize my weekly meeting schedule"

---

## Decision Flow

### Routing Logic

```python
from datetime import datetime, timedelta

def route_scheduling_request(
    event_info: Dict[str, Any],
    target_time: datetime,
    user_id: str
) -> SchedulingResult:
    """
    Route scheduling request to appropriate tier.

    Decision Factors:
    1. Time horizon (days ahead)
    2. Number of events (single vs bulk)
    3. Complexity of constraints
    """
    # Always derive "now" in the user's timezone via TimezoneManager
    from app.core.utils.timezone_utils import get_timezone_manager
    tz_mgr = get_timezone_manager()
    now = tz_mgr.convert_to_user_timezone(datetime.utcnow(), user_timezone)
    days_ahead = (target_time - now).days
    is_bulk = isinstance(event_info, list) or event_info.get("bulk", False)

    # Tier 1: Fast single-event scheduling
    if not is_bulk and days_ahead <= 1:
        return await smart_slot_finder.find_optimal_slot(
            preferred_time=target_time,
            duration_minutes=event_info["duration"],
            user_id=user_id,
            event_title=event_info["title"]
        )

    # Tier 2: Constraint-based optimization
    else:
        return await main_scheduler.schedule_with_constraints(
            events=event_info if is_bulk else [event_info],
            user_id=user_id,
            start_date=target_time,
            end_date=target_time + timedelta(days=7)
        )
```

### Decision Tree

```
┌─────────────────────────┐
│  Scheduling Request     │
└───────────┬─────────────┘
            │
            ▼
      ┌───────────┐
      │ Bulk?     │────Yes───┐
      └─────┬─────┘          │
            No               │
            ▼                │
      ┌───────────┐          │
      │ Days > 1? │────Yes───┤
      └─────┬─────┘          │
            No               │
            ▼                ▼
      ┌─────────────┐  ┌─────────────┐
      │   Tier 1    │  │   Tier 2    │
      │ Smart Slot  │  │    Main     │
      │   Finder    │  │  Scheduler  │
      └─────────────┘  └─────────────┘
```

---

## Tier 1: Smart Slot Finder

### Overview

The Smart Slot Finder is a **fast, heuristic-based scheduling service** designed for real-time single-event scheduling and rescheduling operations.

**Location:** `backend/app/services/scheduling/smart_slot_finder.py`

### Core Algorithm

The Smart Slot Finder uses a **four-step decision pipeline**:

```
┌──────────────────────────────────────────────────────────────┐
│ Step 1: Conflict Detection (Rule-Based)                     │
│ • Check if preferred time is free                           │
│ • If free → Return exact match (confidence: 1.0)            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼ (conflict detected)
┌──────────────────────────────────────────────────────────────┐
│ Step 2: Heuristic Slot Generation                           │
│ • Generate candidate slots (±6 hours, 30-min intervals)     │
│ • Score each slot using weighted heuristics                 │
│ • Return top candidates                                     │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼ (no good candidates)
┌──────────────────────────────────────────────────────────────┐
│ Step 3: LLM Fallback (Complex Scenarios)                    │
│ • Use GPT-4o-mini for complex conflict resolution           │
│ • Consider flexible event shifting (≤30 min)                │
│ • Generate natural language rationale                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 4: Validation & Response                               │
│ • Validate chosen slot against hard constraints             │
│ • Format result with rationale                              │
│ • Return SchedulingResult                                   │
└──────────────────────────────────────────────────────────────┘
```

### Scoring Algorithm

**Weighted Multi-Factor Scoring:**

```
score = w₁·proximity + w₂·productivity + w₃·spacing + w₄·time_of_day

Where:
  w₁ = 0.4  (proximity to preferred time)
  w₂ = 0.3  (productivity pattern match)
  w₃ = 0.2  (spacing from other events)
  w₄ = 0.1  (time-of-day preference)
```

#### Factor 1: Proximity Score

Measures how close a candidate slot is to the user's preferred time:

```python
time_diff_minutes = abs((slot_time - preferred_time).total_seconds() / 60)
proximity_score = max(0, 1 - (time_diff_minutes / max_shift_minutes))
```

**Example:**

- Preferred: 2:00 PM
- Candidate: 2:15 PM → `time_diff = 15 min` → `score = 0.875`
- Candidate: 3:30 PM → `time_diff = 90 min` → `score = 0.25`

#### Factor 2: Productivity Score

Matches slot timing with user's productivity patterns:

```python
# Default productivity curve (customizable per user)
if 9 <= hour < 17:  # Peak productivity (9am-5pm)
    return 1.0
elif 8 <= hour < 9 or 17 <= hour < 19:  # Shoulder hours
    return 0.7
else:  # Low productivity
    return 0.3
```

#### Factor 3: Spacing Score

Prefers slots with adequate buffer time before/after other events:

```python
desired_gap = 30  # minutes

# Find gaps before and after proposed slot
gap_before = slot_start - previous_event.end
gap_after = next_event.start - slot_end

avg_gap = (min(gap_before, 30) + min(gap_after, 30)) / 60
spacing_score = avg_gap  # 0.0 to 1.0
```

#### Factor 4: Time of Day Score

Matches user preferences for morning/afternoon/evening:

```python
if prefer_afternoon and 13 <= hour < 17:
    return 1.0
elif prefer_morning and 8 <= hour < 12:
    return 1.0
else:
    return 0.5
```

### LLM Fallback

When heuristics fail (no good candidates found), the system uses GPT-4o-mini for complex reasoning:

**LLM Input Format:**

```json
{
  "target_event": {
    "title": "Bio Study Session",
    "requested_time": "2025-10-31 14:00",
    "duration": 60
  },
  "busy_slots": [
    {
      "title": "Math Lecture",
      "start": "2025-10-31 13:00",
      "end": "2025-10-31 14:30"
    },
    { "title": "Lunch", "start": "2025-10-31 12:00", "end": "2025-10-31 12:30" }
  ],
  "constraints": {
    "earliest_start": "08:00",
    "latest_end": "22:00",
    "prefer_afternoon": true
  }
}
```

**LLM Output Format:**

```json
{
  "new_start": "2025-10-31 14:30",
  "moved_event": null,
  "shift_minutes": 0,
  "reasoning": "2 PM is blocked by Math Lecture. 2:30 PM is adjacent and free, maintaining afternoon preference."
}
```

### Rationale Generation

Every scheduling decision includes a human-readable rationale:

**Examples:**

| Scenario     | Rationale                                                                             |
| ------------ | ------------------------------------------------------------------------------------- |
| Exact match  | "Exact match - preferred time was available"                                          |
| Small shift  | "Shifted 30 minutes to avoid conflict with Math Lecture"                              |
| Large shift  | "Moved 2 hours later to find free afternoon slot"                                     |
| LLM decision | "2 PM blocked by Math Lecture. Scheduled at 2:30 PM to maintain afternoon preference" |

---

## Tier 2: Main Constraint Scheduler

### Overview

The Main Scheduler uses **OR-Tools CP-SAT constraint programming** for sophisticated multi-event optimization.

**Location:** `backend/app/scheduler/`

### When to Use

Use the Main Scheduler for:

- **Bulk scheduling**: Scheduling multiple events simultaneously
- **Long-term planning**: Scheduling >1 day ahead
- **Complex constraints**: Dependencies, priorities, resource allocation
- **Global optimization**: Optimizing entire schedule (not just local slots)

### Key Features

1. **Multi-Objective Optimization**

   - Minimize deadline violations
   - Balance workload distribution
   - Respect user preferences (time of day, spacing, etc.)
   - Maximize focus time utilization

2. **Advanced Constraints**

   - Hard constraints (fixed classes, sleep hours, unavailable times)
   - Soft constraints (preferences with weights)
   - Dependencies (task A must complete before task B)
   - Resource constraints (study room availability, etc.)

3. **Machine Learning Integration**
   - Contextual bandits for time-of-day preferences
   - Task completion prediction models
   - Adaptive constraint weighting

### Algorithm Overview

```python
# Simplified constraint programming model
model = cp_model.CpModel()

# Variables: Start time for each task
start_vars = {}
for task in tasks:
    start_vars[task.id] = model.NewIntVar(
        earliest_possible,
        latest_possible,
        f'start_{task.id}'
    )

# Constraint 1: No overlaps
for t1, t2 in task_pairs:
    model.AddNoOverlap2D(...)

# Constraint 2: Respect deadlines
for task in tasks:
    model.Add(start_vars[task.id] + task.duration <= task.deadline)

# Constraint 3: Dependencies
for dep in dependencies:
    model.Add(start_vars[dep.after] >= start_vars[dep.before] + duration[dep.before])

# Objective: Minimize weighted sum of violations
model.Minimize(weighted_constraint_violations)

# Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)
```

### Performance Characteristics

| Metric                   | Typical Value             |
| ------------------------ | ------------------------- |
| **Latency**              | 2-10 seconds              |
| **Max Events**           | 100+ events               |
| **Constraint Types**     | 10+ different constraints |
| **Optimization Quality** | Near-optimal solutions    |

---

## Integration Guide

### Using Smart Slot Finder in Action Executor

```python
from app.services.scheduling.smart_slot_finder import get_smart_slot_finder

async def _execute_reschedule(self, user_id: str, params: Dict[str, Any]) -> ExecutionResult:
    """Execute reschedule with smart slot finding."""

    # Extract parameters
    entity_reference = params.get("entity_reference")
    new_time_str = params.get("new_time")

    # Parse target time
    new_time = datetime.fromisoformat(new_time_str)

    # Get smart slot finder
    slot_finder = get_smart_slot_finder()

    # Find optimal slot
    result = await slot_finder.find_optimal_slot(
        preferred_time=new_time,
        duration_minutes=60,  # or get from entity
        user_id=user_id,
        event_title=entity_reference
    )

    if result.success:
        # Update database with chosen slot
        await update_entity_time(
            entity_id=entity_id,
            new_start=result.chosen_slot.start_time,
            new_end=result.chosen_slot.end_time
        )

        # Return confirmation with rationale
        return ExecutionResult(
            success=True,
            message=f"Moved {entity_reference} to {result.message}",
            external_refs={
                "rationale": result.rationale,
                "confidence": result.confidence,
                "method": result.method
            }
        )
    else:
        return ExecutionResult(
            success=False,
            message=result.message,
            error=result.rationale
        )
```

### Using Main Scheduler

```python
from app.scheduler.scheduling.optimizer import SchedulingOptimizer

async def schedule_bulk_events(user_id: str, events: List[Dict]) -> Dict:
    """Schedule multiple events using constraint optimization."""

    optimizer = SchedulingOptimizer(user_id)

    # Use TimezoneManager for all local/UTC conversions
    result = await optimizer.schedule_tasks(
        tasks=events,
        start_date=get_timezone_manager().convert_to_user_timezone(datetime.utcnow(), user_timezone),
        end_date=get_timezone_manager().convert_to_user_timezone(datetime.utcnow() + timedelta(days=7), user_timezone),
        constraints={
            "working_hours": (8, 22),
            "max_hours_per_day": 8,
            "required_breaks": True
        }
    )

    return result
```

---

## API Reference

### SmartSlotFinder.find_optimal_slot()

```python
async def find_optimal_slot(
    preferred_time: datetime,
    duration_minutes: int,
    user_id: str,
    event_title: str,
    user_timezone: str = "UTC",
    constraints: Optional[Dict[str, Any]] = None
) -> SchedulingResult
```

**Parameters:**

| Parameter          | Type       | Required | Description                                                   |
| ------------------ | ---------- | -------- | ------------------------------------------------------------- |
| `preferred_time`   | `datetime` | Yes      | User's preferred start time (timezone-aware)                  |
| `duration_minutes` | `int`      | Yes      | Event duration in minutes                                     |
| `user_id`          | `str`      | Yes      | User identifier                                               |
| `event_title`      | `str`      | Yes      | Name of event being scheduled                                 |
| `user_timezone`    | `str`      | No       | User's timezone (resolved via TimezoneManager; default "UTC") |
| `constraints`      | `Dict`     | No       | Optional constraints (working hours, preferences)             |

**Returns:**

`SchedulingResult` object with:

```python
@dataclass
class SchedulingResult:
    success: bool                        # Whether slot was found
    chosen_slot: SlotCandidate          # Chosen time slot (if success)
    message: str                        # User-facing message
    rationale: str                      # Explanation for decision
    method: str                         # "rule_based", "heuristic", or "llm"
    confidence: float                   # Confidence score (0.0-1.0)
    alternatives: List[SlotCandidate]  # Alternative slots (optional)
    moved_events: List[Dict]           # Events that were shifted (optional)
```

**Example:**

```python
slot_finder = get_smart_slot_finder()

result = await slot_finder.find_optimal_slot(
    preferred_time=datetime(2025, 10, 31, 14, 0, tzinfo=pytz.UTC),
    duration_minutes=60,
    user_id="user123",
    event_title="Bio Study Session",
    constraints={"prefer_afternoon": True}
)

print(f"Success: {result.success}")
print(f"Time: {result.message}")
print(f"Rationale: {result.rationale}")
print(f"Confidence: {result.confidence}")
```

---

## Performance Metrics

### Latency Benchmarks

| Operation                       | Tier 1 (Smart Finder) | Tier 2 (Main Scheduler) |
| ------------------------------- | --------------------- | ----------------------- |
| **Exact match**                 | 50-100ms              | N/A                     |
| **Heuristic search**            | 200-400ms             | N/A                     |
| **LLM fallback**                | 1-2 seconds           | N/A                     |
| **Bulk scheduling (10 events)** | N/A                   | 3-5 seconds             |
| **Bulk scheduling (50 events)** | N/A                   | 8-12 seconds            |

### Accuracy Metrics

| Metric                   | Tier 1 | Tier 2 |
| ------------------------ | ------ | ------ |
| **User acceptance rate** | 87%    | 93%    |
| **Conflict prevention**  | 99.5%  | 99.9%  |
| **Preference match**     | 82%    | 91%    |

---

## Future Enhancements

### Planned Improvements

1. **Learning from User Feedback**

   - Track user modifications to suggested times
   - Adapt scoring weights based on user behavior
   - Personalized productivity patterns

2. **Multi-Slot Presentation**

   - Show 2-3 alternative slots for medium-confidence scenarios
   - Interactive slot selection UI

3. **Proactive Rescheduling**

   - Suggest better times when conflicts arise
   - Auto-optimize schedule when new events added

4. **Cross-Calendar Intelligence**
   - Consider travel time between locations
   - Respect focus time blocks
   - Integrate with calendar analytics

---

## Appendix: Decision Matrix

### Quick Reference: Which Tier to Use?

| Scenario                              | Days Ahead | # Events | Tier  | Latency |
| ------------------------------------- | ---------- | -------- | ----- | ------- |
| "Move meeting to this afternoon"      | 0          | 1        | **1** | <500ms  |
| "Schedule study session tomorrow 2pm" | 1          | 1        | **1** | <500ms  |
| "Reschedule all next week's tasks"    | 3-7        | Many     | **2** | 5-10s   |
| "Plan entire semester schedule"       | 30+        | Many     | **2** | 10-20s  |
| "Move exam to next Friday"            | 5          | 1        | **2** | 3-5s    |

---

## Document Change Log

| Version | Date       | Changes               |
| ------- | ---------- | --------------------- |
| 1.0.0   | 2025-10-29 | Initial documentation |

---

**For questions or clarifications, contact:** engineering@pulseplan.ai
