import { getApiUrl } from '../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabaseAuth } from '@/lib/supabase-rn';
import { userService } from './userService';

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
  conversation_id?: string;
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
  private conversationId: string | null = null;

  private async getStoredConversationId(): Promise<string | null> {
    try {
      const stored = await AsyncStorage.getItem('@conversation_id');
      return stored;
    } catch (error) {
      console.error('Failed to get stored conversation ID:', error);
      return null;
    }
  }

  private async storeConversationId(conversationId: string): Promise<void> {
    try {
      await AsyncStorage.setItem('@conversation_id', conversationId);
      this.conversationId = conversationId;
    } catch (error) {
      console.error('Failed to store conversation ID:', error);
    }
  }

  private async getLocationData(): Promise<{ city?: string; timezone?: string }> {
    try {
      // Get userId from auth session
      const { data: { session } } = await supabaseAuth.auth.getSession();
      const userId = session?.user?.id;
      
      if (userId) {
        try {
          // Try to get location data from server first
          const serverProfile = await userService.getUserProfile(userId);
          if (serverProfile) {
            return {
              city: serverProfile.city,
              timezone: serverProfile.timezone
            };
          }
        } catch (error) {
          console.error('Error getting server location data:', error);
        }
      }
      
      // Fallback to local data from AsyncStorage
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

      // Get conversation_id - prioritize payload, then stored, then memory, then null
      let conversationId = payload.conversation_id || this.conversationId;
      if (!conversationId) {
        conversationId = await this.getStoredConversationId();
        this.conversationId = conversationId;
      }

      // Enrich context with location data
      const enrichedPayload = {
        ...payload,
        conversation_id: conversationId,
        context: await this.enrichContextWithLocation(payload.context)
      };

      console.log(`🗨️ [AGENT-SERVICE] Using conversation_id: ${conversationId} (payload: ${payload.conversation_id}, stored: ${await this.getStoredConversationId()})`);

      const requestBody = {
        query: enrichedPayload.query,
        conversation_id: conversationId,
        context: enrichedPayload.context,
        duration: enrichedPayload.duration
      };

      console.log(`🗨️ [AGENT-SERVICE] Request body:`, requestBody);

      const response = await fetch(getApiUrl('/agents/process'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication expired. Please log in again.');
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log(`🗨️ [AGENT-SERVICE] Response data:`, data);

      // Store conversation_id if received in response
      if (data.conversation_id && data.conversation_id !== conversationId) {
        console.log(`🗨️ [AGENT-SERVICE] Storing new conversation_id: ${data.conversation_id}`);
        await this.storeConversationId(data.conversation_id);
      }

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

      const response = await fetch(getApiUrl('/agents/process'), {
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

      const response = await fetch(getApiUrl('/agents/health'), {
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