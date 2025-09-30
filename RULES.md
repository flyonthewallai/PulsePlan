# PulsePlan – Claude Rules

**Version:** 1.0
**Last updated:** 2025‑09‑25 (America/Denver)

> Paste this file into your repo as `docs/claude-rules.md` (or into Claude’s “Rules” panel). These rules are **non‑negotiable**. Claude must follow them for *every* change, from one‑line edits to large refactors.

---

## 0) Purpose

Keep PulsePlan’s codebase **modular, deduplicated, and production‑grade**. Every change must **improve** code quality, never pile on technical debt, duplicate logic, or leave dead code.

* **Never** create duplicate logic. **Refactor** to a shared function/module instead.
* **Never** disable or comment‑out old functionality while writing a new one on top. **Migrate** or **replace** cleanly.
* **Small, composable modules** > giant files. Prefer **pure functions** for domain logic.
* Every change leaves the repo **lint‑clean, typed, tested, and documented**.

---

## 1) Architecture Invariants (PulsePlan‑specific)

These are the boundaries you **must not violate** without an explicit migration plan.

1. **Core services**

   * **Scheduling Engine** (mission‑critical): deterministic, idempotent, time‑zone aware, pure core.
   * **Sync Services**: Canvas assignment ingest (via user‑created Canvas API key), Google Calendar **two‑way** sync, optional Gmail ingest for summaries.
   * **Background Jobs**: long‑running syncs, cache warmers, missed‑task shifters, email/web‑push notifications.
2. **Data layer**

   * **Primary DB**: Postgres (Supabase). Use **RLS**; all data access through **repository/service** layer—not directly from handlers/views.
   * **Cache/Queues/Rate limits**: Upstash Redis. Use **idempotency keys** and **dedupe keys** for jobs.
   * **Migrations**: via Supabase SQL migrations (or Alembic if present). **Never** mutate schema without a migration file and rollback notes.
3. **Security**

   * **KMS‑managed encryption keys** (AWS KMS) for secrets at rest. **Never** log PII or tokens. Use **parameterized queries** only. Validate and sanitize all input.
4. **Boundaries & layering** (don’t cross the streams):

   * **API layer (FastAPI)** → **Service layer** → **Repository layer** → **DB**.
   * **iOS (Swift)** and **Web (Next.js/TypeScript)** call into the API; **no direct DB access** from clients.
   * **Agent/LLM tools** live in `backend/app/agents/*`; they call services, **not** repositories directly.

> **Assumed layout** (adapt if repo differs; keep same layering):
>
> * `backend/app/api/…` — FastAPI routers (thin)
> * `backend/app/services/…` — orchestration/domain logic
> * `backend/app/repos/…` — DB access (SQL/ORM)
> * `backend/app/schemas/…` — Pydantic I/O models
> * `backend/app/agents/graphs/…` — LangGraph/chat graphs
> * `backend/app/agents/tools/…` — tool adapters (calendar, canvas, email)
> * `backend/app/queues/…` — background tasks / workers
> * `backend/app/core/…` — config, logging, security
> * `backend/tests/…` — unit/integration
> * `web/…` — Next.js app (components, app routes, lib, hooks, api clients, tests)
> * `ios/…` — Swift modules (Networking, Storage, Views, ViewModels, UseCases, Tests)

---

## 2) Non‑negotiable Coding Standards

### 2.1 No duplication, no dead code

* Before writing code, **search** the repo for existing implementations. If similar logic exists, **refactor to a shared module** and replace all call sites.
* If a module is superseded, **delete** or **migrate** it. Do **not** leave disabled blocks, commented‑out functions, or duplicate branches.
* Allowable duplication: **tests/fixtures** only.

### 2.2 Small, modular files

* Each file: **one responsibility**. Split > 300–400 lines unless it’s a cohesive domain module.
* Keep handlers thin; move logic into **services**. Keep services thin; move persistence into **repos**.

### 2.3 Strict quality gates (must pass locally)

* **Python**: ruff (lint), black (format), isort (imports), mypy strict (types), pytest (tests).
* **TypeScript/Next.js**: eslint (strict), prettier, `tsc --noEmit`, vitest/jest.
* **Swift iOS**: SwiftLint, SwiftFormat, unit/UI tests.
* All public APIs: auto‑documented via OpenAPI. Update request/response schemas.

### 2.4 Observability & safety

* Structured logging with request/job IDs. Meaningful log levels. No sensitive data in logs.
* Add metrics counters for major paths (scheduler runs, sync successes/failures, retries).
* Background jobs **idempotent** and **retry‑safe** with exponential backoff.

### 2.5 Security

