# N8N Connected Accounts Integration

This guide explains how to set up n8n to access user's connected accounts (Gmail, Google Calendar, Microsoft Outlook, etc.) through PulsePlan's authentication system.

## Overview

When users connect their accounts through PulsePlan (Google, Microsoft, etc.), the authentication tokens are stored securely in the database. The n8n agent can now access these tokens to perform actions on behalf of the user.

## How It Works

1. **User Authentication**: Users connect their accounts through PulsePlan's OAuth flows
2. **Token Storage**: Access tokens, refresh tokens, and metadata are stored in `calendar_connections` table
3. **Token Sharing**: When sending requests to n8n, PulsePlan includes valid tokens in the payload
4. **n8n Access**: n8n workflows can use these tokens to access connected services

## Payload Structure

The enhanced payload sent to n8n now includes:

```json
{
  "userId": "user-uuid",
  "userEmail": "user@example.com",
  "userName": "John Doe",
  "isPremium": true,
  "city": "San Francisco",
  "timezone": "America/Los_Angeles",
  "query": "Check my emails from today",
  "date": "2024-01-15T10:30:00Z",
  "source": "app",
  "context": {
    "currentPage": "agent",
    "recentTasks": [...],
    "chatHistory": [...],
    "workingHours": {...}
  },
  "connectedAccounts": {
    "google": {
      "accessToken": "ya29.a0...",
      "refreshToken": "1//04...",
      "email": "user@gmail.com",
      "expiresAt": "2024-01-15T11:30:00Z"
    },
    "microsoft": {
      "accessToken": "eyJ0eXAi...",
      "refreshToken": "M.C5...",
      "email": "user@outlook.com",
      "expiresAt": "2024-01-15T11:30:00Z"
    }
  }
}
```

### User Information Fields

The payload now includes comprehensive user information for better context-aware responses:

- **`userName`**: User's display name for personalized interactions
- **`isPremium`**: Subscription status for feature access control
- **`city`**: User's city for location-aware features and local time context
- **`timezone`**: User's timezone (e.g., "America/Los_Angeles", "Europe/London") for accurate time calculations

## N8N Workflow Setup

### 1. Webhook Node Configuration

Your webhook remains the same - it receives the enhanced payload with connected accounts.

### 2. Extract Connected Accounts

Add a **Code Node** after your webhook to extract and validate tokens:

```javascript
// Extract connected accounts from the payload
const connectedAccounts = $json.connectedAccounts || {};

// Check which services are available
const availableServices = Object.keys(connectedAccounts);

// Set up authentication headers for different services
const authHeaders = {};

if (connectedAccounts.google) {
  authHeaders.google = {
    Authorization: `Bearer ${connectedAccounts.google.accessToken}`,
    "Content-Type": "application/json",
  };
}

if (connectedAccounts.microsoft) {
  authHeaders.microsoft = {
    Authorization: `Bearer ${connectedAccounts.microsoft.accessToken}`,
    "Content-Type": "application/json",
  };
}

return {
  json: {
    originalPayload: $json,
    connectedAccounts,
    availableServices,
    authHeaders,
    userEmail:
      connectedAccounts.google?.email ||
      connectedAccounts.microsoft?.email ||
      "unknown",
  },
};
```

### 3. Service Detection Switch

Add a **Switch Node** to route based on available services:

- **Route 1**: `{{ $json.availableServices.includes('google') }}` - Google services available
- **Route 2**: `{{ $json.availableServices.includes('microsoft') }}` - Microsoft services available
- **Route 3**: `{{ $json.availableServices.length === 0 }}` - No connected accounts

### 4. Google Services Integration

#### Gmail Access

Add an **HTTP Request Node** for Gmail:

```javascript
// Configuration
Method: GET
URL: https://gmail.googleapis.com/gmail/v1/users/me/messages
Headers: {{ $json.authHeaders.google }}
Query Parameters:
  - q: is:unread newer_than:1d
  - maxResults: 10
```

#### Google Calendar Access

Add an **HTTP Request Node** for Google Calendar:

```javascript
// Configuration
Method: GET
URL: https://www.googleapis.com/calendar/v3/calendars/primary/events
Headers: {{ $json.authHeaders.google }}
Query Parameters:
  - timeMin: {{ new Date().toISOString() }}
  - timeMax: {{ new Date(Date.now() + 24*60*60*1000).toISOString() }}
  - singleEvents: true
  - orderBy: startTime
```

