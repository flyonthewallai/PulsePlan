import { Request, Response } from 'express';
import intelligentSchedulingService, { Task, TimeSlot, UserPreferences } from '../services/intelligentSchedulingService';

/**
 * Generate an optimized schedule using GPT-4o
 */
export const generateSchedule = async (req: Request, res: Response) => {
  try {
    const { tasks, timeSlots, userPreferences } = req.body;
    
    // Validate request
    if (!tasks || !Array.isArray(tasks) || tasks.length === 0) {
      return res.status(400).json({ error: 'Tasks array is required and must not be empty' });
    }
    
    if (!timeSlots || !Array.isArray(timeSlots) || timeSlots.length === 0) {
      return res.status(400).json({ error: 'Time slots array is required and must not be empty' });
    }
    
    // Validate tasks
    for (const task of tasks) {
      if (!task.id || !task.title || !task.dueDate || !task.estimatedMinutes) {
        return res.status(400).json({ 
          error: 'Each task must have id, title, dueDate, and estimatedMinutes' 
        });
      }
    }
    
    // Validate time slots
    for (const slot of timeSlots) {
      if (!slot.start || !slot.end) {
        return res.status(400).json({ error: 'Each time slot must have start and end times' });
      }
      
      // Check if end time is after start time
      if (new Date(slot.end) <= new Date(slot.start)) {
        return res.status(400).json({ error: 'End time must be after start time for each time slot' });
      }
    }
    
    // Call the scheduling service
    const result = await intelligentSchedulingService.generateSchedule(
      tasks as Task[],
      timeSlots as TimeSlot[],
      userPreferences as UserPreferences
    );
    
    // Return the result
    res.json({
      success: true,
      schedule: result.schedule,
      explanation: result.explanation,
      tokenUsage: result.tokenUsage
    });
  } catch (error: any) {
    console.error('Error generating schedule:', error);
    res.status(500).json({ 
      error: 'Failed to generate schedule',
      message: error.message || 'Unknown error' 
    });
  }
}; 