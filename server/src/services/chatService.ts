import openai from '../config/openai';
import { Task } from '../types/task';
import { ScheduleBlock } from './intelligentSchedulingService';
import supabase from '../config/supabase';
import { AuthenticatedRequest } from '../middleware/authenticate';

const SYSTEM_PROMPT = `You are an AI assistant for a productivity app that helps users manage their tasks and schedule. You have access to the user's tasks and schedule, and can help them:

1. View and manage tasks:
   - List tasks for today, this week, or a specific date
   - Create new tasks with title, description, due date, priority, and estimated duration
   - Update task status (pending, in_progress, completed)
   - Update task priority (high, medium, low)
   - Delete tasks
   - Get task details and suggestions

2. View and manage schedule:
   - Show daily schedule with tasks and breaks
   - Show weekly schedule
   - Suggest optimal task scheduling based on priorities and study times
   - Help plan ahead for upcoming deadlines

3. Provide productivity insights:
   - Analyze task completion patterns
   - Suggest improvements to schedule
   - Help break down large tasks
   - Provide study and productivity tips

Always be concise, helpful, and proactive in suggesting improvements to the user's productivity.

When you show the user's tasks, always use a clean, numbered list. For each task, show:
- Title
- Subject
- Due date (in local time)
- Status (pending, in progress, completed)
`;

export class ChatService {
  private async getTaskContext(req: AuthenticatedRequest): Promise<{ tasks: Task[], schedule: ScheduleBlock[] }> {
    if (!supabase) {
      throw new Error("Supabase is not configured");
    }

    const userId = req.user?.id;
    if (!userId) {
      throw new Error("User not authenticated");
    }

    try {
      // Fetch tasks
      const { data: tasks, error: tasksError } = await supabase
        .from('tasks')
        .select('*')
        .eq('user_id', userId)
        .order('due_date', { ascending: true });

      if (tasksError) {
        throw new Error(`Failed to fetch tasks: ${tasksError.message}`);
      }

      // Fetch schedule blocks
      const { data: scheduleBlocks, error: scheduleError } = await supabase
        .from('schedule_blocks')
        .select('*')
        .eq('user_id', userId)
        .order('start_time', { ascending: true });

      if (scheduleError) {
        throw new Error(`Failed to fetch schedule blocks: ${scheduleError.message}`);
      }

      return {
        tasks: tasks || [],
        schedule: scheduleBlocks || []
      };
    } catch (error) {
      console.error('Error fetching task context:', error);
      throw error;
    }
  }

  async getChatResponse(req: AuthenticatedRequest, messages: { role: 'user' | 'assistant' | 'system', content: string }[]) {
    try {
      // Get current task and schedule context
      const { tasks, schedule } = await this.getTaskContext(req);

      // Format tasks as a clean, numbered list
      const formattedTasks = tasks.length > 0
        ? tasks.map((task, i) =>
            `${i + 1}. ${task.title} (${task.subject}) - Due: ${new Date(task.due_date).toLocaleString()} [${task.status}]`
          ).join('\n')
        : 'No tasks found.';

      const contextMessage = {
        role: 'system' as const,
        content: `${SYSTEM_PROMPT}\n\nCurrent Context:\nTasks:\n${formattedTasks}\n\nSchedule: ${JSON.stringify(schedule)}`
      };

      // Debug log: print the context message being sent to OpenAI
      console.log('Sending context to OpenAI:', JSON.stringify(contextMessage, null, 2));

      const response = await openai.chat.completions.create({
        model: "gpt-4-turbo-preview",
        messages: [contextMessage, ...messages],
        temperature: 0.7,
        max_tokens: 500,
      });

      const content = response.choices[0]?.message?.content;
      if (!content) {
        throw new Error('No response from OpenAI');
      }

      return {
        content,
        usage: response.usage
      };
    } catch (error) {
      console.error('Error in chat service:', error);
      throw error;
    }
  }
}

export const chatService = new ChatService(); 