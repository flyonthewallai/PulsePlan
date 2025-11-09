import { getApiUrl } from '../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabaseAuth } from '@/lib/supabase-rn';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatResponse {
  content: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

class ChatAPIService {
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

  async sendMessage(messages: ChatMessage[]): Promise<ChatResponse> {
    try {
      const token = await this.getAuthToken();
      
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      const response = await fetch(getApiUrl('/chat/message'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ messages }),
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
      console.error('Chat API error:', error);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to send message. Please check your connection and try again.');
    }
  }
}

export const chatAPIService = new ChatAPIService(); 