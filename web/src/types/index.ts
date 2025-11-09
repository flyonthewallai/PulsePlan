export interface Task {
  id: string;
  title: string;
  description?: string;
  due_date: string; // Backend uses snake_case
  priority: 'high' | 'medium' | 'low';
  status: 'todo' | 'in_progress' | 'completed' | 'pending' | 'done' | 'finished';
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

export interface User {
  id: string;
  email: string;
  full_name?: string;
  created_at: string;
}

export interface AgentMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

export interface AgentResponse {
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
  conversationId?: string;
  timestamp?: string;
}

export interface StreakData {
  currentStreak: number;
  longestStreak: number;
  totalTasks: number;
  completionRate: number;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  workingHours: {
    startHour: number;
    endHour: number;
  };
  notifications: {
    taskReminders: boolean;
    dailySummary: boolean;
    weeklyReview: boolean;
  };
}

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start: string;
  end: string;
  allDay?: boolean;
  calendar_type?: 'google' | 'apple' | 'outlook';
  task?: Task;
  color?: string;
  priority?: 'high' | 'medium' | 'low';
  timeblock?: Timeblock; // Full timeblock metadata for details modal
}

export interface Subject {
  id: string;
  name: string;
  color: string;
  icon?: string;
}

// Timeblocks types (unified calendar feed)
export type TimeblockSource = "task" | "calendar" | "busy";
export type TimeblockProvider = "google" | "outlook" | "apple" | "pulse" | null;

export interface Timeblock {
  id: string;
  source: TimeblockSource;
  provider: TimeblockProvider;
  title: string;
  start: string; // ISO8601 UTC
  end: string;   // ISO8601 UTC
  isAllDay: boolean;
  readonly: boolean;
  linkId?: string | null;
  description?: string | null;
  location?: string | null;
  color?: string | null;

  // Rich metadata for calendar events
  htmlLink?: string | null; // Direct link to Google Calendar/Outlook
  attendees?: Array<{ email?: string; name?: string; responseStatus?: string }> | null;
  organizer?: { email?: string; name?: string } | null;
  creator?: { email?: string; name?: string } | null;
  status?: string | null; // Event status (confirmed, tentative, cancelled)
  transparency?: string | null; // opaque or transparent (busy/free)
  visibility?: string | null; // default, public, private
  categories?: string[] | null; // Event categories/labels
  importance?: string | null; // Outlook importance
  sensitivity?: string | null; // Outlook sensitivity
  recurrence?: any | null; // Recurrence rules
  hasAttachments?: boolean;

  // Task-specific metadata
  priority?: 'high' | 'medium' | 'low' | null;
  taskStatus?: 'todo' | 'in_progress' | 'completed' | 'pending' | null;
  estimatedMinutes?: number | null;
  schedulingRationale?: string | null;
  tags?: string[] | null;
  courseId?: string | null;
  courseName?: string | null;
  courseColor?: string | null;
}

export interface TimeblocksResponse {
  items: Timeblock[];
}