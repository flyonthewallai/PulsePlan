import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import type { CalendarEvent, Task, CreateTaskData } from '@/types';
import { api } from '@/lib/api/sdk';
import { colors } from '@/lib/utils/constants';

// Query keys factory for better cache management
export const calendarQueryKeys = {
  all: ['calendar'] as const,
  events: () => [...calendarQueryKeys.all, 'events'] as const,
  eventsByDateRange: (startDate: string, endDate: string) =>
    [...calendarQueryKeys.events(), { startDate, endDate }] as const,
  tasks: () => [...calendarQueryKeys.all, 'tasks'] as const,
  tasksByDateRange: (startDate: string, endDate: string) =>
    [...calendarQueryKeys.tasks(), { startDate, endDate }] as const,
};

// Convert Task to CalendarEvent
const taskToCalendarEvent = (task: Task): CalendarEvent => {
  // Ensure consistent date parsing - parse ISO string to Date
  const startDate = new Date(task.dueDate);
  const durationMs = (task.estimatedDuration || 60) * 60 * 1000;
  const endDate = new Date(startDate.getTime() + durationMs);

  return {
    id: task.id,
    title: task.title,
    description: task.description,
    start: startDate.toISOString(),
    end: endDate.toISOString(),
    task,
    priority: task.priority,
    color: colors.taskColors[task.priority] || colors.taskColors.default,
  };
};

// Convert CalendarEvent updates back to Task updates
const calendarEventUpdatesToTask = (updates: Partial<CalendarEvent>): Partial<Task> => {
  const taskUpdates: Partial<Task> = {};

  if (updates.title !== undefined) taskUpdates.title = updates.title;
  if (updates.description !== undefined) taskUpdates.description = updates.description;
  if (updates.start !== undefined) taskUpdates.dueDate = updates.start;
  if (updates.priority !== undefined) taskUpdates.priority = updates.priority;

  // Calculate estimated duration from start/end times
  if (updates.start && updates.end) {
    const duration = Math.round(
      (new Date(updates.end).getTime() - new Date(updates.start).getTime()) / (1000 * 60)
    );
    taskUpdates.estimatedDuration = Math.max(duration, 15); // Minimum 15 minutes
  }

  return taskUpdates;
};

// Hook for fetching calendar events (tasks) for a date range
export function useCalendarEvents(
  startDate: string,
  endDate: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: calendarQueryKeys.tasksByDateRange(startDate, endDate),
    queryFn: async () => {
      const tasks = await api.tasks.list({
        startDate,
        endDate,
      });
      return tasks.map(taskToCalendarEvent);
    },
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
    enabled: options?.enabled ?? true, // Allow conditional fetching
  });
}

// Hook for creating new calendar events
export function useCreateCalendarEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (eventData: { start: string; end: string; title?: string } & Partial<CreateTaskData>) => {
      const duration = Math.round(
        (new Date(eventData.end).getTime() - new Date(eventData.start).getTime()) / (1000 * 60)
      );

      const taskData: CreateTaskData = {
        title: eventData.title || 'New Event',
        description: eventData.description || '',
        dueDate: eventData.start,
        priority: eventData.priority || 'medium',
        status: eventData.status || 'todo',
        estimatedDuration: Math.max(duration, 15),
        tags: eventData.tags || [],
      };

      return await api.tasks.create(taskData);
    },
    onMutate: async (eventData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: calendarQueryKeys.tasks() });

      // Snapshot previous values
      const previousData = queryClient.getQueriesData({ queryKey: calendarQueryKeys.tasks() });

      // Create optimistic event
      const optimisticTask: Task = {
        id: `temp-${Date.now()}`,
        title: eventData.title || 'New Event',
        description: eventData.description || '',
        dueDate: eventData.start,
        priority: eventData.priority || 'medium',
        status: eventData.status || 'todo',
        estimatedDuration: Math.max(
          Math.round((new Date(eventData.end).getTime() - new Date(eventData.start).getTime()) / (1000 * 60)),
          15
        ),
        tags: eventData.tags || [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      const optimisticEvent = taskToCalendarEvent(optimisticTask);

      // Optimistically update all relevant queries
      queryClient.setQueriesData(
        { queryKey: calendarQueryKeys.tasks() },
        (old: CalendarEvent[] | undefined) => {
          return old ? [...old, optimisticEvent] : [optimisticEvent];
        }
      );

      return { previousData, optimisticEvent };
    },
    onSuccess: (newTask, variables, context) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
    onError: (error, variables, context) => {
      // Restore previous state
      if (context?.previousData) {
        context.previousData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
  });
}

