# Google Contacts Integration

This document outlines the Google Contacts OAuth integration implementation in PulsePlan, which allows users to connect their Google Contacts for AI-powered contact management and communication features.

## Overview

The Google Contacts integration uses the Google People API v1 to access user contacts through OAuth 2.0 authentication. It shares the same OAuth tokens as the Google Calendar and Gmail integrations, providing a unified Google account connection experience.

## Architecture

### Backend Components

1. **OAuth Configuration** (`server/src/config/google.ts`)

   - Includes Google Contacts scopes: `contacts.readonly` and `contacts`
   - Shares OAuth client configuration with Calendar and Gmail

2. **Google Contacts Service** (`server/src/services/googleContactsService.ts`)

   - Handles Google People API interactions
   - Provides methods for reading, searching, and filtering contacts
   - Uses the same authentication tokens as other Google services

3. **API Routes** (`server/src/routes/contactsRoutes.ts`)
   - RESTful endpoints for contacts operations
   - OAuth flow endpoints for connection management
   - Status checking and disconnection endpoints

### Frontend Components

1. **Contacts Service** (`src/services/contactsService.ts`)

   - Frontend interface to backend contacts API
   - Handles OAuth flow initiation and status checking

2. **Contacts Integration Page** (`src/app/(settings)/integrations/contacts.tsx`)
   - User interface for connecting Google Contacts
   - Shows connection status and manages OAuth flow

## API Endpoints

### OAuth Endpoints

- `GET /contacts/auth` - Initiate Google OAuth for Contacts
- `GET /contacts/auth/callback` - Handle OAuth callback
- `DELETE /contacts/disconnect/:userId` - Disconnect Google Contacts
- `GET /contacts/status/:userId` - Get connection status

### Contacts Data Endpoints

- `GET /contacts/list` - Get all contacts with pagination
- `GET /contacts/search` - Search contacts by query
- `GET /contacts/get` - Get specific contact by resource name
- `GET /contacts/filter` - Filter contacts (emails/phones only)
- `GET /contacts/find-by-email` - Find contact by email address
- `GET /contacts/groups` - Get contact groups

## Google Contacts Service Methods

### Core Methods

```typescript
// Get all contacts with pagination
async getContacts(userId: string, pageSize?: number, pageToken?: string): Promise<ContactsResponse>

// Search contacts by query
async searchContacts(userId: string, query: string, pageSize?: number): Promise<ContactsResponse>

// Get specific contact
async getContact(userId: string, resourceName: string): Promise<Contact>
```

### Filtering Methods

```typescript
// Get contacts with email addresses only
async getContactsWithEmails(userId: string): Promise<Contact[]>

// Get contacts with phone numbers only
async getContactsWithPhones(userId: string): Promise<Contact[]>

// Find contact by email address
async findContactByEmail(userId: string, email: string): Promise<Contact | null>
```

### Organization Methods

```typescript
// Get contact groups
async getContactGroups(userId: string): Promise<any[]>
```

## Data Structures

### Contact Interface

```typescript
interface Contact {
  resourceName: string;
  displayName: string;
  emailAddresses?: Array<{
    value: string;
    type?: string;
    formattedType?: string;
  }>;
  phoneNumbers?: Array<{
    value: string;
    type?: string;
    formattedType?: string;
  }>;
  organizations?: Array<{
    name: string;
    title?: string;
  }>;
  photos?: Array<{
    url: string;
  }>;
}
```

### ContactsResponse Interface

```typescript
interface ContactsResponse {
  contacts: Contact[];
  totalCount: number;
  nextPageToken?: string;
}
```

## OAuth Scopes

The integration requires the following Google API scopes:

- `https://www.googleapis.com/auth/contacts.readonly` - Read access to contacts
- `https://www.googleapis.com/auth/contacts` - Full access to contacts (for future write operations)

These scopes are automatically included when users connect their Google account through any Google integration (Calendar, Gmail, or Contacts).

## Database Integration

The contacts integration uses the existing `calendar_connections` table to store OAuth tokens, sharing the same authentication infrastructure as other Google services. This provides:

- Unified token management
- Automatic token refresh
- Consistent connection status across all Google services

## N8N Agent Integration

The Google Contacts integration is automatically available to the N8N agent through the connected accounts system. When a user has connected their Google account, the agent can:

- Access contact information for context
- Find contacts by email for communication tasks
- Use contact data for personalized responses

## Frontend Integration

### Connection Flow

1. User navigates to Settings > Integrations > Contacts
2. Clicks "Add Google Contacts"
3. Redirected to Google OAuth consent screen
4. After approval, returns to app with connected status
5. Connection status updates automatically

### Status Display

The contacts integration page shows:

- Connection status with checkmarks for connected accounts
- Loading states during OAuth flow
- Error handling for failed connections

## Testing

### Test Script

Run the contacts integration test:

```bash
cd server
npx ts-node src/scripts/test-google-contacts.ts
```

### Manual Testing

1. Start the server: `npm run dev`
2. Open the app and navigate to Settings > Integrations > Contacts
3. Connect Google account
4. Test API endpoints with connected user ID

## Error Handling

The integration includes comprehensive error handling for:

- OAuth flow failures
- API rate limiting
- Token expiration
- Network connectivity issues
- Invalid user permissions

## Security Considerations

- OAuth tokens are stored securely in the database
- Sensitive tokens are masked in logs
- API requests use proper authentication headers
- Token refresh is handled automatically

## Future Enhancements

Potential future features include:

- Contact creation and editing
- Contact synchronization
- Advanced search and filtering
- Contact groups management
- Integration with messaging features

## Troubleshooting

### Common Issues

1. **"Google account not connected" error**

   - Ensure user has completed OAuth flow
   - Check token expiration in database
   - Verify Google API credentials

2. **API rate limiting**

   - Implement request throttling
   - Use appropriate page sizes
   - Cache frequently accessed data

3. **Permission errors**
   - Verify OAuth scopes in Google Cloud Console
   - Ensure People API is enabled
   - Check user consent for contacts access

### Debug Information

Enable debug logging by setting environment variables:

```bash
DEBUG=contacts:*
```

This will provide detailed logging for OAuth flows, API requests, and error conditions.
