<p align="center">
  <img src="https://github.com/user-attachments/assets/0833a286-ba32-42a2-a5ca-4ae8bda63168" alt="PulsePlan" width="355"/>
</p>

# PulsePlan - AI-Powered Task & Schedule Management

PulsePlan is a comprehensive productivity application that combines AI-powered task management with seamless calendar integration. Built with React Native and Expo, it offers a modern, intuitive interface for managing your schedule, tasks, and calendar events across multiple platforms.

## 🌟 Key Features

### 📅 **Advanced Calendar Integration**

- **Google Calendar & Microsoft Outlook** seamless synchronization
- **Bidirectional sync** - create, edit, and delete events from either platform
- **Intelligent conflict resolution** with automatic duplicate detection
- **Multiple calendar support** with selective synchronization
- **Real-time sync status** monitoring and error handling

### 🤖 **AI-Powered Task Management**

- Smart task prioritization and scheduling
- AI-generated suggestions for optimal time blocking
- Natural language processing for task creation
- Intelligent deadline and reminder management

### ⚡ **Modern UI/UX**

- Beautiful, responsive design with multiple theme options
- Smooth animations and haptic feedback
- Dark mode and customizable color schemes
- Accessibility-first design principles

### 🔒 **Secure & Private**

- Row-level security with Supabase
- OAuth 2.0 authentication for calendar providers
- End-to-end encryption for sensitive data
- GDPR-compliant data handling

## 🚀 Quick Start

### Prerequisites

- Node.js (v16 or higher)
- Expo CLI: `npm install -g @expo/cli`
- Supabase account
- Google Cloud Console account (for Google Calendar)
- Microsoft Azure account (for Outlook Calendar)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/PulsePlan.git
cd PulsePlan

# Install dependencies
npm run install:all

# Set up environment variables (see SETUP_GUIDE.md)
cp .env.example .env
# Edit .env with your API keys and credentials

# Run database schema
# Execute database-schema.sql in your Supabase SQL editor

# Start the development servers
npm run dev
```

### Calendar Integration Setup

For complete calendar integration setup instructions, see:

- 📖 **[Setup Guide](SETUP_GUIDE.md)** - Step-by-step setup instructions
- 📚 **[Calendar Integration Documentation](CALENDAR_INTEGRATION.md)** - Comprehensive API documentation
- 🔧 **[Database Schema](database-schema.sql)** - Complete database structure

### Verification

Test your calendar integration setup:

```bash
# Verify calendar integration is working
npm run verify-calendar

# Test server health
npm run test:connection

# Verify Supabase configuration
npm run verify-supabase
```

## 🏗️ Architecture

### Frontend (React Native + Expo)

- **Framework**: React Native with Expo SDK 53
- **Navigation**: Expo Router with file-based routing
- **State Management**: React Context API with custom hooks
- **UI Components**: Custom component library with Lucide icons
- **Styling**: StyleSheet with dynamic theming support

### Backend (Node.js + TypeScript)

- **Framework**: Express.js with TypeScript
- **Database**: Supabase PostgreSQL with Row Level Security
- **Authentication**: Supabase Auth + OAuth 2.0 for calendar providers
- **Calendar APIs**: Google Calendar API + Microsoft Graph API
- **Background Tasks**: Automatic calendar synchronization

### Calendar Integration Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PulsePlan     │    │   Backend API    │    │   External      │
│   Client App    │◄──►│   Server         │◄──►│   Calendar      │
│                 │    │                  │    │   Services      │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Calendar    │ │    │ │ Auth         │ │    │ │ Google      │ │
│ │ Integration │ │    │ │ Controllers  │ │    │ │ Calendar    │ │
│ │ Modal       │ │    │ └──────────────┘ │    │ │ API         │ │
│ └─────────────┘ │    │ ┌──────────────┐ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ │ Calendar     │ │    │ ┌─────────────┐ │
│ │ Calendar    │ │    │ │ Controllers  │ │    │ │ Microsoft   │ │
│ │ Service     │ │    │ └──────────────┘ │    │ │ Graph API   │ │
│ └─────────────┘ │    │ ┌──────────────┐ │    │ └─────────────┘ │
└─────────────────┘    │ │ Sync Service │ │    └─────────────────┘
                       │ └──────────────┘ │
                       └──────────────────┘
                                ▲
                                │
                       ┌──────────────────┐
                       │   Supabase       │
                       │   Database       │
                       │                  │
                       │ • Calendar       │
                       │   Connections    │
                       │ • Events         │
                       │ • Sync Status    │
                       │ • Conflicts      │
                       │ • Preferences    │
                       └──────────────────┘
```

## 📱 Application Structure

