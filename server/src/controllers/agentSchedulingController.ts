import { Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authenticate';
import { n8nAgentService } from '../services/n8nAgentService';
import supabase from '../config/supabase';
import n8nAgentConfig from '../config/n8nAgent';

export interface BatchTaskPayload {
  tasks: Array<{
    title: string;
    dueDate: string;
    duration: number;
    priority: 'high' | 'medium' | 'low';
    subject: string;
  }>;
  preferences?: {
    preferredWorkingHours?: { start: string; end: string };
    breakDuration?: number;
    focusSessionDuration?: number;
  };
}

/**
 * Execute database query with timeout handling
 */
const executeWithTimeout = async <T>(
  operation: () => Promise<T>,
  timeoutMs: number,
  operationName: string
): Promise<T> => {
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
};

/**
 * Process multiple tasks through the n8n agent for intelligent scheduling
 */
export const batchProcessTasks = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { tasks, preferences }: BatchTaskPayload = req.body;

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  if (!tasks || !Array.isArray(tasks) || tasks.length === 0) {
    res.status(400).json({ error: 'Tasks array is required and cannot be empty' });
    return;
  }

  try {
    const results: Array<{
      task: string;
      success: boolean;
      data?: any;
      message?: string;
    }> = [];
    const errors: Array<{
      task: string;
      error: string;
    }> = [];

    // Process each task through the n8n agent
    for (const task of tasks) {
      try {
        const agentResponse = await n8nAgentService.createTaskFromUser(
          userId,
          task.title,
          task.dueDate,
          task.duration,
          task.priority,
          task.subject,
          userEmail
        );

        results.push({
          task: task.title,
          success: agentResponse.success,
          data: agentResponse.data,
          message: agentResponse.message || agentResponse.error,
        });
      } catch (error) {
        errors.push({
          task: task.title,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    res.json({
      totalTasks: tasks.length,
      successfulTasks: results.filter(r => r.success).length,
      failedTasks: errors.length,
      results,
      errors,
      preferences: preferences || null,
    });
  } catch (error) {
    console.error('Error in batchProcessTasks:', error);
    res.status(500).json({ error: 'Failed to batch process tasks' });
  }
};

/**
 * Trigger intelligent re-scheduling of existing tasks through n8n agent
 */
export const triggerIntelligentRescheduling = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { includeCompleted = false, priorityFilter, subjectFilter } = req.body;

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  if (!supabase) {
    res.status(500).json({ error: 'Supabase is not configured' });
    return;
  }

  try {
    // Fetch user's existing tasks with timeout handling
    const queryTimeout = n8nAgentConfig.databaseBatchTimeout;
    console.log(`Fetching tasks for rescheduling with timeout ${queryTimeout}ms`);

    const tasks = await executeWithTimeout(
      async () => {
        if (!supabase) {
          throw new Error('Supabase client not available');
        }

        let query = supabase
          .from('tasks')
          .select('*')
          .eq('user_id', userId);

        if (!includeCompleted) {
          query = query.neq('status', 'completed');
        }

        if (priorityFilter) {
          query = query.eq('priority', priorityFilter);
        }

        if (subjectFilter) {
          query = query.eq('subject', subjectFilter);
        }

        const { data: tasks, error } = await query.order('due_date', { ascending: true });

        if (error) {
          throw error;
        }

        return tasks;
      },
      queryTimeout,
      'fetchTasksForRescheduling'
    );

    if (!tasks || tasks.length === 0) {
      res.json({ message: 'No tasks found for rescheduling', tasksProcessed: 0 });
      return;
    }

    // Send all tasks to n8n agent for intelligent scheduling
    const reschedulingResults: Array<{
      taskId: any;
      taskTitle: any;
      success: boolean;
      message?: string;
      error?: string;
    }> = [];

    for (const task of tasks) {
      try {
        const agentResponse = await n8nAgentService.createTaskWithAgent(
          userId,
          task.title,
          task.due_date,
          task.estimated_minutes || 60,
          task.priority || 'medium',
          task.subject,
          'intelligent-reschedule', // Special tool for rescheduling
          userEmail
        );

        reschedulingResults.push({
          taskId: task.id,
          taskTitle: task.title,
          success: agentResponse.success,
          message: agentResponse.message || agentResponse.error,
        });
      } catch (error) {
        reschedulingResults.push({
          taskId: task.id,
          taskTitle: task.title,
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    res.json({
      message: 'Intelligent rescheduling triggered',
      tasksProcessed: tasks.length,
      successfulReschedules: reschedulingResults.filter(r => r.success).length,
      results: reschedulingResults,
    });
  } catch (error) {
    console.error('Error in triggerIntelligentRescheduling:', error);
    res.status(500).json({ error: 'Failed to trigger intelligent rescheduling' });
  }
};

/**
 * Send study session optimization request to n8n agent
 */
export const optimizeStudySession = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { 
    availableHours, 
    subjects, 
    preferredDifficulty, 
    sessionType = 'focus' 
  } = req.body;

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  if (!availableHours || availableHours <= 0) {
    res.status(400).json({ error: 'Available hours must be greater than 0' });
    return;
  }

  try {
    const completePayload = await n8nAgentService.createCompletePayload({
      userId,
      userEmail,
      taskTitle: `Study Session Optimization - ${sessionType}`,
      dueDate: new Date(Date.now() + availableHours * 60 * 60 * 1000).toISOString(),
      duration: availableHours * 60,
      priority: 'high',
      subject: subjects ? subjects.join(', ') : 'General',
      source: 'agent',
      tool: 'study-session-optimizer',
      metadata: {
        availableHours,
        subjects,
        preferredDifficulty,
        sessionType,
      },
    });
    
    const agentResponse = await n8nAgentService.postToAgent(completePayload);

    res.json({
      message: 'Study session optimization triggered',
      sessionType,
      availableHours,
      subjects,
      success: agentResponse.success,
      data: agentResponse.data,
      error: agentResponse.error,
    });
  } catch (error) {
    console.error('Error in optimizeStudySession:', error);
    res.status(500).json({ error: 'Failed to optimize study session' });
  }
};

/**
 * Analyze upcoming deadlines and send recommendations to n8n agent
 */
export const analyzeUpcomingDeadlines = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { daysAhead = 7, priorityThreshold = 'medium' } = req.body;

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  if (!supabase) {
    res.status(500).json({ error: 'Supabase is not configured' });
    return;
  }

  try {
    // Calculate date range
    const now = new Date();
    const futureDate = new Date(now.getTime() + daysAhead * 24 * 60 * 60 * 1000);

    // Fetch tasks with upcoming deadlines with timeout handling
    const queryTimeout = n8nAgentConfig.databaseQueryTimeout;
    console.log(`Fetching upcoming deadlines with timeout ${queryTimeout}ms`);

    const upcomingTasks = await executeWithTimeout(
      async () => {
        if (!supabase) {
          throw new Error('Supabase client not available');
        }

        const { data: upcomingTasks, error } = await supabase
          .from('tasks')
          .select('*')
          .eq('user_id', userId)
          .gte('due_date', now.toISOString())
          .lte('due_date', futureDate.toISOString())
          .neq('status', 'completed')
          .order('due_date', { ascending: true });

        if (error) {
          throw error;
        }

        return upcomingTasks;
      },
      queryTimeout,
      'fetchUpcomingDeadlines'
    );

    if (!upcomingTasks || upcomingTasks.length === 0) {
      res.json({ 
        message: 'No upcoming deadlines found', 
        daysAhead,
        tasksAnalyzed: 0 
      });
      return;
    }

    // Send to n8n agent for deadline analysis
    const completePayload = await n8nAgentService.createCompletePayload({
      userId,
      userEmail,
      taskTitle: `Deadline Analysis - Next ${daysAhead} days`,
      dueDate: futureDate.toISOString(),
      duration: 30, // 30 minutes for analysis
      priority: 'high',
      subject: 'Planning & Analysis',
      source: 'agent',
      tool: 'deadline-analyzer',
      metadata: {
        daysAhead,
        priorityThreshold,
        upcomingTasks: upcomingTasks.map(task => ({
          id: task.id,
          title: task.title,
          dueDate: task.due_date,
          priority: task.priority,
          subject: task.subject,
          estimatedMinutes: task.estimated_minutes,
        })),
        analysisDate: now.toISOString(),
      },
    });
    
    const agentResponse = await n8nAgentService.postToAgent(completePayload);

    res.json({
      message: 'Deadline analysis triggered',
      daysAhead,
      tasksAnalyzed: upcomingTasks.length,
      upcomingTasks: upcomingTasks.map(task => ({
        id: task.id,
        title: task.title,
        dueDate: task.due_date,
        priority: task.priority,
        subject: task.subject,
      })),
      success: agentResponse.success,
      data: agentResponse.data,
      error: agentResponse.error,
    });
  } catch (error) {
    console.error('Error in analyzeUpcomingDeadlines:', error);
    res.status(500).json({ error: 'Failed to analyze upcoming deadlines' });
  }
}; 