import { getApiUrl } from '../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabaseAuth } from '@/lib/supabase-rn';

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

class SchedulingAPIService {
  private async getAuthToken(): Promise<string | null> {
    try {
      // Use the Supabase client to get the current session
      const { data: { session }, error } = await supabaseAuth.auth.getSession();
      
      if (error) {
        console.error('Error getting session:', error.message);
        return null;
      }

      if (!session) {
        console.error('No session found');
        return null;
      }

      if (!session.access_token) {
        console.error('No access token in session');
        return null;
      }

      // Check if session is expired
      if (session.expires_at) {
        const expiryDate = new Date(session.expires_at * 1000);
        const now = new Date();
        if (expiryDate < now) {
          console.error('Session has expired');
          return null;
        }
      }

      return session.access_token;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  }

  async generateSchedule(
    tasks: SchedulingTask[],
    timeSlots: TimeSlot[],
    userPreferences?: UserPreferences
  ): Promise<SchedulingResult> {
    try {
      const token = await this.getAuthToken();
      
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      const response = await fetch(getApiUrl('/scheduling/generate'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          tasks,
          timeSlots,
          userPreferences,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication expired. Please log in again.');
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Scheduling API error:', error);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to generate schedule. Please check your connection and try again.');
    }
  }

  // Helper function to convert tasks from TaskContext format to scheduling format
  convertTasksToSchedulingFormat(tasks: any[]): SchedulingTask[] {
    return tasks.map(task => ({
      id: task.id,
      title: task.title,
      dueDate: task.due_date,
      estimatedMinutes: task.estimated_minutes || 60,
      subject: task.subject,
      priority: task.priority,
    }));
  }

  // Helper function to generate default time slots for a day
  generateDefaultTimeSlots(date: Date, startHour: number = 9, endHour: number = 17): TimeSlot[] {
    const start = new Date(date);
    start.setHours(startHour, 0, 0, 0);
    
    const end = new Date(date);
    end.setHours(endHour, 0, 0, 0);
    
    return [{
      start: start.toISOString(),
      end: end.toISOString(),
    }];
  }

  // Helper function to get user preferences from settings
  getUserPreferences(workingHours?: { startHour: number; endHour: number }): UserPreferences {
    return {
      preferredWorkingHours: workingHours ? {
        start: `${workingHours.startHour.toString().padStart(2, '0')}:00`,
        end: `${workingHours.endHour.toString().padStart(2, '0')}:00`,
      } : undefined,
      breakDuration: 15,
      focusSessionDuration: 90,
    };
  }
}

export const schedulingAPIService = new SchedulingAPIService(); 