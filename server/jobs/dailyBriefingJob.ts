import supabase from '../src/config/supabase';
import { User, JobResult, BriefingData } from '../src/types/scheduler';
import { logger } from './utils/logger';
import { rateLimiter } from './utils/rateLimiter';
import { emailService } from './utils/emailService';
import { enhancedAgentService } from '../src/services/enhancedAgentService';

export class DailyBriefingJob {
  private readonly agentApiUrl: string;

  constructor() {
    this.agentApiUrl = process.env.N8N_AGENT_URL || 'https://pulseplan-agent.fly.dev';
  }

  async execute(): Promise<JobResult[]> {
    logger.logJobStart('Daily Briefing Job');
    
    try {
      // Get eligible users
      const users = await this.getEligibleUsers();
      logger.info(`Found ${users.length} eligible users for daily briefing`);

      if (users.length === 0) {
        logger.info('No eligible users found for daily briefing');
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
            'Daily Briefing',
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
            'Daily Briefing',
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

      logger.logJobComplete('Daily Briefing Job', {
        success: successCount,
        failed: failureCount
      });

      return results;

    } catch (error) {
      logger.error('Daily Briefing Job failed completely', error);
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

      // Filter users who have daily_briefing enabled
      const eligibleUsers = (data || []).filter(user => {
        const preferences = user.email_preferences;
        return preferences && 
               (preferences as any)?.daily_briefing === 'on' &&
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
      // Call the briefing agent API
      const briefingData = await this.getBriefingFromAgent(user.id);
      
      // Send email using briefing data
      const emailResult = await emailService.sendDailyBriefing(
        user.email,
        user.name || 'User',
        briefingData
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

  private async getBriefingFromAgent(userId: string): Promise<BriefingData> {
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
      const data = await enhancedAgentService.generateDailyBriefing(
        userId,
        user.email,
        user.name,
        user.is_premium,
        user.city,
        user.timezone
      );
      
      // Return the briefing data, providing fallbacks if agent data is incomplete
      return {
        summary: data.summary || 'Your briefing is ready!',
        todaysTasks: data.todaysTasks || [],
        upcomingEvents: data.upcomingEvents || [],
        weather: data.weather,
        recommendations: data.recommendations || []
      };

    } catch (error) {
      logger.warn(`Failed to get briefing from agent for user ${userId}`, error);
      
      // Return fallback briefing data
      return {
        summary: 'Unable to generate personalized briefing at this time. Please check your tasks and calendar for today\'s schedule.',
        todaysTasks: [],
        upcomingEvents: [],
        recommendations: ['Check your PulsePlan app for the latest updates']
      };
    }
  }
}

export const dailyBriefingJob = new DailyBriefingJob(); 