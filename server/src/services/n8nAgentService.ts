import n8nAgentConfig from '../config/n8nAgent';
import supabase from '../config/supabase';

export interface N8nAgentPayload {
  userId: string;
  userEmail?: string;
  userName?: string;
  isPremium?: boolean;
  source: 'agent' | 'user';
  tool?: string; // Optional for master agent
  [key: string]: any; // Allow arbitrary additional properties
}

export interface N8nNaturalLanguagePayload {
  userId: string;
  userEmail?: string;
  userName?: string;
  isPremium?: boolean;
  query: string;
  date: string; // ISO 8601 timestamp (current date/time)
  duration?: number; // Optional duration in minutes
  source: 'app' | 'agent' | 'user';
  context?: {
    currentPage?: string;
    userPreferences?: any;
    chatHistory?: any[];
    workingHours?: any;
    [key: string]: any; // Allow arbitrary additional context properties
  };
  // Add authentication tokens for connected services
  connectedAccounts?: {
    google?: {
      accessToken: string;
      refreshToken?: string;
      email: string;
      expiresAt?: string;
    };
    microsoft?: {
      accessToken: string;
      refreshToken?: string;
      email: string;
      expiresAt?: string;
    };
    canvas?: {
      canvasDomain: string;
      accessToken: string;
      refreshToken?: string;
      email: string;
      expiresAt?: string;
    };
    [key: string]: any; // Allow for future integrations
  };
}

export interface N8nAgentResponse {
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
  conversationId?: string;
  timestamp?: string;
}

export class N8nAgentService {
  private readonly baseUrl = n8nAgentConfig.baseUrl;
  private readonly webhookPath = n8nAgentConfig.webhookPath;
  private readonly timeout = n8nAgentConfig.timeout;

  /**
   * Get operation-specific timeout values
   */
  private getTimeout(operation: 'task' | 'natural_language' | 'batch' | 'health'): number {
    const baseTimeout = this.timeout;
    
    switch (operation) {
      case 'natural_language':
        return baseTimeout * 3; // 3x longer for complex AI workflows
      case 'batch':
        return baseTimeout * 2; // 2x longer for batch operations
      case 'task':
        return baseTimeout; // Standard timeout for simple tasks
      case 'health':
        return 5000; // Short timeout for health checks
      default:
        return baseTimeout;
    }
  }

  /**
   * Get user's connected account tokens from the database
   */
  private async getUserConnectedAccounts(userId: string): Promise<any> {
    if (!supabase) {
      console.warn('Supabase not configured, skipping connected accounts');
      return {};
    }

    try {
      const { data: connections, error } = await supabase
        .from('calendar_connections')
        .select('provider, access_token, refresh_token, email, expires_at')
        .eq('user_id', userId);

      if (error) {
        console.error('Error fetching connected accounts:', error);
        return {};
      }

      if (!connections || connections.length === 0) {
        console.log('No connected accounts found for user:', userId);
        return {};
      }

      const connectedAccounts: any = {};

      for (const connection of connections) {
        // Only include valid tokens that haven't expired
        const isExpired = connection.expires_at ? 
          new Date(connection.expires_at) <= new Date() : false;

        if (!isExpired && connection.access_token) {
          connectedAccounts[connection.provider] = {
            accessToken: connection.access_token,
            refreshToken: connection.refresh_token || undefined,
            email: connection.email,
            expiresAt: connection.expires_at,
          };
        } else if (isExpired) {
          console.log(`${connection.provider} token expired for user ${userId}`);
        }
      }

      console.log(`Found ${Object.keys(connectedAccounts).length} valid connected accounts for user ${userId}`);
      return connectedAccounts;
    } catch (error) {
      console.error('Error getting connected accounts:', error);
      return {};
    }
  }

