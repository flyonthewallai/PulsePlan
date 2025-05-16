import openai from '../config/openai';
import { generateSchedulingPrompt } from '../utils/promptTemplates';

// Types for the service
export interface Task {
  id: string;
  title: string;
  dueDate: string;
  estimatedMinutes: number;
  subject?: string;
  priority?: string;
}

export interface TimeSlot {
  start: string;
  end: string;
}

export interface UserPreferences {
  preferredWorkingHours?: { start: string; end: string };
  breakDuration?: number;
  focusSessionDuration?: number;
}

export interface ScheduleBlock {
  taskId: string;
  title: string;
  startTime: string;
  endTime: string;
}

export interface SchedulingResult {
  schedule: ScheduleBlock[];
  explanation: string;
  tokenUsage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

// Maximum number of retry attempts
const MAX_RETRIES = 3;

/**
 * Intelligent scheduling service using GPT-4o
 */
export class IntelligentSchedulingService {
  
  /**
   * Generate a schedule for tasks based on available time slots
   */
  public async generateSchedule(
    tasks: Task[],
    openTimeSlots: TimeSlot[],
    userPreferences?: UserPreferences
  ): Promise<SchedulingResult> {
    // Generate the prompt
    const prompt = generateSchedulingPrompt(tasks, openTimeSlots, userPreferences);
    
    // Track retries
    let retries = 0;
    let error: any;
    
    while (retries < MAX_RETRIES) {
      try {
        // Make the API call to OpenAI GPT-4o
        const response = await openai.chat.completions.create({
          model: 'gpt-4o',
          messages: [
            { role: 'system', content: 'You are an AI assistant specialized in creating optimal study schedules for students.' },
            { role: 'user', content: prompt }
          ],
          temperature: 0.2, // Lower temperature for more consistent output
          max_tokens: 2500,
          response_format: { type: 'text' }, // Ensure we get a text response
        });
        
        // Extract token usage
        const tokenUsage = {
          promptTokens: response.usage?.prompt_tokens || 0,
          completionTokens: response.usage?.completion_tokens || 0,
          totalTokens: response.usage?.total_tokens || 0,
        };
        
        // Extract content from the response
        const content = response.choices[0].message.content || '';
        
        // Parse the JSON schedule from the response
        const scheduleMatch = content.match(/```json\s*({[\s\S]*?})\s*```/);
        
        if (!scheduleMatch || !scheduleMatch[1]) {
          throw new Error('Failed to extract JSON schedule from response');
        }
        
        const scheduleJson = JSON.parse(scheduleMatch[1]);
        
        // Extract the explanation (everything outside the JSON code block)
        let explanation = content
          .replace(/```json\s*{[\s\S]*?}\s*```/, '') // Remove JSON block
          .trim();
        
        // Return the schedule and explanation
        return {
          schedule: scheduleJson.schedule,
          explanation,
          tokenUsage,
        };
      } catch (err) {
        error = err;
        console.error(`Attempt ${retries + 1} failed:`, err);
        retries++;
        
        // Wait before retrying (exponential backoff)
        if (retries < MAX_RETRIES) {
          const delay = Math.pow(2, retries) * 1000; // 2^retries * 1000 ms
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    // If we've exhausted all retries, throw the last error
    throw new Error(`Failed to generate schedule after ${MAX_RETRIES} attempts: ${error.message}`);
  }
  
  /**
   * Validate the generated schedule against constraints
   */
  private validateSchedule(schedule: ScheduleBlock[], tasks: Task[], openTimeSlots: TimeSlot[]): boolean {
    // Check if all tasks are scheduled
    const scheduledTaskIds = new Set(schedule.map(block => block.taskId));
    const allTasksScheduled = tasks.every(task => scheduledTaskIds.has(task.id));
    
    // Check if all time blocks are within available time slots
    const allBlocksInTimeSlots = schedule.every(block => {
      const blockStart = new Date(block.startTime).getTime();
      const blockEnd = new Date(block.endTime).getTime();
      
      return openTimeSlots.some(slot => {
        const slotStart = new Date(slot.start).getTime();
        const slotEnd = new Date(slot.end).getTime();
        return blockStart >= slotStart && blockEnd <= slotEnd;
      });
    });
    
    return allTasksScheduled && allBlocksInTimeSlots;
  }
}

export default new IntelligentSchedulingService(); 