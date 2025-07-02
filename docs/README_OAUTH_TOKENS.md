# OAuth Token Management System

This system automatically captures, securely stores, and includes OAuth tokens in all agent API calls, enabling agents to access users' connected services (Google, Microsoft, Canvas, Notion).

## Features

- **Automatic Token Capture**: Captures tokens during OAuth flows
- **Secure Storage**: Encrypts tokens at rest using AES-256-GCM
- **Auto-Refresh**: Automatically refreshes expired tokens
- **Agent Integration**: Includes tokens in all agent API requests
- **Fallback Handling**: Graceful degradation when tokens are unavailable

## Architecture

### Core Components

1. **Token Service** (`tokenService.ts`) - Manages token storage, retrieval, and refresh
2. **Enhanced Agent Service** (`enhancedAgentService.ts`) - Includes tokens in agent calls
3. **Connection Controller** (`connectionController.ts`) - API for managing connections
4. **Updated OAuth Controllers** - Enhanced to use secure token storage

### Token Flow

```
OAuth Flow → Store Encrypted Tokens → Include in Agent Calls → Auto-Refresh as Needed
```

## Environment Variables

```bash
# Required for token encryption
TOKEN_ENCRYPTION_KEY=your_32_character_encryption_key_here_very_secure

# N8N Agent configuration (existing)
N8N_AGENT_URL=https://pulseplan-agent.fly.dev
N8N_TIMEOUT=30000

# Existing OAuth credentials still required
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
```

## Database Schema

The system uses the existing `calendar_connections` table with encrypted token storage:

```sql
-- Existing table structure (tokens now encrypted)
calendar_connections:
  - id (uuid)
  - user_id (uuid)
  - provider (text) -- 'google', 'microsoft', 'canvas', 'notion'
  - access_token (text) -- ENCRYPTED
  - refresh_token (text) -- ENCRYPTED
  - expires_at (timestamp)
  - scopes (text[])
  - email (text)
  - created_at (timestamp)
  - updated_at (timestamp)
```

## API Endpoints

### Connection Management

#### Get Connection Status

```http
GET /connections/status/:userId
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "userId": "user-123",
    "connections": {
      "google": true,
      "microsoft": false,
      "canvas": false,
      "notion": false
    },
    "hasAnyConnections": true
  }
}
```

#### Get Connected Accounts (Sanitized)

```http
GET /connections/accounts/:userId
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "userId": "user-123",
    "accounts": [
      {
        "provider": "google",
        "email": "user@gmail.com",
        "scopes": ["calendar.read", "calendar.write"],
        "connected_at": "2024-01-01T00:00:00Z",
        "last_updated": "2024-01-15T00:00:00Z",
        "has_access_token": true,
        "has_refresh_token": true,
        "expires_at": "2024-01-16T00:00:00Z"
      }
    ]
  }
}
```

#### Disconnect Provider

```http
DELETE /connections/:provider/:userId
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "Successfully disconnected google for user user-123"
}
```

#### Test Agent Connection

```http
POST /connections/test-agent/:userId
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "userId": "user-123",
    "hasConnections": true,
    "agentHealthy": true,
    "connectionStatus": { "google": true, "microsoft": false },
    "message": "Agent service is healthy and tokens are available"
  }
}
```

#### Refresh Tokens

```http
POST /connections/refresh-tokens/:userId
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider": "google"  // Optional, refresh specific provider
}

Response:
{
  "success": true,
  "message": "Successfully refreshed google tokens for user user-123"
}
```

## Enhanced Agent Payloads

All agent API calls now include `connectedAccounts` with user tokens:

```json
{
  "userId": "user-123",
  "userEmail": "user@example.com",
  "userName": "John Doe",
  "isPremium": true,
  "source": "scheduler",
  "tool": "daily_briefing",
  "connectedAccounts": {
    "google": {
      "access_token": "ya29.a0...",
      "refresh_token": "1//04...",
      "expires_at": "2024-01-16T00:00:00Z",
      "scopes": ["https://www.googleapis.com/auth/calendar"],
      "email": "user@gmail.com"
    },
    "microsoft": {
      "access_token": "eyJ0eXAi...",
      "refresh_token": "M.R3_BAY...",
      "expires_at": "2024-01-16T00:00:00Z",
      "scopes": ["Calendars.Read", "Calendars.ReadWrite"]
    }
  }
}
```

