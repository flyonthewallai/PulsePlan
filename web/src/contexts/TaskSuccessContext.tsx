import { createContext, useContext, useState, useEffect, useRef, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Task } from '../types'
import { useWebSocket } from './WebSocketContext'

// ============================================================================
// TYPE DEFINITIONS - No more 'any' types!
// ============================================================================

interface ConversationalMetadata {
  operation?: string
  entity_type?: string
  task_count?: number
  tasks?: Task[]
  card?: CrudCard
  can_retry?: boolean
  retry_suggestion?: string
  found_tasks?: Task[]
  task_options?: Task[]
  original_query?: string
  workflow_context?: Record<string, unknown>
}

interface SearchData {
  results?: unknown[]
  query?: string
  [key: string]: unknown
}

interface CrudCard {
  operation: string
  entity_type: string
  entity_title: string
  acknowledgement_message?: string
  details?: {
    operation?: string
    task_count?: number
    tasks?: Task[]
    [key: string]: unknown
  }
  [key: string]: unknown
}

interface WebSocketEventData {
  task?: Task
  data?: {
    task?: Task
    created_item?: Task | { task?: Task }
    deleted_item?: Task | { task?: Task }
    card?: CrudCard
    result?: {
      search_data?: SearchData
    }
    search_data?: SearchData
  }
  result?: {
    data?: { task?: Task }
    result?: { search_data?: SearchData }
    search_data?: SearchData
  }
  card?: CrudCard
  deleted_item?: Task | { task?: Task }
  [key: string]: unknown
}

// ============================================================================
// CONTEXT TYPE - Proper React Context pattern instead of globals
// ============================================================================

interface TaskSuccessContextType {
  showSuccessCard: boolean
  successTask: Task | null
  showTaskSuccess: (task: Task) => void
  hideTaskSuccess: () => void
  showDeleteCard: boolean
  deletedTask: Task | null
  showTaskDelete: (task: Task) => void
  hideTaskDelete: () => void
  // Handler registration for chat integration
  registerTaskSuccessHandler: (handler: (task: Task) => void) => void
  registerConversationalHandler: (handler: (message: string, metadata?: ConversationalMetadata) => void) => void
  registerSimpleSuccessHandler: (handler: (operation: string, entityType: string, entityTitle: string, card: CrudCard, acknowledgementMessage?: string) => void) => void
  registerSearchResultsHandler: (handler: (searchData: SearchData) => void) => void
  registerUpdateTaskHandler: (handler: (taskId: string, updates: Partial<Task>) => void) => void
}

const TaskSuccessContext = createContext<TaskSuccessContextType | undefined>(undefined)

