export const colors = {
  background: '#0A0A1F',
  primary: '#4F8CFF',
  accent: '#8E6FFF',
  surface: '#1A1A2E',
  card: '#262638',
  textPrimary: '#FFFFFF',
  textSecondary: '#C6C6D9',
  success: '#4CD964',
  warning: '#FFC043',
  error: '#FF5757',
  taskColors: {
    high: '#FF5757',
    medium: '#FFC043',
    low: '#4CD964',
    default: '#8E6FFF',
  },
};

export const API_ENDPOINTS = {
  TASKS: '/api/v1/tasks',
  USERS: '/api/v1/users',
  AUTH: '/api/v1/auth',
  AGENT: {
    PROCESS: '/api/v1/agents/process',
    HEALTH: '/api/v1/agents/health',
  },
  CALENDAR: '/api/v1/calendar/events',
  PREFERENCES: '/api/v1/user/preferences',
} as const;

export const DAYS_OF_WEEK = [
  'Sunday',
  'Monday', 
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday'
] as const;

export const DAYS_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as const;

export const PRIORITY_COLORS = {
  low: colors.success,
  medium: colors.warning,
  high: colors.error,
} as const;

export const STATUS_COLORS = {
  pending: colors.textSecondary,
  in_progress: colors.primary,
  completed: colors.success,
} as const;

export const LOCAL_STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER_PREFERENCES: 'user_preferences',
  CACHED_TASKS: 'cached_tasks',
  LAST_SYNC: 'last_sync_timestamp',
} as const;