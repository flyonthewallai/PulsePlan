# Rhythm Calendar API Server

This is the backend server for the Rhythm app, handling Google Calendar and Microsoft Outlook Calendar OAuth integration and event fetching, as well as intelligent scheduling powered by GPT-4o.

## Features

- Google and Microsoft OAuth 2.0 authentication
- Calendar events retrieval from both providers
- Event creation for Microsoft Calendar
- Token refresh management
- Supabase database integration for storing connections
- Intelligent scheduling using GPT-4o

## Setup

1. Clone the repository
2. Install dependencies: `npm install`
3. Create a `.env` file in the root directory with the following variables:

```
# Server Configuration
PORT=5000
NODE_ENV=development

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URL=http://localhost:5000/auth/google/callback

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_REDIRECT_URL=http://localhost:5000/auth/microsoft/callback
MICROSOFT_TENANT_ID=common

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# App Configuration
APP_URL=http://localhost:5000
CLIENT_URL=http://localhost:8081
```

4. Build the project: `npm run build`
5. Start the server: `npm run start`

## Development

For development with auto-reloading:

```
npm run dev
```

## API Endpoints

### Authentication

#### Google Calendar

- `GET /auth/google?userId=<user_id>` - Initiate Google OAuth flow
- `GET /auth/google/callback` - Handle Google OAuth callback
- `DELETE /auth/google/:userId` - Disconnect Google Calendar integration

#### Microsoft Outlook Calendar

- `GET /auth/microsoft?userId=<user_id>` - Initiate Microsoft OAuth flow
- `GET /auth/microsoft/callback` - Handle Microsoft OAuth callback
- `DELETE /auth/microsoft/:userId` - Disconnect Microsoft Calendar integration

### Calendar

#### Google Calendar

- `GET /calendar/google/events/:userId` - Get upcoming Google Calendar events

#### Microsoft Calendar

- `GET /calendar/microsoft/events/:userId` - Get upcoming Microsoft Calendar events
- `POST /calendar/microsoft/events/:userId` - Create a new event in Microsoft Calendar

#### Shared

- `GET /calendar/status/:userId` - Get calendar connection status

### Intelligent Scheduling

- `POST /scheduling/generate` - Generate an optimal schedule using GPT-4o

#### Request Format

```json
{
  "tasks": [
    {
      "id": "task-1",
      "title": "Math Assignment",
      "dueDate": "2023-05-20T23:59:59Z",
      "estimatedMinutes": 120,
      "subject": "Mathematics",
      "priority": "high"
    }
  ],
  "timeSlots": [
    {
      "start": "2023-05-15T09:00:00Z",
      "end": "2023-05-15T17:00:00Z"
    }
  ],
  "userPreferences": {
    "preferredWorkingHours": {
      "start": "09:00",
      "end": "17:00"
    },
    "breakDuration": 15,
    "focusSessionDuration": 90
  }
}
```

#### Response Format

```json
{
  "success": true,
  "schedule": [
    {
      "taskId": "task-1",
      "title": "Math Assignment",
      "startTime": "2023-05-15T10:00:00Z",
      "endTime": "2023-05-15T12:00:00Z"
    }
  ],
  "explanation": "Markdown-formatted explanation of the scheduling logic",
  "tokenUsage": {
    "promptTokens": 350,
    "completionTokens": 420,
    "totalTokens": 770
  }
}
```

## Microsoft Azure Setup

To set up Microsoft OAuth:

1. Register an application in the [Azure Portal](https://portal.azure.com/)
2. Go to "App registrations" and create a new registration
3. Set the redirect URI to match your MICROSOFT_REDIRECT_URL
4. Add the required API permissions: `Calendars.Read`, `Calendars.ReadWrite`, `User.Read`, `offline_access`
5. Create a client secret and copy its value
6. Use the Application (client) ID and the secret in your environment variables

## OpenAI Setup

To use the intelligent scheduling features:

1. Create an account on [OpenAI](https://platform.openai.com/)
2. Navigate to API keys and create a new API key
3. Add the API key to your environment variables as OPENAI_API_KEY
4. Ensure your OpenAI account has access to the GPT-4o model

## Required Supabase Setup

Ensure your Supabase database has the required tables and RLS policies:

```sql
-- Calendar connections table
CREATE TABLE calendar_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL CHECK (provider IN ('google', 'microsoft', 'apple')),
  access_token TEXT NOT NULL,
  refresh_token TEXT NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE,
  scopes TEXT[],
  email TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Create index for faster queries
CREATE INDEX idx_calendar_connections_user_id ON calendar_connections(user_id);

-- Enable row-level security
ALTER TABLE calendar_connections ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Calendar connections can only be accessed by the user who created them
CREATE POLICY calendar_connections_policy ON calendar_connections
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- Update users table for Stripe subscription
-- Add these columns to your existing users table
ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'free' NOT NULL;
ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN subscription_id TEXT;
```

## Stripe Integration

To enable the Stripe integration for subscriptions:

1. Create a Stripe account at [stripe.com](https://stripe.com)
2. Set up a product and recurring price for your premium subscription
3. Add the following environment variables to your .env file:
   ```
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   STRIPE_PREMIUM_PRICE_ID=your_premium_price_id
   CLIENT_URL=your_client_url
   ```
4. Set up a webhook endpoint in your Stripe dashboard:
   - URL: `https://your-api-domain.com/stripe/webhook`
   - Events to send: `checkout.session.completed`, `customer.subscription.deleted`
5. Test the integration with Stripe test mode before going live
