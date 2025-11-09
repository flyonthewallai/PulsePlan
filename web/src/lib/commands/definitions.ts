/**
 * Command Registry
 * Centralized registry of all available commands
 */

import type { Command } from '@/lib/commands/types';

export const COMMANDS: Command[] = [
  {
    id: 'todo',
    name: 'todo',
    label: 'Add To-Do',
    description: 'Quickly create a new task',
    icon: 'CheckSquare',
    aliases: ['task', 'add'],
    parameterSchema: [
      {
        name: 'title',
        type: 'string',
        required: true,
        description: 'Task title',
      },
      {
        name: 'due_date',
        type: 'datetime',
        required: false,
        description: 'Due date (e.g., "tomorrow", "next Friday at 5pm")',
      },
      {
        name: 'priority',
        type: 'enum',
        values: ['low', 'medium', 'high'],
        required: false,
        default: 'medium',
        description: 'Task priority',
      },
      {
        name: 'tags',
        type: 'string[]',
        required: false,
        description: 'Tags (e.g., #study, #work)',
      },
    ],
    examples: [
      '/todo Finish essay tomorrow at 5pm',
      '/todo Buy groceries #personal',
      '/todo Study for exam high priority',
    ],
  },
  {
    id: 'schedule',
    name: 'schedule',
    label: 'Schedule Event',
    description: 'Schedule or plan a time block',
    icon: 'Calendar',
    aliases: ['event', 'plan'],
    parameterSchema: [
      {
        name: 'title',
        type: 'string',
        required: true,
        description: 'Event title',
      },
      {
        name: 'start_time',
        type: 'datetime',
        required: true,
        description: 'Start time',
      },
      {
        name: 'duration',
        type: 'number',
        required: false,
        default: 60,
        description: 'Duration in minutes',
      },
      {
        name: 'location',
        type: 'string',
        required: false,
        description: 'Event location',
      },
    ],
    examples: [
      '/schedule Team meeting tomorrow at 2pm',
      '/schedule Study session Friday 3pm for 90 minutes',
      '/schedule Dentist appointment next Tuesday 10am',
    ],
  },
  {
    id: 'reschedule',
    name: 'reschedule',
    label: 'Reschedule',
    description: 'Reschedule existing task or event',
    icon: 'Clock',
    aliases: ['resched', 'move'],
    parameterSchema: [
      {
        name: 'task_identifier',
        type: 'string',
        required: true,
        description: 'Task or event name/ID',
      },
      {
        name: 'new_time',
        type: 'datetime',
        required: true,
        description: 'New date/time',
      },
    ],
    examples: [
      '/reschedule essay to tomorrow',
      '/reschedule team meeting to 3pm',
      '/reschedule study session to next Monday',
    ],
  },
  {
    id: 'focus',
    name: 'focus',
    label: 'Start Focus Session',
    description: 'Start a Pomodoro/focus timer',
    icon: 'Timer',
    aliases: ['pomodoro', 'timer'],
    parameterSchema: [
      {
        name: 'duration',
        type: 'number',
        required: false,
        default: 25,
        description: 'Duration in minutes (default: 25)',
      },
      {
        name: 'task',
        type: 'string',
        required: false,
        description: 'What you\'re focusing on',
      },
    ],
    examples: [
      '/focus',
      '/focus 50 minutes',
      '/focus on essay writing',
    ],
  },
  {
    id: 'briefing',
    name: 'briefing',
    label: 'Daily Briefing',
    description: 'Show today\'s overview',
    icon: 'Newspaper',
    aliases: ['brief', 'today', 'overview'],
    parameterSchema: [],
    examples: [
      '/briefing',
      '/brief',
    ],
  },
  {
    id: 'help',
    name: 'help',
    label: 'Help',
    description: 'List available commands',
    icon: 'HelpCircle',
    aliases: ['commands', '?'],
    parameterSchema: [],
    examples: [
      '/help',
      '/commands',
    ],
  },
];

/**
 * Get command by name or alias
 */
export function getCommand(nameOrAlias: string): Command | undefined {
  const normalized = nameOrAlias.toLowerCase().trim();
  return COMMANDS.find(
    cmd => cmd.name === normalized || cmd.aliases.includes(normalized)
  );
}

/**
 * Get all commands
 */
export function getAllCommands(): Command[] {
  return COMMANDS;
}

/**
 * Fuzzy match command by partial input
 * Returns commands that start with the input
 */
export function matchCommands(partial: string): Command[] {
  const normalized = partial.toLowerCase().trim();
  if (!normalized) return COMMANDS;
  
  return COMMANDS.filter(cmd => {
    const matches = 
      cmd.name.startsWith(normalized) ||
      cmd.aliases.some(alias => alias.startsWith(normalized));
    return matches;
  }).slice(0, 10); // Max 10 suggestions
}