// ============================================================================
// PROVIDER COMPONENT
// ============================================================================

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

  // Use refs for handlers instead of module-level globals (proper React pattern)
  const taskSuccessHandlerRef = useRef<((task: Task) => void) | null>(null)
  const conversationalHandlerRef = useRef<((message: string, metadata?: ConversationalMetadata) => void) | null>(null)
  const simpleSuccessHandlerRef = useRef<((operation: string, entityType: string, entityTitle: string, card: CrudCard, acknowledgementMessage?: string) => void) | null>(null)
  const searchResultsHandlerRef = useRef<((searchData: SearchData) => void) | null>(null)
  const updateTaskHandlerRef = useRef<((taskId: string, updates: Partial<Task>) => void) | null>(null)

  // Helper function to extract task from various event structures
  const extractTask = (data: WebSocketEventData): Task | null => {
    if (data.task) return data.task
    if (data.data?.task) return data.data.task
    if (data.data?.created_item) {
      const item = data.data.created_item
      if ('task' in item && item.task) return item.task
      return item as Task
    }
    if (data.data?.deleted_item) {
      const item = data.data.deleted_item
      if ('task' in item && item.task) return item.task
      return item as Task
    }
    if (data.deleted_item) {
      const item = data.deleted_item
      if ('task' in item && item.task) return item.task
      return item as Task
    }
    return null
  }

  // Helper function to extract search data
  const extractSearchData = (data: WebSocketEventData): SearchData | null => {
    if (data.result?.result?.search_data) return data.result.result.search_data
    if (data.result?.search_data) return data.result.search_data
    if (data.data?.result?.search_data) return data.data.result.search_data
    if (data.data?.search_data) return data.data.search_data
    return null
  }

  // Helper function to extract CRUD card
  const extractCard = (data: WebSocketEventData): CrudCard | null => {
    if (data.data?.card) return data.data.card
    if (data.card) return data.card
    return null
  }

  // Listen for real-time task events from WebSocket
  useEffect(() => {
    if (!socket || !isConnected) return

    // Task created event
    socket.on('task_created', (data: WebSocketEventData) => {
      const task = extractTask(data)
      if (task) {
        queryClient.invalidateQueries({ queryKey: ['tasks'] })
        
        // For search tasks, show with a small delay to ensure clean display
        if (task.workflow_type === 'search') {
          setTimeout(() => showTaskSuccess(task), 100)
        }
      }
    })

    // Workflow completion event
    socket.on('workflow_completion', (data: WebSocketEventData) => {
      if (data.result?.data?.task) {
        queryClient.invalidateQueries({ queryKey: ['tasks'] })
        showTaskSuccess(data.result.data.task)
      } else {
        const searchData = extractSearchData(data)
        if (searchData && searchResultsHandlerRef.current) {
          searchResultsHandlerRef.current(searchData)
        }
      }
    })

    // Task completed event
    socket.on('task_completed', (data: WebSocketEventData) => {
      const searchData = extractSearchData(data)
      if (searchData && searchResultsHandlerRef.current) {
        searchResultsHandlerRef.current(searchData)
        
        // Update the existing task if we have the full task data
        if (data.data?.task && updateTaskHandlerRef.current) {
          updateTaskHandlerRef.current(data.data.task.id, data.data.task)
        }
      }
    })

    // Workflow update event
    socket.on('workflow_update', (data: WebSocketEventData & { event_type?: string }) => {
      if (data.event_type === 'task_created' && data.data?.task) {
        queryClient.invalidateQueries({ queryKey: ['tasks'] })
        showTaskSuccess(data.data.task)
      }
    })

    // Task deleted event
    socket.on('task_deleted', (data: WebSocketEventData) => {
      const task = extractTask(data)
      if (task && task.id && task.title) {
        queryClient.invalidateQueries({ queryKey: ['tasks'] })
        showTaskDelete(task)
      }
    })

    // CRUD success event
    socket.on('crud_success', (data: WebSocketEventData) => {
      const card = extractCard(data)
      if (!card) return

      // Handle task listing success
      if (card.operation === 'listed' && card.entity_type === 'tasks') {
        const taskCount = card.details?.task_count || 0
        const tasks = card.details?.tasks || []
        
        if (conversationalHandlerRef.current) {
          let message = ''
          if (taskCount === 0) {
            message = "You don't have any tasks matching those criteria."
          } else if (taskCount === 1) {
            message = `Here's your task: ${tasks[0]?.title || 'Untitled'}`
          } else {
            message = `Here are your ${taskCount} tasks:`
          }
          
          conversationalHandlerRef.current(message, {
            operation: 'listed',
            entity_type: 'tasks',
            task_count: taskCount,
            tasks: tasks,
            card: card
          })
        }
      } else if (simpleSuccessHandlerRef.current) {
        // Handle other CRUD operations
        simpleSuccessHandlerRef.current(
          card.operation,
          card.entity_type,
          card.entity_title,
          card,
          card.acknowledgement_message
        )
      }
    })

    // Conversational response event
    socket.on('conversational_response', (data: WebSocketEventData) => {
      const responseData = data.data || data
      
      if (conversationalHandlerRef.current && 'message' in responseData) {
        conversationalHandlerRef.current(responseData.message as string, {
          can_retry: responseData.can_retry as boolean | undefined,
          retry_suggestion: responseData.retry_suggestion as string | undefined,
          found_tasks: responseData.found_tasks as Task[] | undefined,
          task_options: responseData.task_options as Task[] | undefined,
          operation: responseData.operation as string | undefined,
          entity_type: responseData.entity_type as string | undefined,
          original_query: responseData.original_query as string | undefined,
          workflow_context: responseData.workflow_context as Record<string, unknown> | undefined
        })
      }
    })

    // CRUD failure event
    socket.on('crud_failure', (data: WebSocketEventData) => {
      const card = extractCard(data)
      if (!card || !conversationalHandlerRef.current) return

      const operationType = card.details?.operation || card.operation
      let message = ''
      
      if (['failed', 'create', 'created'].includes(operationType)) {
        message = `Failed to create "${card.entity_title}". Please try again.`
      } else if (['update', 'updated'].includes(operationType)) {
        message = `Failed to update "${card.entity_title}". Please try again.`
      } else if (['delete', 'deleted'].includes(operationType)) {
        message = `Failed to delete "${card.entity_title}". Please try again.`
      } else {
        message = `Failed to ${operationType} "${card.entity_title}". Please try again.`
      }
      
      conversationalHandlerRef.current(message)
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
    }
  }, [socket, isConnected, queryClient])

  const showTaskSuccess = (task: Task) => {
    if (taskSuccessHandlerRef.current) {
      taskSuccessHandlerRef.current(task)
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
  }

  const hideTaskDelete = () => {
    setShowDeleteCard(false)
    setDeletedTask(null)
  }

  // Handler registration methods (proper React pattern)
  const registerTaskSuccessHandler = (handler: (task: Task) => void) => {
    taskSuccessHandlerRef.current = handler
  }

  const registerConversationalHandler = (handler: (message: string, metadata?: ConversationalMetadata) => void) => {
    conversationalHandlerRef.current = handler
  }

  const registerSimpleSuccessHandler = (handler: (operation: string, entityType: string, entityTitle: string, card: CrudCard, acknowledgementMessage?: string) => void) => {
    simpleSuccessHandlerRef.current = handler
  }

  const registerSearchResultsHandler = (handler: (searchData: SearchData) => void) => {
    searchResultsHandlerRef.current = handler
  }

  const registerUpdateTaskHandler = (handler: (taskId: string, updates: Partial<Task>) => void) => {
    updateTaskHandlerRef.current = handler
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
        registerTaskSuccessHandler,
        registerConversationalHandler,
        registerSimpleSuccessHandler,
        registerSearchResultsHandler,
        registerUpdateTaskHandler,
      }}
    >
      {children}
    </TaskSuccessContext.Provider>
  )
}

