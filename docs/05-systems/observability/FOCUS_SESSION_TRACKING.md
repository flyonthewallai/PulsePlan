# Focus Session Tracking System

**Comprehensive Pomodoro & Focus Analytics for PulsePlan**

---

## 🎯 Overview

The Focus Session Tracking System provides ML-ready data collection for every Pomodoro/focus session, enabling:

- **User Pattern Learning**: Understand when users are most productive
- **Time Estimation Calibration**: Learn how users estimate vs. actual durations
- **Productivity Insights**: AI-powered recommendations based on historical data
- **Predictive Scheduling**: Feed scheduler with real-world focus patterns

---

## 📊 Database Schema

### `focus_sessions` Table

Enhanced from `time_sessions` with comprehensive tracking:

```sql
CREATE TABLE focus_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id),
  task_id uuid REFERENCES tasks(id) ON DELETE SET NULL,

  -- Timing
  start_time timestamptz NOT NULL,
  end_time timestamptz,
  actual_start_time timestamptz,
  actual_end_time timestamptz,
  duration_minutes int,  -- Auto-calculated via trigger
  expected_duration int,

  -- Session Metadata
  session_type text DEFAULT 'pomodoro',
  cycles_completed int DEFAULT 1,
  break_minutes int DEFAULT 0,
  was_completed boolean DEFAULT false,
  context text,  -- Natural language: "Studying for bio exam"

  -- Quality Metrics
  focus_score int CHECK (focus_score >= 1 AND focus_score <= 5),
  interruption_count int DEFAULT 0,
  focus_quality jsonb DEFAULT '{}',
  session_notes text,

  created_at timestamptz NOT NULL DEFAULT now()
);
```

**Key Fields:**

- `context`: Natural language description for semantic analysis
- `focus_score`: User-rated quality (1-5 scale)
- `interruption_count`: Tracks breaks in concentration
- `expected_duration` vs `duration_minutes`: Learn estimation accuracy

### `user_focus_profiles` Table

Aggregated analytics per user:

```sql
CREATE TABLE user_focus_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL UNIQUE REFERENCES users(id),

  -- Average Metrics
  avg_focus_duration_minutes int,
  avg_break_duration_minutes int,
  avg_interruption_count numeric(4,2),
  avg_completion_ratio numeric(4,2),
  avg_underestimation_pct numeric(5,2),

  -- Peak Patterns
  peak_focus_hours int[],  -- e.g., [9, 14, 22]
  peak_focus_days text[],  -- e.g., ['Tue', 'Thu']

  -- Session Stats
  total_sessions_count int DEFAULT 0,
  completed_sessions_count int DEFAULT 0,

  -- Detailed Breakdowns
  focus_by_hour jsonb DEFAULT '{}',
  performance_by_course jsonb DEFAULT '{}',

  -- Metadata
  last_computed_at timestamptz DEFAULT now(),
  sessions_analyzed_count int DEFAULT 0,

  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
```

**Profile Updates:**

- Recomputed via background worker every 5 minutes
- Cached for 1 hour for fast access
- Triggered after each session completion

---

## 🔧 Architecture

### Backend Components

#### 1. **FocusSessionService** (`app/services/focus/focus_session_service.py`)

Core business logic for session tracking:

```python
from app.services.focus import get_focus_session_service

service = get_focus_session_service()

# Start session
result = await service.start_session(
    user_id="user-123",
    expected_duration=25,
    task_id="task-456",
    context="Studying Chapter 5 - Biology"
)

# End session
result = await service.end_session(
    session_id="session-789",
    user_id="user-123",
    was_completed=True,
    focus_score=4,
    interruption_count=1
)

# Get profile analytics
profile = await service.get_user_profile("user-123")
```

**Key Methods:**

- `start_session()`: Create new session with context
- `end_session()`: Record completion metrics
- `compute_user_profile()`: Generate analytics from session data
- `get_session_insights()`: AI-powered feedback per session
- `get_user_sessions()`: Query session history

#### 2. **API Endpoints** (`app/api/v1/endpoints/focus_modules/sessions.py`)

RESTful API for frontend integration:

**Base URL:** `/api/v1/focus-sessions`

| Endpoint                 | Method | Description                        |
| ------------------------ | ------ | ---------------------------------- |
| `/start`                 | POST   | Start new focus session            |
| `/{session_id}/end`      | POST   | End and record session             |
| `/active`                | GET    | Get currently active session       |
| `/history`               | GET    | Query session history with filters |
| `/profile`               | GET    | Get user's analytics profile       |
| `/{session_id}/insights` | GET    | AI insights for specific session   |
| `/{session_id}`          | DELETE | Delete a session                   |

**Authentication:** All endpoints require JWT Bearer token

#### 3. **Background Worker** (`app/workers/focus_profile_worker.py`)

Async profile computation:

```python
from app.workers.focus_profile_worker import start_focus_profile_worker

# In main.py startup:
await start_focus_profile_worker()
```

**Worker Functions:**

- Runs every 5 minutes (configurable)
- Finds users with pending profile updates
- Recomputes profiles for users with new sessions (min 3 sessions)
- Cleans up stale update flags
- Logs success/failure metrics

