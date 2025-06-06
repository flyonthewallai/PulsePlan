# PulsePlan - Complete Technical Specification

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Application Flow](#application-flow)
6. [Frontend Architecture](#frontend-architecture)
7. [Backend Architecture](#backend-architecture)
8. [Database & Authentication](#database--authentication)
9. [Browser Extension](#browser-extension)
10. [Configuration & Build System](#configuration--build-system)
11. [Key Components Detailed Analysis](#key-components-detailed-analysis)
12. [Data Flow & State Management](#data-flow--state-management)
13. [API Integration](#api-integration)
14. [Development Workflow](#development-workflow)
15. [Deployment Architecture](#deployment-architecture)

---

## Project Overview

**PulsePlan** is an AI-powered academic scheduling application designed specifically for students. It's a cross-platform mobile application built with React Native and Expo, featuring:

- **Academic Integration**: Canvas LMS integration via browser extension
- **AI-Powered Scheduling**: GPT-4o integration for intelligent task scheduling
- **Calendar Sync**: Google Calendar, Outlook, and Apple Calendar integration
- **Task Management**: Comprehensive task creation, editing, and tracking
- **Authentication**: Supabase Auth with Google OAuth
- **Freemium Model**: Stripe integration for premium features
- **Real-time Updates**: Live task synchronization across devices

---

## Architecture Overview

PulsePlan follows a **microservice-like architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  React Native App (Expo)  │  Browser Extension (Chrome)    │
│  - iOS/Android/Web        │  - Canvas LMS Integration      │
│  - Main User Interface    │  - Assignment Import           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                │
├─────────────────────────────────────────────────────────────┤
│           Node.js/Express Backend Server                   │
│  - RESTful API endpoints                                   │
│  - Authentication middleware                               │
│  - Business logic                                         │
│  - External service integrations                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 SERVICES LAYER                              │
├─────────────────────────────────────────────────────────────┤
│ Supabase │ OpenAI │ Google │ Microsoft │ Stripe │ Canvas  │
│(Database)│ (AI)   │Calendar│  Graph   │(Payment)│  (LMS)  │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
- **React Native 0.79.2**: Cross-platform mobile development
- **Expo SDK 53**: Development platform and deployment tools
- **Expo Router 5.0.7**: File-based routing system
- **TypeScript 5.8.3**: Static type checking
- **React Context API**: State management
- **Lucide React Native**: Icon library
- **React Native Reanimated**: Smooth animations

### Backend
- **Node.js**: Runtime environment
- **Express.js**: Web application framework
- **TypeScript**: Backend type safety
- **CORS**: Cross-origin resource sharing
- **ts-node**: TypeScript execution for development

### Database & Authentication
- **Supabase**: Backend-as-a-Service (PostgreSQL)
- **Supabase Auth**: Authentication service
- **AsyncStorage**: Local data persistence

### External Integrations
- **OpenAI GPT-4o**: AI assistant and scheduling
- **Google Calendar API**: Calendar integration
- **Microsoft Graph API**: Outlook integration
- **Stripe**: Payment processing
- **Canvas LMS**: Academic data integration

### Development Tools
- **Metro**: React Native bundler
- **Babel**: JavaScript transpiler
- **ESLint/Prettier**: Code formatting and linting

---

## Project Structure

```
PulsePlan/
├── 📁 Root Configuration Files
│   ├── app.json              # Expo app configuration
│   ├── package.json          # Dependencies and scripts
│   ├── tsconfig.json         # TypeScript configuration
│   ├── babel.config.js       # Babel transpiler config
│   ├── metro.config.js       # Metro bundler config
│   ├── polyfills.js          # Node.js polyfills for RN
│   ├── index.ts              # App entry point
│   └── .gitignore            # Git ignore rules
├── 📁 src/                   # Main application source
│   ├── 📁 app/               # Expo Router screens
│   │   ├── _layout.tsx       # Root layout with providers
│   │   ├── index.tsx         # Landing/loading screen
│   │   ├── auth.tsx          # Authentication screen
│   │   ├── onboarding.tsx    # User onboarding flow
│   │   ├── +not-found.tsx    # 404 error screen
│   │   └── 📁 (tabs)/        # Tab navigation group
│   │       ├── _layout.tsx   # Tab bar configuration
│   │       ├── home.tsx      # Today's schedule view
│   │       ├── week.tsx      # Weekly calendar view
│   │       ├── progress.tsx  # Analytics and progress
│   │       └── settings.tsx  # App settings and profile
│   ├── 📁 components/        # Reusable UI components
│   │   ├── TaskCard.tsx      # Individual task display
│   │   ├── TaskCreateModal.tsx   # Task creation form
│   │   ├── TaskDetailsModal.tsx  # Task editing interface
│   │   ├── AIAssistantModal.tsx  # Chat interface
│   │   ├── HourlyScheduleView.tsx # Calendar timeline
│   │   ├── CompletionRing.tsx    # Progress visualization
│   │   ├── BarChart.tsx      # Statistics charts
│   │   ├── ThemeSelector.tsx # Theme switching UI
│   │   └── [other components...]
│   ├── 📁 contexts/          # React Context providers
│   │   ├── AuthContext.tsx   # Authentication state
│   │   ├── TaskContext.tsx   # Task management state
│   │   ├── ThemeContext.tsx  # Theme and styling
│   │   ├── SettingsContext.tsx # App preferences
│   │   ├── PremiumContext.tsx # Subscription state
│   │   └── ProfileContext.tsx # User profile data
│   ├── 📁 lib/               # Core libraries and configs
│   │   ├── supabase-rn.ts    # Supabase client setup
│   │   ├── supabase.ts       # Alternative Supabase config
│   │   ├── polyfills.ts      # React Native polyfills
│   │   └── ws-mock.js        # WebSocket mock for RN
│   ├── 📁 services/          # External service integrations
│   │   ├── schedulingService.ts # AI scheduling logic
│   │   └── chatService.ts    # AI assistant communication
│   ├── 📁 config/            # Configuration files
│   │   ├── api.ts            # API base configuration
│   │   ├── constants.ts      # App constants
│   │   └── supabase.ts       # Supabase configuration
│   ├── 📁 types/             # TypeScript type definitions
│   │   ├── task.ts           # Task-related types
│   │   └── env.d.ts          # Environment variables types
│   ├── 📁 utils/             # Utility functions
│   │   └── markdownParser.ts # Markdown processing
│   ├── 📁 hooks/             # Custom React hooks
│   ├── 📁 constants/         # App-wide constants
│   └── 📁 assets/            # Static assets (images, icons)
├── 📁 server/                # Backend API server
│   ├── package.json          # Server dependencies
│   ├── tsconfig.json         # Server TypeScript config
│   └── 📁 src/               # Server source code
│       ├── index.ts          # Server entry point
│       ├── 📁 routes/        # API route definitions
│       │   ├── authRoutes.ts     # Authentication endpoints
│       │   ├── tasksRoutes.ts    # Task CRUD operations
│       │   ├── calendarRoutes.ts # Calendar sync endpoints
│       │   ├── schedulingRoutes.ts # AI scheduling endpoints
│       │   ├── stripeRoutes.ts   # Payment processing
│       │   ├── scheduleBlocks.ts # Time block management
│       │   └── chat.ts       # AI assistant endpoints
│       ├── 📁 controllers/   # Business logic controllers
│       ├── 📁 services/      # External service integrations
│       ├── 📁 middleware/    # Express middleware
│       ├── 📁 config/        # Server configuration
│       ├── 📁 types/         # Server TypeScript types
│       └── 📁 utils/         # Server utility functions
└── 📁 extension/             # Chrome extension for Canvas
    ├── manifest.json         # Extension configuration
    ├── popup.html            # Extension popup UI
    ├── popup.js              # Popup functionality
    ├── content.js            # Canvas page interaction
    ├── upload.js             # Data sync with PulsePlan
    └── README.md             # Extension documentation
```

---

## Application Flow

### 1. **App Initialization**
```typescript
index.ts → App Registration → Root Layout → Provider Stack
```

### 2. **Authentication Flow**
```typescript
1. User opens app → index.tsx (loading screen)
2. AuthContext checks session status
3. If unauthenticated → auth.tsx (login/signup)
4. If authenticated but needs onboarding → onboarding.tsx
5. If fully authenticated → (tabs)/home.tsx
```

### 3. **Main Application Navigation**
```typescript
Tab Navigation Structure:
├── home.tsx        # Today's tasks and schedule
├── week.tsx        # Weekly calendar view  
├── progress.tsx    # Analytics and streaks
└── settings.tsx    # User preferences and profile
```

### 4. **Task Management Flow**
```typescript
1. Task Creation: TaskCreateModal → TaskContext → API → Database
2. Task Updates: TaskDetailsModal → TaskContext → API → Database  
3. Task Completion: TaskCard interaction → Context update → Sync
4. AI Scheduling: schedulingService → OpenAI API → Schedule generation
```

---

## Frontend Architecture

### **Entry Point Chain**
1. **`index.ts`**: Registers the root component with Expo
2. **`src/app/_layout.tsx`**: Root layout with all context providers
3. **`src/app/index.tsx`**: Initial loading screen with navigation logic
4. **Authentication routing**: Handled by `AuthContext`

### **Context Provider Hierarchy**
```typescript
SafeAreaProvider
└── AuthProvider           # Authentication state
    └── ThemeProvider       # Theme and styling
        └── SettingsProvider # App preferences  
            └── TaskProvider # Task management
                └── AppWithTheme # Main app component
```

### **Routing System (Expo Router)**
- **File-based routing**: Each file in `src/app/` becomes a route
- **Group routing**: `(tabs)` creates tab navigation group
- **Layout files**: `_layout.tsx` defines layout for route groups
- **Dynamic routing**: Navigation handled via `useRouter()` hook

### **State Management Architecture**
- **React Context API**: Primary state management
- **AsyncStorage**: Local persistence for offline capability
- **Supabase realtime**: Live data synchronization (disabled in current config)
- **Optimistic updates**: UI updates immediately, syncs in background

---

## Backend Architecture

### **Server Entry Point (`server/src/index.ts`)**
```typescript
Express App Initialization:
1. Environment configuration loading
2. CORS setup for cross-origin requests
3. Middleware configuration (JSON parsing, raw body for Stripe)
4. Route registration for all API endpoints
5. Port discovery and server startup
6. Health check endpoint for monitoring
```

### **API Route Structure**
```typescript
Base URL: http://localhost:5000 (or dynamic port)

Authentication Routes (/auth):
├── POST /auth/login          # User login
├── POST /auth/register       # User registration  
├── POST /auth/logout         # User logout
└── GET  /auth/profile        # Get user profile

Task Routes (/tasks):
├── GET    /tasks             # Get user tasks
├── POST   /tasks             # Create new task
├── PUT    /tasks/:id         # Update task
└── DELETE /tasks/:id         # Delete task

Calendar Routes (/calendar):
├── GET  /calendar/google     # Google Calendar sync
├── GET  /calendar/microsoft  # Outlook sync
└── POST /calendar/sync       # Manual sync trigger

Scheduling Routes (/scheduling):
├── POST /scheduling/generate # AI schedule generation
└── GET  /scheduling/blocks   # Get schedule blocks

Payment Routes (/stripe):
├── POST /stripe/create-session    # Create payment session
├── POST /stripe/webhook          # Stripe webhook handler
└── GET  /stripe/subscription     # Get subscription status

AI Assistant Routes (/chat):
├── POST /chat/message        # Send message to AI
└── GET  /chat/history        # Get chat history
```

### **Middleware Stack**
1. **CORS**: Configured for development (*) and production (specific origins)
2. **Body Parsing**: JSON for most routes, raw for Stripe webhooks
3. **Authentication**: JWT token validation (implied in routes)
4. **Error Handling**: Centralized error responses
5. **Port Management**: Dynamic port allocation with collision detection

---

## Database & Authentication

### **Supabase Configuration**
- **Database**: PostgreSQL hosted by Supabase
- **Authentication**: Supabase Auth with Google OAuth
- **Storage**: User profile data and task information
- **Real-time**: Disabled for React Native compatibility

### **Authentication Flow**
```typescript
1. User Login/Signup → Supabase Auth
2. JWT Token generation → Stored in AsyncStorage
3. Token validation → Middleware on protected routes
4. Session management → Auto-refresh tokens
5. User state → Managed in AuthContext
```

### **Data Models**
```typescript
User: {
  id: string
  email: string
  full_name?: string
  created_at: string
}

Task: {
  id: string
  user_id: string
  title: string
  description: string
  subject: string
  due_date: string
  estimated_minutes?: number
  status: 'pending' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
  created_at: string
}
```

### **Offline Capability**
- **Local Caching**: Tasks cached in AsyncStorage
- **Sync Strategy**: Background sync when online
- **Conflict Resolution**: Last-write-wins approach
- **Error Handling**: Graceful degradation when offline

---

## Browser Extension

### **Chrome Extension Architecture**
The Canvas sync extension consists of:

1. **`manifest.json`**: Extension configuration
   - **Permissions**: activeTab, scripting, storage
   - **Host permissions**: Canvas LMS domains
   - **Content scripts**: Auto-injection on Canvas pages

2. **`content.js`**: Canvas page interaction
   - **DOM scanning**: Extracts assignment data
   - **Event listeners**: Detects page changes
   - **Data collection**: Assignment titles, due dates, descriptions

3. **`popup.html/js`**: Extension popup interface
   - **User controls**: Sync triggers and settings
   - **Status display**: Last sync time and results
   - **Authentication**: Extension-to-app linking

4. **`upload.js`**: Background service worker
   - **Data processing**: Formats Canvas data for PulsePlan API
   - **API communication**: Sends assignments to backend
   - **Error handling**: Retry logic and user notifications

### **Canvas Integration Flow**
```typescript
1. User navigates to Canvas assignments page
2. Content script detects assignment data
3. Extension popup shows sync options
4. User clicks sync → upload.js processes data
5. Data sent to PulsePlan API → tasks created
6. Confirmation shown in extension popup
```

---

## Configuration & Build System

### **Metro Configuration (`metro.config.js`)**
- **Node.js Polyfills**: Adds browser-compatible versions of Node modules
- **Module Resolution**: Custom alias configuration (@/ for src/)
- **Platform Support**: iOS, Android, web platforms
- **Asset Processing**: Custom asset bundle patterns
- **WebSocket Mocking**: Custom WebSocket implementation for React Native

### **Babel Configuration (`babel.config.js`)**
- **Preset**: babel-preset-expo for React Native compatibility
- **Module Resolver**: Path aliasing for cleaner imports
- **Environment Variables**: react-native-dotenv for .env support
- **Reanimated Plugin**: Enables advanced animations

### **TypeScript Configuration (`tsconfig.json`)**
- **Strict Mode**: Enabled for type safety
- **Path Mapping**: @/* aliases to src/* for clean imports
- **Expo Base**: Extends Expo's recommended TypeScript settings

### **Polyfills System**
- **`polyfills.js`**: Root-level polyfills for Node.js compatibility
- **`src/lib/polyfills.ts`**: React Native specific polyfills
- **WebSocket Mock**: Custom implementation for Supabase realtime compatibility

---

## Key Components Detailed Analysis

### **1. AuthContext (`src/contexts/AuthContext.tsx`)**
**Purpose**: Manages authentication state and navigation logic

**Key Features**:
- Session management with automatic refresh
- Onboarding state tracking per user
- Navigation logic based on auth status
- Error handling and recovery
- AsyncStorage integration for session persistence

**State Management**:
```typescript
interface AuthContextType {
  user: User | null                    # Current authenticated user
  session: Session | null              # Supabase session object
  loading: boolean                     # Loading state for auth operations
  isAuthenticated: boolean             # Computed auth status
  error: string | null                 # Authentication errors
  refreshAuth: () => Promise<void>     # Manual auth refresh
  needsOnboarding: boolean             # Onboarding completion status
  markOnboardingComplete: () => Promise<void> # Mark onboarding done
}
```

**Navigation Logic**:
- Unauthenticated users → `/auth`
- Authenticated users needing onboarding → `/onboarding`
- Fully authenticated users → `/(tabs)/home`

### **2. TaskContext (`src/contexts/TaskContext.tsx`)**
**Purpose**: Manages task state, CRUD operations, and offline synchronization

**Key Features**:
- Task CRUD operations with API integration
- Offline caching with AsyncStorage
- Network status monitoring
- Optimistic updates for better UX
- Error handling and retry logic

**State Management**:
```typescript
interface TaskContextType {
  tasks: Task[]                        # All user tasks
  loading: boolean                     # Loading state for task operations
  error: string | null                 # Task-related errors
  refreshTasks: () => Promise<void>    # Refresh from API
  createTask: (task: CreateTaskData) => Promise<void> # Create new task
  updateTask: (taskId: string, updates: Partial<Task>) => Promise<void> # Update task
  deleteTask: (taskId: string) => Promise<void> # Delete task
  isOnline: boolean                    # Network connectivity status
}
```

**Caching Strategy**:
- Tasks cached locally for offline access
- Background sync when network available
- Last sync timestamp tracking
- Graceful degradation when offline

### **3. ThemeContext (`src/contexts/ThemeContext.tsx`)**
**Purpose**: Manages application theming and visual customization

**Features**:
- Multiple theme variants (standard, vibrant, minimal, etc.)
- Premium theme unlocking
- Dynamic theme switching
- Color system management
- Consistent styling across components

### **4. Main Screens Analysis**

#### **Home Screen (`src/app/(tabs)/home.tsx`)**
- **Purpose**: Today's schedule and immediate tasks
- **Features**: Current task display, quick actions, schedule timeline
- **Components**: TaskCard, HourlyScheduleView, CompletionRing

#### **Week Screen (`src/app/(tabs)/week.tsx`)**
- **Purpose**: Weekly calendar view and planning
- **Features**: Week navigation, task distribution, schedule overview
- **Components**: Calendar grid, task summaries

#### **Progress Screen (`src/app/(tabs)/progress.tsx`)**
- **Purpose**: Analytics, streaks, and performance metrics
- **Features**: Completion statistics, streak tracking, progress charts
- **Components**: BarChart, CompletionRing, StreakModal

#### **Settings Screen (`src/app/(tabs)/settings.tsx`)**
- **Purpose**: User preferences, profile management, app configuration
- **Features**: Theme selection, account settings, subscription management
- **Components**: ThemeSelector, profile forms, premium upgrade options

---

## Data Flow & State Management

### **State Flow Architecture**
```typescript
User Action → Component → Context → Service Layer → API → Database
                ↓           ↓          ↓           ↓       ↓
            UI Update ← State Update ← Response ← HTTP ← SQL Query
```

### **Task Management Flow**
```typescript
1. Task Creation:
   TaskCreateModal → TaskContext.createTask() → API POST /tasks → Supabase Insert

2. Task Update:
   TaskCard interaction → TaskContext.updateTask() → API PUT /tasks/:id → Supabase Update

3. Task Sync:
   App startup → TaskContext.refreshTasks() → API GET /tasks → Supabase Query

4. Offline Handling:
   Action triggers → Local state update → Cache to AsyncStorage → Sync when online
```

### **Authentication Flow**
```typescript
1. Login Attempt:
   AuthScreen → supabase.auth.signInWithPassword() → JWT Token → AsyncStorage

2. Session Management:
   App startup → AuthContext.refreshAuth() → Validate token → Update user state

3. Navigation:
   Auth state change → Navigation logic in AuthContext → Router navigation
```

---

## API Integration

### **External Service Integrations**

#### **OpenAI GPT-4o Integration**
- **Purpose**: AI-powered scheduling and task assistance
- **Endpoint**: `/chat` routes in backend
- **Features**: Natural language task creation, schedule optimization, study tips

#### **Google Calendar API**
- **Purpose**: Calendar synchronization and availability checking
- **Authentication**: OAuth 2.0 flow
- **Features**: Event creation, availability queries, calendar sync

#### **Microsoft Graph API**
- **Purpose**: Outlook calendar integration
- **Authentication**: Microsoft OAuth
- **Features**: Similar to Google Calendar functionality

#### **Stripe API**
- **Purpose**: Payment processing for premium features
- **Features**: Subscription management, webhook handling, payment sessions
- **Security**: Webhook signature verification, secure token handling

#### **Canvas LMS Integration**
- **Purpose**: Academic assignment import
- **Method**: Browser extension data scraping
- **Data Flow**: Extension → PulsePlan API → Task creation

---

## Development Workflow

### **Development Scripts**
```bash
# Frontend Development
npm run start          # Start Expo development server
npm run android        # Run on Android emulator/device
npm run ios           # Run on iOS simulator/device  
npm run web           # Run in web browser

# Backend Development
npm run dev:server    # Start backend server with auto-reload
npm run dev          # Start both frontend and backend concurrently

# Utility Scripts
npm run install:all   # Install dependencies for all components
npm run test:connection # Test API connectivity
npm run verify-supabase # Validate Supabase configuration
```

### **Environment Configuration**
```typescript
Required Environment Variables:
- EXPO_PUBLIC_SUPABASE_URL      # Supabase project URL
- EXPO_PUBLIC_SUPABASE_ANON_KEY # Supabase anonymous key
- OPENAI_API_KEY                # OpenAI API access
- GOOGLE_CLIENT_ID              # Google OAuth credentials
- GOOGLE_CLIENT_SECRET          # Google OAuth secret
- STRIPE_SECRET_KEY             # Stripe payment processing
- STRIPE_WEBHOOK_SECRET         # Stripe webhook verification
```

### **Build Process**
1. **Development**: Expo CLI with hot reloading
2. **Production**: EAS Build for app store deployment
3. **Web**: Expo web build for browser deployment
4. **Extension**: Chrome extension packaging

---

## Deployment Architecture

### **Frontend Deployment**
- **Mobile Apps**: EAS Build → App Stores (iOS App Store, Google Play)
- **Web App**: Expo web build → Static hosting (Vercel, Netlify)
- **Browser Extension**: Chrome Web Store publication

### **Backend Deployment**
- **API Server**: Node.js deployment (Heroku, Railway, VPS)
- **Database**: Supabase hosted PostgreSQL
- **File Storage**: Supabase storage for user assets

### **Environment Separation**
- **Development**: Local servers, test databases
- **Staging**: Deployed servers, staging databases
- **Production**: Production servers, live databases with backups

### **Monitoring & Observability**
- **Health Checks**: `/health` endpoint for service monitoring
- **Error Logging**: Console logging with structured data
- **Performance**: Expo performance monitoring
- **Analytics**: User engagement tracking (can be added)

---

## Security Considerations

### **Authentication Security**
- **JWT Tokens**: Secure token storage in AsyncStorage
- **Token Refresh**: Automatic token refresh to prevent expiration
- **Session Management**: Proper session cleanup on logout
- **OAuth Flow**: Secure third-party authentication

### **API Security**
- **CORS Configuration**: Restricted origins in production
- **Input Validation**: Server-side validation of all inputs
- **Rate Limiting**: Can be implemented for API protection
- **Webhook Security**: Stripe webhook signature verification

### **Data Protection**
- **Local Storage**: Encrypted sensitive data in AsyncStorage
- **Network Communication**: HTTPS for all API communications
- **Database Security**: Supabase Row Level Security (RLS) policies
- **Environment Variables**: Secure credential management

---

## Performance Optimizations

### **Frontend Performance**
- **Lazy Loading**: Components loaded as needed
- **Image Optimization**: Proper image sizing and caching
- **List Virtualization**: For large task lists
- **State Optimization**: Minimal re-renders through proper state design

### **Backend Performance**
- **Connection Pooling**: Database connection optimization
- **Caching**: Response caching for frequently accessed data
- **Async Operations**: Non-blocking API operations
- **Error Recovery**: Graceful error handling and retry logic

### **Offline Performance**
- **Local Caching**: AsyncStorage for offline task access
- **Background Sync**: Automatic sync when connectivity restored
- **Optimistic Updates**: Immediate UI feedback for user actions
- **Network Monitoring**: Real-time connectivity status

---

## Conclusion

PulsePlan is a sophisticated, full-stack academic planning application with a well-architected separation of concerns. The combination of React Native for cross-platform mobile development, Node.js for the backend API, Supabase for managed database and authentication, and strategic integrations with academic and productivity services creates a comprehensive solution for student task management and scheduling.

The application demonstrates modern mobile development best practices including:
- Context-based state management
- Offline-first design
- Cross-platform compatibility  
- Secure authentication flows
- AI integration for enhanced user experience
- Extensible architecture for future feature additions

This specification provides the foundation for any new developer to understand, modify, and extend the PulsePlan application effectively. 