```
PulsePlan/
├── src/                          # Client-side React Native code
│   ├── app/                      # Expo Router pages
│   │   ├── (tabs)/              # Tab-based navigation
│   │   │   ├── index.tsx        # Dashboard/Home screen
│   │   │   ├── calendar.tsx     # Calendar view
│   │   │   ├── tasks.tsx        # Task management
│   │   │   └── settings.tsx     # Settings with calendar integration
│   │   └── auth/                # Authentication screens
│   ├── components/              # Reusable UI components
│   │   ├── CalendarIntegrationModal.tsx  # Calendar connection UI
│   │   └── ...
│   ├── services/                # API client services
│   │   ├── calendarService.ts   # Calendar API client
│   │   └── ...
│   ├── contexts/                # React Context providers
│   └── config/                  # Configuration files
├── server/                       # Backend Node.js server
│   ├── src/
│   │   ├── controllers/         # API endpoint handlers
│   │   │   ├── calendarController.ts        # Google Calendar API
│   │   │   ├── microsoftCalendarController.ts # Microsoft Calendar API
│   │   │   ├── googleAuthController.ts      # Google OAuth
│   │   │   └── microsoftAuthController.ts   # Microsoft OAuth
│   │   ├── routes/              # Express route definitions
│   │   │   └── calendarRoutes.ts           # Calendar API routes
│   │   ├── services/            # Business logic services
│   │   │   └── calendarSyncService.ts      # Calendar synchronization
│   │   ├── config/              # Server configuration
│   │   │   ├── google.ts        # Google API configuration
│   │   │   └── microsoft.ts     # Microsoft API configuration
│   │   └── middleware/          # Express middleware
│   └── package.json
├── scripts/                      # Utility scripts
│   └── verify-calendar-integration.js     # Integration verification
├── database-schema.sql           # Complete database schema
├── CALENDAR_INTEGRATION.md       # Comprehensive API documentation
├── SETUP_GUIDE.md               # Step-by-step setup instructions
└── README.md                    # This file
```

## 📋 Available Scripts

```bash
# Development
npm start                 # Start Expo development server
npm run dev              # Start both server and client concurrently
npm run dev:server       # Start backend server only
npm run dev:client       # Start Expo client only

# Testing & Verification
npm run verify-calendar  # Verify calendar integration setup
npm run test:connection  # Test server connectivity
npm run verify-supabase  # Verify Supabase configuration

# Installation
npm run install:all      # Install all dependencies (client + server)

# Platform-specific
npm run android          # Start Android development
npm run ios             # Start iOS development
npm run web             # Start web development
```

## 🔧 Environment Configuration

Create a `.env` file in the project root with the following structure:

```env
# Server Configuration
PORT=5000
CLIENT_URL=http://localhost:8081

# Supabase Database
EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Google Calendar Integration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URL=http://localhost:5000/auth/google/callback

# Microsoft Calendar Integration
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_REDIRECT_URL=http://localhost:5000/auth/microsoft/callback
MICROSOFT_TENANT_ID=common
```

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## 🎯 Calendar Integration Features

### ✅ Complete Implementation

- **OAuth 2.0 Authentication** for Google and Microsoft calendars
- **Bidirectional Event Synchronization** with conflict resolution
- **Full CRUD Operations** for calendar events
- **Multiple Calendar Support** per provider
- **Intelligent Conflict Detection** with confidence scoring
- **Automatic Token Refresh** and connection management
- **Real-time Sync Status** monitoring
- **User-friendly Integration Interface**
- **Comprehensive Error Handling** and recovery
- **Database Security** with Row Level Security policies

### 🔧 API Endpoints

**Authentication:**

- `GET /auth/google?userId={userId}` - Initiate Google OAuth
- `GET /auth/microsoft?userId={userId}` - Initiate Microsoft OAuth

**Calendar Management:**

- `GET /calendar/status/{userId}` - Get connection status
- `GET /calendar/google/events/{userId}` - Get Google Calendar events
- `GET /calendar/microsoft/events/{userId}` - Get Microsoft Calendar events

**Event Operations:**

- `POST /calendar/google/events/{userId}` - Create Google Calendar event
- `PUT /calendar/google/events/{userId}/{eventId}` - Update event
- `DELETE /calendar/google/events/{userId}/{eventId}` - Delete event

**Synchronization:**

- `POST /calendar/sync/{userId}` - Sync all calendars
- `GET /calendar/sync/status/{userId}` - Get sync status

For complete API documentation, see [CALENDAR_INTEGRATION.md](CALENDAR_INTEGRATION.md).

## 📚 Documentation

- **[Setup Guide](SETUP_GUIDE.md)** - Complete setup instructions for calendar integration
- **[Calendar Integration Docs](CALENDAR_INTEGRATION.md)** - Comprehensive API and feature documentation
- **[Database Schema](database-schema.sql)** - Complete database structure and security policies
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues with the calendar integration:

1. Check the [Setup Guide](SETUP_GUIDE.md) for configuration instructions
2. Run the verification script: `npm run verify-calendar`
3. Check the [troubleshooting section](CALENDAR_INTEGRATION.md#troubleshooting) in the documentation
4. Review server logs for specific error messages

## 🎉 What's Next

Your PulsePlan application now has complete, enterprise-grade calendar integration! The system supports:

- **Seamless OAuth authentication** for Google and Microsoft calendars
- **Bidirectional synchronization** with intelligent conflict resolution
- **Full event management** with all calendar features supported
- **Real-time sync monitoring** and error handling
- **Production-ready security** and performance optimization

Ready to sync your calendars and supercharge your productivity! 🚀
