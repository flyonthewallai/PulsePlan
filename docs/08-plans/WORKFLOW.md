# 🧭 PulsePlan Workflow Automation System — Feature Document

**Goal:** Centralize all automations (AI scheduling, daily briefings, weekly pulse summaries, auto-shifting, and custom routines) into a unified “Workflows” hub that allows users to create, view, and control automated processes.

---

## 🧠 Problem Statement

PulsePlan’s automation capabilities (daily scheduling, weekly pulse, event shifting) currently exist as **disconnected features**, hidden behind backend jobs or UI toggles.
Users lack:

* A clear overview of what automations exist and when they run
* The ability to create custom recurring automations
* Awareness that automation is a **premium differentiator**

**Goal:**
Create a unified **Workflows** system that makes PulsePlan’s intelligence *visible, configurable, and monetizable.*

---

## 🌱 Core Objectives

1. **Unify all automations** (Daily Briefing, Weekly Pulse, Auto-Scheduler, Auto-Shift Events) under a single Workflows dashboard.
2. **Enable custom workflows** (e.g., “Plan my week every Sunday at 6PM”).
3. **Encourage upgrades** through visible, interactive upsells (Premium gating for activation).
4. **Re-use backend execution architecture** (Action Executor + OR-Tools Scheduler) to run all workflows seamlessly.
5. **Lay foundation for future integrations** (Gmail, Canvas, Notion triggers).

---

## ⚙️ Feature Overview

### **1. Unified Workflows Dashboard**

A dedicated page that displays:

* All active automations (system + user-created)
* Status, next run, last run
* Enable/disable toggles
* Upgrade banners for premium workflows

### **2. Workflow Builder (Wizard Modal)**

Allows creation of new workflows using a simple step-by-step UI:

1. **Trigger:** When to run (Time, Event, Manual)
2. **Action:** What to do (e.g., `schedule_period`, `summarize_tasks`)
3. **Confirmation Mode:** Silent, Summary, Require Confirmation
4. **Save & Activate (Premium)**

### **3. System Workflows (Pre-Seeded)**

System automations visible and partially configurable:

| Workflow            | Description                                   | Editable    | Premium     |
| ------------------- | --------------------------------------------- | ----------- | ----------- |
| 🧭 Daily Briefing   | Morning summary of schedule & tasks           | Limited     | ❌           |
| 📆 Weekly Pulse     | Sunday reflection + week plan                 | Limited     | ❌           |
| ⚡ Auto-Shift Events | Auto rebalances tasks when conflicts arise    | Toggle only | ❌           |
| 🪄 Auto Scheduler   | Generates daily/weekly schedule automatically | Full        | ✅ (Premium) |

### **4. Custom Workflows**

User-defined automations leveraging existing PulsePlan actions:

* Example: “Every Friday at 5PM → Generate weekly summary + email it”
* Example: “Every morning at 7AM → Create daily schedule”

---

## 💎 Premium Gating Model

| Tier           | Can View | Can Create/Edit    | Can Activate | Workflow Slots | Trigger Types         |
| -------------- | -------- | ------------------ | ------------ | -------------- | --------------------- |
| **Free**       | ✅        | ✅ (draft/simulate) | ❌            | 0 active       | Time (preview only)   |
| **Premium**    | ✅        | ✅                  | ✅            | 5 active       | Time + Event + Manual |
| **Future Pro** | ✅        | ✅                  | ✅            | Unlimited      | All + AI Conditions   |

**Upsell strategy:**
Free users can build and preview workflows once — but to **activate automation**, they must upgrade.

> “Activate your daily scheduler automatically 🔒 Upgrade to PulsePlan Premium.”

---

## 🧩 Data Model

### Database: `user_workflows`

```sql
CREATE TABLE user_workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  trigger_type TEXT,            -- 'time' | 'event' | 'manual'
  trigger_value TEXT,           -- e.g. '06:00' or 'Sunday'
  actions JSONB,                -- [{ "type": "schedule_period", "params": {...}}, ...]
  confirmation_mode TEXT,       -- 'silent' | 'summary' | 'require'
  active BOOLEAN DEFAULT FALSE,
  premium_required BOOLEAN DEFAULT FALSE,
  is_system BOOLEAN DEFAULT FALSE,
  locked BOOLEAN DEFAULT FALSE,
  last_run TIMESTAMP,
  next_run TIMESTAMP
);
```

### Example Record

```json
{
  "name": "Daily Auto Scheduler",
  "trigger_type": "time",
  "trigger_value": "06:30",
  "actions": [
    { "type": "schedule_period", "params": {"timeframe": "today"} },
    { "type": "send_summary", "params": {"mode": "summary"} }
  ],
  "confirmation_mode": "summary",
  "active": true,
  "premium_required": true
}
```

---

## 🧠 Execution Flow

### 1. Trigger Detection

Background scheduler (Celery, Supabase cron, or internal async loop) runs every 5 minutes:

