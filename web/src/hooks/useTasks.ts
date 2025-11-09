import { useQuery, useMutation, useQueryClient, QueryClient } from '@tanstack/react-query'
import { api } from '../lib/api/sdk'
import type { Task, CreateTaskData } from '../lib/utils/types'
import { addPendingTaskMutation, removePendingTaskMutation } from './useTaskUpdates'
import { TASK_CACHE_KEYS } from './cacheKeys'

// Main tasks query hook
export const useTasks = (params?: {
  startDate?: string;
  endDate?: string;
  status?: Task['status'];
  priority?: Task['priority'];
}) => {
  // Normalize params to ensure consistent query keys
  const normalizedParams = params || undefined
  const queryKey = [...TASK_CACHE_KEYS.TASKS, normalizedParams]

  return useQuery({
    queryKey,
    queryFn: () => api.tasks.list(params),
    staleTime: 1 * 60 * 1000, // 1 minute - reduced from 5 to catch fresh Canvas syncs
    gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)
    refetchOnWindowFocus: true, // Refetch when returning to tab
    refetchOnMount: true, // Always refetch on mount to catch updates
    retry: 2,
  })
}

// Create task mutation
export const useCreateTask = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (taskData: CreateTaskData) => api.tasks.create(taskData),
    onSuccess: () => {
      // Invalidate all task queries
      queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
    },
    onError: (error) => {
      console.error('Failed to create task:', error)
    }
  })
}

// Update task mutation with optimistic updates
export const useUpdateTask = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string, updates: Partial<Task> }) => 
      api.tasks.update(id, updates),
    
    // Optimistic update - update UI immediately
    onMutate: async ({ id, updates }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
      
      // Snapshot the previous value
      const previousTasks = queryClient.getQueryData(TASK_CACHE_KEYS.TASKS)
      
      // Optimistically update the cache
      queryClient.setQueryData(TASK_CACHE_KEYS.TASKS, (old: Task[] | undefined) => {
        if (!old) return old
        return old.map(task => 
          task.id === id 
            ? { ...task, ...updates }
            : task
        )
      })
      
      // Return a context object with the snapshotted value
      return { previousTasks }
    },
    
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, _variables, context) => {
      console.error('Failed to update task:', err)
      if (context?.previousTasks) {
        queryClient.setQueryData(TASK_CACHE_KEYS.TASKS, context.previousTasks)
      }
    },
    
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
    }
  })
}

// Toggle task status mutation (optimized for performance)
export const useToggleTask = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (taskId: string) => {
      // Get task from primary cache key (most common case)
      const primaryTasks = queryClient.getQueryData<Task[]>(TASK_CACHE_KEYS.TASKS)
      let task = primaryTasks?.find(t => t.id === taskId)

      // Fallback: check specific query variation used by component
      if (!task) {
        const componentTasks = queryClient.getQueryData<Task[]>(['tasks', undefined])
        task = componentTasks?.find(t => t.id === taskId)
      }

      if (!task) {
        throw new Error('Task not found')
      }

      const newStatus = task.status === 'completed' ? 'pending' : 'completed'
      return api.tasks.update(taskId, { status: newStatus })
    },
    
    // Lightweight optimistic update
    onMutate: async (taskId) => {
      // Mark this task as having a pending mutation
      addPendingTaskMutation(taskId)

      // Cancel outgoing refetches (async, non-blocking)
      queryClient.cancelQueries({ queryKey: TASK_CACHE_KEYS.TASKS })

      // Only update the primary cache keys for immediate UI response
      const primaryQueryKeys = [TASK_CACHE_KEYS.TASKS, ['tasks', undefined]]
      const previousData = new Map()

      // Update only essential cache keys
      primaryQueryKeys.forEach(queryKey => {
        const previousTasks = queryClient.getQueryData(queryKey)
        if (previousTasks) {
          previousData.set(queryKey, previousTasks)
          queryClient.setQueryData(queryKey, (old: Task[] | undefined) => {
            if (!old) return old
            return old.map(task =>
              task.id === taskId
                ? {
                    ...task,
                    status: task.status === 'completed' ? 'pending' : 'completed' as const
                  }
                : task
            )
          })
        }
      })

      return { previousData }
    },
    
    onError: (err, taskId, context) => {
      console.error('Failed to toggle task:', err)
      // Remove pending mutation tracking on error
      removePendingTaskMutation(taskId)
      
      if (context?.previousData) {
        // Restore all previous query data on error
        for (const [queryKey, previousTasks] of context.previousData) {
          queryClient.setQueryData(queryKey, previousTasks)
        }
      }
    },
    
    onSettled: (_, error, taskId) => {
      // Remove pending mutation tracking
      removePendingTaskMutation(taskId)

      // Refresh cache asynchronously to ensure consistency
      if (!error) {
        // Use invalidation instead of manual cache updates for better performance
        queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
      }
    }
  })
}

// Delete task mutation
export const useDeleteTask = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (taskId: string) => api.tasks.delete(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
    },
    onError: (error) => {
      console.error('Failed to delete task:', error)
    }
  })
}

// Utility function to invalidate all task-related queries
export const invalidateTaskQueries = (queryClient: QueryClient) => {
  queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
}
