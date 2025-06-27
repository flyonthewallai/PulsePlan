# Agent Status System Integration

This document explains how to integrate with the PulsePlan Agent Status System to provide real-time feedback to users about which tools the AI agent is currently using.

## Overview

The agent status system provides:

- **HTTP endpoints** for n8n workflows to send status updates
- **Queue system** to handle multiple status updates without blocking
- **WebSocket support** for real-time frontend updates
- **Event-driven architecture** for extensibility

## Architecture

```
n8n Workflow → HTTP POST → Queue → Processing → WebSocket → Frontend
```

## HTTP API Endpoints

### 1. Update Agent Status (for n8n)

**POST** `/api/agent-status`

Send status updates from n8n workflows.

**Request Body:**

```json
{
  "tool": "Gmail",
  "status": "active",
  "userId": "user-123",
  "message": "Processing emails",
  "metadata": {
    "workflowId": "workflow-456",
    "executionId": "exec-789"
  }
}
```

**Status Values:**

- `active` - Tool is currently being used
- `completed` - Tool finished successfully
- `error` - Tool encountered an error
- `idle` - Agent is idle (no active tools)

**Response:**

```json
{
  "success": true,
  "message": "Agent status update queued successfully",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Get Current Status (for frontend)

**GET** `/api/agent-status`

Get current agent status for authenticated user.

**Headers:**

```
Authorization: Bearer <jwt-token>
```

**Response:**

```json
{
  "userId": "user-123",
  "currentTool": "Gmail",
  "status": "active",
  "lastUpdate": "2024-01-15T10:30:00.000Z",
  "toolHistory": [
    {
      "tool": "Gmail",
      "status": "active",
      "timestamp": "2024-01-15T10:30:00.000Z",
      "message": "Processing emails"
    }
  ]
}
```

### 3. Get Queue Statistics

**GET** `/api/agent-status/stats`

Get system statistics (for monitoring).

**Response:**

```json
{
  "totalUsers": 5,
  "totalQueuedItems": 2,
  "processingUsers": 1,
  "activeUsers": 3,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## n8n Integration

### Step 1: Add HTTP Request Node

In each n8n sub-workflow, add an **HTTP Request** node right after the entry point:

**Node Configuration:**

- **Method:** POST
- **URL:** `https://your-backend.com/api/agent-status`
- **Headers:**
  ```json
  {
    "Content-Type": "application/json"
  }
  ```

### Step 2: Configure Request Body

**For Tool Start:**

```json
{
  "tool": "Gmail",
  "status": "active",
  "userId": "{{ $json.userId }}",
  "message": "Starting email processing",
  "metadata": {
    "workflowId": "{{ $workflow.id }}",
    "executionId": "{{ $execution.id }}",
    "nodeId": "gmail-processor"
  }
}
```

**For Tool Completion:**

```json
{
  "tool": "Gmail",
  "status": "completed",
  "userId": "{{ $json.userId }}",
  "message": "Email processing completed successfully",
  "metadata": {
    "workflowId": "{{ $workflow.id }}",
    "executionId": "{{ $execution.id }}",
    "itemsProcessed": "{{ $json.emailCount }}"
  }
}
```

**For Tool Error:**

```json
{
  "tool": "Gmail",
  "status": "error",
  "userId": "{{ $json.userId }}",
  "message": "Email processing failed: {{ $json.error.message }}",
  "metadata": {
    "workflowId": "{{ $workflow.id }}",
    "executionId": "{{ $execution.id }}",
    "errorCode": "{{ $json.error.code }}"
  }
}
```

### Step 3: Tool Names

Use consistent tool names across workflows:

- `Gmail` - Email processing
- `Calendar` - Calendar operations
- `Notion` - Note-taking and organization
- `Canvas` - Learning management
- `Contacts` - Contact management
- `Scheduling` - Intelligent scheduling
- `Tasks` - Task management
- `Analysis` - Data analysis
- `Research` - Web research
- `Planning` - Strategic planning

### Step 4: Workflow Examples

**Gmail Workflow:**

```
Start → HTTP Status (active) → Gmail API → Process Emails → HTTP Status (completed) → End
                                     ↓
                              Error Handler → HTTP Status (error)
```

**Calendar Workflow:**

```
Start → HTTP Status (active) → Calendar API → Sync Events → HTTP Status (completed) → End
                                        ↓
                               Error Handler → HTTP Status (error)
```

## Frontend Integration

### WebSocket Connection

```typescript
import io from "socket.io-client";

const socket = io("http://localhost:5000");

// Authenticate
socket.emit("authenticate", {
  userId: "user-123",
  userEmail: "user@example.com",
});

// Listen for status updates
socket.on("agent_status_update", (data) => {
  console.log("Agent status update:", data);
  updateUI(data.status);
});

// Listen for authentication confirmation
socket.on("authenticated", (data) => {
  console.log("WebSocket authenticated:", data);
});

// Handle errors
socket.on("auth_error", (error) => {
  console.error("WebSocket auth error:", error);
});
```

### React Hook Example

```typescript
import { useState, useEffect } from "react";
import io, { Socket } from "socket.io-client";

interface AgentStatus {
  currentTool?: string;
  status: "idle" | "active" | "error";
  lastUpdate: string;
  toolHistory: Array<{
    tool: string;
    status: string;
    timestamp: string;
    message?: string;
  }>;
}

export const useAgentStatus = (userId: string) => {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    const newSocket = io("http://localhost:5000");

    newSocket.emit("authenticate", { userId });

    newSocket.on("agent_status", (data: AgentStatus) => {
      setStatus(data);
    });

    newSocket.on("agent_status_update", (data: any) => {
      setStatus(data.status);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [userId]);

  return { status, socket };
};
```

### UI Component Example

```typescript
import React from "react";
import { useAgentStatus } from "./hooks/useAgentStatus";

const AgentStatusIndicator: React.FC<{ userId: string }> = ({ userId }) => {
  const { status } = useAgentStatus(userId);

  if (!status || status.status === "idle") {
    return <div className="agent-status idle">Pulse is ready</div>;
  }

  if (status.status === "error") {
    return (
      <div className="agent-status error">
        ⚠️ Pulse encountered an error with {status.currentTool}
      </div>
    );
  }

  return (
    <div className="agent-status active">
      <div className="spinner" />
      Pulse is using {status.currentTool}...
    </div>
  );
};

export default AgentStatusIndicator;
```

## Performance Considerations

### Queue System

- **Automatic queuing** prevents overwhelming the system
- **100ms delay** between processing items
- **50 item limit** per user queue
- **Automatic cleanup** of old statuses

### WebSocket Optimization

- **Per-user broadcasting** (not global)
- **Event-driven updates** only when status changes
- **Connection tracking** for efficient resource usage

### Memory Management

- **20 item history limit** per user
- **24-hour automatic cleanup** of old statuses
- **Efficient Map-based storage**

## Monitoring and Debugging

### Health Check

```bash
curl http://localhost:5000/api/agent-status/stats
```

### Log Messages

The system provides detailed logging:

- `📊 Agent status queued` - Status added to queue
- `🔄 Agent status updated` - Status processed
- `📡 Broadcasted` - WebSocket message sent
- `🗑️ Cleared agent status` - User status cleaned up

### Testing

Run the test suite:

```bash
npm run build
node dist/scripts/test-agent-status.js
```

## Security

### Authentication

- **No authentication required** for n8n POST requests (internal)
- **JWT authentication required** for GET requests (frontend)
- **User isolation** - users only see their own status

### Rate Limiting

Consider adding rate limiting for production:

```typescript
// Add to routes/agentStatusRoutes.ts
import rateLimit from "express-rate-limit";

const statusUpdateLimit = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute
  message: "Too many status updates",
});

router.post("/", statusUpdateLimit, updateAgentStatus);
```

## Troubleshooting

### Common Issues

1. **Status not updating**

   - Check n8n HTTP request configuration
   - Verify userId is being passed correctly
   - Check server logs for errors

2. **WebSocket not connecting**

   - Verify CORS configuration
   - Check authentication payload
   - Ensure Socket.IO client version compatibility

3. **Queue backing up**
   - Check for processing errors in logs
   - Monitor queue statistics endpoint
   - Verify user cleanup is working

### Debug Mode

Enable detailed logging:

```typescript
// In development
console.log("Debug mode enabled");
agentStatusService.on("statusUpdate", console.log);
```

## Examples

### Complete n8n Workflow Integration

1. **Workflow Start Node:**

```json
{
  "tool": "Gmail",
  "status": "active",
  "userId": "{{ $json.userId }}",
  "message": "Starting Gmail integration"
}
```

2. **Workflow Success Node:**

```json
{
  "tool": "Gmail",
  "status": "completed",
  "userId": "{{ $json.userId }}",
  "message": "Successfully processed {{ $json.emailCount }} emails"
}
```

3. **Workflow Error Node:**

```json
{
  "tool": "Gmail",
  "status": "error",
  "userId": "{{ $json.userId }}",
  "message": "Gmail API error: {{ $json.error.message }}"
}
```

This system provides a simple yet powerful way to give users real-time insight into what their AI agent is doing, improving transparency and user experience.
