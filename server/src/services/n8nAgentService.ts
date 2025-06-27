import n8nAgentConfig from '../config/n8nAgent';
import supabase from '../config/supabase';
import { cacheService, CACHE_CONFIG } from './cacheService';

export interface N8nAgentPayload {
  userId: string;
  userEmail?: string;
  userName?: string;
  isPremium?: boolean;
  city?: string;
  timezone?: string;
  source: 'agent' | 'user';
  tool?: string; // Optional for master agent
  [key: string]: any; // Allow arbitrary additional properties
}

export interface N8nNaturalLanguagePayload {
  userId: string;
  userEmail?: string;
  userName?: string;
  isPremium?: boolean;
  city?: string;
  timezone?: string;
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
  private readonly databaseTimeout = n8nAgentConfig.databaseTimeout;
  private readonly databaseQueryTimeout = n8nAgentConfig.databaseQueryTimeout;
  private readonly databaseBatchTimeout = n8nAgentConfig.databaseBatchTimeout;

  /**
   * Get operation-specific timeout values
   */
  private getTimeout(operation: 'task' | 'natural_language' | 'batch' | 'health' | 'database' | 'database_query' | 'database_batch'): number {
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
      case 'database':
        return this.databaseTimeout; // Database operation timeout
      case 'database_query':
        return this.databaseQueryTimeout; // Individual query timeout
      case 'database_batch':
        return this.databaseBatchTimeout; // Batch database operation timeout
      default:
        return baseTimeout;
    }
  }

  /**
   * Execute database query with timeout handling
   */
  private async executeWithTimeout<T>(
    operation: () => Promise<T>,
    timeoutMs: number,
    operationName: string
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error(`Database operation '${operationName}' timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      operation()
        .then((result) => {
          clearTimeout(timeoutId);
          resolve(result);
        })
        .catch((error) => {
          clearTimeout(timeoutId);
          reject(error);
        });
    });
  }

  /**
   * Get comprehensive user information with caching
   */
  private async getUserInfo(userId: string): Promise<{ 
    userName?: string; 
    isPremium?: boolean; 
    timezone?: string; 
    city?: string;
    school?: string;
    academicYear?: string;
    userType?: string;
    preferences?: any;
    workingHours?: any;
    studyPreferences?: any;
    workPreferences?: any;
    integrationPreferences?: any;
    notificationPreferences?: any;
    onboardingComplete?: boolean;
    onboardingStep?: number;
    avatarUrl?: string;
    lastLoginAt?: string;
  }> {
    // Try cache first
    const cachedUserInfo = await cacheService.get<{
      userName?: string; 
      isPremium?: boolean; 
      timezone?: string; 
      city?: string;
      school?: string;
      academicYear?: string;
      userType?: string;
      preferences?: any;
      workingHours?: any;
      studyPreferences?: any;
      workPreferences?: any;
      integrationPreferences?: any;
      notificationPreferences?: any;
      onboardingComplete?: boolean;
      onboardingStep?: number;
      avatarUrl?: string;
      lastLoginAt?: string;
    }>(
      CACHE_CONFIG.KEYS.USER_INFO, 
      userId
    );
    
    if (cachedUserInfo) {
      console.log(`📝 User info cache hit for user ${userId}`);
      return cachedUserInfo;
    }

    // Cache miss - fetch from database
    if (!supabase) {
      console.warn('Supabase not configured, skipping user info');
      return {};
    }

    try {
      const queryTimeout = this.getTimeout('database_query');
      console.log(`📊 Fetching comprehensive user info from DB for user ${userId} with timeout ${queryTimeout}ms`);

      const result = await this.executeWithTimeout(
        async () => {
          if (!supabase) {
            throw new Error('Supabase client not available');
          }

          const { data: userData, error } = await supabase
            .from('users')
            .select(`
              name, 
              subscription_status, 
              timezone, 
              city,
              school,
              academic_year,
              user_type,
              preferences,
              working_hours,
              study_preferences,
              work_preferences,
              integration_preferences,
              notification_preferences,
              onboarding_complete,
              onboarding_step,
              avatar_url,
              last_login_at
            `)
            .eq('id', userId)
            .single();

          if (error) {
            throw error;
          }

          return userData;
        },
        queryTimeout,
        'getUserInfo'
      );

      if (!result) {
        console.log('No user info found for user:', userId);
        return {};
      }

      const userInfo = {
        userName: result.name || undefined,
        isPremium: result.subscription_status === 'premium',
        timezone: result.timezone || 'UTC',
        city: result.city || undefined,
        school: result.school || undefined,
        academicYear: result.academic_year || undefined,
        userType: result.user_type || undefined,
        preferences: result.preferences || {},
        workingHours: result.working_hours || { endHour: 17, startHour: 9 },
        studyPreferences: result.study_preferences || {},
        workPreferences: result.work_preferences || {},
        integrationPreferences: result.integration_preferences || {},
        notificationPreferences: result.notification_preferences || {},
        onboardingComplete: result.onboarding_complete || false,
        onboardingStep: result.onboarding_step || 0,
        avatarUrl: result.avatar_url || undefined,
        lastLoginAt: result.last_login_at || undefined
      };

      // Cache the result
      await cacheService.set(
        CACHE_CONFIG.KEYS.USER_INFO,
        userId,
        userInfo,
        CACHE_CONFIG.TTL.USER_INFO
      );

      console.log(`📊 Found and cached comprehensive user info for user ${userId}:`, { 
        hasName: !!userInfo.userName, 
        isPremium: userInfo.isPremium,
        timezone: userInfo.timezone,
        hasCity: !!userInfo.city,
        hasSchool: !!userInfo.school,
        userType: userInfo.userType,
        onboardingComplete: userInfo.onboardingComplete
      });
      
      return userInfo;
    } catch (error) {
      console.error('Error getting user info:', error);
      if (error instanceof Error && error.message.includes('timed out')) {
        console.error(`Database query timed out when fetching user info for user ${userId}`);
      }
      return {};
    }
  }

  /**
   * Get user's connected account tokens with caching
   */
  private async getUserConnectedAccounts(userId: string): Promise<any> {
    // Try cache first
    const cachedAccounts = await cacheService.get<any>(
      CACHE_CONFIG.KEYS.USER_CONNECTED_ACCOUNTS, 
      userId
    );
    
    if (cachedAccounts) {
      console.log(`📝 Connected accounts cache hit for user ${userId}`);
      return cachedAccounts;
    }

    // Cache miss - fetch from database
    if (!supabase) {
      console.warn('Supabase not configured, skipping connected accounts');
      return {};
    }

    try {
      const queryTimeout = this.getTimeout('database_query');
      console.log(`📊 Fetching connected accounts from DB for user ${userId} with timeout ${queryTimeout}ms`);

      const result = await this.executeWithTimeout(
        async () => {
          if (!supabase) {
            throw new Error('Supabase client not available');
          }

          const { data: connections, error } = await supabase
            .from('calendar_connections')
            .select('provider, access_token, refresh_token, email, expires_at')
            .eq('user_id', userId);

          if (error) {
            throw error;
          }

          return connections;
        },
        queryTimeout,
        'getUserConnectedAccounts'
      );

      const connections = result;

      if (!connections || connections.length === 0) {
        console.log('No connected accounts found for user:', userId);
        const emptyResult = {};
        
        // Cache empty result with shorter TTL
        await cacheService.set(
          CACHE_CONFIG.KEYS.USER_CONNECTED_ACCOUNTS,
          userId,
          emptyResult,
          60 // 1 minute TTL for empty results
        );
        
        return emptyResult;
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

      // Cache the result
      await cacheService.set(
        CACHE_CONFIG.KEYS.USER_CONNECTED_ACCOUNTS,
        userId,
        connectedAccounts,
        CACHE_CONFIG.TTL.USER_CONNECTED_ACCOUNTS
      );

      console.log(`📊 Found and cached ${Object.keys(connectedAccounts).length} valid connected accounts for user ${userId}`);
      return connectedAccounts;
    } catch (error) {
      console.error('Error getting connected accounts:', error);
      if (error instanceof Error && error.message.includes('timed out')) {
        console.error(`Database query timed out when fetching connected accounts for user ${userId}`);
      }
      return {};
    }
  }

  /**
   * Create a complete N8nAgentPayload with user information
   * This is a helper method for controllers that need to create custom payloads
   */
  async createCompletePayload(
    basePayload: Omit<N8nAgentPayload, 'userName' | 'isPremium' | 'city' | 'timezone'>
  ): Promise<N8nAgentPayload> {
    const userInfo = await this.getUserInfo(basePayload.userId);
    
    // Destructure basePayload to maintain proper field order
    const { userId, userEmail, ...rest } = basePayload;
    
    return {
      userId,
      userEmail,
      userName: userInfo.userName,
      isPremium: userInfo.isPremium,
      city: userInfo.city,
      timezone: userInfo.timezone,
      ...rest,
    } as N8nAgentPayload;
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
    // Get user information to include in payload
    const userInfo = await this.getUserInfo(userId);
    
    const payload: N8nAgentPayload = {
      userId,
      userEmail,
      userName: userInfo.userName,
      isPremium: userInfo.isPremium,
      city: userInfo.city,
      timezone: userInfo.timezone,
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
    // Get user information to include in payload
    const userInfo = await this.getUserInfo(userId);
    
    const payload: N8nAgentPayload = {
      userId,
      userEmail,
      userName: userInfo.userName,
      isPremium: userInfo.isPremium,
      city: userInfo.city,
      timezone: userInfo.timezone,
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

  /**
   * Create a complete N8nNaturalLanguagePayload with user information
   * This is a helper method for controllers that need to create natural language payloads
   */
  async createCompleteNaturalLanguagePayload(
    basePayload: Omit<N8nNaturalLanguagePayload, 'userName' | 'isPremium' | 'city' | 'timezone'>
  ): Promise<N8nNaturalLanguagePayload> {
    const userInfo = await this.getUserInfo(basePayload.userId);
    
    // Destructure basePayload to maintain proper field order
    const { userId, userEmail, ...rest } = basePayload;
    
    return {
      userId,
      userEmail,
      userName: userInfo.userName,
      isPremium: userInfo.isPremium,
      city: userInfo.city,
      timezone: userInfo.timezone,
      ...rest,
    } as N8nNaturalLanguagePayload;
  }
}

export const n8nAgentService = new N8nAgentService(); 