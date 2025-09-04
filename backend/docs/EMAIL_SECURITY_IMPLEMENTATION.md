# Email Security Implementation

## Overview

This document outlines the secure email access implementation for PulsePlan's AI agent system. The implementation prioritizes user safety by requiring explicit approval for all email sends while providing secure access to user email accounts.

## Security Architecture

### 1. Token Encryption & Storage

**Encryption Service** (`backend/app/security/encryption.py`):
- **AES-256-GCM encryption** for OAuth tokens
- **User-specific key derivation** using PBKDF2 with 100,000 iterations
- **Salt format**: `"pulseplan:user:{user_id}:v{version}"`
- **Token format**: `"v{version}:{iv_hex}:{auth_tag_hex}:{encrypted_hex}"`
- **KMS support** ready for Phase 2 implementation

**Token Service** (`backend/app/services/token_service.py`):
- Secure retrieval of encrypted OAuth tokens
- Automatic token refresh for expired credentials
- Redis caching with TTL for performance
- Row-level security via Supabase

### 2. OAuth Integration

**Supported Providers**:
- **Gmail**: Full send/read access via Google API
- **Outlook**: Full send/read access via Microsoft Graph API
- **System Email**: One-way sending for agent notifications

**OAuth Scopes**:
- **Google**: `gmail.send`, `gmail.readonly`, `calendar` (existing)
- **Microsoft**: `mail.send`, `mail.read`, `calendars.readwrite` (existing)

**Security Features**:
- CSRF protection via state parameters
- Secure redirect handling
- Token encryption before storage
- Automatic token refresh

### 3. Mandatory User Verification System

**Core Safety Principle**: **NO EMAIL CAN BE SENT WITHOUT EXPLICIT USER APPROVAL**

#### Email Draft Verification Process

1. **Agent Request**: Agent attempts to send email via email tool
2. **Draft Creation**: System creates `EmailDraft` object with all details
3. **Verification Required**: `EmailVerificationRequired` exception is raised
4. **User Presentation**: Frontend shows draft with all details for approval
5. **User Decision**: User must explicitly approve or reject
6. **Secure Send**: Only after approval is the email actually sent

#### Safety Constraints Implementation

**Backend Constraints** (`backend/app/agents/tools/email.py`):
```python
class EmailVerificationRequired(Exception):
    """Exception raised when email needs user approval"""
    def __init__(self, draft: EmailDraft, message: str):
        self.draft = draft
        self.message = message

async def _handle_send_with_verification(...):
    # ALWAYS require user approval for email sends
    raise EmailVerificationRequired(
        draft=draft,
        message=f"PulsePlan needs your approval to send this email to {', '.join(recipients)}"
    )
```