// Hook for updating calendar events
export function useUpdateCalendarEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ eventId, updates }: { eventId: string; updates: Partial<CalendarEvent> }) => {
      const taskUpdates = calendarEventUpdatesToTask(updates);
      return await api.tasks.update(eventId, taskUpdates);
    },
    onMutate: async ({ eventId, updates }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: calendarQueryKeys.tasks() });

      // Snapshot previous values
      const previousData = queryClient.getQueriesData({ queryKey: calendarQueryKeys.tasks() });

      // Optimistically update all relevant queries
      queryClient.setQueriesData(
        { queryKey: calendarQueryKeys.tasks() },
        (old: CalendarEvent[] | undefined) => {
          if (!old) return [];
          
          return old.map(event => {
            if (event.id === eventId) {
              const updatedEvent = { ...event, ...updates };
              
              // Update the task object if it exists
              if (event.task && updates.task) {
                updatedEvent.task = { ...event.task, ...updates.task };
              }
              
              return updatedEvent;
            }
            return event;
          });
        }
      );

      return { previousData };
    },
    onSuccess: (updatedTask, variables, context) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
    onError: (error, variables, context) => {
      // Restore previous state
      if (context?.previousData) {
        context.previousData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
  });
}

// Hook for deleting calendar events
export function useDeleteCalendarEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (eventId: string) => {
      return await api.calendar.deleteEvent(eventId);
    },
    onMutate: async (eventId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: calendarQueryKeys.tasks() });

      // Snapshot previous values
      const previousData = queryClient.getQueriesData({ queryKey: calendarQueryKeys.tasks() });

      // Optimistically remove the event
      queryClient.setQueriesData(
        { queryKey: calendarQueryKeys.tasks() },
        (old: CalendarEvent[] | undefined) => {
          return old ? old.filter(event => event.id !== eventId) : [];
        }
      );

      return { previousData };
    },
    onSuccess: (data, eventId, context) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
    onError: (error, eventId, context) => {
      // Restore previous state
      if (context?.previousData) {
        context.previousData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
  });
}

// Hook for duplicating calendar events
export function useDuplicateCalendarEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (event: CalendarEvent) => {
      if (!event.task) {
        throw new Error('Cannot duplicate event without task data');
      }

      // Create new task data based on existing event
      const duplicatedTaskData: CreateTaskData = {
        title: `${event.task.title} (Copy)`,
        description: event.task.description || '',
        dueDate: event.start,
        priority: event.task.priority,
        status: 'todo', // Always start duplicates as todo
        estimatedDuration: event.task.estimatedDuration,
        tags: event.task.tags || [],
      };

      return await api.tasks.create(duplicatedTaskData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
  });
}

// Hook for batch operations
export function useBatchUpdateCalendarEvents() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: Array<{ eventId: string; updates: Partial<CalendarEvent> }>) => {
      const promises = updates.map(({ eventId, updates: eventUpdates }) => {
        const taskUpdates = calendarEventUpdatesToTask(eventUpdates);
        return api.tasks.update(eventId, taskUpdates);
      });
      
      return await Promise.all(promises);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
  });
}

// Utility hook for invalidating calendar data
export function useInvalidateCalendar() {
  const queryClient = useQueryClient();

  return {
    invalidateAll: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.all });
    },
    invalidateEvents: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.events() });
    },
    invalidateTasks: () => {
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.tasks() });
    },
    invalidateDateRange: (startDate: string, endDate: string) => {
      queryClient.invalidateQueries({ 
        queryKey: calendarQueryKeys.tasksByDateRange(startDate, endDate) 
      });
    },
  };
}