// ============================================================================
// HOOK
// ============================================================================

export function useTaskSuccess() {
  const context = useContext(TaskSuccessContext)
  if (context === undefined) {
    throw new Error('useTaskSuccess must be used within a TaskSuccessProvider')
  }
  return context
}

// ============================================================================
// LEGACY EXPORTS - For backward compatibility during migration
// ============================================================================

export const setGlobalAddTaskSuccessMessage = (fn: (task: Task) => void) => {
  console.warn('setGlobalAddTaskSuccessMessage is deprecated. Use registerTaskSuccessHandler from useTaskSuccess() instead.')
}

export const setGlobalAddConversationalMessage = (fn: (message: string, metadata?: ConversationalMetadata) => void) => {
  console.warn('setGlobalAddConversationalMessage is deprecated. Use registerConversationalHandler from useTaskSuccess() instead.')
}

export const setGlobalAddSimpleSuccessCard = (fn: (operation: string, entityType: string, entityTitle: string, card: CrudCard, acknowledgementMessage?: string) => void) => {
  console.warn('setGlobalAddSimpleSuccessCard is deprecated. Use registerSimpleSuccessHandler from useTaskSuccess() instead.')
}

export const setGlobalAddSearchResults = (fn: (searchData: SearchData) => void) => {
  console.warn('setGlobalAddSearchResults is deprecated. Use registerSearchResultsHandler from useTaskSuccess() instead.')
}

export const setGlobalUpdateTask = (fn: (taskId: string, updates: Partial<Task>) => void) => {
  console.warn('setGlobalUpdateTask is deprecated. Use registerUpdateTaskHandler from useTaskSuccess() instead.')
}