**Frontend Safety** (`src/components/EmailDraftCard.tsx`):
- Clear display of recipient, subject, and message body
- Expandable message preview
- Explicit "Send Email" confirmation dialog
- Clear sender identification (user's email account)
- Cancel/reject option always available

## Implementation Components

### Backend Components

1. **Email Tools** (`backend/app/agents/tools/email.py`):
   - `EmailManagerTool`: Smart routing between providers
   - `GmailUserTool`: Gmail API integration with real HTTP calls
   - `OutlookUserTool`: Microsoft Graph API integration
   - `SystemEmailTool`: System notifications

2. **API Endpoints** (`backend/app/api/v1/endpoints/email.py`):
   - `/email/send`: Creates draft, requires approval
   - `/email/approve-draft`: Processes user approval
   - `/email/list`: Lists emails (read-only, no approval needed)
   - `/email/get`: Gets specific email (read-only)
   - `/email/connection-status`: Shows connected accounts

3. **Security Infrastructure**:
   - OAuth providers with token refresh
   - AES-256-GCM encryption service
   - Token service with secure retrieval
   - Redis caching for performance

### Frontend Components

1. **Email Service** (`src/services/emailService.ts`):
   - Handles all email API interactions
   - OAuth flow initiation
   - Draft approval workflow
   - Connection management

2. **Email Draft Card** (`src/components/EmailDraftCard.tsx`):
   - User-friendly draft approval interface
   - Clear display of all email details
   - Confirmation dialogs for safety
   - Visual feedback during send process

3. **Mail Integration Screen** (`src/app/(settings)/integrations/mail.tsx`):
   - OAuth connection management
   - Provider status display
   - Connection/disconnection flows

## Security Features

### 1. Email Send Safety

- **100% User Approval Required**: No email can be sent without explicit user consent
- **Visual Draft Preview**: User sees exactly what will be sent to whom
- **Confirmation Dialogs**: Multiple confirmation steps prevent accidental sends
- **Clear Attribution**: User knows which account is being used to send

### 2. Token Security

- **Encryption at Rest**: All OAuth tokens encrypted with user-specific keys
- **Secure Transmission**: HTTPS-only API calls
- **Token Rotation**: Automatic refresh of expired tokens
- **Revocation Support**: Easy disconnect from providers

### 3. Access Controls

- **Scoped Permissions**: Minimal required OAuth scopes
- **User Context**: All operations tied to authenticated user
- **Read/Write Separation**: Read operations don't require approval
- **Provider Isolation**: Each provider handled separately

## Usage Flow

### 1. Email Connection
```typescript
// User connects Gmail
await emailService.connectGmail(userId);
// OAuth flow completes, tokens encrypted and stored
```

### 2. Agent Email Request
```python
# Agent wants to send email
result = await email_tool.send_email({
    "to": ["user@example.com"],
    "subject": "Meeting Reminder",
    "body": "Don't forget about our meeting tomorrow at 2 PM"
}, context)
# Result contains draft requiring approval
```

### 3. User Approval
```typescript
// Frontend shows EmailDraftCard
<EmailDraftCard 
    draft={draft}
    onApprove={approveDraft}
    onReject={rejectDraft}
/>
// User clicks "Send Email" → confirmation dialog → API call
```

### 4. Secure Send
```python
# After approval, email actually sent
result = await email_tool.execute({
    "operation": "approve_send",
    "draft_id": draft_id
}, context)
```

## Error Handling

### 1. Network Errors
- Graceful degradation with user feedback
- Retry mechanisms for temporary failures
- Clear error messages for connection issues

### 2. Token Errors
- Automatic token refresh attempts
- OAuth re-authentication flow when needed
- Clear messaging when accounts need reconnection

### 3. API Errors
- Provider-specific error handling
- Rate limiting awareness
- Fallback to alternative providers when possible

## Monitoring & Observability

### 1. Security Logging
- All email operations logged with user context
- Draft creation and approval events tracked
- Failed attempts and security violations monitored

### 2. Performance Monitoring
- Token refresh success rates
- API response times for email providers
- User approval workflow completion rates

### 3. Error Tracking
- Authentication failures
- API integration issues
- User experience problems

## Future Enhancements

### 1. Enhanced Security (Phase 2)
- AWS KMS integration for token encryption
- Advanced threat detection
- Email content scanning for sensitive information

### 2. User Experience
- Bulk email approval
- Template management
- Smart recipient suggestions

### 3. Provider Expansion
- Apple Mail integration
- Additional enterprise providers
- Custom SMTP support

## Testing Strategy

### 1. Security Testing
- Token encryption/decryption validation
- OAuth flow security testing
- Access control verification

### 2. Integration Testing
- Gmail API integration tests
- Microsoft Graph API integration tests
- End-to-end approval workflow tests

### 3. User Experience Testing
- Draft approval flow usability
- Error handling scenarios
- Cross-platform compatibility

## Conclusion

This implementation provides a secure, user-controlled email access system that prioritizes safety above convenience. The mandatory approval system ensures users maintain complete control over their email communications while allowing the AI agent to assist with email composition and management.

Key security principles:
- **Never send without explicit approval**
- **Encrypt all stored tokens**
- **Minimize required permissions**
- **Clear user communication**
- **Comprehensive error handling**

The system is designed to be extensible, secure, and user-friendly while meeting the highest standards for handling sensitive email communications.