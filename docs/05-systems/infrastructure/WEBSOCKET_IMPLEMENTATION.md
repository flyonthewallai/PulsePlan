# WebSocket Real-time Agent Workflow Updates

## Overview

This implementation provides seamless real-time updates for agent workflows, replacing the previous polling mechanism with WebSocket-based live updates. Users now see task cards that update in real-time as workflows execute, providing instant feedback on search results and tool execution progress.

## Architecture

### Backend WebSocket Infrastructure

#### WebSocket Manager (`app/core/websocket.py`)

- Manages WebSocket connections using Socket.IO
- Handles authentication and user session management
- Manages workflow subscriptions and broadcasting
- Provides typed event emission methods

#### Key Features:

- **Authentication**: Token-based authentication for WebSocket connections
- **Subscription Management**: Users can subscribe to specific workflow IDs
- **Event Broadcasting**: Real-time emission of workflow events to subscribed clients
- **Error Handling**: Graceful handling of disconnections and failed messages

#### Event Types:

- `node_update`: Node status changes (executing, completed, failed)
- `tool_update`: Tool execution progress and results
- `search_results`: Complete search results with synthesis
- `workflow_status`: Overall workflow completion status

### Frontend WebSocket Client

#### Custom Hook (`src/hooks/useWorkflowWebSocket.ts`)

- React Native compatible WebSocket client using Socket.IO
- Typed event listeners for different update types
- Automatic connection management and reconnection
- Callback registration system for event handling

#### Key Features:

- **Auto-connect**: Automatically connects when user credentials are available
- **Event Filtering**: Separate callbacks for different event types
- **Connection State**: Real-time connection and authentication status
- **Cleanup**: Proper subscription cleanup on component unmount

### Integration with Search Workflow

#### Updated Search Graph (`backend/app/agents/graphs/search_graph.py`)

- All node functions now async to support WebSocket emission
- Real-time event emission at each workflow step:
  - Query analysis start/completion
  - Web search tool execution progress
  - Result synthesis and formatting
  - Final workflow completion

#### Task Card Updates (`src/components/AgentTaskCard.tsx`)

- Replaced polling with WebSocket subscriptions
- Real-time tool status updates
- Instant search result display
- Seamless status transitions

## Usage Example

### Frontend Component

```typescript
import { useWorkflowWebSocket } from "@/hooks/useWorkflowWebSocket";

const MyComponent = () => {
  const { subscribeToWorkflow, onSearchResults } = useWorkflowWebSocket({
    userId: user.id,
    token: user.access_token,
    autoConnect: true,
  });

  useEffect(() => {
    subscribeToWorkflow(workflowId);

    const unsubscribe = onSearchResults((results, workflowId) => {
      console.log("Search completed:", results);
      // Update UI with results
    });

    return unsubscribe;
  }, []);
};
```

### Backend Workflow Node

```python
async def web_search_node(self, state: WorkflowState) -> WorkflowState:
    workflow_id = state.get("trace_id", "unknown")

    # Emit tool start event
    await websocket_manager.emit_tool_update(workflow_id, "WebSearchTool", "executing")

    # Execute search
    search_result = await web_search_tool.execute(search_input, context)

    # Emit tool completion
    await websocket_manager.emit_tool_update(
        workflow_id,
        "WebSearchTool",
        "completed",
        f"Found {len(results)} results",
        execution_time
    )

    return state
```

## Benefits

### User Experience

- **Instant Feedback**: Users see live progress as searches execute
- **No Loading States**: Seamless transition from task initiation to results
- **Real-time Status**: Live tool execution progress and status updates
- **Immediate Results**: Search results appear as soon as available

### Technical Benefits

- **Reduced Server Load**: No more periodic polling requests
- **Lower Latency**: WebSocket connections provide instant updates
- **Better Scaling**: Eliminates polling overhead for many concurrent users
- **Cleaner Architecture**: Event-driven updates instead of request/response cycles

### Development Benefits

