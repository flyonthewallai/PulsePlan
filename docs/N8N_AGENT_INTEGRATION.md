# n8n Agent Integration Documentation

## Overview

The PulsePlan backend now integrates with a hosted n8n agent at `https://pulseplan-agent.fly.dev/` to enable intelligent task scheduling, automation, and advanced workflow capabilities.

## Architecture

```
PulsePlan Backend (Express.js) → n8n Agent (Fly.dev) → Task Processing & Automation
```

## Configuration

### Environment Variables

Add these optional environment variables to your `.env` file:

```env
# n8n Agent Configuration
N8N_AGENT_URL=https://pulseplan-agent.fly.dev
N8N_WEBHOOK_PATH=/webhook/agent
N8N_TIMEOUT=10000
N8N_RETRY_ATTEMPTS=3
N8N_RETRY_DELAY=1000
N8N_HEALTH_CHECK_INTERVAL=30000

# Feature Flags
N8N_ENABLE_BATCH_PROCESSING=true
N8N_ENABLE_INTELLIGENT_RESCHEDULING=true
N8N_ENABLE_STUDY_OPTIMIZATION=true
N8N_ENABLE_DEADLINE_ANALYSIS=true

# Logging
N8N_ENABLE_LOGGING=true
N8N_LOG_LEVEL=info
```

## API Endpoints

### Basic Agent Operations

#### 1. Health Check

```http
GET /agent/health
Authorization: Bearer <token>
```

**Response:**

```json
{
  "healthy": true,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "agent_url": "https://pulseplan-agent.fly.dev"
}
```

#### 2. Create Task with Agent

```http
POST /agent/task
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Study for Chemistry Exam",
  "dueDate": "2024-01-22T20:00:00.000Z",
  "duration": 120,
  "priority": "high",
  "subject": "Chemistry",
  "tool": "smart-schedule"
}
```

#### 3. Create User Task

```http
POST /agent/user-task
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Finish Math Homework",
  "dueDate": "2024-01-18T23:59:00.000Z",
  "duration": 90,
  "priority": "medium",
  "subject": "Mathematics"
}
```

#### 4. Custom Agent Request

```http
POST /agent/custom
Authorization: Bearer <token>
Content-Type: application/json

{
  "taskTitle": "Custom Task",
  "dueDate": "2024-01-20T15:00:00.000Z",
  "duration": 60,
  "priority": "low",
  "subject": "Custom",
  "source": "user",
  "tool": "custom-tool",
  "customField": "any custom data",
  "metadata": {
    "key": "value"
  }
}
```

### Advanced Operations

#### 5. Batch Process Tasks

```http
POST /agent/batch-process
Authorization: Bearer <token>
Content-Type: application/json

{
  "tasks": [
    {
      "title": "Study Biology Chapter 1",
      "dueDate": "2024-01-19T18:00:00.000Z",
      "duration": 90,
      "priority": "high",
      "subject": "Biology"
    },
    {
      "title": "Complete Physics Lab Report",
      "dueDate": "2024-01-21T09:00:00.000Z",
      "duration": 120,
      "priority": "medium",
      "subject": "Physics"
    }
  ],
  "preferences": {
    "preferredWorkingHours": {
      "start": "09:00",
      "end": "17:00"
    },
    "breakDuration": 15,
    "focusSessionDuration": 45
  }
}
```

#### 6. Intelligent Rescheduling

```http
POST /agent/reschedule
Authorization: Bearer <token>
Content-Type: application/json

{
  "includeCompleted": false,
  "priorityFilter": "high",
  "subjectFilter": "Mathematics"
}
```

#### 7. Study Session Optimization

```http
POST /agent/optimize-session
Authorization: Bearer <token>
Content-Type: application/json

{
  "availableHours": 3,
  "subjects": ["Chemistry", "Biology"],
  "preferredDifficulty": "medium",
  "sessionType": "focus"
}
```

#### 8. Deadline Analysis

```http
POST /agent/analyze-deadlines
Authorization: Bearer <token>
Content-Type: application/json

{
  "daysAhead": 7,
  "includeCompleted": false
}
```

## Enhanced Task Creation

### Using the Enhanced Task Controller

The existing `/tasks` endpoint now supports agent integration:

