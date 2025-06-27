# PulsePlan Backend API Server

A comprehensive backend API server for the PulsePlan productivity application, featuring intelligent scheduling, calendar integrations, caching infrastructure, and AI-powered automation.

## 🚀 Features

### Core Functionality

- **Intelligent Scheduling**: GPT-4o powered task scheduling and optimization
- **Calendar Integration**: Google Calendar and Microsoft Outlook synchronization
- **AI Agent Integration**: N8N workflow automation and intelligent task management
- **Apple Pay Integration**: Secure subscription management via Apple's App Store
- **Real-time Caching**: High-performance caching with Upstash Redis
- **Task Management**: Comprehensive CRUD operations with offline sync support

### Advanced Features

- **Multi-layer Caching**: Upstash Redis + in-memory cache for optimal performance
- **Agent Status Monitoring**: Real-time AI agent availability and health checks
- **Canvas LMS Integration**: Academic assignment synchronization
- **Contact Management**: Google Contacts integration
- **Email Integration**: Gmail API connectivity
- **Performance Monitoring**: Comprehensive cache statistics and health endpoints

## 🛠 Technology Stack

- **Runtime**: Node.js with TypeScript
- **Framework**: Express.js with comprehensive middleware
- **Database**: Supabase (PostgreSQL) with Row Level Security
- **Caching**: Upstash Redis (serverless) + LRU in-memory cache
- **AI Integration**: OpenAI GPT-4o + N8N workflow automation
- **Payment Processing**: Apple Pay with server-side receipt verification
- **Authentication**: Supabase Auth with OAuth integrations

## 📦 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account and project
- Upstash Redis account
- OpenAI API key

### Installation

1. **Clone and install dependencies**

   ```bash
   git clone <repository-url>
   cd server
   npm install
   ```

2. **Environment Configuration**

   Create a `.env` file with the following variables:

   ```bash
   # Server Configuration
   PORT=5000
   NODE_ENV=development

   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_SERVICE_KEY=your_supabase_service_role_key

   # Upstash Redis Configuration (Required for caching)
   UPSTASH_REDIS_REST_URL=https://your-redis-endpoint.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your_upstash_auth_token

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key

   # Google OAuth & Services
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URL=http://localhost:5000/auth/google/callback

   # Microsoft OAuth
   MICROSOFT_CLIENT_ID=your_microsoft_client_id
   MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
   MICROSOFT_REDIRECT_URL=http://localhost:5000/auth/microsoft/callback
   MICROSOFT_TENANT_ID=common

   # N8N Agent Integration (Optional)
   N8N_WEBHOOK_URL=your_n8n_webhook_endpoint
   N8N_API_KEY=your_n8n_api_key

   # Apple Pay Configuration
   APPLE_SHARED_SECRET=your_apple_shared_secret

   # App Configuration
   APP_URL=http://localhost:5000
   CLIENT_URL=http://localhost:8081
   ```

3. **Build and Start**
   ```bash
   npm run build
   npm start
   ```

### Development Mode

For development with auto-reloading:

```bash
npm run dev
```

## 📚 API Documentation

### 🔐 Authentication Endpoints

#### Google OAuth

- `GET /auth/google?userId=<user_id>` - Initiate Google OAuth flow
- `GET /auth/google/callback` - Handle OAuth callback
- `DELETE /auth/google/:userId` - Disconnect Google integration

#### Microsoft OAuth

- `GET /auth/microsoft?userId=<user_id>` - Initiate Microsoft OAuth flow
- `GET /auth/microsoft/callback` - Handle OAuth callback
- `DELETE /auth/microsoft/:userId` - Disconnect Microsoft integration

#### User Profile Management

- `GET /auth/user/:userId/profile` - Get comprehensive user profile with caching
- `PUT /auth/user/:userId/profile` - Update user profile (name, city, timezone, preferences, etc.)

**Comprehensive Profile Data:**
The system now caches all user profile information including:

- **Basic Info**: name, email, avatar, timezone, city
- **Academic**: school, academic year, user type
- **Preferences**: working hours, study preferences, work preferences
- **Settings**: integration preferences, notification preferences
- **Status**: subscription status, onboarding progress
- **Timestamps**: creation date, last login, last update

**Caching Strategy:**

