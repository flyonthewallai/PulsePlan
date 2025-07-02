import { Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authenticate';
import supabase from '../config/supabase';
import { logger } from '../../jobs/utils/logger';
import { enhancedAgentService } from '../services/enhancedAgentService';

/**
 * POST /agents/briefing
 * Generate daily briefing data for a user
 */
export const generateBriefing = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const { userId } = req.body;

  if (!userId) {
    res.status(400).json({ error: 'userId is required' });
    return;
  }

  try {
    logger.info(`Generating briefing for user ${userId}`);

    // Get user info first for fallback
    const userInfo = await getUserInfo(userId);
    if (!userInfo) {
      res.status(404).json({ error: 'User not found' });
      return;
    }

    // Try to use the enhanced agent service first
    try {
      const agentResponse = await enhancedAgentService.generateDailyBriefing(
        userId,
        userInfo.email,
        userInfo.name,
        userInfo.is_premium || false,
        userInfo.city,
        userInfo.timezone
      );

      logger.info(`Agent briefing generated successfully for user ${userId}`);
      res.json({
        ...agentResponse,
        source: 'agent',
        timestamp: new Date().toISOString()
      });
      return;
    } catch (agentError) {
      logger.warn(`Agent service failed for user ${userId}, using fallback:`, agentError);
    }

    // Fallback to local generation if agent service fails
    const todaysTasks = await getTodaysTasks(userId);
    const upcomingEvents = await getUpcomingEvents(userId);
    
    const summary = generateBriefingSummary(userInfo, todaysTasks, upcomingEvents);
    const recommendations = generateRecommendations(todaysTasks, upcomingEvents);

    const briefingData = {
      summary,
      todaysTasks,
      upcomingEvents,
      recommendations,
      weather: null,
      connectedAccounts: await enhancedAgentService.getUserConnectionStatus(userId),
      source: 'fallback',
      timestamp: new Date().toISOString()
    };

    logger.info(`Fallback briefing generated successfully for user ${userId}`);
    res.json(briefingData);

  } catch (error) {
    logger.error(`Error generating briefing for user ${userId}`, error);
    res.status(500).json({ 
      error: 'Failed to generate briefing',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * POST /agents/weekly-pulse
 * Generate weekly pulse data for a user
 */
export const generateWeeklyPulse = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const { userId } = req.body;

  if (!userId) {
    res.status(400).json({ error: 'userId is required' });
    return;
  }

  try {
    logger.info(`Generating weekly pulse for user ${userId}`);

    // Get user info first for fallback
    const userInfo = await getUserInfo(userId);
    if (!userInfo) {
      res.status(404).json({ error: 'User not found' });
      return;
    }

    // Try to use the enhanced agent service first
    try {
      const agentResponse = await enhancedAgentService.generateWeeklyPulse(
        userId,
        userInfo.email,
        userInfo.name,
        userInfo.is_premium || false,
        userInfo.city,
        userInfo.timezone
      );

      logger.info(`Agent weekly pulse generated successfully for user ${userId}`);
      res.json({
        ...agentResponse,
        source: 'agent',
        timestamp: new Date().toISOString()
      });
      return;
    } catch (agentError) {
      logger.warn(`Agent service failed for user ${userId}, using fallback:`, agentError);
    }

    // Fallback to local generation if agent service fails
    const now = new Date();
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - now.getDay());
    weekStart.setHours(0, 0, 0, 0);

    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    weekEnd.setHours(23, 59, 59, 999);

    const weeklyStats = await getWeeklyStats(userId, weekStart, weekEnd);
    const achievements = generateAchievements(weeklyStats);
    const nextWeekRecommendations = generateNextWeekRecommendations(weeklyStats);

    const weeklyPulseData = {
      completedTasks: weeklyStats.completedTasks,
      totalTasks: weeklyStats.totalTasks,
      productivityScore: calculateProductivityScore(weeklyStats),
      weeklyGoals: weeklyStats.weeklyGoals || [],
      achievements,
      nextWeekRecommendations,
      weeklyStats: {
        weekStart: weekStart.toISOString(),
        weekEnd: weekEnd.toISOString(),
        ...weeklyStats
      },
      connectedAccounts: await enhancedAgentService.getUserConnectionStatus(userId),
      source: 'fallback',
      timestamp: new Date().toISOString()
    };

    logger.info(`Fallback weekly pulse generated successfully for user ${userId}`);
    res.json(weeklyPulseData);

  } catch (error) {
    logger.error(`Error generating weekly pulse for user ${userId}`, error);
    res.status(500).json({ 
      error: 'Failed to generate weekly pulse',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

// Helper functions

async function getUserInfo(userId: string): Promise<any> {
  if (!supabase) {
    throw new Error('Supabase client not available');
  }

  const { data, error } = await supabase
    .from('users')
    .select('id, name, email, timezone, preferences')
    .eq('id', userId)
    .single();

  if (error) {
    logger.error('Error fetching user info', error);
    return null;
  }

  return data;
}

async function getTodaysTasks(userId: string): Promise<any[]> {
  if (!supabase) {
    return [];
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  try {
    const { data, error } = await supabase
      .from('tasks')
      .select('id, title, due_date, priority, status, subject')
      .eq('user_id', userId)
      .gte('due_date', today.toISOString())
      .lt('due_date', tomorrow.toISOString())
      .neq('status', 'completed')
      .order('due_date', { ascending: true });

    if (error) {
      logger.error('Error fetching today\'s tasks', error);
      return [];
    }

    return data || [];
  } catch (error) {
    logger.error('Error in getTodaysTasks', error);
    return [];
  }
}

async function getUpcomingEvents(userId: string): Promise<any[]> {
  if (!supabase) {
    return [];
  }

  const now = new Date();
  const next24Hours = new Date(now.getTime() + 24 * 60 * 60 * 1000);

  try {
    const { data, error } = await supabase
      .from('events')
      .select('id, title, start_time, end_time, calendar_provider')
      .eq('user_id', userId)
      .gte('start_time', now.toISOString())
      .lte('start_time', next24Hours.toISOString())
      .order('start_time', { ascending: true });

    if (error) {
      logger.error('Error fetching upcoming events', error);
      return [];
    }

    return data || [];
  } catch (error) {
    logger.error('Error in getUpcomingEvents', error);
    return [];
  }
}

async function getWeeklyStats(userId: string, weekStart: Date, weekEnd: Date): Promise<any> {
  if (!supabase) {
    return { completedTasks: 0, totalTasks: 0 };
  }

  try {
    // Get completed tasks this week
    const { data: completedTasks, error: completedError } = await supabase
      .from('tasks')
      .select('id')
      .eq('user_id', userId)
      .eq('status', 'completed')
      .gte('updated_at', weekStart.toISOString())
      .lte('updated_at', weekEnd.toISOString());

    // Get total tasks this week (created or due this week)
    const { data: totalTasks, error: totalError } = await supabase
      .from('tasks')
      .select('id')
      .eq('user_id', userId)
      .or(`created_at.gte.${weekStart.toISOString()},due_date.gte.${weekStart.toISOString()}`)
      .or(`created_at.lte.${weekEnd.toISOString()},due_date.lte.${weekEnd.toISOString()}`);

    if (completedError || totalError) {
      logger.error('Error fetching weekly stats', { completedError, totalError });
      return { completedTasks: 0, totalTasks: 0 };
    }

    return {
      completedTasks: completedTasks?.length || 0,
      totalTasks: totalTasks?.length || 0,
      weekStart: weekStart.toISOString(),
      weekEnd: weekEnd.toISOString()
    };
  } catch (error) {
    logger.error('Error in getWeeklyStats', error);
    return { completedTasks: 0, totalTasks: 0 };
  }
}

function generateBriefingSummary(userInfo: any, tasks: any[], events: any[]): string {
  const userName = userInfo?.name || 'there';
  const taskCount = tasks.length;
  const eventCount = events.length;

  let summary = `Good morning, ${userName}! `;

  if (taskCount === 0 && eventCount === 0) {
    summary += "You have a light day ahead with no urgent tasks or events scheduled. Perfect time to focus on your goals!";
  } else if (taskCount > 0 && eventCount === 0) {
    summary += `You have ${taskCount} task${taskCount > 1 ? 's' : ''} to focus on today. No events scheduled, so you'll have good focus time.`;
  } else if (taskCount === 0 && eventCount > 0) {
    summary += `You have ${eventCount} event${eventCount > 1 ? 's' : ''} scheduled today. Good time to prepare and make the most of your meetings.`;
  } else {
    summary += `You have ${taskCount} task${taskCount > 1 ? 's' : ''} and ${eventCount} event${eventCount > 1 ? 's' : ''} today. Time to balance productivity with your schedule!`;
  }

  return summary;
}

function generateRecommendations(tasks: any[], events: any[]): string[] {
  const recommendations: string[] = [];

  if (tasks.length > 0) {
    const highPriorityTasks = tasks.filter(task => task.priority === 'high');
    if (highPriorityTasks.length > 0) {
      recommendations.push(`Start with your ${highPriorityTasks.length} high-priority task${highPriorityTasks.length > 1 ? 's' : ''} first thing this morning.`);
    }
    
    if (tasks.length >= 5) {
      recommendations.push("Consider using the Pomodoro technique to stay focused with this busy schedule.");
    }
  }

  if (events.length > 0) {
    recommendations.push("Review your meeting agendas and prepare any necessary materials in advance.");
  }

  if (tasks.length === 0 && events.length === 0) {
    recommendations.push("Use this free time to plan ahead or work on long-term goals.");
    recommendations.push("Consider reviewing your weekly objectives and making progress on important projects.");
  }

  return recommendations;
}

function generateAchievements(stats: any): string[] {
  const achievements: string[] = [];
  const completionRate = stats.totalTasks > 0 ? (stats.completedTasks / stats.totalTasks) * 100 : 0;

  if (completionRate >= 80) {
    achievements.push("🏆 Outstanding productivity this week - you completed over 80% of your tasks!");
  } else if (completionRate >= 60) {
    achievements.push("🎯 Great job this week - you maintained good productivity momentum!");
  } else if (completionRate >= 40) {
    achievements.push("📈 Solid progress this week - you're building good habits!");
  }

  if (stats.completedTasks >= 10) {
    achievements.push("🚀 Task master - you completed 10+ tasks this week!");
  } else if (stats.completedTasks >= 5) {
    achievements.push("✅ Productive week - you stayed on top of your tasks!");
  }

  if (achievements.length === 0) {
    achievements.push("🌱 Every step counts - you're building toward your goals!");
  }

  return achievements;
}

function generateNextWeekRecommendations(stats: any): string[] {
  const recommendations: string[] = [];
  const completionRate = stats.totalTasks > 0 ? (stats.completedTasks / stats.totalTasks) * 100 : 0;

  if (completionRate < 50) {
    recommendations.push("Focus on breaking large tasks into smaller, manageable chunks.");
    recommendations.push("Set realistic daily goals to build momentum.");
  } else if (completionRate < 80) {
    recommendations.push("Continue your current pace and look for ways to optimize your workflow.");
    recommendations.push("Consider time-blocking to protect your focus time.");
  } else {
    recommendations.push("You're crushing it! Consider taking on a stretch goal or new challenge.");
    recommendations.push("Share your productivity strategies with others who might benefit.");
  }

  recommendations.push("Review and plan your upcoming week every Sunday evening.");
  
  return recommendations;
}

function calculateProductivityScore(stats: any): number {
  if (stats.totalTasks === 0) return 0;
  
  const completionRate = (stats.completedTasks / stats.totalTasks) * 100;
  
  // Scale the score (0-100) with some bonus for high task volume
  let score = completionRate;
  
  // Bonus for completing many tasks
  if (stats.completedTasks >= 10) {
    score += 5;
  } else if (stats.completedTasks >= 5) {
    score += 2;
  }
  
  return Math.min(Math.round(score), 100);
} 