```python
for workflow in workflow_repo.get_due_workflows():
    if workflow.active:
        for action in workflow.actions:
            await action_executor.execute(action.type, user_id=workflow.user_id, **action.params)
        workflow_repo.mark_executed(workflow.id)
```

### 2. Action Execution

Actions map to the same handlers used by the conversational system (e.g., `schedule_period`, `summarize_day`, `auto_shift_conflicts`).

### 3. Confirmation Mode Behavior

| Mode                 | Behavior                                                         |
| -------------------- | ---------------------------------------------------------------- |
| Silent               | Executes directly, no gate                                       |
| Summary              | Executes → Sends confirmation summary to user (with undo option) |
| Require Confirmation | Creates gate (pending user review)                               |

### 4. System Workflow Integration

System workflows (Daily Briefing, Weekly Pulse, etc.) are seeded on account creation and stored in the same table with:

```sql
is_system = TRUE, locked = TRUE
```

Users can toggle them on/off from the same dashboard for clarity.

---

## 🧱 Backend Implementation Plan

### Phase 1 — Database & Model Setup (1 day)

* Create `user_workflows` table
* Add ORM + Pydantic models (`Workflow`, `WorkflowAction`)
* Add migration

### Phase 2 — CRUD & Runner Services (2–3 days)

**Files:**

* `/backend/app/services/workflows/workflow_service.py`
* `/backend/app/services/workflows/runner.py`

Key functions:

```python
async def create_workflow(user_id, name, trigger_type, actions, ...): ...
async def get_due_workflows(): ...
async def run_due_workflows(): ...
async def toggle_workflow(user_id, workflow_id, active): ...
```

### Phase 3 — API Endpoints (1–2 days)

* `GET /api/v1/workflows` – list all workflows (system + custom)
* `POST /api/v1/workflows` – create/edit workflow
* `PATCH /api/v1/workflows/{id}` – enable/disable
* `DELETE /api/v1/workflows/{id}` – remove workflow
* `POST /api/v1/workflows/simulate` – simulate run (free tier preview)

### Phase 4 — Frontend (3–4 days)

**Folder:** `/frontend/app/pages/workflows/`

Components:

* `WorkflowsList.tsx` – unified dashboard
* `WorkflowCard.tsx` – card UI
* `CreateWorkflowModal.tsx` – builder wizard
* `WorkflowTemplates.tsx` – list of prebuilt templates

**Design highlights:**

* Section 1: Active Automations (system + custom)
* Section 2: Build Your Own (Premium-locked button)
* Section 3: Template Carousel
* Upsell banners for locked workflows

---

## 🔒 Premium Logic Integration

* On `POST /workflows` → If `premium_required=True` and `user.premium=False` → return `403` with upgrade CTA.
* Free tier can simulate once (run once manually, auto-disable).
* Premium gating logic shared with existing plan system.

---

## 🧩 Example User Flow

### 1. User navigates to **Workflows**

Sees:

```
System Automations
- Daily Briefing (Enabled)
- Weekly Pulse (Enabled)
- Auto-Shift Events (Enabled)

Custom Workflows
- None
[ + Create New Workflow ]
```

### 2. Clicks “Create New Workflow”

Wizard:

* Trigger: Every morning 6:00 AM
* Action: Create my daily schedule
* Confirmation: Summary mode
* Save → “Activate (Premium)”

### 3. Free user sees upsell:

> “Auto-scheduling is a premium feature. Upgrade to unlock daily automation.”

---

## 📈 Success Metrics

| Category    | Metric                                 | Target |
| ----------- | -------------------------------------- | ------ |
| Adoption    | % users visiting Workflows page        | ≥ 60%  |
| Conversion  | Upgrade clicks from workflow gating    | ≥ 20%  |
| Engagement  | Avg. active workflows per premium user | 3+     |
| Performance | Average execution time per workflow    | < 5s   |
| Quality     | Error rate in workflow executions      | < 1%   |

---

## 🧠 Future Extensions

* Conditional logic (“If I have >3 tasks left by 6PM → reschedule tomorrow”)
* Workflow sharing (export templates)
* Integration triggers (Gmail unread summary, Canvas due dates)
* Agent chaining (run multi-step actions across tools)

---

## ✅ Summary

| Area               | Decision                                         |
| ------------------ | ------------------------------------------------ |
| **Core concept**   | Unified dashboard for all automations            |
| **Primary UX**     | “Workflows” page with system + custom sections   |
| **Premium gating** | Build free → Activate premium                    |
| **Data model**     | Unified `user_workflows` table                   |
| **Backend**        | Celery/Supabase job + Action Executor reuse      |
| **Integration**    | System workflows visible alongside custom        |
| **Outcome**        | Transparency, engagement, and clear upgrade path |

---

Would you like me to now **add the schema + Python service stubs** (`workflow_service.py`, `runner.py`, and a seed file for system workflows`) as the next section, in the same implementation doc style? That would let you start coding it directly.
