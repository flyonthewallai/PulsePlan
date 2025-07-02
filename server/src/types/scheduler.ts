export interface User {
  id: string;
  email: string;
  name?: string;
  is_premium: boolean;
  email_preferences: {
    daily_briefing?: 'on' | 'off';
    weekly_pulse?: 'on' | 'off';
  };
  timezone?: string;
}

export interface AgentResponse {
  success: boolean;
  data?: any;
  error?: string;
  message?: string;
}

export interface EmailData {
  to: string;
  subject: string;
  html: string;
  from?: string;
}

export interface JobResult {
  success: boolean;
  userId: string;
  email: string;
  error?: string;
  timestamp: Date;
}

export interface RateLimiter {
  wait(): Promise<void>;
}

export interface Logger {
  info(message: string, data?: any): void;
  error(message: string, error?: any): void;
  warn(message: string, data?: any): void;
}

export interface EmailService {
  sendEmail(data: EmailData): Promise<{ success: boolean; error?: string }>;
}

export interface BriefingData {
  weather?: string;
  todaysTasks?: any[];
  upcomingEvents?: any[];
  summary?: string;
  recommendations?: string[];
}

export interface WeeklyPulseData {
  completedTasks?: number;
  totalTasks?: number;
  productivityScore?: number;
  weeklyGoals?: any[];
  achievements?: string[];
  nextWeekRecommendations?: string[];
  weeklyStats?: any;
} 