// Design tokens mirrored from React Native theme

// Colors - matching RN theme
export const colors = {
  backgroundDark: '#0A0A1F',
  primaryBlue: '#4F8CFF',
  accentPurple: '#8E6FFF',
  textPrimary: '#FFFFFF',
  textSecondary: '#C6C6D9',
  premiumThemeName: 'rgba(255, 255, 255, 0.5)',
  taskColors: {
    high: '#FF5757',
    medium: '#FFC043',
    low: '#4CD964',
    default: '#3B82F6', // Blue-500 for minimal calendar design
  },
  success: '#4CD964',
  warning: '#FFC043',
  error: '#FF5757',
  // Light mode colors
  backgroundLight: '#FFFFFF',
  textPrimaryLight: '#1A1A1A',
  textSecondaryLight: '#6B7280',
  // Neutral colors for web
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
  },
} as const;

// Spacing values
export const spacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '0.75rem',   // 12px
  lg: '1rem',      // 16px
  xl: '1.5rem',    // 24px
  '2xl': '2rem',   // 32px
  '3xl': '3rem',   // 48px
  '4xl': '4rem',   // 64px
} as const;

// Border radius values
export const borderRadius = {
  none: '0',
  sm: '0.125rem',  // 2px
  md: '0.25rem',   // 4px
  lg: '0.5rem',    // 8px
  xl: '0.75rem',   // 12px
  '2xl': '1rem',   // 16px
  full: '9999px',
} as const;

// Shadow definitions
export const shadows = {
  small: '0 2px 4px rgba(0, 0, 0, 0.1)',
  medium: '0 4px 8px rgba(0, 0, 0, 0.15)',
  large: '0 6px 12px rgba(0, 0, 0, 0.2)',
} as const;

// Calendar specific constants
export const CALENDAR_CONSTANTS = {
  HOURS_IN_DAY: 24,
  MINUTES_IN_HOUR: 60,
  DEFAULT_SLOT_DURATION: 30, // minutes
  GRID_HOUR_HEIGHT: 120, // pixels per hour (taller blocks to match reference)
  GRID_MARGIN_LEFT: 60, // pixels for hour labels
  GRID_DAY_WIDTH: 160, // pixels per day column
  HEADER_HEIGHT: 56, // pixels for calendar header (h-14)
  ALL_DAY_ROW_HEIGHT: 48, // pixels for all-day events row (h-12)
  MIN_EVENT_HEIGHT: 20, // minimum height for an event
  EVENT_BORDER_RADIUS: 4,
  EVENT_PADDING: 8,
  OVERLAP_OFFSET: 2, // pixels to offset overlapping events
  SNAP_THRESHOLD: 15, // minutes to snap to
  WORKING_HOURS: {
    start: 9, // 9 AM
    end: 17,  // 5 PM
  },
  DAYS_OF_WEEK: [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'
  ],
  DAYS_OF_WEEK_SHORT: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
} as const;

// API endpoints
export const API_ENDPOINTS = {
  // Auth
  AUTH_LOGIN: '/api/v1/auth/login',
  AUTH_LOGOUT: '/api/v1/auth/logout',
  AUTH_REFRESH: '/api/v1/auth/refresh',
  
  // Tasks
  TASKS_LIST: '/api/v1/tasks',
  TASKS_CREATE: '/api/v1/tasks',
  TASKS_UPDATE: (id: string) => `/api/v1/tasks/${id}`,
  TASKS_DELETE: (id: string) => `/api/v1/tasks/${id}`,
  
  // Calendar
  CALENDAR_EVENTS: '/api/v1/calendar/events',
  CALENDAR_CREATE_EVENT: '/api/v1/calendar/events',
  CALENDAR_UPDATE_EVENT: (id: string) => `/api/v1/calendar/events/${id}`,
  CALENDAR_DELETE_EVENT: (id: string) => `/api/v1/calendar/events/${id}`,
  CALENDAR_SYNC: '/api/v1/calendar/sync',
  
  // Scheduling
  SCHEDULING_GENERATE: '/api/v1/scheduling/generate',
  
  // AI Assistant - Unified System
  AI_PROCESS: '/api/v1/agents/process',
  AI_HEALTH: '/api/v1/agents/health',
  
  // User
  USER_PROFILE: '/api/v1/user/profile',
  USER_PREFERENCES: '/api/v1/user/preferences',
  
  // Referrals
  REFERRALS_SEND: '/api/v1/referrals/send',
  
  // Analytics
  ANALYTICS_DASHBOARD: '/api/v1/analytics/dashboard',
  ANALYTICS_STREAKS: '/api/v1/analytics/streaks',
} as const;

// Environment variables with fallbacks
export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  API_URL: import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL || '',
  SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
  APP_NAME: import.meta.env.VITE_APP_NAME || 'PulsePlan',
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
} as const;

// Validation constants
export const VALIDATION = {
  MIN_PASSWORD_LENGTH: 8,
  MAX_TASK_TITLE_LENGTH: 200,
  MAX_TASK_DESCRIPTION_LENGTH: 1000,
  MAX_EVENT_TITLE_LENGTH: 200,
  MAX_EVENT_DESCRIPTION_LENGTH: 2000,
} as const;

// Animation constants
export const ANIMATIONS = {
  DURATION_FAST: 150,
  DURATION_NORMAL: 300,
  DURATION_SLOW: 500,
  EASING_EASE_OUT: 'cubic-bezier(0.0, 0, 0.2, 1)',
  EASING_EASE_IN_OUT: 'cubic-bezier(0.4, 0, 0.2, 1)',
} as const;