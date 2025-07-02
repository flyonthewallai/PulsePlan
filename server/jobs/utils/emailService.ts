import { Resend } from 'resend';
import { EmailService, EmailData } from '../../src/types/scheduler';
import { logger } from './logger';

class ResendEmailService implements EmailService {
  private resend: Resend;
  private readonly fromEmail: string;
  private readonly dailyBriefingTemplateId: string;
  private readonly weeklyPulseTemplateId: string;

  constructor() {
    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) {
      throw new Error('RESEND_API_KEY environment variable is required');
    }

    this.resend = new Resend(apiKey);
    this.fromEmail = process.env.RESEND_FROM_EMAIL || 'noreply@pulseplan.com';
    this.dailyBriefingTemplateId = process.env.RESEND_DAILY_BRIEFING_TEMPLATE_ID || '';
    this.weeklyPulseTemplateId = process.env.RESEND_WEEKLY_PULSE_TEMPLATE_ID || '';
  }

  async sendEmail(data: EmailData): Promise<{ success: boolean; error?: string }> {
    try {
      const result = await this.resend.emails.send({
        from: data.from || this.fromEmail,
        to: data.to,
        subject: data.subject,
        html: data.html,
      });

      if (result.error) {
        logger.error('Resend API error', result.error);
        return { success: false, error: result.error.message };
      }

      logger.info('Email sent successfully', { 
        messageId: result.data?.id,
        to: data.to,
        subject: data.subject 
      });

      return { success: true };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      logger.error('Failed to send email', { error: errorMessage, to: data.to });
      return { success: false, error: errorMessage };
    }
  }

  async sendDailyBriefing(
    to: string, 
    userName: string, 
    briefingData: any
  ): Promise<{ success: boolean; error?: string }> {
    try {
      // For now, always use HTML fallback until template API is confirmed
      // TODO: Add template support when Resend API structure is verified
      const html = this.generateDailyBriefingHTML(userName, briefingData);
      return this.sendEmail({
        to,
        subject: `Your Daily Briefing - ${new Date().toLocaleDateString()}`,
        html
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return { success: false, error: errorMessage };
    }
  }

  async sendWeeklyPulse(
    to: string, 
    userName: string, 
    weeklyData: any
  ): Promise<{ success: boolean; error?: string }> {
    try {
      // For now, always use HTML fallback until template API is confirmed
      // TODO: Add template support when Resend API structure is verified
      const html = this.generateWeeklyPulseHTML(userName, weeklyData);
      return this.sendEmail({
        to,
        subject: `Your Weekly Pulse™ - Week of ${new Date().toLocaleDateString()}`,
        html
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return { success: false, error: errorMessage };
    }
  }

  private generateDailyBriefingHTML(userName: string, data: any): string {
    const fallbackData = {
      summary: data?.summary || 'No briefing data available.',
      todaysTasks: data?.todaysTasks || [],
      upcomingEvents: data?.upcomingEvents || [],
      recommendations: data?.recommendations || []
    };

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Daily Briefing</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #4F46E5; color: white; padding: 20px; border-radius: 8px; text-align: center; }
          .content { padding: 20px 0; }
          .section { margin: 20px 0; }
          .section h3 { color: #374151; border-bottom: 2px solid #E5E7EB; padding-bottom: 5px; }
          .task, .event { background: #F9FAFB; padding: 10px; margin: 5px 0; border-left: 4px solid #4F46E5; }
          .footer { text-align: center; color: #6B7280; font-size: 12px; margin-top: 30px; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>🌅 Good Morning, ${userName}!</h1>
          <p>Your Daily Briefing for ${new Date().toLocaleDateString()}</p>
        </div>
        
        <div class="content">
          <div class="section">
            <h3>📋 Summary</h3>
            <p>${fallbackData.summary}</p>
          </div>
          
          ${fallbackData.todaysTasks.length > 0 ? `
          <div class="section">
            <h3>✅ Today's Tasks</h3>
            ${fallbackData.todaysTasks.map((task: any) => `
              <div class="task">
                <strong>${task.title || task}</strong>
                ${task.due_time ? `<br><small>Due: ${task.due_time}</small>` : ''}
              </div>
            `).join('')}
          </div>
          ` : ''}
          
          ${fallbackData.upcomingEvents.length > 0 ? `
          <div class="section">
            <h3>📅 Upcoming Events</h3>
            ${fallbackData.upcomingEvents.map((event: any) => `
              <div class="event">
                <strong>${event.title || event}</strong>
                ${event.start_time ? `<br><small>${event.start_time}</small>` : ''}
              </div>
            `).join('')}
          </div>
          ` : ''}
          
          ${fallbackData.recommendations.length > 0 ? `
          <div class="section">
            <h3>💡 Recommendations</h3>
            <ul>
              ${fallbackData.recommendations.map((rec: string) => `<li>${rec}</li>`).join('')}
            </ul>
          </div>
          ` : ''}
        </div>
        
        <div class="footer">
          <p>Have a productive day! 🚀</p>
          <p>PulsePlan - Your AI-Powered Productivity Assistant</p>
        </div>
      </body>
      </html>
    `;
  }

  private generateWeeklyPulseHTML(userName: string, data: any): string {
    const fallbackData = {
      completedTasks: data?.completedTasks || 0,
      totalTasks: data?.totalTasks || 0,
      productivityScore: data?.productivityScore || 0,
      achievements: data?.achievements || [],
      nextWeekRecommendations: data?.nextWeekRecommendations || []
    };

    const completionRate = fallbackData.totalTasks > 0 
      ? Math.round((fallbackData.completedTasks / fallbackData.totalTasks) * 100)
      : 0;

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Weekly Pulse™</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #7C3AED; color: white; padding: 20px; border-radius: 8px; text-align: center; }
          .content { padding: 20px 0; }
          .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
          .stat { background: #F3F4F6; padding: 15px; border-radius: 8px; text-align: center; }
          .stat-number { font-size: 24px; font-weight: bold; color: #7C3AED; }
          .section { margin: 20px 0; }
          .section h3 { color: #374151; border-bottom: 2px solid #E5E7EB; padding-bottom: 5px; }
          .achievement { background: #ECFDF5; padding: 10px; margin: 5px 0; border-left: 4px solid #10B981; }
          .footer { text-align: center; color: #6B7280; font-size: 12px; margin-top: 30px; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>📊 Weekly Pulse™</h1>
          <p>Your productivity summary for ${userName}</p>
          <p>Week of ${new Date().toLocaleDateString()}</p>
        </div>
        
        <div class="content">
          <div class="stats">
            <div class="stat">
              <div class="stat-number">${fallbackData.completedTasks}</div>
              <div>Tasks Completed</div>
            </div>
            <div class="stat">
              <div class="stat-number">${completionRate}%</div>
              <div>Completion Rate</div>
            </div>
          </div>
          
          ${fallbackData.achievements.length > 0 ? `
          <div class="section">
            <h3>🏆 This Week's Achievements</h3>
            ${fallbackData.achievements.map((achievement: string) => `
              <div class="achievement">${achievement}</div>
            `).join('')}
          </div>
          ` : ''}
          
          ${fallbackData.nextWeekRecommendations.length > 0 ? `
          <div class="section">
            <h3>🎯 Next Week's Focus</h3>
            <ul>
              ${fallbackData.nextWeekRecommendations.map((rec: string) => `<li>${rec}</li>`).join('')}
            </ul>
          </div>
          ` : ''}
        </div>
        
        <div class="footer">
          <p>Keep up the great work! 💪</p>
          <p>PulsePlan - Your AI-Powered Productivity Assistant</p>
        </div>
      </body>
      </html>
    `;
  }
}

export const emailService = new ResendEmailService(); 