### 5. Microsoft Services Integration

#### Outlook Email Access

Add an **HTTP Request Node** for Outlook:

```javascript
// Configuration
Method: GET
URL: https://graph.microsoft.com/v1.0/me/messages
Headers: {{ $json.authHeaders.microsoft }}
Query Parameters:
  - $filter: isRead eq false and receivedDateTime ge {{ new Date(Date.now() - 24*60*60*1000).toISOString() }}
  - $top: 10
  - $orderby: receivedDateTime desc
```

#### Microsoft Calendar Access

Add an **HTTP Request Node** for Microsoft Calendar:

```javascript
// Configuration
Method: GET
URL: https://graph.microsoft.com/v1.0/me/events
Headers: {{ $json.authHeaders.microsoft }}
Query Parameters:
  - $filter: start/dateTime ge '{{ new Date().toISOString() }}' and start/dateTime le '{{ new Date(Date.now() + 24*60*60*1000).toISOString() }}'
  - $orderby: start/dateTime
  - $top: 10
```

### 6. Error Handling

Add **HTTP Request Error Handling**:

```javascript
// In a Code Node for error handling
if ($json.error) {
  const errorCode = $json.error.code || $json.statusCode;

  if (errorCode === 401) {
    // Token expired - inform PulsePlan to refresh
    return {
      json: {
        success: false,
        error: "authentication_expired",
        message: "User needs to reconnect their account",
        provider: $("Switch").first().json.provider,
      },
    };
  }

  return {
    json: {
      success: false,
      error: "api_error",
      message: `Service error: ${$json.error.message || "Unknown error"}`,
      statusCode: errorCode,
    },
  };
}
```

## Example Workflows

### Email Summary Workflow

1. **Webhook** receives request with query about emails
2. **Code Node** extracts Google/Microsoft tokens
3. **Switch Node** routes to appropriate email service
4. **HTTP Request** fetches recent emails
5. **Code Node** processes and summarizes emails
6. **AI Node** formats the summary
7. **Respond to Webhook** returns formatted email summary

### Calendar Management Workflow

1. **Webhook** receives calendar-related query
2. **Code Node** extracts authentication tokens
3. **HTTP Request** fetches calendar events
4. **Code Node** processes calendar data
5. **Switch Node** determines if action is needed (create/update/delete)
6. **HTTP Request** performs calendar action if needed
7. **Respond to Webhook** returns calendar information

### Smart Task Creation

1. **Webhook** receives task creation request
2. **Code Node** extracts connected accounts
3. **HTTP Request** checks calendar for availability
4. **HTTP Request** checks emails for context
5. **AI Node** suggests optimal scheduling
6. **HTTP Request** creates calendar event
7. **Respond to Webhook** confirms task creation

## Security Considerations

1. **Token Expiration**: Always check token expiration before use
2. **Refresh Tokens**: Implement token refresh logic for expired tokens
3. **Scope Validation**: Only access data within granted scopes
4. **Error Handling**: Gracefully handle authentication failures
5. **Logging**: Never log sensitive tokens or user data

## Testing

Use the test script to verify connected accounts:

```bash
# Test with a user who has connected accounts
node server/src/scripts/test-n8n-agent.ts
```

## Troubleshooting

### Common Issues

1. **No Connected Accounts**: User hasn't connected any services

   - **Solution**: Guide user to connect accounts in settings

2. **Expired Tokens**: Access tokens have expired

   - **Solution**: Implement token refresh or ask user to reconnect

3. **Insufficient Permissions**: Token doesn't have required scopes

   - **Solution**: Update OAuth scopes and ask user to reconnect

4. **API Rate Limits**: Too many requests to external services
   - **Solution**: Implement request throttling and caching

### Debug Steps

1. Check if tokens are present in the payload
2. Verify token expiration dates
3. Test API calls with tokens directly
4. Check n8n execution logs for detailed errors
5. Verify OAuth scopes match required permissions

## Future Enhancements

1. **Token Refresh**: Automatic token refresh when expired
2. **More Services**: Support for additional services (Slack, Notion, etc.)
3. **Granular Permissions**: More specific scope management
4. **Caching**: Cache API responses to reduce external calls
5. **Webhooks**: Real-time updates from connected services
