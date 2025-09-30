import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Task } from '../types'
import { useWebSocket } from './WebSocketContext'

// Global function to add task success messages to chat
let globalAddTaskSuccessMessage: ((task: Task) => void) | null = null

// Global function to add conversational responses to chat
let globalAddConversationalMessage: ((message: string, metadata?: any) => void) | null = null

// Global function to add simple success cards to chat
let globalAddSimpleSuccessCard: ((operation: string, entityType: string, entityTitle: string, card: any, acknowledgementMessage?: string) => void) | null = null

// Global function to add search results to chat
let globalAddSearchResults: ((searchData: any) => void) | null = null

// Global function to update existing task
let globalUpdateTask: ((taskId: string, updates: any) => void) | null = null

export const setGlobalAddTaskSuccessMessage = (fn: (task: Task) => void) => {
  globalAddTaskSuccessMessage = fn
}

export const setGlobalAddConversationalMessage = (fn: (message: string, metadata?: any) => void) => {
  globalAddConversationalMessage = fn
}

export const setGlobalAddSimpleSuccessCard = (fn: (operation: string, entityType: string, entityTitle: string, card: any, acknowledgementMessage?: string) => void) => {
  globalAddSimpleSuccessCard = fn
}

export const setGlobalAddSearchResults = (fn: (searchData: any) => void) => {
  globalAddSearchResults = fn
}

export const setGlobalUpdateTask = (fn: (taskId: string, updates: any) => void) => {
  globalUpdateTask = fn
}

interface TaskSuccessContextType {
  showSuccessCard: boolean
  successTask: Task | null
  showTaskSuccess: (task: Task) => void
  hideTaskSuccess: () => void
  showDeleteCard: boolean
  deletedTask: Task | null
  showTaskDelete: (task: Task) => void
  hideTaskDelete: () => void
}

const TaskSuccessContext = createContext<TaskSuccessContextType | undefined>(undefined)

interface TaskSuccessProviderProps {
  children: ReactNode
}

