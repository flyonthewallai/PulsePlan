/**
 * Generates a prompt for the scheduling assistant
 */
export function generateSchedulingPrompt(
  tasks: Array<{
    id: string;
    title: string;
    dueDate: string;
    estimatedMinutes: number;
    subject?: string;
    priority?: string;
  }>,
  openTimeSlots: Array<{
    start: string;
    end: string;
  }>,
  userPreferences?: {
    preferredWorkingHours?: { start: string; end: string };
    breakDuration?: number;
    focusSessionDuration?: number;
  }
) {
  return `
You are an intelligent scheduling assistant that helps students organize their study time efficiently.

## TASKS TO SCHEDULE
${tasks.map(task => 
  `- Task ID: ${task.id}
   Title: ${task.title}
   Due Date: ${task.dueDate}
   Estimated Duration: ${task.estimatedMinutes} minutes
   ${task.subject ? `Subject: ${task.subject}` : ''}
   ${task.priority ? `Priority: ${task.priority}` : ''}`
).join('\n\n')}

## AVAILABLE TIME SLOTS
${openTimeSlots.map(slot => 
  `- ${new Date(slot.start).toLocaleString()} to ${new Date(slot.end).toLocaleString()}`
).join('\n')}

${userPreferences ? `
## USER PREFERENCES
${userPreferences.preferredWorkingHours ? 
  `- Preferred Working Hours: ${userPreferences.preferredWorkingHours.start} to ${userPreferences.preferredWorkingHours.end}` : ''}
${userPreferences.breakDuration ? 
  `- Preferred Break Duration: ${userPreferences.breakDuration} minutes` : ''}
${userPreferences.focusSessionDuration ? 
  `- Preferred Focus Session Duration: ${userPreferences.focusSessionDuration} minutes` : ''}
` : ''}

## INSTRUCTIONS
1. Analyze the tasks and their due dates, estimated durations, and available time slots.
2. Generate an optimal daily schedule for completing these tasks.
3. Prioritize tasks based on due dates and estimated completion time.
4. Allocate appropriate time blocks for each task within the available slots.
5. Include short breaks between tasks when appropriate.
6. Your response MUST include:
   a. A JSON schedule in this format:
   \`\`\`json
   {
     "schedule": [
       {
         "taskId": "task-id-1",
         "title": "Task Title",
         "startTime": "2023-05-15T14:00:00Z",
         "endTime": "2023-05-15T15:30:00Z"
       }
     ]
   }
   \`\`\`
   b. A markdown-formatted explanation of your scheduling logic and recommendations.

## REASONING REQUIREMENTS
- Explain why you scheduled each task at its specific time
- Mention any considerations for task difficulty or priority
- Explain how you've optimized the schedule for productivity
- Provide any additional recommendations for task management
`;
} 