# iOS Notification System Documentation

## Overview

The PulsePlan iOS Notification System provides comprehensive push notification capabilities through a dual-layer architecture that combines **predictable scheduled notifications** (jobs) with **intelligent contextual alerts** (agent tools). This system ensures users receive baseline notifications while allowing AI agents to send smart, context-aware alerts when needed.

## Architecture

```mermaid
graph TB
    subgraph "Scheduled Notifications (Jobs)"
        A[Daily Briefing Job] --> B[iOS Notification Service]
        C[Weekly Summary Job] --> B
        D[Due Date Reminder Job] --> B
        E[Achievement Job] --> B
    end
    
    subgraph "Contextual Notifications (Agent Tools)"
        F[Conflict Detection] --> G[Notification Manager Tool]
        H[Schedule Changes] --> G
        I[Urgent Deadlines] --> G
        J[Smart Suggestions] --> G
        G --> B
    end
    
    B --> K[Apple Push Notification Service]
    K --> L[iOS Devices]
    
    subgraph "Data Layer"
        M[(Device Registration)]
        N[(Notification Logs)]
        O[(User Preferences)]
        P[(Scheduled Queue)]
    end
    
    B --> M
    B --> N
    B --> O
    B --> P
```

## Core Components

### 1. Notification Jobs (`app/jobs/notifications.py`)

**Purpose:** Handles predictable, scheduled notifications that run automatically.

**Job Types:**

#### Daily Briefings
- **Schedule:** Every morning at user's preferred time
- **Content:** Today's tasks, upcoming deadlines, motivational messages
- **Features:** Timezone-aware, personalized content, smart scheduling

#### Weekly Summaries  
- **Schedule:** Sunday evenings or Monday mornings
- **Content:** Productivity analytics, achievements, recommendations
- **Integration:** Uses WeeklyPulseTool for AI-generated insights

#### Due Date Reminders
- **Schedule:** Multiple times daily (6 hours, 1 day, 3 days, 7 days before)
- **Content:** Assignment reminders with urgency-based priority
- **Features:** Duplicate prevention, course context, deep linking

#### Achievement Notifications
- **Schedule:** Daily achievement detection
- **Content:** Completion streaks, productivity milestones, perfect weeks
- **Features:** Pattern recognition, motivational messaging

### 2. Notification Manager Tool (`app/agents/tools/notifications.py`)

**Purpose:** Enables AI agents to send intelligent, contextual notifications based on detected conditions.

**Contextual Alert Types:**

#### Conflict Detection
- **Trigger:** Calendar conflicts detected by agents
- **Content:** Conflict details with resolution suggestions
- **Priority:** High (immediate attention needed)

#### Schedule Changes
- **Trigger:** Automatic reschedules performed by system
- **Content:** What changed, why, and new schedule
- **Priority:** Normal (informational)

#### Urgent Deadlines
- **Trigger:** Agent detects critical timing issues
- **Content:** Time-sensitive assignments needing action
- **Priority:** Critical (immediate action required)

#### Smart Suggestions
- **Trigger:** AI identifies optimization opportunities
- **Content:** Personalized productivity recommendations
- **Priority:** Low (helpful but not urgent)

#### Workload Warnings
- **Trigger:** System detects schedule overload
- **Content:** Load analysis with adjustment suggestions
- **Priority:** Normal (planning assistance)

#### Focus Time Reminders
- **Trigger:** Upcoming deep work sessions
- **Content:** Preparation tips and session details
- **Priority:** Normal (productivity enhancement)

### 3. iOS Notification Service (`app/services/ios_notification_service.py`)

**Purpose:** Handles Apple Push Notification service (APNs) integration and device management.

**Key Features:**
- **APNs Integration:** JWT authentication, HTTP/2 protocol
- **Device Management:** Registration, validation, cleanup
- **Bulk Processing:** Efficient batch sending for large user bases
- **Error Handling:** APNs error processing and recovery
- **Analytics:** Success rates and delivery statistics

## Database Schema

### Core Tables

