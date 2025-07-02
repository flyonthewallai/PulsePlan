import { Logger } from '../../src/types/scheduler';

class SchedulerLogger implements Logger {
  private formatMessage(level: string, message: string, data?: any): string {
    const timestamp = new Date().toISOString();
    const dataStr = data ? ` | Data: ${JSON.stringify(data)}` : '';
    return `[${timestamp}] [${level.toUpperCase()}] ${message}${dataStr}`;
  }

  info(message: string, data?: any): void {
    console.log(this.formatMessage('info', message, data));
  }

  error(message: string, error?: any): void {
    const errorData = error instanceof Error 
      ? { message: error.message, stack: error.stack }
      : error;
    console.error(this.formatMessage('error', message, errorData));
  }

  warn(message: string, data?: any): void {
    console.warn(this.formatMessage('warn', message, data));
  }

  // Job-specific logging methods
  logJobStart(jobName: string): void {
    this.info(`🚀 Starting job: ${jobName}`);
  }

  logJobComplete(jobName: string, results: { success: number; failed: number }): void {
    this.info(`✅ Completed job: ${jobName}`, results);
  }

  logUserResult(jobName: string, userId: string, email: string, success: boolean, error?: string): void {
    if (success) {
      this.info(`✅ ${jobName} success for user ${userId} (${email})`);
    } else {
      this.error(`❌ ${jobName} failed for user ${userId} (${email})`, error);
    }
  }

  logRateLimit(waitTime: number): void {
    this.info(`⏱️ Rate limiting: waiting ${waitTime}ms`);
  }
}

export const logger = new SchedulerLogger(); 