import supabase from '../src/config/supabase';
import { User, JobResult, WeeklyPulseData } from '../src/types/scheduler';
import { logger } from './utils/logger';
import { rateLimiter } from './utils/rateLimiter';
import { emailService } from './utils/emailService';
import { enhancedAgentService } from '../src/services/enhancedAgentService';

export class WeeklyPulseJob {
  private readonly agentApiUrl: string;

  constructor() {
    this.agentApiUrl = process.env.N8N_AGENT_URL || 'https://pulseplan-agent.fly.dev';
  }

  async execute(): Promise<JobResult[]> {
    logger.logJobStart('Weekly Pulse Job');
    
    try {
      // Get eligible users
      const users = await this.getEligibleUsers();
      logger.info(`Found ${users.length} eligible users for weekly pulse`);

      if (users.length === 0) {
        logger.info('No eligible users found for weekly pulse');
        return [];
      }

      const results: JobResult[] = [];

      // Process each user
      for (const user of users) {
        try {
          await rateLimiter.wait(); // Respect rate limit

          const result = await this.processUser(user);
          results.push(result);

          logger.logUserResult(
            'Weekly Pulse',
            user.id,
            user.email,
            result.success,
            result.error
          );

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          const failedResult: JobResult = {
            success: false,
            userId: user.id,
            email: user.email,
            error: errorMessage,
            timestamp: new Date()
          };
          results.push(failedResult);

          logger.logUserResult(
            'Weekly Pulse',
            user.id,
            user.email,
            false,
            errorMessage
          );
        }
      }

      // Log final results
      const successCount = results.filter(r => r.success).length;
      const failureCount = results.filter(r => !r.success).length;

      logger.logJobComplete('Weekly Pulse Job', {
        success: successCount,
        failed: failureCount
      });

      return results;

    } catch (error) {
      logger.error('Weekly Pulse Job failed completely', error);
      throw error;
    }
  }

  private async getEligibleUsers(): Promise<User[]> {
    if (!supabase) {
      throw new Error('Supabase client not available');
    }

    try {
      const { data, error } = await supabase
        .from('users')
        .select(`
          id,
          email,
          name,
          is_premium,
          email_preferences,
          timezone
        `)
        .eq('is_premium', true)
        .not('email_preferences', 'is', null);

      if (error) {
        logger.error('Error fetching users from database', error);
        throw error;
      }

      // Filter users who have weekly_pulse enabled
      const eligibleUsers = (data || []).filter(user => {
        const preferences = user.email_preferences;
        return preferences && 
               (preferences as any)?.weekly_pulse === 'on' &&
               user.email; // Ensure email exists
      });

      return eligibleUsers.map(user => ({
        id: user.id,
        email: user.email,
        name: user.name,
        is_premium: user.is_premium,
        email_preferences: user.email_preferences as any,
        timezone: user.timezone
      }));

    } catch (error) {
      logger.error('Error in getEligibleUsers', error);
      throw error;
    }
  }

  private async processUser(user: User): Promise<JobResult> {
    try {
      // Call the weekly pulse agent API
      const weeklyData = await this.getWeeklyPulseFromAgent(user.id);
      
      // Send email using weekly pulse data
      const emailResult = await emailService.sendWeeklyPulse(
        user.email,
        user.name || 'User',
        weeklyData
      );

      if (!emailResult.success) {
        return {
          success: false,
          userId: user.id,
          email: user.email,
          error: emailResult.error || 'Failed to send email',
          timestamp: new Date()
        };
      }

      return {
        success: true,
        userId: user.id,
        email: user.email,
        timestamp: new Date()
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return {
        success: false,
        userId: user.id,
        email: user.email,
        error: errorMessage,
        timestamp: new Date()
      };
    }
  }

  private async getWeeklyPulseFromAgent(userId: string): Promise<WeeklyPulseData> {
    try {
      await rateLimiter.wait(); // Apply rate limiting to agent calls too

      // Get user details for the enhanced agent service
      const { data: user, error } = await supabase!
        .from('users')
        .select('email, name, is_premium, city, timezone')
        .eq('id', userId)
        .single();

      if (error || !user) {
        throw new Error('Failed to get user details');
      }

      // Use enhanced agent service (includes OAuth tokens)
      const data = await enhancedAgentService.generateWeeklyPulse(
        userId,
        user.email,
        user.name,
        user.is_premium,
        user.city,
        user.timezone
      );
      
      // Return the weekly pulse data, providing fallbacks if agent data is incomplete
      return {
        completedTasks: data.completedTasks || 0,
        totalTasks: data.totalTasks || 0,
        productivityScore: data.productivityScore || 0,
        weeklyGoals: data.weeklyGoals || [],
        achievements: data.achievements || [],
        nextWeekRecommendations: data.nextWeekRecommendations || [],
        weeklyStats: data.weeklyStats
      };

    } catch (error) {
      logger.warn(`Failed to get weekly pulse from agent for user ${userId}`, error);
      
      // Return fallback weekly pulse data
      return {
        completedTasks: 0,
        totalTasks: 0,
        productivityScore: 0,
        weeklyGoals: [],
        achievements: ['You maintained your productivity streak this week!'],
        nextWeekRecommendations: [
          'Check your PulsePlan app for personalized recommendations',
          'Review and plan your upcoming tasks',
          'Set weekly goals for improved productivity'
        ],
        weeklyStats: null
      };
    }
  }
}

export const weeklyPulseJob = new WeeklyPulseJob(); 