#### `ios_devices`
```sql
CREATE TABLE ios_devices (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    device_token VARCHAR(64) NOT NULL UNIQUE,
    device_model VARCHAR(100),
    ios_version VARCHAR(20),
    app_version VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0
);
```

**Purpose:** Tracks iOS device registrations for push notifications.

#### `notification_logs`
```sql
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    success BOOLEAN NOT NULL,
    devices_targeted INTEGER DEFAULT 1,
    devices_successful INTEGER DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Purpose:** Complete audit trail of all notification sends for analytics and debugging.

#### `scheduled_notifications`
```sql
CREATE TABLE scheduled_notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    notification_data JSONB,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3
);
```

**Purpose:** Queue for notifications scheduled for future delivery.

#### `notification_preferences`
```sql
CREATE TABLE notification_preferences (
    user_id UUID PRIMARY KEY,
    daily_briefing_enabled BOOLEAN DEFAULT true,
    daily_briefing_time TIME DEFAULT '08:00',
    weekly_summary_enabled BOOLEAN DEFAULT true,
    contextual_notifications_enabled BOOLEAN DEFAULT true,
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    max_notifications_per_hour INTEGER DEFAULT 10
);
```

**Purpose:** Granular user preferences for all notification types.

#### `notification_templates`
```sql
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) UNIQUE,
    title_template VARCHAR(255),
    body_template TEXT,
    category VARCHAR(50),
    priority VARCHAR(20),
    template_variables JSONB
);
```

**Purpose:** Reusable notification templates with variable substitution.

## API Reference

### Notification Jobs

#### Run Daily Briefings
```python
from app.jobs.notifications import run_daily_briefings

result = await run_daily_briefings()
# Returns: {
#   "job": "daily_briefings",
#   "total_users": 150,
#   "sent_notifications": 142,
#   "failed_notifications": 8,
#   "execution_time": 12.34
# }
```

#### Run Weekly Summaries
```python
from app.jobs.notifications import run_weekly_summaries

result = await run_weekly_summaries()
# Returns similar structure with weekly analytics
```

#### Run Due Date Reminders
```python
from app.jobs.notifications import run_due_date_reminders

result = await run_due_date_reminders()
# Returns: {
#   "total_assignments": 89,
#   "sent_notifications": 76,
#   "failed_notifications": 13
# }
```

### Notification Manager Tool

#### Send Contextual Notification
```python
from app.agents.tools.notifications import NotificationManagerTool

tool = NotificationManagerTool()
result = await tool.execute({
    "user_id": "user_123",
    "notification_type": "conflict_detected",
    "title": "⚠️ Schedule conflict detected",
    "message": "I found a conflict between Math Study and Team Meeting",
    "urgency": "high",
    "conflict_data": {
        "conflict_type": "calendar_overlap",
        "affected_tasks": ["math_study", "team_meeting"],
        "suggested_action": "reschedule_math_study"
    }
}, context={})
```

### iOS Notification Service

#### Send Individual Notification
```python
from app.services.ios_notification_service import get_ios_notification_service

service = get_ios_notification_service()
success = await service.send_notification(
    user_id="user_123",
    notification={
        "title": "Daily Briefing",
        "body": "You have 3 tasks scheduled today",
        "category": "briefing",
        "priority": "normal",
        "data": {
            "type": "daily_briefing",
            "deep_link": "pulseplan://briefing/daily"
        }
    }
)
```

#### Register Device
```python
success = await service.register_device(
    user_id="user_123",
    device_token="64_character_hex_string",
    device_info={
        "model": "iPhone14,2",
        "ios_version": "17.1.1", 
        "app_version": "1.2.3"
    }
)
```

#### Bulk Send Notifications
```python
notifications = [
    {
        "user_id": "user_1",
        "notification": {"title": "Test", "body": "Message 1"}
    },
    {
        "user_id": "user_2", 
        "notification": {"title": "Test", "body": "Message 2"}
    }
]

