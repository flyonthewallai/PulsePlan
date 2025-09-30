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
}

export interface Subject {
  id: string;
  name: string;
  color: string;
  icon?: string;
}