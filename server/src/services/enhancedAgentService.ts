import axios, { AxiosRequestConfig } from 'axios';
import { tokenService } from './tokenService';
import { AgentPayloadWithTokens } from '../types/tokens';
import { logger } from '../../jobs/utils/logger';

class EnhancedAgentService {
  private readonly baseURL: string;
  private readonly timeout: number;

  constructor() {
    this.baseURL = process.env.N8N_AGENT_URL || 'https://pulseplan-agent.fly.dev';
    this.timeout = parseInt(process.env.N8N_TIMEOUT || '30000', 10);
  }

  /**
   * Make an API call to the agent with user tokens included
   */
  private async makeAgentRequest(
    endpoint: string,
    payload: any,
    options: AxiosRequestConfig = {}
  ): Promise<any> {
    try {
      const url = `${this.baseURL}${endpoint}`;
      
      const config: AxiosRequestConfig = {
        method: 'POST',
        url,
        data: payload,
        timeout: this.timeout,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      };

      logger.info(`Making agent request to ${endpoint}`, {
        userId: payload.userId,
        hasTokens: !!payload.connectedAccounts
      });

      const response = await axios(config);
      
      logger.info(`Agent request successful for ${endpoint}`, {
        userId: payload.userId,
        status: response.status
      });

      return response.data;
    } catch (error) {
      logger.error(`Agent request failed for ${endpoint}`, {
        userId: payload.userId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Prepare payload with user tokens and metadata
   */
  private async preparePayloadWithTokens(
    userId: string,
    basePayload: any,
    source: 'agent' | 'user' | 'scheduler' = 'agent'
  ): Promise<AgentPayloadWithTokens> {
    try {
      // Get user tokens
      const userTokens = await tokenService.getUserTokensForAgent(userId);
      
      // Build connected accounts object
      const connectedAccounts: AgentPayloadWithTokens['connectedAccounts'] = {};
      
      if (userTokens.google) {
        connectedAccounts.google = {
          access_token: userTokens.google.access_token,
          refresh_token: userTokens.google.refresh_token,
          expires_at: userTokens.google.expires_at,
          scopes: userTokens.google.scopes,
          email: undefined // Will be populated if needed
        };
      }
      
      if (userTokens.microsoft) {
        connectedAccounts.microsoft = {
          access_token: userTokens.microsoft.access_token,
          refresh_token: userTokens.microsoft.refresh_token,
          expires_at: userTokens.microsoft.expires_at,
          scopes: userTokens.microsoft.scopes,
          email: undefined // Will be populated if needed
        };
      }
      
      if (userTokens.canvas) {
        connectedAccounts.canvas = {
          access_token: userTokens.canvas.access_token,
          refresh_token: userTokens.canvas.refresh_token,
          expires_at: userTokens.canvas.expires_at,
          scopes: userTokens.canvas.scopes
        };
      }
      
      if (userTokens.notion) {
        connectedAccounts.notion = {
          access_token: userTokens.notion.access_token,
          refresh_token: userTokens.notion.refresh_token,
          expires_at: userTokens.notion.expires_at,
          scopes: userTokens.notion.scopes
        };
      }

      // Build the enhanced payload
      const enhancedPayload: AgentPayloadWithTokens = {
        ...basePayload,
        userId,
        source,
        connectedAccounts: Object.keys(connectedAccounts).length > 0 ? connectedAccounts : undefined
      };

      return enhancedPayload;
    } catch (error) {
      logger.error(`Error preparing payload with tokens for user ${userId}`, error);
      
      // Return payload without tokens on error
      return {
        ...basePayload,
        userId,
        source
      };
    }
  }

  /**
   * Generate daily briefing with user tokens
   */
  async generateDailyBriefing(
    userId: string,
    userEmail?: string,
    userName?: string,
    isPremium: boolean = false,
    city?: string,
    timezone?: string
  ): Promise<any> {
    const basePayload = {
      userEmail,
      userName,
      isPremium,
      city,
      timezone,
      tool: 'daily_briefing'
    };

    const payload = await this.preparePayloadWithTokens(userId, basePayload, 'scheduler');
    return this.makeAgentRequest('/agents/briefing', payload);
  }

  /**
   * Generate weekly pulse with user tokens
   */
  async generateWeeklyPulse(
    userId: string,
    userEmail?: string,
    userName?: string,
    isPremium: boolean = false,
    city?: string,
    timezone?: string
  ): Promise<any> {
    const basePayload = {
      userEmail,
      userName,
      isPremium,
      city,
      timezone,
      tool: 'weekly_pulse'
    };

    const payload = await this.preparePayloadWithTokens(userId, basePayload, 'scheduler');
    return this.makeAgentRequest('/agents/weekly-pulse', payload);
  }

  /**
   * Chat with agent including user tokens
   */
  async chatWithAgent(
    userId: string,
    message: string,
    context?: any,
    userEmail?: string,
    userName?: string,
    isPremium: boolean = false
  ): Promise<any> {
    const basePayload = {
      message,
      context,
      userEmail,
      userName,
      isPremium,
      tool: 'chat'
    };

    const payload = await this.preparePayloadWithTokens(userId, basePayload, 'user');
    return this.makeAgentRequest('/agents/chat', payload);
  }

  /**
   * Generate schedule with user tokens
   */
  async generateSchedule(
    userId: string,
    preferences?: any,
    userEmail?: string,
    userName?: string,
    isPremium: boolean = false,
    timezone?: string
  ): Promise<any> {
    const basePayload = {
      preferences,
      userEmail,
      userName,
      isPremium,
      timezone,
      tool: 'scheduling'
    };

    const payload = await this.preparePayloadWithTokens(userId, basePayload, 'agent');
    return this.makeAgentRequest('/agents/schedule', payload);
  }

  /**
   * Analyze tasks with user tokens
   */
  async analyzeTasks(
    userId: string,
    tasks: any[],
    userEmail?: string,
    userName?: string,
    isPremium: boolean = false
  ): Promise<any> {
    const basePayload = {
      tasks,
      userEmail,
      userName,
      isPremium,
      tool: 'task_analysis'
    };

    const payload = await this.preparePayloadWithTokens(userId, basePayload, 'agent');
    return this.makeAgentRequest('/agents/analyze-tasks', payload);
  }

  /**
   * Generic agent request with tokens
   */
  async makeGenericRequest(
    endpoint: string,
    userId: string,
    requestData: any,
    source: 'agent' | 'user' | 'scheduler' = 'agent'
  ): Promise<any> {
    const payload = await this.preparePayloadWithTokens(userId, requestData, source);
    return this.makeAgentRequest(endpoint, payload);
  }

  /**
   * Health check for agent service
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseURL}/health`, {
        timeout: 5000
      });
      return response.status === 200;
    } catch (error) {
      logger.error('Agent service health check failed', error);
      return false;
    }
  }

  /**
   * Get user's connected accounts status
   */
  async getUserConnectionStatus(userId: string): Promise<{
    google: boolean;
    microsoft: boolean;
    canvas: boolean;
    notion: boolean;
  }> {
    return tokenService.getUserConnectionStatus(userId);
  }

  /**
   * Check if user has any connected accounts
   */
  async hasConnectedAccounts(userId: string): Promise<boolean> {
    const status = await this.getUserConnectionStatus(userId);
    return status.google || status.microsoft || status.canvas || status.notion;
  }
}

export const enhancedAgentService = new EnhancedAgentService(); 