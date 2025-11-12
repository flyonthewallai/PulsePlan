import { useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksAPI } from '@/lib/api/sdk'
import { toast } from '@/lib/toast'
import { useTaskSuccess } from '@/contexts/TaskSuccessContext'
import { addPendingTaskMutation, removePendingTaskMutation } from './useTaskUpdates'
import type { Task, CreateTaskData } from '@/types'

export function useTaskMutations() {
  const queryClient = useQueryClient()
  const { showTaskSuccess } = useTaskSuccess()

  // Create task mutation with optimistic updates
  const createTask = useMutation({
    mutationFn: async (data: CreateTaskData) => {
      const result = await tasksAPI.createTask(data)
      if (result.error) throw new Error(result.error)
      return result.data
    },
    onMutate: async (newTask) => {
      await queryClient.cancelQueries({ queryKey: ['tasks'] })
      
      const previousTasks = queryClient.getQueryData(['tasks'])
      
      const optimisticTask: Task = {
        id: `temp-${Date.now()}`,
        ...newTask,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      
      queryClient.setQueryData(['tasks'], (old: Task[] | undefined) => 
        old ? [...old, optimisticTask] : [optimisticTask]
      )
      
      return { previousTasks }
    },
    onSuccess: (newTask) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('Task created successfully')
      
      // Show success card with the created task
      if (newTask) {
        showTaskSuccess(newTask)
      }
    },
    onError: (error, newTask, context) => {
      if (context?.previousTasks) {
        queryClient.setQueryData(['tasks'], context.previousTasks)
      }
      toast.error('Failed to create task', error instanceof Error ? error.message : 'Please try again')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // Update task mutation with optimistic updates
  const updateTask = useMutation({
    mutationFn: async ({ taskId, updates }: { taskId: string; updates: Partial<Task> }) => {
      const result = await tasksAPI.updateTask(taskId, updates)
      if (result.error) throw new Error(result.error)
      return result.data
    },
    onMutate: async ({ taskId, updates }) => {
      // Mark this task as having a pending mutation to prevent real-time updates
      addPendingTaskMutation(taskId)
      
      await queryClient.cancelQueries({ queryKey: ['tasks'] })
      
      const previousTasks = queryClient.getQueryData(['tasks'])
      
      queryClient.setQueryData(['tasks'], (old: Task[] | undefined) => 
        old ? old.map(task => 
          task.id === taskId 
            ? { ...task, ...updates, updated_at: new Date().toISOString() }
            : task
        ) : []
      )
      
      return { previousTasks }
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      
      // Different success messages based on what was updated
      if (variables.updates.status === 'completed') {
        toast.success('Task completed! 🎉')
      } else if (variables.updates.status === 'in_progress') {
        toast.success('Task started')
      } else if (variables.updates.due_date) {
        toast.success('Task rescheduled successfully')
      } else {
        toast.success('Task updated successfully')
      }
    },
    onError: (error, variables, context) => {
      // Remove pending mutation tracking on error
      removePendingTaskMutation(variables.taskId)
      
      if (context?.previousTasks) {
        queryClient.setQueryData(['tasks'], context.previousTasks)
      }
      toast.error('Failed to update task', error instanceof Error ? error.message : 'Please try again')
    },
    onSettled: (data, error, variables) => {
      // Remove pending mutation tracking when mutation completes
      removePendingTaskMutation(variables.taskId)
      
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // Delete task mutation with optimistic updates
  const deleteTask = useMutation({
    mutationFn: async (taskId: string) => {
      const result = await tasksAPI.deleteTask(taskId)
      if (result.error) throw new Error(result.error)
      return result.data
    },
    onMutate: async (taskId) => {
      await queryClient.cancelQueries({ queryKey: ['tasks'] })
      
      const previousTasks = queryClient.getQueryData(['tasks'])
      
      queryClient.setQueryData(['tasks'], (old: Task[] | undefined) => 
        old ? old.filter(task => task.id !== taskId) : []
      )
      
      return { previousTasks }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('Task deleted successfully')
    },
    onError: (error, taskId, context) => {
      if (context?.previousTasks) {
        queryClient.setQueryData(['tasks'], context.previousTasks)
      }
      toast.error('Failed to delete task', error instanceof Error ? error.message : 'Please try again')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // Toggle task status (common operation)
  const toggleTaskStatus = useMutation({
    mutationFn: async (task: Task) => {
      const newStatus = task.status === 'completed' ? 'pending' : 'completed'
      const result = await tasksAPI.updateTask(task.id, { status: newStatus })
      if (result.error) throw new Error(result.error)
      return result.data
    },
    onMutate: async (task) => {
      // Mark this task as having a pending mutation to prevent real-time updates
      addPendingTaskMutation(task.id)
      
      await queryClient.cancelQueries({ queryKey: ['tasks'] })
      
      const previousTasks = queryClient.getQueryData(['tasks'])
      const newStatus = task.status === 'completed' ? 'pending' : 'completed'
      
      queryClient.setQueryData(['tasks'], (old: Task[] | undefined) => 
        old ? old.map(t => 
          t.id === task.id 
            ? { ...t, status: newStatus, updated_at: new Date().toISOString() }
            : t
        ) : []
      )
      
      return { previousTasks, newStatus }
    },
    onSuccess: (data, task, context) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      
      if (context?.newStatus === 'completed') {
        toast.success('Task completed! 🎉')
      } else {
        toast.success('Task marked as pending')
      }
    },
    onError: (error, task, context) => {
      // Remove pending mutation tracking on error
      removePendingTaskMutation(task.id)
      
      if (context?.previousTasks) {
        queryClient.setQueryData(['tasks'], context.previousTasks)
      }
      toast.error('Failed to update task status', error instanceof Error ? error.message : 'Please try again')
    },
    onSettled: (data, error, task) => {
      // Remove pending mutation tracking when mutation completes
      removePendingTaskMutation(task.id)
      
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  return {
    createTask,
    updateTask,
    deleteTask,
    toggleTaskStatus,
  }
}