* Never print or persist secrets/tokens. Use secrets manager & env vars.
* Validate all external payloads (zod/Pydantic). Reject unknown fields unless explicitly allowed.
* Enforce RLS and per‑user scoping in all queries.

---

## 3) Required Change Workflow (what Claude must do every time)

**Step 0 – Understand scope**

* Read the issue/task. Identify domain, call sites, and invariants affected (scheduler, sync, security, etc.).

**Step 1 – Global duplicate/impact scan** *(run these searches; adapt paths as needed)*

* `rg -n "schedule|scheduling|timeblock|time-block|reschedule|shift" backend`
* `rg -n "canvas|assignment|course|due_date|sync_token" backend`
* `rg -n "google|calendar|gcal|event|sync|etag|ics" backend`
* `rg -n "idempot|dedupe|retry|backoff|queue|worker" backend`
* `rg -n "parse_ical|to_utc|from_utc|localize|tzinfo" backend`
* `rg -n "token|quota|plan|usage|gate|feature_flag" backend web`
* `rg -n "date|time|tz|timezone" web ios backend`
* Search for **similar function names** and **copy‑paste blocks**. If found, **consolidate** into a shared module.

**Step 2 – Plan the refactor**

* Decide: extract shared function? create `services/shared/` module? introduce interface?
* Write a short **Refactor Plan** (bullets) before coding.

**Step 3 – Implement (no duplicates)**

* Create or extend a **single source of truth**. Replace call sites to use it.
* Remove superseded code and unused imports. Delete commented or dead code.

**Step 4 – Tests & types**

* Add/adjust unit tests for new/changed logic.
* Add integration test for critical flows (e.g., scheduler + GCal conflict handling; Canvas ingest idempotency).
* Ensure types are correct (mypy/tsc).

**Step 5 – Quality gates**

* Run all linters/formatters. Ensure `pre-commit` passes if configured.

**Step 6 – Migration & rollback (if schema or data)**

* Create migration file with forward + rollback.
* Provide backfill script if needed. Document in PR.

**Step 7 – Output the checklist in PR**
Claude must output the following in every PR description:

* **CHANGE SUMMARY** – what & why.
* **FILES CHANGED** – list with reasons per file.
* **NO‑DUPLICATE PROOF** – show where existing logic lived and how you consolidated it (links/paths/rg outputs).
* **TEST PLAN** – commands, cases, fixtures.
* **RISK & ROLLBACK** – risks, feature flag/kill‑switch if applicable.
* **OBSERVABILITY** – logs/metrics added.

---

## 4) PulsePlan Domain Rules (apply during edits)

### 4.1 Scheduling engine

* Keep core scheduling logic **pure** (no I/O). Inputs: tasks/events/constraints; Output: proposed schedule with reasons.
* Must be **stable** (same inputs → same result) and **deterministic across time zones**. Use timezone‑aware datetimes everywhere.
* When shifting missed tasks, preserve constraints and priorities; provide annotated reasons.
* Complexity: aim ≤ O((T+E) log(T+E)). Avoid N² scans.

### 4.2 Canvas initial + continuous sync

* Initial sync runs as a **background job** with pagination and rate‑limit respect.
* Deduplicate by **Canvas assignment ID + course ID**. Use **upserts**.
* Map fields: title, due_at, course, html_url, points, submission state.
* Store sync checkpoints (e.g., last seen updated_at) to support incremental sync.

### 4.3 Google Calendar two‑way

* Store external IDs, etags, and sync tokens.
* Conflict policy: user edits in GCal **win** unless explicitly overridden by PulsePlan with user confirmation.
* Create/update/delete events atomically; retry on 409/412 with token refresh.

### 4.4 Token/quota gating (free vs premium)

* Gate **expensive** features (bulk reschedule, multi‑calendar merge, daily email digests) via plan checks.
* Track usage in Redis with **per‑user counters + TTL**. Expose clear errors when limits exceeded.

### 4.5 Background jobs

* Each job must declare: **idempotency key**, **dedupe key**, **retry policy**, **max run time**.
* Jobs **never** mutate state partially; wrap mutations in a **transaction**.

### 4.6 API contracts

* Do not break public routes. If changing I/O, bump version or add new route; deprecate old with a date.

---

## 5) File/Module Conventions

### 5.1 Python (FastAPI backend)

* **Routers**: small; call services. No DB in routers.
* **Services**: orchestration & domain logic. Pure helpers in `services/shared/*`.
* **Repos**: only SQL/ORM and data mapping. No business logic.
* **Schemas**: Pydantic `BaseModel` for request/response. Use `Annotated` types where helpful.
* **Config**: load once; inject via dependency or settings object.
* **Testing**: `tests/unit` for pure logic; `tests/integration` for API/DB; use factories/fixtures.

### 5.2 TypeScript (Next.js web)

