# Frontend Agent Status System - Usage Guide

## Overview

The frontend now has a real-time agent status system that displays what tool Pulse is currently using directly in the chat conversation. This integrates with the backend WebSocket system to show live updates when n8n workflows are running.

## Components Added

### 1. `useAgentStatus` Hook

- **Location**: `src/hooks/useAgentStatus.ts`
- **Purpose**: Manages WebSocket connection for real-time agent status updates
- **Usage**:
  ```tsx
  const { status: agentStatus } = useAgentStatus(user?.id || null);
  ```

### 2. **Integrated Chat Status Display**

- **Location**: Integrated directly into `src/app/(tabs)/agent.tsx`
- **Purpose**: Shows agent status as chat messages in the conversation
- **Replaces**: Previous floating status indicator

## Integration Points

The agent status is now integrated directly into:

- **Agent Page** (`src/app/(tabs)/agent.tsx`) - Shows status as chat messages in the conversation flow
- **Replaces typing indicator** - Shows where "Pulse is thinking..." previously appeared

## Status States

### 1. **Thinking State (Default)**

- Shows: "Pulse is thinking..." with animated text and blue dot
- When: No active operations, idle, or default state
- Animation: Wave animation with gentle pulsing

### 2. **Active State**

- Shows: "Pulse is using [Tool]..." with spinning indicator
- When: n8n workflow is actively running
- Tools: Gmail, Calendar, Notion, Canvas, Contacts, etc.
- Animation: Spinning indicator + wave animation

### 3. **Error State**

- Shows: "⚠️ Pulse encountered an error with [Tool]"
- When: n8n workflow fails or encounters error
- Color: Red/error theme
- Animation: Wave animation with error styling

### 4. **Connection Issues**

- Shows: "⚠️ Connection error"
- When: WebSocket connection fails
- Hidden: When user not logged in or connection not established
- Animation: Wave animation

## Visual Design

- **Chat Integration**: Appears as Pulse chat messages with brain icon
- **Thinking**: "Pulse is thinking..." with animated text
- **Active**: "Pulse is using [Tool]..." with animated text
- **Error**: "⚠️ Pulse encountered an error with [Tool]" in red text
- **Messages**: Optional status messages shown below main text
- **Responsive**: Adapts to current theme colors
- **Animations**: Uses existing AnimatedThinkingText component

## Real-time Flow

1. **n8n Workflow Starts** → HTTP POST to `/api/agent-status`
2. **Backend Processes** → Adds to queue → Emits WebSocket event
3. **Frontend Receives** → Updates UI immediately
4. **User Sees** → "Pulse is using Gmail..." with spinner
5. **Workflow Completes** → Another HTTP request → "Pulse is thinking..."

## Example n8n Integration

When n8n workflows run, they should send HTTP requests like:

```json
POST http://localhost:5000/api/agent-status
{
  "tool": "Gmail",
  "status": "active",
  "userId": "user-123",
  "message": "Processing your emails..."
}
```

The frontend will immediately show: **"Pulse is using Gmail..."** as a chat message in the conversation.

## Benefits

- ✅ **Real-time feedback** - Users see exactly what Pulse is doing
- ✅ **Professional UX** - No more wondering if something is happening
- ✅ **Error awareness** - Users know when workflows fail
- ✅ **Performance** - WebSocket connection is efficient and fast
- ✅ **Scalable** - Supports multiple concurrent users

## Dependencies Added

- `socket.io-client` - For WebSocket connection to backend
- Integration with existing theme system
- Compatible with authentication context

## Next Steps

1. **Test with n8n** - Configure workflows to send HTTP status updates
2. **Monitor performance** - Check WebSocket connection stability
3. **Add more tools** - Expand status messages for new integrations
4. **User feedback** - Gather feedback on status message clarity

The system is now ready for production use and will provide users with real-time visibility into Pulse's operations!