- **5-minute TTL** for user profile data (changes infrequently)
- **Multi-layer caching**: Memory cache + Upstash Redis
- **Automatic invalidation** when profile is updated
- **Fallback support** for offline scenarios

### 📅 Calendar Integration

#### Google Calendar

- `GET /calendar/google/events/:userId` - Fetch upcoming events
- `POST /calendar/google/events/:userId` - Create new event

#### Microsoft Calendar

- `GET /calendar/microsoft/events/:userId` - Fetch upcoming events
- `POST /calendar/microsoft/events/:userId` - Create new event

#### Universal

- `GET /calendar/status/:userId` - Get connection status for all providers

### 🤖 AI Agent & Scheduling

#### Intelligent Scheduling

- `POST /scheduling/generate` - Generate optimized schedule using GPT-4o

**Request Format:**

```json
{
  "tasks": [
    {
      "id": "task-1",
      "title": "Study Mathematics",
      "dueDate": "2024-12-20T23:59:59Z",
      "estimatedMinutes": 120,
      "subject": "Mathematics",
      "priority": "high"
    }
  ],
  "timeSlots": [
    {
      "start": "2024-12-15T09:00:00Z",
      "end": "2024-12-15T17:00:00Z"
    }
  ],
  "userPreferences": {
    "preferredWorkingHours": { "start": "09:00", "end": "17:00" },
    "breakDuration": 15,
    "focusSessionDuration": 90
  }
}
```

#### N8N Agent Integration

- `POST /agent/task` - Create task through AI agent
- `POST /agent/query` - Natural language scheduling queries
- `POST /agent/chat` - Interactive AI assistant
- `GET /agent/status` - Agent availability and health

**Enhanced Payload Structure:**
The N8N agent now receives comprehensive user context including:

- **User Information**: `userName`, `isPremium`, `city`, `timezone`
- **Connected Accounts**: Google, Microsoft, and Canvas authentication tokens
- **Context Data**: Current page, chat history, working hours, and preferences

This enables location-aware and timezone-aware intelligent responses from the AI agent.

### 💳 Apple Pay Integration

- `POST /apple-pay/verify-receipt` - Verify App Store receipt
- `GET /apple-pay/subscription-status/:userId` - Get subscription status
- `POST /apple-pay/update-subscription` - Update subscription data
- `POST /apple-pay/cancel-subscription` - Handle subscription cancellation

### 📊 Cache Management & Monitoring

#### Cache Operations

- `GET /cache/stats` - Cache performance statistics
- `GET /cache/health` - Cache system health check
- `POST /cache/clear` - Clear all caches (admin)
- `DELETE /cache/user/:userId` - Clear user-specific cache

#### Manual Cache Invalidation

- `POST /cache/invalidate` - Selective cache invalidation

**Request Format:**

```json
{
  "userId": "user-123",
  "cacheTypes": ["userInfo", "userAccounts", "userSubscription"]
}
```

### 📝 Task Management

- `GET /tasks/:userId` - Get user tasks
- `POST /tasks` - Create new task
- `PUT /tasks/:taskId` - Update task
- `DELETE /tasks/:taskId` - Delete task

### 📞 Contact Integration

- `GET /contacts/google/:userId` - Fetch Google contacts
- `POST /contacts/sync/:userId` - Sync contacts from provider

## ⚙ Service Integrations

### Upstash Redis Setup

