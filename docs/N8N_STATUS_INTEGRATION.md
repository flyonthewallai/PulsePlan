# n8n Status Integration Guide

## Overview

This guide explains how to integrate n8n workflows with Pulse's real-time status system. When n8n workflows run, they can send HTTP requests to notify the frontend about their progress, allowing users to see real-time updates about what Pulse is doing.

## Architecture

```
n8n Workflow → HTTP Request → Backend → WebSocket → Frontend UI
```

## Available Endpoints

### 1. Workflow Start Notification

**POST** `/api/n8n/status/start`

Notify when a workflow begins execution.

**Request Body:**

```json
{
  "userId": "user-123",
  "workflowName": "Email Processing",
  "message": "Starting email analysis..."
}
```

**Response:**

```json
{
  "success": true,
  "message": "Workflow start notification sent successfully",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Workflow Completion Notification

**POST** `/api/n8n/status/complete`

Notify when a workflow completes successfully.

**Request Body:**

```json
{
  "userId": "user-123",
  "workflowName": "Email Processing",
  "message": "Processed 15 emails successfully"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Workflow completion notification sent successfully",
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

### 3. Workflow Error Notification

**POST** `/api/n8n/status/error`

Notify when a workflow encounters an error.

**Request Body:**

```json
{
  "userId": "user-123",
  "workflowName": "Email Processing",
  "error": "Failed to authenticate with Gmail API"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Workflow error notification sent successfully",
  "timestamp": "2024-01-15T10:32:00.000Z"
}
```

### 4. Subworkflow Status Update

**POST** `/api/n8n/status/subworkflow`

Notify when entering or completing a subworkflow.

**Request Body:**

```json
{
  "userId": "user-123",
  "mainWorkflow": "Email Processing",
  "subworkflow": "Gmail API",
  "status": "active",
  "message": "Fetching emails from Gmail..."
}
```

**Status Values:**

- `active`: Subworkflow is running
- `completed`: Subworkflow finished successfully
- `error`: Subworkflow encountered an error

**Response:**

```json
{
  "success": true,
  "message": "Subworkflow status notification sent successfully",
  "timestamp": "2024-01-15T10:31:00.000Z"
}
```

### 5. Custom Status Update

**POST** `/api/n8n/status/custom`

Send any custom status update.

**Request Body:**

```json
{
  "userId": "user-123",
  "tool": "Calendar Sync",
  "status": "active",
  "message": "Syncing calendar events...",
  "metadata": {
    "eventsProcessed": 25,
    "totalEvents": 100
  }
}
```

**Status Values:**

- `active`: Tool/workflow is running
- `completed`: Tool/workflow finished successfully
- `error`: Tool/workflow encountered an error
- `idle`: Tool/workflow is idle

**Response:**

```json
{
  "success": true,
  "message": "Custom status notification sent successfully",
  "timestamp": "2024-01-15T10:33:00.000Z"
}
```

## n8n Integration Examples

### Example 1: Basic Workflow with Status Updates

```javascript
// At the start of your workflow
const startResponse = await fetch(
  "http://localhost:5000/api/n8n/status/start",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      userId: "{{ $json.userId }}",
      workflowName: "Email Processing",
      message: "Starting email analysis workflow...",
    }),
  }
);

// In the middle of your workflow (subworkflow)
const subworkflowResponse = await fetch(
  "http://localhost:5000/api/n8n/status/subworkflow",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      userId: "{{ $json.userId }}",
      mainWorkflow: "Email Processing",
      subworkflow: "Gmail API",
      status: "active",
      message: "Fetching emails from Gmail...",
    }),
  }
);

// At the end of your workflow
const completeResponse = await fetch(
  "http://localhost:5000/api/n8n/status/complete",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      userId: "{{ $json.userId }}",
      workflowName: "Email Processing",
      message: "Successfully processed 15 emails",
    }),
  }
);
```

### Example 2: Error Handling

```javascript
// In your error handling node
try {
  // Your workflow logic
} catch (error) {
  const errorResponse = await fetch(
    "http://localhost:5000/api/n8n/status/error",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        userId: "{{ $json.userId }}",
        workflowName: "Email Processing",
        error: error.message,
      }),
    }
  );

  throw error; // Re-throw to stop workflow
}
```

### Example 3: Complex Workflow with Multiple Subworkflows

```javascript
// Main workflow starts
await fetch("http://localhost:5000/api/n8n/status/start", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "{{ $json.userId }}",
    workflowName: "Daily Briefing",
    message: "Starting daily briefing generation...",
  }),
});

// Subworkflow 1: Email Analysis
await fetch("http://localhost:5000/api/n8n/status/subworkflow", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "{{ $json.userId }}",
    mainWorkflow: "Daily Briefing",
    subworkflow: "Email Analysis",
    status: "active",
    message: "Analyzing today's emails...",
  }),
});

// After email analysis completes
await fetch("http://localhost:5000/api/n8n/status/subworkflow", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "{{ $json.userId }}",
    mainWorkflow: "Daily Briefing",
    subworkflow: "Email Analysis",
    status: "completed",
    message: "Found 5 important emails",
  }),
});

// Subworkflow 2: Calendar Analysis
await fetch("http://localhost:5000/api/n8n/status/subworkflow", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "{{ $json.userId }}",
    mainWorkflow: "Daily Briefing",
    subworkflow: "Calendar Analysis",
    status: "active",
    message: "Checking today's calendar...",
  }),
});

// Main workflow completes
await fetch("http://localhost:5000/api/n8n/status/complete", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "{{ $json.userId }}",
    workflowName: "Daily Briefing",
    message: "Daily briefing generated successfully",
  }),
});
```

## Frontend Display

When n8n sends these status updates, the frontend will display:

1. **Workflow Start**: "Pulse is using [WorkflowName]..."
2. **Subworkflow Active**: "Pulse is using [MainWorkflow] > [Subworkflow]..."
3. **Workflow Complete**: Status returns to "Pulse is thinking..."
4. **Workflow Error**: "⚠️ Pulse encountered an error with [WorkflowName]"

## Best Practices

### 1. Always Include userId

Make sure every request includes the `userId` field so the status updates are sent to the correct user.

### 2. Use Descriptive Messages

Provide clear, user-friendly messages that explain what Pulse is doing.

### 3. Handle Errors Gracefully

Always send error notifications when workflows fail, and include meaningful error messages.

### 4. Update Status Frequently

Send status updates for major steps in your workflow to keep users informed.

### 5. Use Subworkflows for Complex Processes

Break down complex workflows into subworkflows and send status updates for each step.

## Testing

### Test with curl

```bash
# Test workflow start
curl -X POST http://localhost:5000/api/n8n/status/start \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-user-123",
    "workflowName": "Test Workflow",
    "message": "Testing status updates..."
  }'

# Test subworkflow status
curl -X POST http://localhost:5000/api/n8n/status/subworkflow \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-user-123",
    "mainWorkflow": "Test Workflow",
    "subworkflow": "Test Subworkflow",
    "status": "active",
    "message": "Testing subworkflow..."
  }'

# Test workflow completion
curl -X POST http://localhost:5000/api/n8n/status/complete \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-user-123",
    "workflowName": "Test Workflow",
    "message": "Test completed successfully"
  }'
```

### Monitor WebSocket Events

Check the server logs to see WebSocket events being broadcast:

```bash
# Server logs will show:
📊 Agent status updated: test-user-123 - Test Workflow - active
📡 Broadcasted agent_status_update to 1 socket(s) for user test-user-123
```

## Troubleshooting

### Common Issues

1. **Status not appearing in frontend**

   - Check that the WebSocket connection is established
   - Verify the `userId` matches the authenticated user
   - Check server logs for WebSocket broadcast messages

2. **HTTP request fails**

   - Verify the server is running on the correct port
   - Check that the endpoint URL is correct
   - Ensure all required fields are included in the request

3. **Status updates not real-time**
   - Check WebSocket connection status in browser dev tools
   - Verify the frontend is listening for `agent_status_update` events
   - Check server logs for WebSocket connection issues

### Debug Mode

Enable debug logging by checking the server console for:

- WebSocket connection messages
- Agent status update logs
- Broadcast confirmation messages

## Security Priorities & Hardening

### Immediate Security Concerns

**1. Token Security & Rotation**
- Store OAuth tokens per-user encrypted (KMS or libsodium), add token_version, rotation jobs, and least-privilege scopes per provider
- Add a central token refresh service (async job) with jittered backoff and circuit breakers; never refresh on hot paths

**2. Policy/Guardrails Layer**
- Add a small policies/ module (or table) enforcing: allowed tools per user, scopes, time windows, write permissions
- Gate every agent step through it and log policy decisions

**3. Idempotency & Exactly-Once**
- Create an idempotency_records table (keyed by user_id + effect_hash, TTL) and require it for side-effects (calendar creates, emails, task writes)

**4. DecisionTrace with Redaction**
- Keep the trace, but add PII redaction (emails, subjects, event titles) and prompt/version metadata:
- model, prompt_id/version, temperature, tool_versions, policy_version

**5. Rate Limiting Granularity**
- Keep SlowAPI for HTTP, and implement per-integration token buckets in Redis (keyed user_id:google_calendar, etc.) with burst + sustained limits
- Add global provider caps

### Architecture Priorities

**1. Agent Graph Shape**
- Formalize across graphs: Plan → Gate(Policy/Rate) → Execute(Tool) → Reconcile(Conflicts) → Summarize(Trace/Event)
- Keep tool calls deterministic; avoid hidden routers

**2. Bridge-Free Cutover (no external orchestrator)**
- Implement LangGraph orchestration in the backend now; do not keep any external flow engine
- For legacy behaviors, re-encode flows directly as graphs and typed tools
- Use feature flags to roll out by cohort and a kill switch to fall back to a safe, read-only plan (no writes) if needed—still inside the same backend

### Data Model Additions (minimal)

```sql
decision_traces(
  id, job_id, user_id, inputs, steps, policy_checks, 
  summary, model, prompt_id, prompt_version, created_at
)

idempotency_records(
  user_id, effect_hash, created_at, ttl
)

oauth_tokens(
  user_id, provider, enc_access_token, enc_refresh_token, 
  expires_at, scopes, token_version
)

rate_counters(
  user_id, integration, window_start, count
) -- or just Redis
```

### Project Structure Tweaks

Add focused modules:
```
app/
  policies/                # gates, scopes, ABAC rules
  ratelimit/               # Redis token buckets per integration
  idempotency/             # effect keys, dedupe helpers
  prompts/                 # prompt registry (versioned)
  traces/                  # DecisionTrace writer + redactors
  repositories/            # DB read/write boundaries
```

### Security Checklist (MVP-ready)

- HSTS, TLS 1.2+, strict CORS allowlist, JWT with per-session JTI and short TTL + refresh
- Webhooks: HMAC verify, timestamp skew check, idempotency
- Secrets: no provider tokens in logs/traces; mask at source
- Data residency & FERPA (Canvas): document data classes and retention

### Migration Plan Priority

**Phase 1 (Immediate)**: Token security + policies implementation
**Phase 2**: LangGraph cutover - becomes sole orchestrator by end of phase
**Phase 3-4**: Port remaining behaviors as graphs/tools, maintain single backend throughout

### Performance & Deployment

- Uvicorn: start with workers = CPU*2 for API; separate Dramatiq worker pool
- httpx: enable connection pooling
- Redis: enable client-side caching for hot keys (rate counters, small caches)
- Caching: cache Canvas lists & calendar reads with conservative TTL + ETag/If-None-Match where supported

### Testing & SLOs

**SLOs**: P50 plan ≤ 600 ms, P95 tool call ≤ 1.5 s, job success ≥ 99.5%, webhook verify 100%

**Testing Matrix**:
- Contract tests (OpenAPI snapshot)
- respx/VCR for HTTP 
- Property-based tests for schedulers
- Golden-path agent runs asserting DecisionTrace steps
- Chaos tests for upstream 429/5xx

**Fail Drills**: provider 429 storm, token expiry mid-flow, Redis outage (graceful degrade), email provider 5xx

## Current Security Notes

- These endpoints do not require authentication since n8n needs to send updates directly
- The `userId` field is used to route updates to the correct user
- **CRITICAL**: Implement rate limiting and HMAC verification immediately for production
- Monitor for potential abuse of these endpoints
- Add request validation and sanitization for all status message fields
