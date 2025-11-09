# Intent Boundary Clarification Guide

## Tricky Intent Pairs - Decision Rules

This guide helps disambiguate semantically similar intents that MiniLM might confuse.

---

## 1️⃣ calendar_event vs scheduling

### calendar_event
**Rule**: Structured event with specific details (time, location, attendees, recurrence)

✅ **Use when**:
- Adding a specific event with **concrete details**
- Event has **participants** or **location**
- Creating **recurring** calendar entries
- "Put X on my calendar"

**Examples**:
- "add team standup every monday at 9am to calendar" ✓
- "create calendar entry for dr smith office hours wednesday 2-3pm" ✓
- "put final exam may 15th at 10am on my schedule" ✓
- "mark dentist appointment next tuesday at noon" ✓

### scheduling
**Rule**: Time-blocking for work/activities without creating formal events

✅ **Use when**:
- **Blocking out time** for activities
- Reserving time **without specific details**
- General planning: "set aside time for X"
- Focus on **allocating hours**, not creating events

**Examples**:
- "block time to work on the assignment" ✓
- "allocate 2 hours for studying tomorrow" ✓
- "reserve time this weekend for the project" ✓
- "set aside time for deep work on thursday" ✓

**Key Difference**:
- `calendar_event` → "Add meeting with Sarah at 3pm in Room 201" (structured)
- `scheduling` → "Block 3 hours for project work tomorrow" (time allocation)

---

## 2️⃣ reschedule vs adjust_plan

### reschedule
**Rule**: Move or change time/date of ONE existing item

✅ **Use when**:
- Moving a **single** event/task to different time
- Keywords: "move", "postpone", "delay", "shift", "bump"
- Affects **one specific thing**

**Examples**:
- "postpone the 2pm call until tomorrow same time" ✓
- "move tomorrow's appointment to monday" ✓
- "shift the exam review from 3pm to 5pm" ✓
- "bump the study session to friday instead of thursday" ✓

### adjust_plan
**Rule**: Restructure, reorganize, or optimize the ENTIRE schedule

✅ **Use when**:
- Reorganizing **whole schedule** or **multiple items**
- Keywords: "reorganize", "restructure", "rebalance", "optimize", "rework"
- Affects **overall plan**

**Examples**:
- "reorganize my entire week to fit the new assignment" ✓
- "restructure my schedule around exam prep" ✓
- "rebalance my workload for better efficiency" ✓
- "optimize my plan to prioritize urgent items" ✓

**Key Difference**:
- `reschedule` → "Move Monday's meeting to Thursday" (one item)
- `adjust_plan` → "Rework my whole schedule for finals week" (whole plan)

---

## 3️⃣ briefing vs status vs search vs user_data_query

### briefing
**Rule**: High-level summary or overview of schedule/tasks for a time period

✅ **Use when**:
- Requesting a **summary** or **overview**
- Keywords: "briefing", "rundown", "agenda", "what's coming up"
- Time-oriented: "today's plan", "this week's overview"

**Examples**:
- "give me rundown of what's coming up today" ✓
- "summary of tomorrow's schedule please" ✓
- "what do i have planned for this week?" ✓
- "agenda for next monday" ✓

### status
**Rule**: Progress metrics, completion rates, or performance tracking

✅ **Use when**:
- Asking about **progress** or **completion**
- Keywords: "how am i doing", "progress", "completion rate", "metrics"
- Focus on **performance/stats**

**Examples**:
- "how many tasks have i completed this week?" ✓
- "show my productivity metrics for last month" ✓
- "what's my progress on the research paper?" ✓
- "how am i doing on my goals this semester?" ✓

### search
**Rule**: Find or filter specific items by criteria

✅ **Use when**:
- Looking for **specific items** with filters
- Keywords: "find", "search", "look up", "filter", "show me X where..."
- Focus on **retrieval with criteria**

**Examples**:
- "find all tasks tagged urgent" ✓
- "search for todos with high priority" ✓
- "show assignments due this week" ✓
- "filter calendar events by location" ✓

### user_data_query
**Rule**: Ask for personal data/information (general "show me my X")

✅ **Use when**:
- General data requests: "show me my X", "what are my X"
- No specific filters or criteria
- Just viewing **owned data**

**Examples**:
- "what tasks are on my plate right now?" ✓
- "show me my calendar events for tomorrow" ✓
- "list all my pending todos" ✓
- "what meetings do i have this afternoon?" ✓

**Key Differences**:
- `briefing` → "What's my plan today?" (summary)
- `status` → "How many tasks did I complete?" (metrics)
- `search` → "Find tasks tagged 'urgent'" (filtered query)
- `user_data_query` → "Show me my tasks" (general data view)

---

## 4️⃣ task_management vs scheduling

### task_management
**Rule**: Create, update, or track TODO items (things to do)

✅ **Use when**:
- Creating/updating **action items** or **todos**
- Keywords: "task", "todo", "assignment", "complete", "track"
- Focus on **what needs to be done**

**Examples**:
- "add task to submit the report by friday" ✓
- "create todo for buying textbook" ✓
- "mark task as complete for homework" ✓
- "track progress on the coding assignment" ✓

### scheduling
**Rule**: Block or allocate TIME (when to do things)

✅ **Use when**:
- Allocating **time blocks**
- Keywords: "block time", "allocate", "reserve time"
- Focus on **when to do it**

**Examples**:
- "block 3 hours for homework tomorrow" ✓
- "allocate morning for studying" ✓
- "reserve friday afternoon for project work" ✓

**Key Difference**:
- `task_management` → "Add task: finish homework" (WHAT)
- `scheduling` → "Block 2 hours to do homework" (WHEN)

---

## Quick Decision Tree

```
User says: "Move my 3pm meeting to 4pm"
├─ Affects ONE item? → YES
├─ Moving to different time? → YES
└─ Intent: reschedule ✓

User says: "Reorganize my whole week"
├─ Affects MULTIPLE items? → YES
├─ Restructuring plan? → YES
└─ Intent: adjust_plan ✓

User says: "Add standup at 9am every Monday"
├─ Has specific time/recurrence? → YES
├─ Creating structured event? → YES
└─ Intent: calendar_event ✓

User says: "Block 2 hours for coding"
├─ Time allocation without event? → YES
├─ Just reserving time? → YES
└─ Intent: scheduling ✓

User says: "What's my plan today?"
├─ Asking for summary? → YES
└─ Intent: briefing ✓

User says: "How many tasks did I finish?"
├─ Asking for metrics? → YES
└─ Intent: status ✓

User says: "Find tasks tagged urgent"
├─ Searching with criteria? → YES
└─ Intent: search ✓

User says: "Show me my tasks"
├─ General data request? → YES
└─ Intent: user_data_query ✓
```

---

## Training Impact

With 45 additional borderline examples:
- **2,481 total pairs** (up from 2,316)
- **Explicit hard negatives** for confusing pairs
- **624 positive pairs** covering all 23 intents
- **1:2.98 ratio** (optimal for contrastive learning)

### Expected Improvement:
- **Before**: Model may confuse "block time" (scheduling) with "add event" (calendar_event)
- **After**: Model learns crisp boundaries with >0.15 similarity margin between confusing pairs

---

## Usage During Inference

When the model returns low confidence (<0.6) on confusing pairs, use this guide to:
1. Check the top-2 predictions
2. Apply decision rules above
3. Return the more specific intent based on keywords and structure
