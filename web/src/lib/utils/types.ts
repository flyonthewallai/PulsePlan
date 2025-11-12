// Shared domain types - mirrored from React Native app

export interface AgentResponse {
  success: boolean;
  conversation_id: string;
  task_id?: string;
  immediate_response?: string;
  intent: string;
  action: string;
  confidence: number;
  requires_followup: boolean;
  metadata: Record<string, any>;
  timestamp?: string;
  // Legacy fields for backward compatibility
  message?: string;
  data?: any;
  error?: string;
  conversationId?: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  due_date: string; // Backend uses snake_case
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'scheduled' | 'rescheduled';
  task_type?: 'task' | 'assignment' | 'todo' | 'event' | 'exam' | 'quiz' | 'meeting' | 'appointment' | 'deadline' | 'class' | 'social' | 'personal' | 'work' | 'study' | 'reading' | 'project' | 'hobby' | 'admin';
  estimatedDuration?: number;
  estimated_minutes?: number; // Backend field
  scheduledHour?: number;
  tags?: string[];
  scheduling_rationale?: string;
  createdAt: string;
  updatedAt: string;
  // Course information
  course_id?: string;
  color?: string; // Course color
  courses?: {
    id: string;
    name: string;
    color: string;
    icon?: string;
    canvas_course_code?: string;
  };
}

export type CreateTaskData = Omit<Task, 'id' | 'createdAt' | 'updatedAt'>;

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// Calendar Event types
export interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  start: string | { dateTime: string; timeZone?: string };
  end: string | { dateTime: string; timeZone?: string };
  location?: string;
  attendees?: Array<{
    email: string;
    displayName?: string;
    responseStatus?: string;
  }>;
  organizer?: {
    name?: string;
    email: string;
  };
  htmlLink?: string;
  webLink?: string;
  status?: string;
  source: 'google' | 'microsoft';
  calendarId?: string;
  isAllDay?: boolean;
  colorId?: string;
  categories?: string[];
  importance?: string;
  sensitivity?: string;
  recurrence?: any;
}

export interface Calendar {
  id: string;
  summary: string;
  name?: string;
  description?: string;
  primary?: boolean;
  isDefault?: boolean;
  accessRole?: string;
  backgroundColor?: string;
  foregroundColor?: string;
  color?: string;
  canEdit?: boolean;
  canShare?: boolean;
  timeZone?: string;
  selected?: boolean;
}

export interface ConnectionStatus {
  connected: boolean;
  providers: Array<{
    provider: 'google' | 'microsoft';
    email: string;
    connectedAt: string;
    expiresAt?: string;
    isActive: boolean;
  }>;
}

export interface CreateEventRequest {
  summary: string;
  description?: string;
  start: string;
  end: string;
  location?: string;
  attendees?: string[] | Array<{ email: string; name?: string }>;
  calendarId?: string;
  isAllDay?: boolean;
  reminders?: any;
  colorId?: string;
  visibility?: string;
  importance?: string;
  categories?: string[];
  sensitivity?: string;
  showAs?: string;
  recurrence?: any;
}

// Scheduling types
export interface SchedulingTask {
  id: string;
  title: string;
  dueDate: string;
  estimatedMinutes: number;
  subject?: string;
  priority?: string;
}

export interface TimeSlot {
  start: string;
  end: string;
}

export interface UserPreferences {
  preferredWorkingHours?: { start: string; end: string };
  breakDuration?: number;
  focusSessionDuration?: number;
}

export interface ScheduleBlock {
  taskId: string;
  title: string;
  startTime: string;
  endTime: string;
}

export interface SchedulingResult {
  success: boolean;
  schedule: ScheduleBlock[];
  explanation: string;
  tokenUsage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

// User and Auth types
export interface User {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

// Analytics types
export interface DashboardStats {
  tasksCompleted: number;
  tasksOverdue: number;
  tasksUpcoming: number;
  currentStreak: number;
  weeklyGoalProgress: number;
  focusSessionsToday: number;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Form and validation types
export interface FormError {
  field: string;
  message: string;
}

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
}