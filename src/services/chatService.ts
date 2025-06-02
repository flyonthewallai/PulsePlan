import { getApiUrl } from '../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

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
      // Get the session from the Supabase storage format
      const sessionData = await AsyncStorage.getItem('supabase.auth.token');
      
      if (!sessionData) {
        console.error('No session found in AsyncStorage');
        return null;
      }

      const session = JSON.parse(sessionData);
      
      if (!session || !session.access_token) {
        console.error('Invalid session or missing access token');
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