# Agent Status System - Quick Start

## Overview

Real-time agent status system that shows users which tool Pulse is currently using.

## Architecture

```
n8n Workflow → HTTP POST → Queue → Processing → WebSocket → Frontend UI
```

## Quick Setup

### 1. Backend (Already Implemented)

- ✅ HTTP endpoint: `POST /api/agent-status`
- ✅ WebSocket support with Socket.IO
- ✅ Queue system for handling multiple updates
- ✅ Authentication for frontend requests

### 2. Test the System

**Start the server:**

```bash
npm run build
npm run dev
```

**Test the queue system:**

```bash
node dist/scripts/test-agent-status.js
```

**Test HTTP endpoint (with server running):**

```bash
node dist/scripts/test-http-endpoint.js
```

### 3. n8n Integration

Add HTTP Request node to each workflow:

**URL:** `http://your-backend.com/api/agent-status`
**Method:** POST
**Body:**

```json
{
  "tool": "Gmail",
  "status": "active",
  "userId": "{{ $json.userId }}",
  "message": "Processing emails"
}
```

### 4. Frontend Integration

**Install Socket.IO client:**

```bash
npm install socket.io-client
```

**React Hook:**

```typescript
import { useState, useEffect } from "react";
import io from "socket.io-client";

export const useAgentStatus = (userId: string) => {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const socket = io("http://localhost:5000");

    socket.emit("authenticate", { userId });

    socket.on("agent_status_update", (data) => {
      setStatus(data.status);
    });

    return () => socket.close();
  }, [userId]);

  return status;
};
```

**UI Component:**

```typescript
const AgentStatus = ({ userId }) => {
  const status = useAgentStatus(userId);

  if (!status || status.status === "idle") {
    return <div>Pulse is ready</div>;
  }

  return (
    <div>
      <div className="spinner" />
      Pulse is using {status.currentTool}...
    </div>
  );
};
```

## API Endpoints

| Method | Endpoint                  | Purpose            | Auth Required |
| ------ | ------------------------- | ------------------ | ------------- |
| POST   | `/api/agent-status`       | n8n status updates | No            |
| GET    | `/api/agent-status`       | Get user status    | Yes           |
| GET    | `/api/agent-status/stats` | System statistics  | Yes           |
| DELETE | `/api/agent-status`       | Clear user status  | Yes           |

## Status Values

- `active` - Tool is currently running
- `completed` - Tool finished successfully
- `error` - Tool encountered an error
- `idle` - No active tools

## Tool Names

Use consistent names across workflows:

- `Gmail`, `Calendar`, `Notion`, `Canvas`, `Contacts`
- `Scheduling`, `Tasks`, `Analysis`, `Research`, `Planning`

## Performance Features

- ✅ **Queue system** - Handles rapid updates without blocking
- ✅ **Per-user isolation** - Users only see their own status
- ✅ **Memory management** - Automatic cleanup of old data
- ✅ **WebSocket optimization** - Efficient real-time updates
- ✅ **Error handling** - Robust error recovery

## Monitoring

**Check system health:**

```bash
curl http://localhost:5000/api/agent-status/stats
```

**View logs:**

- `📊 Agent status queued` - Status added to queue
- `🔄 Agent status updated` - Status processed
- `📡 Broadcasted` - WebSocket message sent

## Next Steps

1. **Configure n8n workflows** with HTTP Request nodes
2. **Implement frontend WebSocket connection**
3. **Add rate limiting** for production
4. **Set up monitoring** and alerting
5. **Test with real workflows** and user scenarios

The system is designed to be simple, performant, and provide great user insight into AI agent activities!