- **Type Safety**: Fully typed WebSocket events and handlers
- **Reusable**: WebSocket hook can be used for any workflow type
- **Extensible**: Easy to add new event types for different workflows
- **Backwards Compatible**: Falls back to simulation if WebSocket unavailable

## Event Flow

### Search Workflow Example

1. User submits search query
2. Frontend receives immediate task card response
3. Frontend subscribes to workflow WebSocket updates
4. Backend search workflow begins execution:
   - Emits `node_update` for query analysis
   - Emits `tool_update` for web search execution
   - Emits `search_results` with complete results
   - Emits `workflow_status` for completion
5. Frontend receives events and updates UI in real-time
6. User sees seamless progression from query to results

## Configuration

### Backend Dependencies

- `python-socketio==5.10.0` - Socket.IO server implementation
- FastAPI integration via `socketio.ASGIApp`

### Frontend Dependencies

- `socket.io-client` - Socket.IO client for React Native
- Configured with CORS and proper transport fallbacks

### Environment Variables

No additional environment variables required. Uses existing FastAPI configuration.

## Error Handling

### Connection Issues

- Automatic reconnection on disconnect
- Fallback to simulation if WebSocket unavailable
- Graceful handling of authentication failures

### Workflow Errors

- Error events broadcast to subscribed clients
- UI shows failed status with error details
- Proper cleanup on workflow failures

## Future Enhancements

### Planned Features

1. **Message Queuing**: Ensure event delivery even during brief disconnections
2. **Room-based Broadcasting**: Efficient scaling for multiple concurrent workflows
3. **Event History**: Allow clients to request recent events on reconnection
4. **Rate Limiting**: Prevent WebSocket event spam
5. **Metrics**: WebSocket connection and event metrics for monitoring

### Additional Workflow Types

- Calendar operations with real-time updates
- Task management with live synchronization
- Email sending with delivery confirmations
- Multi-step scheduling with progress tracking

## Monitoring

### WebSocket Statistics Endpoint

- `GET /api/v1/websocket/stats` - Current connection metrics
- Total connections, unique users, active workflows
- Useful for monitoring and debugging

### Logging

- Comprehensive logging of WebSocket events
- Connection lifecycle tracking
- Error logging with context

## Testing

### Manual Testing

1. Start backend with WebSocket support
2. Connect frontend client
3. Submit search query
4. Verify real-time updates in browser dev tools
5. Check task card updates happen instantly

### Integration Testing

- WebSocket connection and authentication
- Event emission and reception
- Subscription management
- Error handling and recovery

## Migration from Polling

### Key Changes

1. Removed polling logic from `AgentTaskCard.tsx`
2. Added WebSocket subscription in task card lifecycle
3. Updated search graph to emit events at each step
4. Added fallback simulation for backwards compatibility

### Backwards Compatibility

- Old polling endpoints still available
- Simulation fallback if WebSocket not connected
- Graceful degradation for unsupported clients

This WebSocket implementation provides a foundation for real-time updates across all agent workflows, significantly improving user experience while reducing server overhead.

## Implementation Status

✅ **COMPLETED** - The WebSocket implementation has been successfully completed and tested. The backend is running with WebSocket support, and the frontend has been updated to use real-time updates instead of polling.

### What's Working:

- ✅ WebSocket server running on FastAPI with Socket.IO
- ✅ Authentication using Supabase tokens
- ✅ Real-time workflow updates for search operations
- ✅ Frontend WebSocket client hook (`useWorkflowWebSocket`)
- ✅ AgentTaskCard component updated to use WebSocket events
- ✅ Search workflow emits real-time updates at each step
- ✅ Fallback simulation for non-search tasks or when WebSockets are unavailable

### Testing Results:

- ✅ Backend starts successfully with WebSocket support
- ✅ Health endpoint responds correctly
- ✅ WebSocket stats endpoint accessible
- ✅ No more Socket.IO compatibility issues
- ✅ Authentication integration working with existing auth system
