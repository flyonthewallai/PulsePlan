# Canvas Integration Guide

This document explains how to use the Canvas LMS integration in PulsePlan.

## Overview

The Canvas integration allows users to securely connect their Canvas LMS account and automatically sync assignments into their PulsePlan task list. The system provides:

- **Secure token storage** using envelope encryption
- **Idempotent syncing** that prevents duplicates
- **Resilient background jobs** that can resume after interruption
- **Delta sync** for efficient incremental updates
- **Comprehensive error handling** with automatic reauth

## Architecture

### Components

1. **Token Storage** (`canvas_token_service.py`)
   - Encrypts and stores Canvas API tokens
   - Handles token validation and reauth
   - Uses envelope encryption for security

2. **Sync Jobs**
   - **Initial Backfill** (`canvas_backfill_job.py`): First-time full sync
   - **Delta Sync** (`canvas_delta_sync_job.py`): Incremental updates

3. **API Endpoints** (`canvas_integration.py`)
   - REST API for frontend integration
   - Background job queuing
   - Status monitoring

4. **Database Models**
   - `integration_canvas`: Integration settings and status
   - `external_cursor`: Sync progress tracking
   - `assignment_import`: Staging table for raw data
   - Enhanced `tasks` table with external source tracking

## API Usage

### 1. Connect Canvas

```http
POST /api/v1/canvas/connect
Content-Type: application/json

{
  "canvas_url": "https://canvas.university.edu",
  "api_token": "your_canvas_api_token"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Canvas integration connected successfully",
  "user_id": "user-123",
  "canvas_url": "https://canvas.university.edu",
  "status": "connected",
  "stored_at": "2023-10-01T12:00:00Z"
}
```

### 2. Trigger Sync

```http
POST /api/v1/canvas/sync
Content-Type: application/json

{
  "sync_type": "full",
  "force_restart": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Full Canvas sync job queued successfully",
  "sync_id": "sync-456",
  "status": "queued"
}
```

### 3. Check Status

```http
GET /api/v1/canvas/status
```

**Response:**
```json
{
  "user_id": "user-123",
  "connected": true,
  "canvas_url": "https://canvas.university.edu",
  "status": "ok",
  "last_sync": "2023-10-01T12:00:00Z",
  "assignments_count": 42
}
```

### 4. Get Assignments

```http
GET /api/v1/canvas/assignments?limit=50&include_completed=false
```

**Response:**
```json
{
  "success": true,
  "user_id": "user-123",
  "assignments": [
    {
      "id": "task-789",
      "title": "Math Homework 5",
      "description": "Complete exercises 1-20",
      "due_date": "2023-10-15T23:59:00Z",
      "external_source": "canvas",
      "external_id": "12345",
      "subject": "Mathematics"
    }
  ],
  "count": 1
}
```

### 5. Disconnect

```http
DELETE /api/v1/canvas/disconnect
```

## Sync Process

### Initial Backfill

The initial backfill process:

1. **Fetch Courses**: Gets all active and recently completed courses
2. **Fetch Assignments**: For each course, fetches all published assignments
3. **Stage Data**: Stores raw Canvas payloads in staging table
4. **Process**: Converts assignments to tasks with proper mapping
5. **Track Progress**: Uses cursors to enable resumption

### Delta Sync

The delta sync process (runs every 15-30 minutes):

1. **Check Updates**: Fetches assignments updated since last sync
2. **Compare**: Checks if Canvas version is newer than our version
3. **Update/Create**: Updates existing tasks or creates new ones
4. **Delete Check**: Identifies assignments removed from Canvas
5. **Update Timestamp**: Records successful sync completion

## Error Handling

### 401 Unauthorized
- Automatically marks integration as `needs_reauth`
- User must reconnect Canvas integration
- Previous data is preserved

### Network/Timeout Errors
- Exponential backoff retry
- Progress is maintained via cursors
- Job can resume from interruption point

### Partial Failures
- Individual course failures don't stop entire sync
- Error details are logged and reported
- Successful portions are committed

## Data Mapping

### Canvas Assignment → PulsePlan Task

| Canvas Field | PulsePlan Field | Notes |
|--------------|-----------------|--------|
| `name` | `title` | Assignment title |
| `description` | `description` | HTML stripped |
| `due_at` | `due_date` | ISO timestamp |
| `points_possible` | Used for `estimated_minutes` | Points × 3 minutes |
| `course.name` | `subject` | Course name |
| `id` | `external_id` | Canvas assignment ID |
| `course_id` | `external_course_id` | Canvas course ID |
| `updated_at` | `external_updated_at` | Last Canvas update |

### Task Types

- `online_quiz` → `exam`
- `discussion_topic` → `task`
- Default → `assignment`

## Security

### Token Encryption
- Uses envelope encryption with user-specific keys
- Tokens are never logged or exposed
- KMS integration ready for production

### Database Security
- Row Level Security (RLS) policies
- Unique constraints prevent duplicates
- Foreign key cascades for cleanup

### API Security
- Rate limiting on all endpoints
- Input validation and sanitization
- Authentication required

## Performance

### Optimization Features
- Batch processing for large datasets
- Database indexes for fast queries
- Pagination for API responses
- Background job processing

### Scalability
- Handles 10+ courses with 100+ assignments
- Efficient delta sync for regular updates
- Cursor-based progress tracking
- Graceful error recovery

## Monitoring

### Integration Status
- `ok`: Integration working normally
- `needs_reauth`: Token expired or revoked
- `error`: Sync failures or other issues

### Sync Tracking
- `last_full_sync_at`: Last complete backfill
- `last_delta_at`: Last incremental sync
- `last_error_code`: Most recent error

### Logging
- Structured logging with correlation IDs
- Error details with context
- Performance metrics

## Testing

Run the test suite:

```bash
cd backend
python test_canvas_integration.py
```

This validates:
- Database models and constraints
- Token encryption/decryption
- Job initialization
- API model validation
- Complete integration flow

## Deployment

1. **Run Migration**:
   ```sql
   -- Apply database migration
   \i migrations/add_canvas_integration_tables.sql
   ```

2. **Configure Environment**:
   ```bash
   # Add to .env
   CANVAS_INTEGRATION_ENABLED=true
   ```

3. **Background Jobs**:
   - Set up recurring delta sync job (every 15-30 minutes)
   - Configure job queue for background processing
   - Monitor job success rates

The Canvas integration is production-ready and follows all security and performance best practices!