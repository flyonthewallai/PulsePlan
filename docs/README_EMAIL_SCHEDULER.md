# PulsePlan Email Scheduler System

A comprehensive backend scheduler built with TypeScript and `node-cron` that automates daily briefing and weekly pulse email campaigns for premium PulsePlan users.

## 🚀 Features

- **Daily Briefing Job**: Runs every day at 8:00 AM local time
- **Weekly Pulse Job**: Runs every Sunday at 6:00 PM local time
- **Rate Limiting**: Respects 5 requests/second across all operations
- **Fallback Handling**: Graceful degradation when agent data is unavailable
- **Comprehensive Logging**: Per-user success/failure tracking
- **Manual Testing**: Admin endpoints for manual job execution
- **Environment Validation**: Startup validation of required configuration
- **Graceful Shutdown**: Proper cleanup on server termination

## 📁 Directory Structure

```
server/
├── jobs/
│   ├── utils/
│   │   ├── logger.ts          # Logging utility
│   │   ├── rateLimiter.ts     # Rate limiting (5 req/sec)
│   │   └── emailService.ts    # Resend email service
│   ├── dailyBriefingJob.ts    # Daily briefing job logic
│   ├── weeklyPulseJob.ts      # Weekly pulse job logic
│   └── scheduler.ts           # Main scheduler with node-cron
├── src/
│   ├── types/
│   │   └── scheduler.ts       # TypeScript interfaces
│   ├── controllers/
│   │   └── briefingController.ts  # Agent API endpoints
│   └── routes/
│       ├── briefingRoutes.ts      # /agents/* routes
│       └── schedulerRoutes.ts     # /scheduler/* routes
└── .env.example               # Environment variables template
```

## 🔧 Environment Configuration

### Required Variables

```env
# Database
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# Email Service (Resend)
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=noreply@pulseplan.com

# Agent API
AGENT_API_BASE_URL=http://localhost:5000
```

### Optional Variables

```env
# Email Templates (use template IDs or fallback to HTML)
RESEND_DAILY_BRIEFING_TEMPLATE_ID=your_template_id
RESEND_WEEKLY_PULSE_TEMPLATE_ID=your_template_id
```

## 📊 Database Schema Requirements

The scheduler expects these Supabase tables and columns:

### Users Table

```sql
users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  name TEXT,
  is_premium BOOLEAN DEFAULT FALSE,
  email_preferences JSONB DEFAULT '{}',
  timezone TEXT
)
```

### Email Preferences Structure

```json
{
  "daily_briefing": "on", // or "off"
  "weekly_pulse": "on" // or "off"
}
```

### Tasks Table

```sql
tasks (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  title TEXT NOT NULL,
  due_date TIMESTAMP,
  priority TEXT,
  status TEXT,
  subject TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)
```

### Events Table

```sql
events (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  title TEXT NOT NULL,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  calendar_provider TEXT
)
```

## 🎯 API Endpoints

### Agent Endpoints (No Auth Required)

#### Generate Daily Briefing

```http
POST /agents/briefing
Content-Type: application/json

{
  "userId": "user-123"
}
```

**Response:**

```json
{
  "summary": "Good morning, John! You have 3 tasks and 2 events today...",
  "todaysTasks": [...],
  "upcomingEvents": [...],
  "recommendations": [...],
  "weather": null,
  "timestamp": "2024-01-15T08:00:00.000Z"
}
```

#### Generate Weekly Pulse

```http
POST /agents/weekly-pulse
Content-Type: application/json

{
  "userId": "user-123"
}
```

**Response:**

```json
{
  "completedTasks": 12,
  "totalTasks": 15,
  "productivityScore": 85,
  "achievements": [...],
  "nextWeekRecommendations": [...],
  "weeklyStats": {...},
  "timestamp": "2024-01-14T18:00:00.000Z"
}
```

### Scheduler Management Endpoints (Auth Required)

#### Get Scheduler Status

```http
GET /scheduler/status
Authorization: Bearer <token>
```

#### Manual Job Execution

```http
POST /scheduler/run-daily-briefing
POST /scheduler/run-weekly-pulse
Authorization: Bearer <token>
```

#### Start/Stop Scheduler

```http
POST /scheduler/start
POST /scheduler/stop
Authorization: Bearer <token>
```

## ⚡ Rate Limiting

The system implements a 5 requests/second rate limiter that applies to:

- Agent API calls (`/agents/briefing`, `/agents/weekly-pulse`)
- Email sending via Resend
- All scheduler operations

## 📝 Logging System

The logger provides structured logging with timestamps:

```typescript
// Job lifecycle
logger.logJobStart("Daily Briefing Job");
logger.logJobComplete("Daily Briefing Job", { success: 10, failed: 2 });

// Per-user results
logger.logUserResult("Daily Briefing", userId, email, success, error);

// Rate limiting
logger.logRateLimit(waitTime);
```

**Log Format:**

```
[2024-01-15T08:00:00.000Z] [INFO] 🚀 Starting job: Daily Briefing Job
[2024-01-15T08:00:15.000Z] [INFO] ✅ Daily Briefing success for user-123 (user@example.com)
[2024-01-15T08:00:30.000Z] [INFO] ✅ Completed job: Daily Briefing Job | Data: {"success":10,"failed":2}
```

## 🔄 Job Scheduling

### Daily Briefing Job