result = await service.send_bulk_notifications(notifications, batch_size=100)
```

## Configuration

### Environment Variables

```bash
# APNs Configuration
APNS_TEAM_ID=ABC123DEF4
APNS_KEY_ID=XYZ789ABC1
APNS_BUNDLE_ID=com.flyonthewall.pulseplan
APNS_ENVIRONMENT=development  # or 'production'
APNS_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

# Notification Settings
NOTIFICATIONS_ENABLED=true
NOTIFICATION_RATE_LIMIT_ENABLED=true
MAX_NOTIFICATIONS_PER_HOUR=10
MAX_CONTEXTUAL_NOTIFICATIONS_PER_HOUR=5

# Job Scheduling
DAILY_BRIEFING_SCHEDULE="0 8 * * *"      # 8 AM daily
WEEKLY_SUMMARY_SCHEDULE="0 18 * * 0"     # 6 PM Sunday
DUE_DATE_REMINDER_SCHEDULE="0 */6 * * *"  # Every 6 hours
ACHIEVEMENT_SCHEDULE="0 20 * * *"         # 8 PM daily
```

### APNs Certificate Setup

1. **Create APNs Key:**
   - Go to Apple Developer Console
   - Create new APNs Authentication Key
   - Download `.p8` file and note Key ID and Team ID

2. **Configure Environment:**
   ```bash
   export APNS_PRIVATE_KEY="$(cat /path/to/AuthKey_XYZ789ABC1.p8)"
   export APNS_KEY_ID="XYZ789ABC1"
   export APNS_TEAM_ID="ABC123DEF4"
   ```

## Notification Types & Templates

### Scheduled Notifications

#### Daily Briefing Templates
```json
{
  "template_key": "daily_briefing_tasks",
  "title_template": "Good morning! Here's your daily briefing",
  "body_template": "You have {task_count} tasks scheduled today. {upcoming_deadlines_text}",
  "variables": ["task_count", "upcoming_deadlines_text"]
}
```

#### Due Date Reminders
```json
{
  "template_key": "due_date_critical", 
  "title_template": "⚠️ Due in {hours} hours: {assignment_name}",
  "body_template": "{course_name} - Submit soon to avoid being late!",
  "variables": ["hours", "assignment_name", "course_name"]
}
```

#### Weekly Summaries
```json
{
  "template_key": "weekly_excellent",
  "title_template": "Outstanding week! You scored {score}/10", 
  "body_template": "Completed {completed_tasks} tasks with excellent productivity",
  "variables": ["score", "completed_tasks"]
}
```

### Contextual Notifications

#### Conflict Detection
```json
{
  "template_key": "conflict_detected",
  "title_template": "⚠️ Schedule conflict detected",
  "body_template": "I found a conflict between {item1} and {item2}. Tap to resolve.",
  "variables": ["item1", "item2"]
}
```

#### Schedule Updates
```json
{
  "template_key": "schedule_updated",
  "title_template": "📅 Schedule automatically updated",
  "body_template": "I moved {task_name} to {new_time} due to {reason}",
  "variables": ["task_name", "new_time", "reason"] 
}
```

## User Experience

### Deep Linking

All notifications include deep links for direct app navigation:

- **Daily Briefings:** `pulseplan://briefing/daily`
- **Weekly Summaries:** `pulseplan://analytics/weekly`
- **Assignment Reminders:** `pulseplan://assignment/{assignment_id}`
- **Schedule Conflicts:** `pulseplan://schedule/conflicts`
- **Task Details:** `pulseplan://task/{task_id}`
- **Settings:** `pulseplan://settings/notifications`

### Notification Categories

iOS notification categories enable interactive actions:

- **`briefing`** - Daily briefings with "View Schedule" action
- **`deadline`** - Due date reminders with "Start Task" action
- **`conflict`** - Schedule conflicts with "Resolve" action
- **`achievement`** - Achievements with "View Progress" action

### User Preferences

Granular notification controls available in app settings:

**Scheduled Notifications:**
- Daily briefing enable/disable + time selection
- Weekly summary enable/disable
- Due date reminders with timing options
- Achievement notifications toggle