### Frontend Components

#### **Focus Session Service** (`web/src/services/focusSessionService.ts`)

TypeScript API client:

```typescript
import {
  startFocusSession,
  endFocusSession,
  getActiveSession,
  getFocusProfile,
} from "@/services/focusSessionService";

// Start session
const session = await startFocusSession({
  expected_duration: 25,
  task_id: "task-123",
  context: "Working on assignment",
  session_type: "pomodoro",
});

// End session
await endFocusSession(session.id, {
  was_completed: true,
  focus_score: 4,
  interruption_count: 1,
  session_notes: "Great session!",
});

// Get profile
const profile = await getFocusProfile();
console.log(`Average: ${profile.avg_focus_duration_minutes}min`);
console.log(`Peak hours: ${profile.peak_focus_hours}`);
```

#### **PomodoroPage Integration**

The Pomodoro timer now automatically:

1. **Starts session** when timer begins
2. **Resumes session** if page reloads during active timer
3. **Ends session** when timer completes or is cancelled
4. **Tracks interruptions** via pause/resume

---

## 📈 Use Cases

### 1. **Real-Time Session Tracking**

```typescript
// User starts 25-min Pomodoro for "Biology Assignment"
const session = await startFocusSession({
  expected_duration: 25,
  task_id: "bio-assignment-123",
  context: "Studying Chapter 5 - Cellular Respiration",
  session_type: "pomodoro",
});
// → session.id: "session-abc123"

// User completes 22 minutes (interrupted once)
await endFocusSession(session.id, {
  was_completed: false,
  interruption_count: 1,
  focus_score: 3,
  session_notes: "Got distracted by notification",
});
// → Profile update scheduled
```

### 2. **User Productivity Insights**

```python
# Get user's focus profile
profile = await focus_service.get_user_profile("user-123")

print(f"Average focus: {profile['avg_focus_duration_minutes']}min")
# → "Average focus: 42min"

print(f"Peak hours: {profile['peak_focus_hours']}")
# → "Peak hours: [9, 14, 22]"

print(f"Underestimates by: {profile['avg_underestimation_pct']}%")
# → "Underestimates by: -12.5%"
```

### 3. **AI Scheduler Integration**

```python
# Feed scheduler with real user data
user_profile = await focus_service.get_user_profile(user_id)

scheduler_input = {
    'user_id': user_id,
    'tasks': tasks,
    'constraints': {
        'typical_focus_duration': user_profile['avg_focus_duration_minutes'],
        'peak_hours': user_profile['peak_focus_hours'],
        'underestimation_factor': 1 + (user_profile['avg_underestimation_pct'] / 100)
    }
}

# Scheduler now knows:
# - User typically focuses for 42min (not standard 25min)
# - User is most productive at 9AM, 2PM, 10PM
# - Add 12.5% buffer to user's time estimates
```

### 4. **Session-Specific Insights**

```python
insights = await focus_service.get_session_insights(user_id, session_id)

for insight in insights['insights']:
    print(f"[{insight['type']}] {insight['message']}")

# Output:
# [positive] "Great job! You focused 30min, 25% longer than your average."
# [positive] "Perfect focus! No interruptions during this session."
# [positive] "You rated this session highly. Keep up the great work!"
```

---

## 🔍 Analytics Metrics

### Session-Level Metrics

| Metric                  | Type  | Description                         |
| ----------------------- | ----- | ----------------------------------- |
| `duration_minutes`      | int   | Actual time spent (auto-calculated) |
| `expected_duration`     | int   | User's initial estimate             |
| `completion_percentage` | float | (actual / expected) × 100           |
| `focus_score`           | int   | User rating 1-5                     |
| `interruption_count`    | int   | Number of breaks/pauses             |
| `was_completed`         | bool  | Finished vs abandoned               |

### Profile-Level Metrics

| Metric                       | Type  | Description              |
| ---------------------------- | ----- | ------------------------ |
| `avg_focus_duration_minutes` | int   | Mean session length      |
| `avg_completion_ratio`       | float | Typical completion rate  |
| `avg_underestimation_pct`    | float | Estimation accuracy      |
| `peak_focus_hours`           | int[] | Top 3 productive hours   |
| `peak_focus_days`            | str[] | Top 3 productive days    |
| `focus_by_hour`              | jsonb | Sessions per hour (0-23) |
| `performance_by_course`      | jsonb | Stats grouped by course  |

---

## 🎓 ML Training Data

### Features for Predictive Model

**User-Level Features:**

```python
features = {
    'avg_focus_duration': 42,
    'avg_interruptions': 0.8,
    'completion_ratio': 0.85,
    'underestimation_pct': -12.5,
    'peak_hour_variance': 4.2,
    'consistency_score': 0.78
}
```

**Session-Level Features:**

```python
features = {
    'hour_of_day': 14,
    'day_of_week': 2,  # Tuesday
    'expected_duration': 25,
    'task_type': 'assignment',
    'course_id': 'bio-101',
    'recent_interruptions': 2,
    'time_since_last_session': 180  # minutes
}
```

**Target Variable:**