- **Schedule**: Every day at 8:00 AM (configurable timezone)
- **Cron**: `0 0 8 * * *`
- **Process**:
  1. Query premium users with `daily_briefing: 'on'`
  2. Call `/agents/briefing` for each user
  3. Send personalized email via Resend
  4. Log results per user

### Weekly Pulse Job

- **Schedule**: Every Sunday at 6:00 PM (configurable timezone)
- **Cron**: `0 0 18 * * 0`
- **Process**:
  1. Query premium users with `weekly_pulse: 'on'`
  2. Call `/agents/weekly-pulse` for each user
  3. Send weekly summary email via Resend
  4. Log results per user

## 🛡️ Error Handling & Fallbacks

### Agent API Failures

When agent endpoints fail, the system provides fallback data:

**Daily Briefing Fallback:**

```json
{
  "summary": "Unable to generate personalized briefing at this time...",
  "todaysTasks": [],
  "upcomingEvents": [],
  "recommendations": ["Check your PulsePlan app for the latest updates"]
}
```

**Weekly Pulse Fallback:**

```json
{
  "completedTasks": 0,
  "totalTasks": 0,
  "achievements": ["You maintained your productivity streak this week!"],
  "nextWeekRecommendations": [
    "Check your PulsePlan app for personalized recommendations"
  ]
}
```

### Email Template Fallbacks

If Resend template IDs aren't configured, the system generates beautiful HTML emails with:

- Responsive design
- Branded styling
- Fallback content structure
- Professional formatting

## 🚦 Getting Started

### 1. Install Dependencies

```bash
cd server
npm install node-cron resend
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual values
```

### 3. Start Server

```bash
npm run dev
```

The scheduler will automatically start with the server and display:

```
📅 Email scheduler started successfully
📋 Daily Briefing: Every day at 8:00 AM
📊 Weekly Pulse: Every Sunday at 6:00 PM
```

### 4. Test Manually

```bash
# Test daily briefing
curl -X POST http://localhost:5000/scheduler/run-daily-briefing \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test weekly pulse
curl -X POST http://localhost:5000/scheduler/run-weekly-pulse \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check scheduler status
curl http://localhost:5000/scheduler/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔧 Development & Testing

### Manual Job Execution

```typescript
// In code
import { emailScheduler } from "./jobs/scheduler";

await emailScheduler.runDailyBriefingNow();
await emailScheduler.runWeeklyPulseNow();
```

### Environment Validation

The scheduler validates required environment variables on startup:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `RESEND_API_KEY`
- `AGENT_API_BASE_URL`

### Graceful Shutdown

```typescript
// The scheduler handles SIGINT and SIGTERM
process.on("SIGINT", async () => {
  await emailScheduler.shutdown();
  process.exit(0);
});
```

## 📈 Monitoring & Metrics

### Scheduler Status API

```json
{
  "isRunning": true,
  "dailyBriefingActive": true,
  "weeklyPulseActive": true,
  "nextDailyBriefing": "2024-01-16T08:00:00.000Z",
  "nextWeeklyPulse": "2024-01-21T18:00:00.000Z",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Success Metrics

Each job execution returns detailed results:

```typescript
interface JobResult {
  success: boolean;
  userId: string;
  email: string;
  error?: string;
  timestamp: Date;
}
```

## 🔒 Security Considerations

1. **Rate Limiting**: Prevents API abuse with 5 req/sec limit
2. **Environment Validation**: Fails fast on missing configuration
3. **Error Isolation**: Single user failures don't stop job execution
4. **Authentication**: Admin endpoints require valid JWT tokens
5. **Fallback Data**: No sensitive data in fallback responses

## 🎨 Email Templates

### Resend Template Support

Configure template IDs in environment variables:

```env
RESEND_DAILY_BRIEFING_TEMPLATE_ID=template_123
RESEND_WEEKLY_PULSE_TEMPLATE_ID=template_456
```

### Template Data Structure

**Daily Briefing Template Variables:**

```json
{
  "userName": "John",
  "summary": "Your briefing summary...",
  "todaysTasks": [...],
  "upcomingEvents": [...],
  "recommendations": [...],
  "date": "1/15/2024"
}
```

**Weekly Pulse Template Variables:**

```json
{
  "userName": "John",
  "completedTasks": 12,
  "totalTasks": 15,
  "productivityScore": 85,
  "achievements": [...],
  "nextWeekRecommendations": [...],
  "weekOf": "1/15/2024"
}
```

### HTML Fallback Templates

Beautiful responsive HTML templates are generated automatically when template IDs aren't configured, featuring:

- Modern design with PulsePlan branding
- Mobile-responsive layout
- Structured content sections
- Professional typography

## 🚀 Production Deployment

### Environment Setup

```bash
# Production environment variables
RESEND_API_KEY=re_live_key_here
AGENT_API_BASE_URL=https://your-production-api.com
SUPABASE_URL=https://your-project.supabase.co
```

### Monitoring

The system provides comprehensive logging for production monitoring:

- Job execution success/failure rates
- Per-user email delivery status
- Rate limiting metrics
- Error tracking and reporting

### Scaling Considerations

- Rate limiter handles high user volumes gracefully
- Database queries are optimized with proper indexing
- Email service (Resend) scales automatically
- Scheduler is timezone-aware for global users

---

## 📞 Support

For issues or questions:

1. Check the logs for detailed error information
2. Verify environment variable configuration
3. Test individual components using manual endpoints
4. Monitor scheduler status via `/scheduler/status` endpoint

The system is designed to be robust, scalable, and maintainable for production use! 🎉