**Contextual Notifications:**
- Master contextual toggle
- Individual type toggles (conflicts, suggestions, etc.)
- Rate limiting preferences
- Quiet hours configuration

## Performance & Monitoring

### Metrics Collection

The system tracks comprehensive metrics:

**Delivery Metrics:**
- Total notifications sent
- Success/failure rates by type
- Device targeting efficiency
- APNs error code distribution

**User Engagement:**
- Notification open rates (when available)
- Deep link click-through rates
- User preference changes
- Device registration trends

**System Performance:**
- Job execution times
- Batch processing efficiency
- APNs response times
- Database query performance

### Monitoring Dashboards

**Real-time Monitoring:**
- Current notification queue size
- Active device count
- Recent delivery success rates
- Error rate alerts

**Historical Analytics:**
- Daily/weekly notification volumes
- User engagement trends
- Preference adoption rates
- System reliability metrics

## Error Handling & Recovery

### APNs Error Responses

The system handles all APNs error conditions:

**400 Bad Request:** Invalid payload format
- Log error and skip notification
- Alert developers for payload issues

**403 Forbidden:** Authentication failure
- Refresh JWT token
- Retry notification once

**410 Gone:** Invalid device token
- Mark device as inactive
- Remove from future deliveries

**429 Too Many Requests:** Rate limited
- Implement exponential backoff
- Reschedule delivery

**500+ Server Errors:** APNs service issues
- Retry with backoff
- Queue for later delivery

### Failure Recovery

**Device Failures:**
- Track consecutive failure count
- Disable after 5 consecutive failures
- Re-enable on successful app launch

**Job Failures:**
- Automatic retry with exponential backoff
- Alert administrators after 3 failures
- Graceful degradation to prevent user impact

**Database Issues:**
- Connection pooling with retry logic
- Read replica fallbacks for queries
- Transaction rollback on errors

## Security & Privacy

### Data Protection

**User Data:**
- Device tokens encrypted at rest
- Notification content logged with user consent
- Automatic data expiration (logs older than 90 days)
- GDPR-compliant data export/deletion

**APNs Integration:**
- JWT tokens with short expiration (55 minutes)
- Private key secure storage
- TLS 1.2+ for all APNs communication
- Certificate pinning for additional security

### Privacy Controls

**User Control:**
- Granular notification preferences
- Easy unsubscribe from any type
- Clear data usage explanations
- Opt-out of analytics collection

**Data Minimization:**
- Only collect necessary device info
- No personal data in notification payloads
- Anonymized analytics where possible
- Regular data cleanup processes

## Testing

### Unit Tests

**Notification Jobs:**
```python
# Test daily briefing generation
async def test_daily_briefing_content():
    jobs = NotificationJobs()
    briefing = await jobs._generate_daily_briefing("test_user")
    assert briefing["tasks_count"] >= 0
    assert "summary" in briefing
```

**Notification Tool:**
```python
# Test contextual notification validation
async def test_notification_validation():
    tool = NotificationManagerTool()
    
    valid_input = {
        "user_id": "test_user",
        "notification_type": "conflict_detected", 
        "title": "Test Conflict",
        "message": "Test message"
    }
    
    assert tool.validate_input(valid_input) == True
```

**iOS Service:**
```python
# Test device registration
async def test_device_registration():
    service = get_ios_notification_service()
    
    success = await service.register_device(
        user_id="test_user",
        device_token="a" * 64,  # Valid hex string
        device_info={"model": "iPhone", "ios_version": "17.0"}
    )
    
    assert success == True
```

### Integration Tests

**End-to-End Notification Flow:**
```python
async def test_notification_flow():
    # Register device
    service = get_ios_notification_service()
    await service.register_device(user_id, device_token, device_info)
    
    # Send notification via tool
    tool = NotificationManagerTool()
    result = await tool.execute(notification_data, context)
    
    # Verify logging
    logs = await get_notification_logs(user_id)
    assert len(logs) == 1
    assert logs[0]["success"] == True
```

### Load Testing

