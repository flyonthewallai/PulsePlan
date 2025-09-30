# PulsePlan Web App

A React + TypeScript web application that ports the existing React Native iOS app to the web with near-feature parity. Built with Vite, Tailwind CSS, and modern web technologies.

## 🚀 Features

- **Authentication**: Email/password, Google, Apple, and Magic Link sign-in via Supabase
- **Dashboard**: Task overview, completion statistics, and quick actions
- **Calendar View**: Weekly calendar with drag-and-drop task scheduling (coming soon)
- **Task Management**: Full CRUD operations for tasks with priority and status tracking
- **Streaks & Analytics**: Progress tracking and productivity metrics (coming soon)
- **AI Agent**: Conversational task management and scheduling assistant (coming soon)
- **Settings**: User preferences, integrations, and app configuration (coming soon)

## 🛠️ Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS + Radix UI components
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Authentication**: Supabase Auth
- **API Client**: Custom fetch-based client with TypeScript
- **Drag & Drop**: @dnd-kit (for calendar scheduling)
- **Forms**: React Hook Form + Zod validation

## 📋 Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Access to the existing PulsePlan backend API
- Supabase project with configured auth providers

## ⚡ Quick Start

### 1. Install Dependencies

```bash
cd web
npm install
```

### 2. Environment Setup

Copy the environment template and fill in your values:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
# Supabase Configuration (required)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here

# Backend API Configuration
VITE_API_BASE_URL=http://localhost:5000

# App Configuration  
VITE_APP_NAME=PulsePlan
VITE_APP_VERSION=1.0.0
```

### 3. Configure Supabase Auth

In your Supabase dashboard:

1. **Authentication > URL Configuration**:
   - Add `http://localhost:5173` to redirect URLs
   - Add `https://app.pulseplan.app` for production

2. **Authentication > Providers**:
   - Enable Google OAuth (add your Google client credentials)
   - Enable Apple OAuth (add your Apple client credentials)
   - Configure email settings for Magic Links

### 4. Backend Setup

Ensure your FastAPI backend is running and accessible:

```bash
# Backend must be running on http://localhost:5000 (default)
# Or update VITE_API_BASE_URL to match your backend URL
```

### 5. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## 📁 Project Structure

```
web/src/
├── app/                    # App configuration and providers
│   ├── providers.tsx       # React Query, Router, Supabase providers
│   └── routes.tsx          # Route definitions and protected routes
├── components/             # Reusable UI components
│   ├── layout/            # Layout components (AppShell, etc.)
│   └── ui/                # Base UI components (buttons, inputs, etc.)
├── features/              # Feature-specific components
│   ├── auth/              # Authentication components
│   ├── calendar/          # Calendar components (coming soon)
│   ├── tasks/             # Task management components
│   ├── streaks/           # Streaks and analytics components
│   ├── ai/                # AI agent components
│   └── settings/          # Settings components
├── lib/                   # Core utilities and configuration
│   ├── api/               # API client and SDK
│   ├── config.ts          # Environment configuration
│   ├── constants.ts       # App constants and theme
│   ├── supabase.ts        # Supabase client and auth functions
│   └── utils.ts           # Common utilities
├── pages/                 # Page components
├── types/                 # TypeScript type definitions
└── hooks/                 # Custom React hooks
```

## 🔧 Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

## 🎨 Design System

The app uses a dark theme consistent with the React Native version:

### Colors
- **Background**: `#0A0A1F` (Dark blue-black)
- **Primary**: `#4F8CFF` (Blue)
- **Accent**: `#8E6FFF` (Purple)
- **Surface**: `#1A1A2E` / `#262638` (Dark surfaces)
- **Text**: `#FFFFFF` (Primary) / `#C6C6D9` (Secondary)

### Typography
- **Font**: Inter (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700

## 🔐 Authentication Flow

1. **OAuth Providers**: Google and Apple sign-in redirect to `/auth/callback`
2. **Magic Links**: Email-based passwordless authentication
3. **Session Management**: Automatic token refresh via Supabase
4. **Protected Routes**: `AuthGate` component guards authenticated pages

## 📡 API Integration

### Backend Compatibility
- Maintains identical API contracts with the React Native app
- Uses the same FastAPI endpoints and data structures
- Supports the same Supabase auth integration

### API Client Architecture
```typescript
// Centralized API client with auto-retry and error handling
const result = await tasksAPI.getTasks()
if (result.error) {
  // Handle error
} else {
  // Use result.data
}
```

## 🎯 Feature Parity Checklist

### ✅ Completed
- [x] Supabase email + Google/Apple login works; session persisted; protected routes
- [x] Basic dashboard with task statistics and overview
- [x] API SDK with identical endpoints as React Native app
- [x] Responsive layout with mobile navigation
- [x] Theme and design tokens matching React Native version

### 🚧 In Progress / Coming Soon
- [ ] Weekly calendar renders tasks/events from the same endpoints as RN
- [ ] Drag-to-reschedule updates backend; optimistic update + rollback on error
- [ ] Create/edit task modal with validation mirrors RN fields
- [ ] Streaks page matches RN metrics
- [ ] AI agent side panel can send/receive messages to same endpoint
- [ ] Settings reads/writes user preferences and integrations

## 🚀 Deployment

### Environment Variables for Production
```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_BASE_URL=https://api.pulseplan.app
```

### CORS Configuration
Ensure your backend allows these origins:
- `http://localhost:5173` (development)
- `https://app.pulseplan.app` (production)

### Build and Deploy
```bash
# Build for production
npm run build

# The dist/ folder can be deployed to any static hosting service
# (Vercel, Netlify, AWS S3, etc.)
```

### Vercel Deployment
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

## 🔍 Development Notes

### Code Style
- Uses existing RN patterns and naming conventions
- TypeScript strict mode enabled
- ESLint + Prettier for consistent formatting

### State Management
- React Query for server state
- Local state with React hooks
- No global state management library (keeps it simple)

### Performance
- Lazy loading for route components
- Optimistic updates for better UX
- Image optimization and caching

### Testing (Future)
- Vitest for unit tests
- Playwright for E2E testing
- Mock API responses for development

## 🤝 Contributing

1. Follow existing code patterns and conventions
2. Keep components small and focused
3. Use TypeScript strict types
4. Test on both desktop and mobile viewports
5. Maintain feature parity with React Native app

## 📚 Additional Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Radix UI Documentation](https://www.radix-ui.com/)

## 🆘 Troubleshooting

### Common Issues

**Build fails with TypeScript errors**:
```bash
npm run type-check  # Check for type errors
```

**Supabase auth not working**:
- Verify environment variables are set correctly
- Check redirect URLs in Supabase dashboard
- Ensure OAuth providers are configured

**API calls failing**:
- Check backend is running and accessible
- Verify CORS is configured for your domain
- Check network requests in browser dev tools

**Styles not loading**:
- Ensure Tailwind is properly configured
- Check CSS import order in main.tsx
- Verify PostCSS configuration

### Support
For issues related to the web app, check the existing React Native implementation for reference patterns and API usage.