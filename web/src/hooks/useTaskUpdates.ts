import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '../contexts/WebSocketContext'
import { TASK_CACHE_KEYS, TODO_CACHE_KEYS } from './cacheKeys'
import { supabaseClient } from '../lib/supabaseClient'
import { pendingTodoMutations } from './useTodoUpdates'

// Track pending task mutations to prevent race conditions
export const pendingTaskMutations = new Set<string>()

export const addPendingTaskMutation = (taskId: string) => {
  pendingTaskMutations.add(taskId)
}

export const removePendingTaskMutation = (taskId: string) => {
  pendingTaskMutations.delete(taskId)
}

export const useTaskUpdates = () => {
  const queryClient = useQueryClient()
  const { socket, isConnected } = useWebSocket()
  
  useEffect(() => {
    // Set up Supabase real-time subscription for tasks
    const channel = supabaseClient
      .channel('tasks-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'tasks'
        },
        (payload) => {
          // Check if this task has a pending mutation to avoid race conditions
          if (payload.new?.id && pendingTaskMutations.has(payload.new.id)) {
            return
          }
          
          queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
        }
      )
      .subscribe()

    return () => {
      supabaseClient.removeChannel(channel)
    }
  }, [queryClient])
  
  useEffect(() => {
    if (!socket || !isConnected) {
      return
    }
    
    // Listen for task creation events
    const handleTaskCreated = (data: any) => {
      // Extract task/todo from various possible data structures
      let task = null
      if (data.task) {
        task = data.task
      } else if (data.data?.task) {
        task = data.data.task
      } else if (data.data?.created_item?.task) {
        task = data.data.created_item.task
      } else if (data.data?.created_item) {
        task = data.data.created_item
      } else if (data.data && data.data.id) {
        // Direct task/todo data in data.data (agent-created items)
        task = data.data
      }
      
      if (!task) {
        return
      }
      
      // Handle todos
      if (task.type === 'todo') {
        // Invalidate and immediately refetch to ensure UI updates
        queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        queryClient.refetchQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        return
      }
      
      // Handle tasks
      queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
    }
    
    // Listen for task update events
    const handleTaskUpdated = (data: any) => {
      // Extract task/todo from various possible data structures
      let task = null
      if (data.task) {
        task = data.task
      } else if (data.data?.task) {
        task = data.data.task
      } else if (data.data?.updated_item?.task) {
        task = data.data.updated_item.task
      } else if (data.data?.updated_item) {
        task = data.data.updated_item
      } else if (data.data && typeof data.data === 'object' && data.data.id) {
        // The task/todo data might be directly in data.data
        task = data.data
      }
      
      if (!task) {
        return
      }
      
      // Handle todos
      if (task.type === 'todo') {
        if (pendingTodoMutations.has(task.id)) {
          return
        }
        queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        queryClient.refetchQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        return
      }
      
      // Handle tasks
      if (task.id && pendingTaskMutations.has(task.id)) {
        return
      }
      queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
    }
    
    // Listen for task deletion events
    const handleTaskDeleted = (data: any) => {
      
      // Extract task/todo from various possible data structures
      let task = null
      if (data.task) {
        task = data.task
      } else if (data.data?.task) {
        task = data.data.task
      } else if (data.data?.deleted_item?.task) {
        task = data.data.deleted_item.task
      } else if (data.data?.deleted_item) {
        task = data.data.deleted_item
      } else if (data.data && data.data.id) {
        // Direct task/todo data in data.data (agent-deleted items)
        task = data.data
      }
      
      if (!task) {
        return
      }
      
      // Handle todos
      if (task.type === 'todo') {
        queryClient.invalidateQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        queryClient.refetchQueries({ queryKey: TODO_CACHE_KEYS.TODOS })
        return
      }
      
      // Handle tasks
      queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
    }
    
    // Listen for Canvas sync completion
    const handleCanvasSync = (data: any) => {
      queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
    }
    
    // Listen for workflow completion that might affect tasks
    const handleWorkflowCompletion = (data: any) => {
      // Check if workflow completion includes task data
      if (data.result?.data?.task || data.result?.task) {
        queryClient.invalidateQueries({ queryKey: TASK_CACHE_KEYS.TASKS })
      }
    }
    
    // Register event listeners
    socket.on('task_created', handleTaskCreated)
    socket.on('task_updated', handleTaskUpdated)
    socket.on('task_deleted', handleTaskDeleted)
    socket.on('canvas_sync_completed', handleCanvasSync)
    socket.on('workflow_completion', handleWorkflowCompletion)
    
    // Cleanup function
    return () => {
      socket.off('task_created', handleTaskCreated)
      socket.off('task_updated', handleTaskUpdated)
      socket.off('task_deleted', handleTaskDeleted)
      socket.off('canvas_sync_completed', handleCanvasSync)
      socket.off('workflow_completion', handleWorkflowCompletion)
    }
  }, [socket, isConnected, queryClient])
}