1. Create account at [console.upstash.com](https://console.upstash.com)
2. Create a new Redis database
3. Copy the REST URL and token to your environment variables
4. The system provides automatic failover to in-memory cache if Upstash is unavailable

### Google Services Setup

1. **Google Cloud Console**

   - Create project at [console.cloud.google.com](https://console.cloud.google.com)
   - Enable Google Calendar API and Gmail API
   - Create OAuth 2.0 credentials

2. **Required Scopes**
   ```
   https://www.googleapis.com/auth/calendar
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/contacts.readonly
   ```

### Microsoft Azure Setup

1. **Azure Portal Configuration**
   - Register app at [portal.azure.com](https://portal.azure.com)
   - Configure redirect URIs
   - Add API permissions: `Calendars.Read`, `Calendars.ReadWrite`, `User.Read`, `offline_access`

### OpenAI Configuration

1. **API Setup**
   - Create account at [platform.openai.com](https://platform.openai.com)
   - Generate API key
   - Ensure GPT-4o model access

### Apple Developer Setup

1. **App Store Connect**
   - Configure In-App Purchases
   - Set up subscription products
   - Generate shared secret for receipt verification

## 🗄 Database Schema

### Required Supabase Tables

```sql
-- Users table (extend as needed)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  subscription_status TEXT DEFAULT 'free' NOT NULL,
  apple_transaction_id TEXT,
  subscription_expires_at TIMESTAMP WITH TIME ZONE,
  timezone TEXT DEFAULT 'UTC',
  city TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Calendar connections
CREATE TABLE calendar_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL CHECK (provider IN ('google', 'microsoft')),
  access_token TEXT NOT NULL,
  refresh_token TEXT NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE,
  scopes TEXT[],
  email TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Tasks table
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  due_date TIMESTAMP WITH TIME ZONE,
  estimated_minutes INTEGER,
  subject TEXT,
  priority TEXT CHECK (priority IN ('low', 'medium', 'high')),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_calendar_connections_user_id ON calendar_connections(user_id);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- Row Level Security
ALTER TABLE calendar_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY calendar_connections_policy ON calendar_connections
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY tasks_policy ON tasks
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
```

## 🚀 Performance & Monitoring

### Cache Performance Metrics

The system provides comprehensive cache monitoring:

- **Hit Ratios**: Memory cache vs Redis performance
- **Response Times**: Cache vs database query performance
- **Health Status**: Real-time cache availability monitoring
- **Automatic Failover**: Graceful degradation when cache unavailable

### Performance Benefits

- **90% Database Query Reduction**: Through intelligent caching
- **5-10x Faster Response Times**: For cached user data
- **Global Edge Locations**: Via Upstash's worldwide infrastructure
- **Automatic Scaling**: Handles traffic spikes seamlessly

### Monitoring Endpoints

```bash
# Health check
curl http://localhost:5000/cache/health

# Performance statistics
curl http://localhost:5000/cache/stats \
  -H "Authorization: Bearer <token>"
```

## 🔧 Development

### Available Scripts

```bash
npm run dev          # Development with auto-reload
npm run build        # TypeScript compilation
npm run start        # Production server
npm run test         # Run test suite (if configured)
```

### Project Structure

```
server/
├── src/
│   ├── config/          # Service configurations
│   │   ├── supabase.ts
│   │   ├── redis.ts     # Upstash Redis setup
│   │   ├── openai.ts
│   │   └── n8nAgent.ts
│   ├── controllers/     # Route handlers
│   ├── middleware/      # Authentication, caching, etc.
│   ├── routes/          # API route definitions
│   ├── services/        # Business logic
│   │   ├── cacheService.ts
│   │   ├── n8nAgentService.ts
│   │   └── calendarSyncService.ts
│   ├── types/           # TypeScript definitions
│   └── index.ts         # Server entry point
├── docs/                # Additional documentation
└── package.json
```

## 🔒 Security Considerations

- **Environment Variables**: Never commit `.env` files
- **API Keys**: Rotate regularly and use least-privilege access
- **CORS**: Configured for specific origins in production
- **Rate Limiting**: Implement for production deployments
- **Input Validation**: All endpoints validate input data
- **Apple Pay Security**: Server-side receipt verification only

## 🚀 Deployment

### Environment-Specific Configurations

```bash
# Development
NODE_ENV=development
PORT=5000

# Production
NODE_ENV=production
PORT=process.env.PORT || 5000
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Upstash Redis database created and connected
- [ ] Supabase database schema deployed
- [ ] Google/Microsoft OAuth apps configured
- [ ] Apple shared secret configured
- [ ] CORS origins restricted to production domains
- [ ] Health check endpoints accessible
- [ ] Cache monitoring configured

## 📖 Additional Documentation

- **Caching Strategy**: `docs/CACHING_STRATEGY.md`
- **Apple Pay Integration**: `docs/APPLE_PAY_INTEGRATION.md`
- **N8N Agent Setup**: `docs/N8N_AGENT_INTEGRATION.md`
- **Technical Specification**: `docs/TECHNICAL_SPECIFICATION.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues or questions:

- Check the documentation in `/docs`
- Review API endpoint examples above
- Verify environment variable configuration
- Check cache health via monitoring endpoints

---

**Built with ❤️ for optimal productivity and intelligent automation**
