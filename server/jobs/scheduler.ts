import * as cron from 'node-cron';
import { dailyBriefingJob } from './dailyBriefingJob';
import { weeklyPulseJob } from './weeklyPulseJob';
import { logger } from './utils/logger';

export class EmailScheduler {
  private dailyBriefingTask: cron.ScheduledTask | null = null;
  private weeklyPulseTask: cron.ScheduledTask | null = null;
  private isRunning: boolean = false;

  constructor() {
    this.validateEnvironment();
  }

  private validateEnvironment(): void {
    const requiredEnvVars = [
      'SUPABASE_URL',
      'SUPABASE_SERVICE_KEY',
      'RESEND_API_KEY',
      'AGENT_API_BASE_URL'
    ];

    const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
    
    if (missingVars.length > 0) {
      logger.error(`Missing required environment variables: ${missingVars.join(', ')}`);
      throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
    }

    logger.info('Environment validation passed');
  }

  start(): void {
    if (this.isRunning) {
      logger.warn('Scheduler is already running');
      return;
    }

    try {
      // Daily Briefing Job - runs every day at 8:00 AM local time
      // Cron format: second minute hour day month day-of-week
      this.dailyBriefingTask = cron.schedule('0 0 8 * * *', async () => {
        logger.info('🌅 Daily Briefing Job triggered');
        try {
          const results = await dailyBriefingJob.execute();
          logger.info(`Daily Briefing Job completed: ${results.length} users processed`);
        } catch (error) {
          logger.error('Daily Briefing Job execution failed', error);
        }
      }, {
        timezone: 'America/New_York' // Adjust timezone as needed
      });

      // Weekly Pulse Job - runs every Sunday at 6:00 PM local time
      // Cron format: second minute hour day month day-of-week (0 = Sunday)
      this.weeklyPulseTask = cron.schedule('0 0 18 * * 0', async () => {
        logger.info('📊 Weekly Pulse Job triggered');
        try {
          const results = await weeklyPulseJob.execute();
          logger.info(`Weekly Pulse Job completed: ${results.length} users processed`);
        } catch (error) {
          logger.error('Weekly Pulse Job execution failed', error);
        }
      }, {
        timezone: 'America/New_York' // Adjust timezone as needed
      });

      // Tasks are automatically started by default
      // this.dailyBriefingTask.start();
      // this.weeklyPulseTask.start();

      this.isRunning = true;
      logger.info('📅 Email scheduler started successfully');
      logger.info('📋 Daily Briefing: Every day at 8:00 AM');
      logger.info('📊 Weekly Pulse: Every Sunday at 6:00 PM');

    } catch (error) {
      logger.error('Failed to start email scheduler', error);
      throw error;
    }
  }

  stop(): void {
    if (!this.isRunning) {
      logger.warn('Scheduler is not running');
      return;
    }

    try {
      if (this.dailyBriefingTask) {
        this.dailyBriefingTask.stop();
        this.dailyBriefingTask = null;
      }

      if (this.weeklyPulseTask) {
        this.weeklyPulseTask.stop();
        this.weeklyPulseTask = null;
      }

      this.isRunning = false;
      logger.info('📅 Email scheduler stopped successfully');

    } catch (error) {
      logger.error('Error stopping email scheduler', error);
      throw error;
    }
  }

  // Manual job execution methods for testing
  async runDailyBriefingNow(): Promise<void> {
    logger.info('🔧 Manually executing Daily Briefing Job');
    try {
      const results = await dailyBriefingJob.execute();
      logger.info(`Manual Daily Briefing Job completed: ${results.length} users processed`);
    } catch (error) {
      logger.error('Manual Daily Briefing Job execution failed', error);
      throw error;
    }
  }

  async runWeeklyPulseNow(): Promise<void> {
    logger.info('🔧 Manually executing Weekly Pulse Job');
    try {
      const results = await weeklyPulseJob.execute();
      logger.info(`Manual Weekly Pulse Job completed: ${results.length} users processed`);
    } catch (error) {
      logger.error('Manual Weekly Pulse Job execution failed', error);
      throw error;
    }
  }

  // Get scheduler status
  getStatus(): {
    isRunning: boolean;
    dailyBriefingActive: boolean;
    weeklyPulseActive: boolean;
    nextDailyBriefing: string | null;
    nextWeeklyPulse: string | null;
  } {
    return {
      isRunning: this.isRunning,
      dailyBriefingActive: !!this.dailyBriefingTask,
      weeklyPulseActive: !!this.weeklyPulseTask,
      nextDailyBriefing: this.getNextRunTime('daily'),
      nextWeeklyPulse: this.getNextRunTime('weekly')
    };
  }

  private getNextRunTime(jobType: 'daily' | 'weekly'): string | null {
    const now = new Date();
    let nextRun: Date;

    if (jobType === 'daily') {
      // Next 8:00 AM
      nextRun = new Date(now);
      nextRun.setHours(8, 0, 0, 0);
      
      // If it's already past 8:00 AM today, schedule for tomorrow
      if (nextRun <= now) {
        nextRun.setDate(nextRun.getDate() + 1);
      }
    } else {
      // Next Sunday at 6:00 PM
      nextRun = new Date(now);
      nextRun.setHours(18, 0, 0, 0);
      
      // Calculate days until next Sunday
      const daysUntilSunday = (7 - now.getDay()) % 7;
      if (daysUntilSunday === 0 && now.getHours() >= 18) {
        // If it's Sunday and already past 6 PM, schedule for next Sunday
        nextRun.setDate(nextRun.getDate() + 7);
      } else {
        nextRun.setDate(nextRun.getDate() + daysUntilSunday);
      }
    }

    return nextRun.toISOString();
  }

  // Graceful shutdown
  async shutdown(): Promise<void> {
    logger.info('🔄 Shutting down email scheduler gracefully...');
    
    // Stop scheduled tasks
    this.stop();
    
    // Wait a moment for any ongoing jobs to complete
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    logger.info('✅ Email scheduler shutdown complete');
  }
}

// Create singleton instance
export const emailScheduler = new EmailScheduler();

// Graceful shutdown handlers
process.on('SIGINT', async () => {
  logger.info('Received SIGINT, shutting down gracefully...');
  await emailScheduler.shutdown();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Received SIGTERM, shutting down gracefully...');
  await emailScheduler.shutdown();
  process.exit(0);
}); 