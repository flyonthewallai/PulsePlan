import { getApiUrl } from '../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabaseAuth } from '@/lib/supabase-rn';

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface AgentResponse {
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
  conversationId?: string;
  timestamp?: string;
}

export interface AgentQueryPayload {
  query: string;
  context?: {
    currentPage?: string;
    userPreferences?: any;
    recentTasks?: any[];
    chatHistory?: AgentMessage[];
    conversationId?: string;
    location?: {
      city?: string;
      timezone?: string;
    };
  };
  duration?: number;
}

class AgentAPIService {
  private async getLocationData(): Promise<{ city?: string; timezone?: string }> {
    try {
      const profileData = await AsyncStorage.getItem('profileData');
      if (profileData) {
        const parsed = JSON.parse(profileData);
        return {
          city: parsed.city,
          timezone: parsed.timezone
        };
      }
    } catch (error) {
      console.error('Error getting location data:', error);
    }
    return {};
  }

  private async enrichContextWithLocation(context: any = {}): Promise<any> {
    const locationData = await this.getLocationData();
    return {
      ...context,
      location: locationData
    };
  }

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

  /**
   * Send a natural language query to the n8n agent
   */
  async sendQuery(payload: AgentQueryPayload): Promise<AgentResponse> {
    try {
      const token = await this.getAuthToken();
      
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Enrich context with location data
      const enrichedPayload = {
        ...payload,
        context: await this.enrichContextWithLocation(payload.context)
      };

      const response = await fetch(getApiUrl('/agent/query'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(enrichedPayload),
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
      console.error('Agent API error:', error);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to send query to agent. Please check your connection and try again.');
    }
  }

  /**
   * Send a chat message to the n8n agent
   */
  async sendChatMessage(
    message: string, 
    conversationId?: string,
    context?: any
  ): Promise<AgentResponse> {
    try {
      const token = await this.getAuthToken();
      
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Enrich context with location data
      const enrichedContext = await this.enrichContextWithLocation(context);

      const response = await fetch(getApiUrl('/agent/chat'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          message,
          conversationId,
          context: enrichedContext
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
      console.error('Agent chat API error:', error);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to send chat message to agent. Please check your connection and try again.');
    }
  }

  /**
   * Check agent health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const token = await this.getAuthToken();
      
      if (!token) {
        return false;
      }

      const response = await fetch(getApiUrl('/agent/health'), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();
      return data.healthy || false;
    } catch (error) {
      console.error('Agent health check error:', error);
      return false;
    }
  }

  /**
   * Process quick action through agent
   */
  async processQuickAction(action: string, context?: any): Promise<AgentResponse> {
    const actionQueries: { [key: string]: string } = {
      'priority': 'What are my highest priority tasks that I should focus on right now?',
      'next': 'Based on my current tasks and schedule, what should I work on next?',
      'schedule': 'Create a quick schedule for my remaining tasks today.',
      'progress': 'How am I doing with my tasks today? Give me a quick progress update.',
      'todo': 'List my current to-do tasks',
      'calendar': 'Show me my calendar for today',
      'email': 'Check my recent emails',
      'notes': 'Show me my recent notes',
    };

    const query = actionQueries[action.toLowerCase()] || action;
    
    return this.sendQuery({
      query,
      context: {
        ...context,
        quickAction: action,
        currentPage: 'agent'
      }
    });
  }

  /**
   * Handle task creation through natural language
   */
  async createTaskFromText(text: string, context?: any): Promise<AgentResponse> {
    return this.sendQuery({
      query: text,
      context: {
        ...context,
        intent: 'task_creation',
        currentPage: 'tasks'
      }
    });
  }

  /**
   * Handle scheduling through natural language  
   */
  async scheduleFromText(text: string, context?: any): Promise<AgentResponse> {
    return this.sendQuery({
      query: text,
      context: {
        ...context,
        intent: 'scheduling',
        currentPage: 'schedule'
      }
    });
  }

  /**
   * Handle email through natural language
   */
  async emailFromText(text: string, context?: any): Promise<AgentResponse> {
    return this.sendQuery({
      query: text,
      context: {
        ...context,
        intent: 'email',
        currentPage: 'email'
      }
    });
  }
}

export const agentAPIService = new AgentAPIService(); 