* Collocate component, styles, and tests. Hooks in `web/lib/hooks`.
* No direct fetch in components for complex flows; use **action** or **api client** in `web/lib/api`.
* Reusable utilities live in `web/lib/utils/*`. No duplication across pages.
* Strict TS; never use `any` except typed escape hatches with justification.

### 5.3 Swift (iOS)

* MVVM (Views ↔ ViewModels ↔ UseCases ↔ Repositories ↔ Networking).
* Use `Codable` models mirrored to backend schemas.
* Side‑effects only in UseCases/Repositories. Views stay declarative.
* Persist small caches via Keychain/UserDefaults as appropriate (no secrets in plaintext).

---

## 6) Prohibited Patterns (fail the PR if present)

* Copy‑pasted logic with small tweaks; duplicated validators/parsers; repeated date/tz conversions.
* Commented‑out, disabled, or shadowed old implementations kept alongside new ones.
* Giant god‑objects or grab‑bag util files (`utils.py` with 1,000 lines). Split them.
* Swallowing exceptions (`except Exception: pass`) or logging without action.
* Unbounded loops/pollers; blocking I/O in async routes; time zone naive datetimes.

---

## 7) Refactor Playbooks

**7.1 Duplicate extraction**

1. Identify all copies with `rg` and name heuristics.
2. Write a **single** canonical function in `services/shared/` (or equivalent).
3. Replace call sites; delete old functions.
4. Run tests; add coverage for shared behavior.

**7.2 API handler slimming**

1. Move logic from router → service; preserve request validation.
2. Inject repositories/services; add tests.

**7.3 Background job hardening**

1. Add idempotency + dedupe key computation.
2. Wrap mutations in transaction.
3. Add metrics and structured logs.

---

## 8) Checklists (Claude must include these in PR body)

**NO‑DUPLICATE CHECKLIST**

* [ ] I searched for existing logic and found none **OR** consolidated duplicates.
* [ ] I removed dead/commented code and unused imports.
* [ ] I created/updated a shared module and rewired call sites.

**SCHEDULER SAFETY CHECKLIST** (if touched)

* [ ] Pure core functions unchanged/covered by tests.
* [ ] Deterministic + TZ‑aware verified by tests.
* [ ] Complexity acceptable; no N² regressions.

**SYNC SAFETY CHECKLIST** (Canvas/GCal/Gmail)

* [ ] Idempotent upserts; external IDs stored.
* [ ] Incremental tokens/etags handled.
* [ ] Rate‑limits/backoff implemented; retries bounded.

**SECURITY & PRIVACY**

* [ ] No secrets/PII in logs.
* [ ] Inputs validated; RLS respected.
* [ ] Keys managed via KMS/secrets manager.

**QUALITY GATES**

* [ ] ruff/black/isort/mypy pass.
* [ ] eslint/prettier/tsc pass.
* [ ] SwiftLint/SwiftFormat pass.
* [ ] Unit + integration tests added/updated and passing.

---

## 9) Commit & PR Standards

* **Commit message** format:

  * `feat(scope): clear one‑line summary`
  * `fix(scope): …`, `refactor(scope): …`, `chore(scope): …`, `test(scope): …`
* **PR Template** must include: Change Summary, Files Changed (with rationale), No‑Duplicate Proof, Test Plan, Risk & Rollback, Observability.

---

## 10) Example: Removing duplicate date parsing

**Anti‑pattern found:** `parse_ical()` duplicated in `calendar_utils.py` and `services/schedule/dates.py`.

**Action:**

* Create `backend/app/services/shared/dates.py` with a single `parse_ical()` and `to_utc()/from_utc()` helpers (TZ‑aware).
* Replace imports at call sites; delete old copies.
* Add unit tests to `tests/unit/services/shared/test_dates.py`.

---

## 11) Claude Output Contract (every change)

Claude must attach this to the end of its diff/explanation:

```
CHANGE SUMMARY:
- <what changed & why>

FILES CHANGED:
- <path>: <reason>
- <path>: <reason>

NO‑DUPLICATE PROOF:
- Searched for <keywords>. Consolidated <old paths> → <new shared path>.

TEST PLAN:
- Commands: <pytest>, <vitest>, <xcodebuild>…
- Cases: <list of representative cases>

RISK & ROLLBACK:
- Risks: <list>
- Rollback: <how to revert / feature flag>

OBSERVABILITY:
- Logs: <added where>
- Metrics: <added which counters/gauges>
```

---

## 12) Final Notes

* Prefer **composition over inheritance**. Prefer **pure core** + thin adapters.
* If a rule must be broken, document **why** and propose a **follow‑up** to restore invariants.
* When in doubt: **refactor first**, then implement.