  /**
   * Send a task to the n8n agent for processing
   */
  async postToAgent(payload: N8nAgentPayload): Promise<N8nAgentResponse> {
    const url = `${this.baseUrl}${this.webhookPath}`;
    
    try {
      console.log(`Sending request to n8n agent: ${url}`);
      console.log('Payload:', JSON.stringify(payload, null, 2));

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.getTimeout('task'));

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('n8n agent response:', data);

      return {
        success: true,
        data,
        message: 'Successfully processed by n8n agent',
      };
    } catch (error) {
      console.error('Error communicating with n8n agent:', error);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return {
            success: false,
            error: 'Request to n8n agent timed out',
          };
        }
        return {
          success: false,
          error: `Agent error: ${error.message}`,
        };
      }
      
      return {
        success: false,
        error: 'Unknown error occurred while communicating with n8n agent',
      };
    }
  }

  /**
   * Create a task through the n8n agent (smart scheduling and automation)
   */
  async createTaskWithAgent(
    userId: string,
    taskTitle: string,
    dueDate: string,
    duration: number,
    priority: 'high' | 'medium' | 'low',
    subject: string,
    tool?: string,
    userEmail?: string
  ): Promise<N8nAgentResponse> {
    const payload: N8nAgentPayload = {
      userId,
      userEmail,
      taskTitle,
      dueDate,
      duration,
      priority,
      subject,
      source: 'agent',
      tool,
    };

    return this.postToAgent(payload);
  }

  /**
   * Send user-initiated task to n8n agent
   */
  async createTaskFromUser(
    userId: string,
    taskTitle: string,
    dueDate: string,
    duration: number,
    priority: 'high' | 'medium' | 'low',
    subject: string,
    userEmail?: string
  ): Promise<N8nAgentResponse> {
    const payload: N8nAgentPayload = {
      userId,
      userEmail,
      taskTitle,
      dueDate,
      duration,
      priority,
      subject,
      source: 'user',
    };

    return this.postToAgent(payload);
  }

  /**
   * Process natural language query through the master agent with connected accounts
   */
  async processNaturalLanguage(payload: N8nNaturalLanguagePayload): Promise<N8nAgentResponse> {
    const url = `${this.baseUrl}${this.webhookPath}`;
    const timeoutMs = this.getTimeout('natural_language');
    
    try {
      // Enhance payload with user's connected accounts
      const connectedAccounts = await this.getUserConnectedAccounts(payload.userId);
      const enhancedPayload = {
        ...payload,
        connectedAccounts,
      };

      console.log(`Sending natural language query to n8n agent: ${url}`);
      console.log(`Timeout set to: ${timeoutMs}ms (${timeoutMs / 1000}s)`);
      console.log('Query:', payload.query);
      console.log('Connected accounts:', Object.keys(connectedAccounts));
      console.log('Full payload:', JSON.stringify({
        ...enhancedPayload,
        // Mask sensitive tokens in logs
        connectedAccounts: Object.keys(connectedAccounts).reduce((acc, provider) => {
          acc[provider] = {
            ...connectedAccounts[provider],
            accessToken: '***MASKED***',
            refreshToken: connectedAccounts[provider].refreshToken ? '***MASKED***' : undefined,
          };
          return acc;
        }, {} as any)
      }, null, 2));

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(enhancedPayload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('n8n agent natural language response:', data);

      // Return the n8n response directly, preserving its structure
      return {
        success: data.success || true,
        data: data.data,
        message: data.message,
        conversationId: data.conversationId,
        timestamp: data.timestamp,
      };
    } catch (error) {
      console.error('Error processing query:', error);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return {
            success: false,
            error: 'Query timed out',
          };
        }
        return {
          success: false,
          error: `Agent error: ${error.message}`,
        };
      }
      
      return {
        success: false,
        error: 'Unknown error occurred while communicating with n8n agent',
      };
    }
  }

  /**
   * Health check for the n8n agent
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'HEAD',
        signal: AbortSignal.timeout(this.getTimeout('health')),
      });
      return response.ok;
    } catch (error) {
      console.error('n8n agent health check failed:', error);
      return false;
    }
  }
}

export const n8nAgentService = new N8nAgentService(); 