**Bulk Notification Performance:**
```python
async def test_bulk_notification_performance():
    notifications = generate_test_notifications(1000)
    
    start_time = time.time()
    result = await service.send_bulk_notifications(notifications)
    execution_time = time.time() - start_time
    
    assert result["successful_sends"] >= 950  # 95% success rate
    assert execution_time < 30  # Complete within 30 seconds
```

## Deployment

### Production Checklist

**APNs Configuration:**
- [ ] Production APNs certificates configured
- [ ] Private keys securely stored (not in code)
- [ ] Team ID and Key ID verified
- [ ] Bundle ID matches production app

**Database Setup:**
- [ ] All notification tables created
- [ ] Indexes optimized for query patterns
- [ ] Row Level Security policies enabled
- [ ] Backup strategy implemented

**Monitoring Setup:**
- [ ] Notification metrics dashboard
- [ ] Error rate alerts configured  
- [ ] Performance monitoring enabled
- [ ] Log aggregation configured

**Security Verification:**
- [ ] TLS certificates valid
- [ ] JWT token rotation working
- [ ] Device token validation active
- [ ] Rate limiting configured

### Scaling Considerations

**High Volume Scenarios:**
- **Database:** Connection pooling, read replicas
- **APNs:** HTTP/2 connection reuse, request pipelining  
- **Jobs:** Horizontal scaling with job locks
- **Rate Limiting:** Redis-based distributed limiting

**Global Deployment:**
- **Timezone Handling:** UTC storage, local conversion
- **APNs Regions:** Use appropriate APNs endpoints
- **Data Compliance:** Regional data storage requirements

## Troubleshooting

### Common Issues

**Notifications Not Delivered:**
1. Check device token validity
2. Verify APNs certificates not expired
3. Confirm user preferences allow notifications
4. Review APNs error logs

**High Failure Rates:**
1. Monitor APNs response codes
2. Check JWT token generation
3. Verify payload format compliance
4. Review network connectivity

**Performance Issues:**
1. Analyze database query times
2. Monitor batch processing efficiency
3. Check APNs request timing
4. Review job execution patterns

### Debug Tools

**Device Token Validation:**
```python
from app.services.ios_notification_service import get_ios_notification_service

service = get_ios_notification_service()
is_valid = service._validate_device_token(device_token)
print(f"Device token valid: {is_valid}")
```

**Manual Notification Send:**
```python
# Test notification to specific device
result = await service._send_to_device(device_token, {
    "title": "Test Notification",
    "body": "This is a test",
    "data": {"test": True}
})
print(f"Send result: {result}")
```

**Job Execution Test:**
```python
# Run specific job manually
from app.jobs.notifications import get_notification_jobs

jobs = get_notification_jobs()
result = await jobs.send_daily_briefings(batch_size=10)
print(f"Job result: {result}")
```

## Best Practices

### Notification Content

**Do:**
- Keep titles under 60 characters
- Make messages actionable and clear
- Include relevant context
- Use emojis sparingly for visual appeal
- Test on different iOS versions

**Don't:**
- Send generic "Update available" messages
- Include sensitive data in notifications
- Overwhelm users with frequent alerts
- Use technical jargon or error codes

### User Experience

**Timing:**
- Respect user timezones and quiet hours
- Batch related notifications together
- Avoid notification storms during busy periods
- Consider user's typical app usage patterns

**Personalization:**
- Tailor content to user's specific data
- Respect user's notification preferences
- Learn from user interaction patterns
- Provide easy preference management

### System Reliability

**Error Handling:**
- Always have fallback mechanisms
- Log errors for debugging but don't spam logs
- Implement circuit breakers for external services
- Monitor system health continuously

**Performance:**
- Optimize database queries with proper indexes
- Use connection pooling for external services
- Implement caching where appropriate
- Monitor and alert on performance degradation

This documentation provides comprehensive guidance for implementing, maintaining, and troubleshooting the iOS notification system in PulsePlan. The dual-layer architecture ensures both reliable baseline notifications and intelligent contextual alerts while maintaining excellent user experience and system performance.