# Canvas Integration Setup Guide

This guide explains how to set up and use the Canvas LMS integration with PulsePlan.

## Overview

The Canvas integration allows you to seamlessly sync assignments, grades, and due dates from your Canvas LMS to PulsePlan. It consists of:

1. **Chrome Extension** - Scrapes Canvas data from your browser
2. **Mobile App Integration** - QR code connection flow
3. **Backend API** - Processes and stores Canvas data
4. **Auto-sync** - Weekly automatic synchronization

## Features

✅ **Automatic Assignment Detection** - Detects assignments from Canvas dashboard and course pages  
✅ **Grade Scraping** - Extracts grades, points, and percentages  
✅ **Due Date Parsing** - Intelligent date extraction from various formats  
✅ **QR Code Connection** - One-time setup via QR code scanning  
✅ **Auto-sync** - Weekly background synchronization  
✅ **Status Tracking** - Real-time sync status and assignment counts

## Setup Instructions

### 1. Database Setup

Run the migration to add Canvas support to your database:

```sql
-- Run the migration file
\i server/migrations/001_add_canvas_fields.sql
```

### 2. Chrome Extension Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `extension/` folder
4. The PulsePlan Canvas Sync extension should now appear in your toolbar

### 3. Mobile App Connection

1. Open the PulsePlan mobile app
2. Go to **Settings** → **Integrations** → **Canvas LMS**
3. Tap "Connect Canvas" to generate a QR code
4. In Chrome, click the PulsePlan extension icon
5. Click "Scan QR Code" and scan the code from your mobile app
6. The extension will connect to your PulsePlan account

### 4. Canvas Usage

1. Navigate to any Canvas LMS page (dashboard, course assignments, etc.)
2. The extension automatically detects and stores assignments
3. Click the extension icon to see detected assignments
4. Click "Sync to PulsePlan" to upload assignments to your account

## API Endpoints

### Canvas Routes (`/canvas`)

- `POST /upload-data` - Upload Canvas assignments (used by extension)
- `GET /status` - Get Canvas integration status
- `POST /generate-connection-code` - Generate QR code for connection
- `POST /connect-extension` - Complete extension connection
- `GET /test-connection` - Test API connectivity

### Example API Usage

```javascript
// Get Canvas integration status
const response = await fetch("/canvas/status", {
  headers: {
    Authorization: `Bearer ${authToken}`,
  },
});

// Generate QR connection code
const qrResponse = await fetch("/canvas/generate-connection-code", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${authToken}`,
  },
});
```

## Data Structure

### Canvas Assignment Object

```typescript
interface CanvasAssignment {
  id: string; // Unique Canvas assignment ID
  title: string; // Assignment title
  course: string; // Course name
  dueDate?: string; // ISO date string
  url?: string; // Canvas assignment URL
  grade?: object; // Grade information (points, percentage, letter)
  status?: string; // Assignment status (pending, completed, etc.)
  scraped: string; // Timestamp when scraped
}
```

### Database Schema

#### Tasks Table (Canvas fields)

```sql
ALTER TABLE tasks ADD COLUMN:
- source VARCHAR(50) DEFAULT 'manual'
- canvas_id VARCHAR(255) UNIQUE
- canvas_url TEXT
- canvas_grade JSONB
- canvas_points DECIMAL(10,2)
- canvas_max_points DECIMAL(10,2)
```

#### Canvas Integrations Table

```sql
CREATE TABLE canvas_integrations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  is_active BOOLEAN DEFAULT false,
  last_sync TIMESTAMP WITH TIME ZONE,
  assignments_synced INTEGER DEFAULT 0,
  extension_version VARCHAR(50),
  connection_code VARCHAR(255),
  connection_code_expiry TIMESTAMP WITH TIME ZONE,
  connected_at TIMESTAMP WITH TIME ZONE
);
```

## Chrome Extension Architecture

### Files Structure

```
extension/
├── manifest.json       # Extension configuration (Manifest v3)
├── content.js         # Canvas page scraping logic
├── popup.html         # Extension popup interface
├── popup.js           # Popup interaction logic
├── upload.js          # Background service worker
└── icon.png           # Extension icon
```

### Content Script Features

- **Smart Detection** - Identifies Canvas assignment pages
- **Multi-format Parsing** - Handles dashboard cards, todo items, and course pages
- **Grade Extraction** - Parses various grade formats (points, percentages, letters)
- **Duplicate Prevention** - Caches assignments to avoid duplicates
- **Real-time Updates** - Uses MutationObserver for dynamic content

### Auto-sync Logic

The extension automatically syncs assignments:

- **Initial sync** - 1 hour after installation
- **Weekly sync** - Every 7 days
- **Manual sync** - Via popup button
- **Badge indicators** - Shows sync status and errors

## Mobile App Integration

### Canvas Service

```typescript
// Get integration status
const status = await CanvasService.getIntegrationStatus(authToken);

// Generate QR code
const qrData = await CanvasService.generateConnectionCode(authToken);

// Test connection
const test = await CanvasService.testConnection();
```

### Canvas Modal Component

- **Status Display** - Shows connection status and sync statistics
- **QR Code Generation** - Creates connection codes with 10-minute expiry
- **Real-time Updates** - Refreshes status automatically
- **Error Handling** - User-friendly error messages

## Troubleshooting

### Common Issues

1. **Extension not detecting assignments**

   - Ensure you're on a Canvas LMS page (\*.instructure.com)
   - Check that assignments are visible on the page
   - Try refreshing the page

2. **QR code connection fails**

   - Ensure both devices are connected to the internet
   - Check that the QR code hasn't expired (10 minutes)
   - Try generating a new QR code

3. **Sync fails**

   - Verify you're logged into PulsePlan
   - Check your internet connection
   - Look for error messages in the extension popup

4. **Missing grades**
   - Grades may not be available for all assignments
   - Check if grades are visible on the Canvas page
   - Some assignments may not have grades yet

### Debug Mode

Enable debug logging in the extension:

```javascript
// In browser console
chrome.storage.local.set({ debug_mode: true });
```

### API Testing

Test the Canvas API endpoints:

```bash
# Test connection
curl https://api.pulseplan.flyonthewalldev.com/canvas/test-connection

# Get status (requires auth)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.pulseplan.flyonthewalldev.com/canvas/status
```

## Security Considerations

- **JWT Authentication** - All API calls require valid authentication
- **Row Level Security** - Database policies ensure user data isolation
- **Connection Codes** - QR codes expire after 10 minutes
- **HTTPS Only** - All communication uses secure connections
- **No Password Storage** - Extension doesn't store Canvas credentials

## Future Enhancements

- **Real-time Sync** - WebSocket-based live updates
- **Grade Notifications** - Push notifications for new grades
- **Assignment Filtering** - Custom filters for assignment types
- **Bulk Operations** - Mass assignment management
- **Canvas API Integration** - Direct Canvas API access (requires Canvas API key)

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review browser console for error messages
3. Contact support with specific error details
4. Include extension version and Canvas LMS URL

---

**Note**: This integration requires Canvas LMS access and works with any Canvas instance (\*.instructure.com domains).