export function TaskSuccessProvider({ children }: TaskSuccessProviderProps) {
  const [showSuccessCard, setShowSuccessCard] = useState(false)
  const [successTask, setSuccessTask] = useState<Task | null>(null)
  const [showDeleteCard, setShowDeleteCard] = useState(false)
  const [deletedTask, setDeletedTask] = useState<Task | null>(null)
  const { socket, isConnected } = useWebSocket()
  const queryClient = useQueryClient()

  // Listen for real-time task creation events from WebSocket
  useEffect(() => {
    if (!socket || !isConnected) {
      return
    }

    // Listen for task creation events
    socket.on('task_created', (data: any) => {

      // Handle data from emit_to_user (wrapped) vs direct emission
      let task = null
      if (data.task) {
        // Direct task data
        task = data.task
      } else if (data.data && data.data.task) {
        // Task in data.data.task
        task = data.data.task
      } else if (data.data && data.data.created_item && data.data.created_item.task) {
        // From emit_to_user with nested structure
        task = data.data.created_item.task
      } else if (data.data && data.data.created_item) {
        // From emit_to_user structure
        task = data.data.created_item
      }

      if (task) {
        // Invalidate tasks cache to refresh the UI
        queryClient.invalidateQueries({ queryKey: ['tasks'] })
        
        // For search tasks, show the task card with a small delay to ensure clean display
        if (task.workflow_type === 'search') {
          setTimeout(() => {
            showTaskSuccess(task)
          }, 100) // Small delay to ensure thinking indicator is cleared
        } else {
          // Don't show task card for simple CRUD operations
          // They will be handled by the crud_success event
        }
      }
    })

    socket.on('workflow_completion', (data: any) => {




      // Handle workflow completion events if they contain task data
      if (data.result?.data?.task) {


        // Invalidate tasks cache to refresh the UI
        queryClient.invalidateQueries({ queryKey: ['tasks'] })

        showTaskSuccess(data.result.data.task)
      } else if (data.result?.result?.search_data) {

        
        if (globalAddSearchResults) {
          globalAddSearchResults(data.result.result.search_data)
        } else {

        }
      } else if (data.result?.search_data) {

        
        if (globalAddSearchResults) {
          globalAddSearchResults(data.result.search_data)
        } else {

        }
      } else {

      }
    })

    // Listen for task completion events
    socket.on('task_completed', (data: any) => {








      
      // Test if search data exists
      const searchData = data.data?.task?.result?.search_data


      
      // Handle search results from task completion
      if (data.data?.task?.result?.search_data) {

        
        // Update the existing search task with results
        const updatedTask = data.data.task
        if (globalAddSearchResults) {
          globalAddSearchResults(data.data.task.result.search_data)
        } else {

        }
        
        // Update the existing task card instead of creating a new one
        if (globalUpdateTask) {
          globalUpdateTask(updatedTask.id, updatedTask)
        } else {

        }
      } else if (data.data?.result?.search_data) {

        
        if (globalAddSearchResults) {
          globalAddSearchResults(data.data.result.search_data)
        } else {

        }
      } else if (data.data?.search_data) {

        
        if (globalAddSearchResults) {
          globalAddSearchResults(data.data.search_data)
        } else {

        }
      } else if (data.result?.search_data) {

        
        if (globalAddSearchResults) {
          globalAddSearchResults(data.result.search_data)
        } else {

        }
      } else {

      }
    })

    // Subscribe to workflow updates - listen for any workflow events
    socket.on('workflow_update', (data: any) => {


      if (data.event_type === 'task_created') {


        // Invalidate tasks cache to refresh the UI
        queryClient.invalidateQueries({ queryKey: ['tasks'] })

        // Show success card if task data is available
        if (data.data?.task) {
          showTaskSuccess(data.data.task)
        }
      }
    })

    // Listen for task deletion events
    socket.on('task_deleted', (data: any) => {


      // Handle different data structures from different emission sources
      let task = null
      if (data.data && data.data.deleted_item && data.data.deleted_item.task) {
        // From emit_to_user wrapper structure with nested task (most specific first)
        task = data.data.deleted_item.task

      } else if (data.task) {
        // Direct task data (from workflow_update events)
        task = data.task

      } else if (data.deleted_item && data.deleted_item.task) {
        // Direct deleted_item structure with nested task
        task = data.deleted_item.task

      } else if (data.data && data.data.task) {
        // Another possible structure
        task = data.data.task

      } else if (data.data && data.data.deleted_item) {
        // From emit_to_user wrapper structure (fallback)
        task = data.data.deleted_item

      } else if (data.deleted_item) {
        // Direct deleted_item structure (fallback)
        task = data.deleted_item

      }






      if (task && task.id && task.title) {
        // Validate required fields exist

        // Invalidate tasks cache to refresh the UI
        queryClient.invalidateQueries({ queryKey: ['tasks'] })
        showTaskDelete(task)
      } else {


      }
    })

    // Listen for CRUD success events (task listing, etc.)
    socket.on('crud_success', (data: any) => {


      // Handle different data structures
      let card = null
      if (data.data && data.data.card) {
        card = data.data.card
      } else if (data.card) {
        card = data.card
      }

      if (card) {

        
        // Handle task listing success
        if (card.operation === 'listed' && card.entity_type === 'tasks') {
          const taskCount = card.details?.task_count || 0
          const tasks = card.details?.tasks || []
          

          
          // Add conversational message about the task listing
          if (globalAddConversationalMessage) {
            let message = ''
            if (taskCount === 0) {
              message = "You don't have any tasks matching those criteria."
            } else if (taskCount === 1) {
              message = `Here's your task: ${tasks[0]?.title || 'Untitled'}`
            } else {
              message = `Here are your ${taskCount} tasks:`
            }
            
            globalAddConversationalMessage(message, {
              operation: 'listed',
              entity_type: 'tasks',
              task_count: taskCount,
              tasks: tasks,
              card: card
            })
          } else {

          }
        }
        // Handle other CRUD operations (delete, update, etc.)
        else {

          
          if (globalAddSimpleSuccessCard) {
            globalAddSimpleSuccessCard(
              card.operation,
              card.entity_type,
              card.entity_title,
              card,
              card.acknowledgement_message
            )
          } else {

          }
        }
      } else {

      }
    })

    // Add a catch-all listener to see what other events we might be missing
    socket.onAny((eventName, ...args) => {
      if (eventName.includes('task') || eventName.includes('workflow') || eventName.includes('crud')) {
      }
    })

    // Listen for conversational responses (multiple tasks found, no tasks found, etc.)
    socket.on('conversational_response', (data: any) => {

      
      // Extract the actual data from the WebSocket wrapper
      const responseData = data.data || data

      
      // Add the conversational response to chat as a regular message
      if (globalAddConversationalMessage) {
        globalAddConversationalMessage(responseData.message, {
          can_retry: responseData.can_retry,
          retry_suggestion: responseData.retry_suggestion,
          found_tasks: responseData.found_tasks,
          task_options: responseData.task_options,
          operation: responseData.operation,
          entity_type: responseData.entity_type,
          original_query: responseData.original_query,
          workflow_context: responseData.workflow_context
        })
      } else {

      }
    })

    // Listen for CRUD failure events
    socket.on('crud_failure', (data: any) => {


      // Handle different data structures
      let card = null
      if (data.data && data.data.card) {
        card = data.data.card
      } else if (data.card) {
        card = data.card
      }

      if (card) {

        
        // Add conversational message about the failure
        if (globalAddConversationalMessage) {
          let message = ''
          
          // Determine the operation type from the card details or operation field
          const operationType = card.details?.operation || card.operation
          
          if (operationType === 'failed' || operationType === 'create' || operationType === 'created') {
            message = `Failed to create "${card.entity_title}". Please try again.`
          } else if (operationType === 'update' || operationType === 'updated') {
            message = `Failed to update "${card.entity_title}". Please try again.`
          } else if (operationType === 'delete' || operationType === 'deleted') {
            message = `Failed to delete "${card.entity_title}". Please try again.`
          } else {
            // Fallback for unknown operations
            message = `Failed to ${operationType} "${card.entity_title}". Please try again.`
          }
          
          globalAddConversationalMessage(message)
        } else {

        }
      }
    })

    return () => {
      socket.off('task_created')
      socket.off('task_deleted')
      socket.off('crud_success')
      socket.off('crud_failure')
      socket.off('workflow_completion')
      socket.off('task_completed')
      socket.off('workflow_update')
      socket.off('conversational_response')
      socket.offAny()
    }
  }, [socket, isConnected])

  const showTaskSuccess = (task: Task) => {


    if (globalAddTaskSuccessMessage) {

      globalAddTaskSuccessMessage(task)
    } else {

      setSuccessTask(task)
      setShowSuccessCard(true)
    }
  }

  const hideTaskSuccess = () => {
    setShowSuccessCard(false)
    setSuccessTask(null)
  }

  const showTaskDelete = (task: Task) => {

    setDeletedTask(task)
    setShowDeleteCard(true)
    
    // Card will persist until manually closed
  }

  const hideTaskDelete = () => {
    setShowDeleteCard(false)
    setDeletedTask(null)
  }

  return (
    <TaskSuccessContext.Provider
      value={{
        showSuccessCard,
        successTask,
        showTaskSuccess,
        hideTaskSuccess,
        showDeleteCard,
        deletedTask,
        showTaskDelete,
        hideTaskDelete,
      }}
    >
      {children}
    </TaskSuccessContext.Provider>
  )
}

export function useTaskSuccess() {
  const context = useContext(TaskSuccessContext)
  if (context === undefined) {
    throw new Error('useTaskSuccess must be used within a TaskSuccessProvider')
  }
  return context
}
