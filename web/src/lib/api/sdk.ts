import { apiClient } from './client';
import { API_ENDPOINTS } from '../utils/constants';
import type {
  Task,
  CreateTaskData,
  CalendarEvent,
  CreateEventRequest,
  SchedulingTask,
  TimeSlot,
  UserPreferences,
  SchedulingResult,
  User,
  DashboardStats,
  Streak,
  AgentResponse,
  ApiResponse,
  PaginatedResponse,
} from '../utils/types';
import type { CalendarEvent as LocalCalendarEvent } from '../../types';

// Modern, clean API functions with proper typing
export const tasksApi = {
  list: async (params?: {
    startDate?: string;
    endDate?: string;
    status?: Task['status'];
    priority?: Task['priority'];
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.startDate) searchParams.append('startDate', params.startDate);
    if (params?.endDate) searchParams.append('endDate', params.endDate);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.priority) searchParams.append('priority', params.priority);

    const query = searchParams.toString();
    const endpoint = query ? `${API_ENDPOINTS.TASKS_LIST}?${query}` : API_ENDPOINTS.TASKS_LIST;

    const response = await apiClient.get<{tasks: Task[], count: number}>(endpoint);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data?.tasks || [];
  },

  create: async (task: CreateTaskData) => {
    const response = await apiClient.post<Task>(API_ENDPOINTS.TASKS_CREATE, task);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  update: async (id: string, updates: Partial<Task>) => {
    const response = await apiClient.patch<Task>(API_ENDPOINTS.TASKS_UPDATE(id), updates);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  delete: async (id: string) => {
    const response = await apiClient.delete<void>(API_ENDPOINTS.TASKS_DELETE(id));
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data;
  },
};

export const calendarApi = {
  getEvents: async (params: {
    startDate: string;
    endDate: string;
    providers?: ('google' | 'microsoft')[];
  }) => {
    const searchParams = new URLSearchParams({
      startDate: params.startDate,
      endDate: params.endDate,
    });
    
    params.providers?.forEach(provider => {
      searchParams.append('providers', provider);
    });
    
    const response = await apiClient.get<CalendarEvent[]>(`${API_ENDPOINTS.CALENDAR_EVENTS}?${searchParams}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || [];
  },

  createEvent: async (event: CreateEventRequest) => {
    const response = await apiClient.post<CalendarEvent>(API_ENDPOINTS.CALENDAR_CREATE_EVENT, event);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  updateEvent: async (id: string, updates: Partial<CreateEventRequest>) => {
    const response = await apiClient.patch<CalendarEvent>(API_ENDPOINTS.CALENDAR_UPDATE_EVENT(id), updates);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  deleteEvent: async (id: string) => {
    const response = await apiClient.delete<void>(API_ENDPOINTS.CALENDAR_DELETE_EVENT(id));
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data;
  },

  sync: async () => {
    const response = await apiClient.post(API_ENDPOINTS.CALENDAR_SYNC);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data;
  },
};

export const schedulingApi = {
  generateSchedule: async (data: {
    tasks: SchedulingTask[];
    timeSlots: TimeSlot[];
    userPreferences?: UserPreferences;
  }) => {
    const response = await apiClient.post<SchedulingResult>(API_ENDPOINTS.SCHEDULING_GENERATE, data);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },
};

export const aiApi = {
  // Unified agent system - single endpoint for all agent interactions
  process: async (payload: {
    query: string;
    conversation_id?: string;
    include_history?: boolean;
    context?: any;
  }) => {
    const response = await apiClient.post<AgentResponse>(API_ENDPOINTS.AI_PROCESS, payload);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  // Legacy compatibility methods
  chat: async (message: string, conversationId?: string) => {
    return aiApi.process({
      query: message,
      conversation_id: conversationId,
      include_history: true
    });
  },

  sendQuery: async (payload: { query: string; context?: any }) => {
    return aiApi.process({
      query: payload.query,
      context: payload.context,
      include_history: true
    });
  },

  getStatus: async () => {
    const response = await apiClient.get(API_ENDPOINTS.AI_HEALTH);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data;
  },
};

export const userApi = {
  getProfile: async () => {
    const response = await apiClient.get<User>(API_ENDPOINTS.USER_PROFILE);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  updateProfile: async (updates: Partial<User>) => {
    const response = await apiClient.patch<User>(API_ENDPOINTS.USER_PROFILE, updates);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  getPreferences: async () => {
    const response = await apiClient.get<UserPreferences>(API_ENDPOINTS.USER_PREFERENCES);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  updatePreferences: async (preferences: Partial<UserPreferences>) => {
    const response = await apiClient.patch<UserPreferences>(API_ENDPOINTS.USER_PREFERENCES, preferences);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },
};

export interface Hobby {
  id: string;
  name: string;
  icon: 'Music' | 'Camera' | 'Book' | 'Gamepad2' | 'Palette' | 'Target' | 'MountainSnow' | 'Heart' | 'Bike' | 'Dumbbell' | 'Mountain';
  preferred_time: 'morning' | 'afternoon' | 'evening' | 'night' | 'any';
  specific_time: { start: string; end: string } | null;
  days: string[];
  duration_min: number;
  duration_max: number;
  flexibility: 'low' | 'medium' | 'high';
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateHobbyRequest {
  name: string;
  icon: string;
  preferred_time: string;
  specific_time: { start: string; end: string } | null;
  days: string[];
  duration_min: number;
  duration_max: number;
  flexibility: string;
  notes: string;
}

export const hobbiesApi = {
  parseHobby: async (description: string) => {
    const response = await apiClient.post<{
      success: boolean;
      hobby: {
        name: string;
        preferred_time: 'morning' | 'afternoon' | 'evening' | 'night' | 'any';
        specific_time: { start: string; end: string } | null;
        days: string[];
        duration: { min: number; max: number };
        flexibility: 'low' | 'medium' | 'high';
        notes: string;
        icon: 'Music' | 'Camera' | 'Book' | 'Gamepad2' | 'Palette' | 'Target' | 'MountainSnow' | 'Heart' | 'Bike' | 'Dumbbell' | 'Mountain';
      } | null;
      error?: string;
      confidence: number;
    }>('/api/v1/user-management/hobbies/parse', { description });

    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  list: async (includeInactive = false) => {
    const params = includeInactive ? '?include_inactive=true' : '';
    const response = await apiClient.get<Hobby[]>(`/api/v1/user-management/hobbies${params}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  get: async (id: string) => {
    const response = await apiClient.get<Hobby>(`/api/v1/user-management/hobbies/${id}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  create: async (hobby: CreateHobbyRequest) => {
    const response = await apiClient.post<Hobby>('/api/v1/user-management/hobbies', hobby);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  update: async (id: string, updates: Partial<CreateHobbyRequest>) => {
    const response = await apiClient.patch<Hobby>(`/api/v1/user-management/hobbies/${id}`, updates);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  delete: async (id: string, permanent = false) => {
    const params = permanent ? '?permanent=true' : '';
    const response = await apiClient.delete<void>(`/api/v1/user-management/hobbies/${id}${params}`);
    if (response.error) {
      throw new Error(response.error);
    }
  },
};

export const analyticsApi = {
  getDashboardStats: async () => {
    const response = await apiClient.get<DashboardStats>(API_ENDPOINTS.ANALYTICS_DASHBOARD);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },

  getStreaks: async () => {
    const response = await apiClient.get<Streak[]>(API_ENDPOINTS.ANALYTICS_STREAKS);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || [];
  },
};

export const referralApi = {
  sendInvite: async (friendEmail: string) => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      API_ENDPOINTS.REFERRALS_SEND,
      { friend_email: friendEmail }
    );
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  },
};

export const healthApi = {
  check: async (): Promise<boolean> => {
    return apiClient.testConnection();
  },
};

// Export all APIs as a single clean object
export const api = {
  tasks: tasksApi,
  calendar: calendarApi,
  scheduling: schedulingApi,
  ai: aiApi,
  user: userApi,
  analytics: analyticsApi,
  referral: referralApi,
  health: healthApi,
};

export default api;

// Legacy exports for backward compatibility
export const tasksAPI = {
  getTasks: tasksApi.list,
  createTask: tasksApi.create,
  updateTask: tasksApi.update,
  deleteTask: tasksApi.delete,
};

export const agentAPI = {
  chat: aiApi.chat,
  sendQuery: aiApi.sendQuery,
  getStatus: aiApi.getStatus,
};

export const userAPI = {
  getProfile: userApi.getProfile,
  updateProfile: userApi.updateProfile,
  getPreferences: userApi.getPreferences,
  updatePreferences: userApi.updatePreferences,
};

export { commandsAPI } from './commands';