```python
target = {
    'actual_duration': 30,
    'was_completed': True,
    'focus_quality': 4
}
```

### Model Types

1. **Duration Predictor**: Predict actual time given user estimate

   - Input: User estimate, time of day, recent history
   - Output: Calibrated duration with confidence interval

2. **Completion Probability**: Predict if session will be completed

   - Input: Session context, user patterns, time slot
   - Output: P(completion) ∈ [0, 1]

3. **Focus Quality Predictor**: Predict expected focus score
   - Input: Environmental factors, user state, task difficulty
   - Output: Expected focus_score (1-5)

---

## 🛠️ Implementation Checklist

### ✅ Completed

- [x] Database migration (`focus_sessions` + `user_focus_profiles`)
- [x] Backend service layer (`FocusSessionService`)
- [x] REST API endpoints (`/api/v1/focus-sessions`)
- [x] Frontend service (`focusSessionService.ts`)
- [x] PomodoroPage integration (auto-tracking)
- [x] Background worker (profile computation)
- [x] Unit tests (`test_focus_sessions.py`)
- [x] API documentation (docstrings)
- [x] RLS policies (row-level security)
- [x] Caching layer (Redis)

### 🔄 Future Enhancements

- [ ] Focus quality AI inference (detect distractions via browser activity)
- [ ] Break recommendation engine
- [ ] Weekly/monthly analytics dashboard
- [ ] Export focus data to CSV/JSON
- [ ] Integration with calendar events (auto-detect meeting focus)
- [ ] Gamification (streaks, badges, leaderboards)
- [ ] Social features (compare with peers, anonymized)
- [ ] Mobile push notifications for insights

---

## 📊 Example Queries

### Get User's Most Productive Hours

```sql
SELECT
  jsonb_object_keys(focus_by_hour) AS hour,
  (focus_by_hour->>jsonb_object_keys(focus_by_hour))::int AS session_count
FROM user_focus_profiles
WHERE user_id = 'user-123'
ORDER BY session_count DESC
LIMIT 3;
```

### Find Users Who Underestimate Time

```sql
SELECT
  user_id,
  avg_underestimation_pct,
  total_sessions_count
FROM user_focus_profiles
WHERE avg_underestimation_pct < -10  -- Underestimate by >10%
  AND total_sessions_count >= 20
ORDER BY avg_underestimation_pct ASC;
```

### Session Completion Rate by Hour

```sql
SELECT
  EXTRACT(HOUR FROM start_time) AS hour,
  COUNT(*) FILTER (WHERE was_completed) AS completed,
  COUNT(*) AS total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE was_completed) / COUNT(*), 1) AS completion_rate
FROM focus_sessions
WHERE user_id = 'user-123'
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY hour
ORDER BY hour;
```

---

## 🔐 Security & Privacy

### Row-Level Security (RLS)

All tables have RLS enabled:

```sql
-- Users can only access their own sessions
CREATE POLICY "Users can view own focus sessions"
  ON focus_sessions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own focus sessions"
  ON focus_sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

### Data Retention

- Sessions retained indefinitely (for ML training)
- Can be anonymized for research (remove PII)
- Users can export/delete via GDPR compliance endpoint

---

## 🚀 Deployment

### Environment Variables

```env
# Supabase (already configured)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Redis (for caching)
REDIS_URL=redis://localhost:6379
```

### Startup Script

Add to `backend/main.py`:

```python
from app.workers.focus_profile_worker import start_focus_profile_worker

@app.on_event("startup")
async def startup_event():
    # Start background worker
    await start_focus_profile_worker()
    logger.info("Focus Profile Worker started")
```

### Testing

```bash
# Run backend tests
cd backend
pytest tests/test_focus_sessions.py -v

# Run API integration tests
pytest tests/test_focus_sessions.py::TestFocusSessionService -v

# Run specific test
pytest tests/test_focus_sessions.py::test_start_session_success -v
```

---

## 📚 Related Documentation

- [SCHEDULER_SYSTEM_DOCUMENTATION.md](./SCHEDULER_SYSTEM_DOCUMENTATION.md) - How scheduler uses focus data
- [TIMEBLOCKS_ARCHITECTURE.md](./TIMEBLOCKS_ARCHITECTURE.md) - Integration with calendar
- [PHASE_1_IMPLEMENTATION_SUMMARY.md](./PHASE_1_IMPLEMENTATION_SUMMARY.md) - Overall system architecture

---

## 🤝 Contributing

When adding new features to focus tracking:

1. **Update schema**: Create migration in `backend/migrations/`
2. **Update service**: Add methods to `FocusSessionService`
3. **Add tests**: Write unit tests in `test_focus_sessions.py`
4. **Document**: Update this file + add docstrings
5. **Update frontend**: Sync TypeScript types in `focusSessionService.ts`

---

## 📞 Support

For questions or issues:

- Backend: See `app/services/focus/focus_session_service.py`
- Frontend: See `web/src/services/focusSessionService.ts`
- Database: See migration `create_focus_sessions_and_profiles.sql`

---

**Last Updated:** 2025-10-29  
**Version:** 1.0.0  
**Author:** PulsePlan Engineering Team