```http
POST /tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Study for Final Exam",
  "description": "Comprehensive review for Chemistry final",
  "subject": "Chemistry",
  "due_date": "2024-01-25T10:00:00.000Z",
  "estimated_minutes": 180,
  "status": "pending",
  "priority": "high",
  "use_agent": true
}
```

**Response with Agent Processing:**

```json
{
  "id": "task-123",
  "title": "Study for Final Exam",
  "user_id": "user-456",
  "subject": "Chemistry",
  "due_date": "2024-01-25T10:00:00.000Z",
  "estimated_minutes": 180,
  "status": "pending",
  "priority": "high",
  "created_at": "2024-01-15T10:30:00.000Z",
  "agent_processed": true,
  "agent_message": "Successfully processed by n8n agent",
  "agent_data": {
    "scheduled_blocks": [...],
    "calendar_events": [...],
    "recommendations": [...]
  }
}
```

## Service Usage in Code

### Using the N8nAgentService

```typescript
import { n8nAgentService } from "../services/n8nAgentService";

// Basic task creation
const response = await n8nAgentService.createTaskFromUser(
  userId,
  "Study for Chemistry Exam",
  "2024-01-22T20:00:00.000Z",
  120,
  "high",
  "Chemistry"
);

// Agent-driven task with tool
const agentResponse = await n8nAgentService.createTaskWithAgent(
  userId,
  "Intelligent Study Session",
  "2024-01-20T15:00:00.000Z",
  90,
  "medium",
  "Mathematics",
  "smart-schedule"
);

// Custom payload
const customResponse = await n8nAgentService.postToAgent({
  userId,
  taskTitle: "Custom Task",
  dueDate: "2024-01-18T14:00:00.000Z",
  duration: 60,
  priority: "low",
  subject: "Custom",
  source: "user",
  customField: "any data",
});

// Health check
const isHealthy = await n8nAgentService.healthCheck();
```

## Testing

### Run the Test Script

```bash
# In the server directory
npm run test:n8n
```

This will run comprehensive tests including:

- Health check
- Basic task creation
- Agent-driven task creation
- Custom payload testing

### Manual Testing with curl

```bash
# Health check
curl -X GET http://localhost:5000/agent/health \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create task
curl -X POST http://localhost:5000/agent/task \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "dueDate": "2024-01-22T20:00:00.000Z",
    "duration": 60,
    "priority": "medium",
    "subject": "Testing"
  }'
```

## Error Handling

The integration includes comprehensive error handling:

- **Timeout handling**: Requests timeout after 10 seconds (configurable)
- **Retry logic**: Failed requests are retried up to 3 times with exponential backoff
- **Fallback behavior**: If the agent fails, the backend continues with standard task creation
- **Health monitoring**: Regular health checks to monitor agent availability

## Expected n8n Agent Response Format

Your n8n workflow should return responses in this format:

```json
{
  "success": true,
  "message": "Task processed successfully",
  "data": {
    "taskId": "generated-task-id",
    "scheduleBlocks": [...],
    "calendarEvents": [...],
    "recommendations": [...]
  }
}
```

## Security Considerations

- All requests require authentication
- User ID is automatically injected into requests
- CORS is configured to allow requests from the n8n agent
- Timeout and retry limits prevent resource exhaustion

## Troubleshooting

### Common Issues

1. **Agent not responding**: Check the health endpoint first
2. **Timeout errors**: Increase the timeout value in configuration
3. **Authentication errors**: Ensure the token is valid and user is authenticated
4. **Payload validation**: Ensure required fields are present in requests

### Debugging

Enable detailed logging by setting:

```env
N8N_ENABLE_LOGGING=true
N8N_LOG_LEVEL=debug
```

### Monitoring

The service logs all interactions with the n8n agent, including:

- Request payloads
- Response data
- Error messages
- Performance metrics

## Integration Benefits

1. **Intelligent Scheduling**: Tasks are automatically scheduled based on context
2. **Workflow Automation**: Complex workflows can be triggered from simple task creation
3. **Centralized Logic**: Business logic is centralized in n8n workflows
4. **Scalability**: The agent can handle multiple requests and complex processing
5. **Flexibility**: Custom tools and workflows can be easily added to n8n