## Usage Examples

### Using Enhanced Agent Service

```typescript
import { enhancedAgentService } from "../services/enhancedAgentService";

// Generate daily briefing with tokens
const briefing = await enhancedAgentService.generateDailyBriefing(
  userId,
  userEmail,
  userName,
  isPremium,
  city,
  timezone
);

// Chat with agent (includes tokens)
const response = await enhancedAgentService.chatWithAgent(
  userId,
  "What's on my calendar today?",
  context,
  userEmail,
  userName,
  isPremium
);

// Check connection status
const hasConnections = await enhancedAgentService.hasConnectedAccounts(userId);
```

### Using Token Service Directly

```typescript
import { tokenService } from "../services/tokenService";

// Get user tokens
const tokens = await tokenService.getUserTokensForAgent(userId);

// Check specific provider
const hasGoogle = await tokenService.hasProviderConnected(userId, "google");

// Store new tokens (during OAuth)
await tokenService.storeUserTokens(userId, "google", {
  access_token: "token...",
  refresh_token: "refresh...",
  expires_at: "2024-01-16T00:00:00Z",
  scopes: ["calendar.read"],
  email: "user@gmail.com",
});
```

## Security Features

### Token Encryption

- **Algorithm**: AES-256-GCM
- **Key**: Derived from `TOKEN_ENCRYPTION_KEY` environment variable
- **Storage**: Only encrypted tokens stored in database
- **Transmission**: Tokens only included in agent API calls

### Access Control

- All connection management endpoints require authentication
- Tokens never exposed in client-facing APIs
- Sanitized account information only

### Error Handling

- Graceful fallback when tokens unavailable
- Automatic token refresh on expiration
- Comprehensive logging without exposing sensitive data

## Scheduler Integration

The email scheduler automatically uses enhanced agent service:

```typescript
// Daily briefing job automatically includes tokens
const briefingData = await enhancedAgentService.generateDailyBriefing(
  user.id,
  user.email,
  user.name,
  user.is_premium,
  user.city,
  user.timezone
);
```

## Production Deployment

### Required Environment Variables

```bash
# Critical: Set a secure 32-character encryption key
TOKEN_ENCRYPTION_KEY=your_very_secure_32_character_key_here

# N8N Agent configuration (existing)
N8N_AGENT_URL=https://your-agent-api.com
N8N_TIMEOUT=30000

# OAuth credentials (existing)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
```

### Security Checklist

- [ ] Set secure `TOKEN_ENCRYPTION_KEY`
- [ ] Use HTTPS for all OAuth redirects
- [ ] Monitor token refresh rates
- [ ] Set up token cleanup jobs for deleted users
- [ ] Enable database encryption at rest
- [ ] Configure proper CORS policies

## Monitoring & Logging

The system logs:

- Token storage/retrieval operations
- Token refresh operations
- Agent API calls with token status
- Connection status changes
- Errors (without exposing tokens)

Example logs:

```
[INFO] Successfully stored google tokens for user user-123
[INFO] Enhanced agent briefing generated for user user-123
[WARN] Agent service failed for user user-456, using fallback
[ERROR] Error refreshing microsoft token for user user-789
```

## Migration from Existing System

The system is backward compatible:

1. Existing unencrypted tokens work normally
2. New tokens are automatically encrypted
3. Existing OAuth flows enhanced automatically
4. No breaking changes to existing APIs

## Troubleshooting

### Common Issues

1. **Tokens not found**: Check if user completed OAuth flow
2. **Agent calls failing**: Verify `AGENT_API_BASE_URL` and agent health
3. **Token refresh errors**: Check OAuth provider credentials
4. **Encryption errors**: Verify `TOKEN_ENCRYPTION_KEY` is set

### Debug Commands

```typescript
// Test connection status
GET /connections/status/:userId

// Test agent connectivity
POST /connections/test-agent/:userId

// Force token refresh
POST /connections/refresh-tokens/:userId
```
