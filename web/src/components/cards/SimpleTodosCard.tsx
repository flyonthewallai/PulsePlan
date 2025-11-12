import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { X, Loader2, List } from 'lucide-react'
import { useTodos, useToggleTodo } from '@/hooks/todos'
import { TODO_CACHE_KEYS } from '@/hooks/shared'
import { useTodoUpdates, pendingTodoMutations } from '@/hooks/todos'
import { useQueryClient } from '@tanstack/react-query'
import type { Todo } from '../../services/tasks'
import { useTodoFiltering } from './hooks/useTodoFiltering'
import { TodoListItem } from './TodoListItem'
import { SimpleTodosCardModal } from './SimpleTodosCardModal'

type TodoTimeFilter = 'all' | 'due_soon'

export function SimpleTodosCard() {
  const [showModal, setShowModal] = useState(false)
  const [timeFilter, setTimeFilter] = useState<TodoTimeFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [localTodoStates, setLocalTodoStates] = useState<Record<string, boolean>>({})

  // Enable real-time todo updates
  useTodoUpdates()
  
  const queryClient = useQueryClient()
  const { data: todosResponse, isLoading, error } = useTodos()
  const toggleTodo = useToggleTodo()

  // Prefetch todos data on component mount
  useEffect(() => {
    queryClient.prefetchQuery({
      queryKey: TODO_CACHE_KEYS.TODOS,
      queryFn: () => queryClient.getQueryData(TODO_CACHE_KEYS.TODOS) || todosResponse,
      staleTime: 5 * 60 * 1000,
    })
  }, [queryClient, todosResponse])

  // Extract todos from response
  const allTodos = (todosResponse as any)?.data || []

  // Helper function to get effective completed state
  const getEffectiveCompletedState = useCallback((todo: Todo) => {
    return localTodoStates.hasOwnProperty(todo.id) ? localTodoStates[todo.id] : todo.completed
  }, [localTodoStates])

  // Use filtering hook
  const { allTodosFiltered, undatedTodos } = useTodoFiltering({
    todos: allTodos,
    timeFilter,
    searchQuery,
    getEffectiveCompletedState,
  })

  // Card todos - always show all todos regardless of filter
  const cardTodos = useMemo(() => {
    let cardTodosList = allTodos

    // Apply search filter if there's a search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim()
      cardTodosList = cardTodosList.filter((todo: Todo) =>
        todo.title.toLowerCase().includes(query) ||
        todo.description?.toLowerCase().includes(query) ||
        todo.tags?.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // Sort todos for card display
    const sorted = cardTodosList.sort((a: Todo, b: Todo) => {
      const aCompleted = getEffectiveCompletedState(a)
      const bCompleted = getEffectiveCompletedState(b)
      
      // Incomplete todos first
      if (aCompleted !== bCompleted) {
        return aCompleted ? 1 : -1
      }
      
      // Then by due date
      const aDate = a.due_date ? new Date(a.due_date) : null
      const bDate = b.due_date ? new Date(b.due_date) : null
      
      if (!aDate && !bDate) {
        return a.title.localeCompare(b.title)
      }
      if (!aDate) return 1
      if (!bDate) return -1
      
      return aDate.getTime() - bDate.getTime()
    })

    return sorted
  }, [allTodos, searchQuery, getEffectiveCompletedState])

  // Toggle handler
  const handleToggleTodo = useCallback((todoId: string) => {
    setLocalTodoStates(prev => {
      const currentTodo = allTodos.find((todo: Todo) => todo.id === todoId)
      if (!currentTodo) return prev

      const currentState = prev[todoId] ?? currentTodo.completed
      return { ...prev, [todoId]: !currentState }
    })

    toggleTodo.mutate(todoId)
  }, [allTodos, toggleTodo])

  // Clean up local states when todos data changes
  useEffect(() => {
    if (allTodos.length > 0) {
      setLocalTodoStates(prev => {
        const newStates: Record<string, boolean> = {}
        Object.keys(prev).forEach(todoId => {
          const todo = allTodos.find((t: Todo) => t.id === todoId)
          if (todo) {
            const hasPendingMutation = pendingTodoMutations.has(todoId)
            if (hasPendingMutation || prev[todoId] !== todo.completed) {
              newStates[todoId] = prev[todoId]
            }
          }
        })
        return newStates
      })
    }
  }, [allTodos])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showModal) {
        setShowModal(false)
      }
    }
    
    if (showModal) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [showModal])

  // Helper functions
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  return (
    <>
      <div 
        className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 cursor-pointer hover:bg-neutral-800/60 transition-colors h-full flex flex-col"
        onClick={() => setShowModal(true)}
      >
        <div className="flex items-center justify-between mb-4 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            TO-DOS
          </span>
          <div className="w-4 h-4 flex items-center justify-center">
            <List size={16} className="text-gray-400" />
          </div>
        </div>
        
        <div className="space-y-2.5 flex-1 flex flex-col">
          {isLoading ? (
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-4 h-4 rounded-full border-2 border-gray-500 flex items-center justify-center mt-0.5">
                  <Loader2 size={10} className="text-gray-400 animate-spin" />
                </div>
                <div className="flex-1">
                  <span className="text-sm font-medium text-gray-400">
                    Loading to-dos...
                  </span>
                  <div className="text-xs text-gray-500 mt-1">
                    Please wait
                  </div>
                </div>
              </div>
            </div>
          ) : error ? (
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-4 h-4 rounded-full border-2 border-red-500 flex items-center justify-center mt-0.5">
                  <X size={10} className="text-red-400" />
                </div>
                <div className="flex-1">
                  <span className="text-sm font-medium text-red-400">
                    Error loading to-dos
                  </span>
                  <div className="text-xs text-gray-500 mt-1">
                    {error instanceof Error ? error.message : 'Failed to load to-dos'}
                  </div>
                </div>
              </div>
            </div>
          ) : cardTodos.length > 0 ? (
            <div className="space-y-1.5">
              {cardTodos.slice(0, 4).map((todo: Todo) => (
                <TodoListItem
                  key={todo.id}
                  todo={todo}
                  isCompleted={getEffectiveCompletedState(todo)}
                  onToggle={handleToggleTodo}
                  variant="card"
                  formatDate={formatDate}
                  formatTime={formatTime}
                />
              ))}
              {cardTodos.length > 4 && (
                <div className="text-xs text-gray-500 pt-1 text-right">
                  +{cardTodos.length - 4} more
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-4 h-4 rounded-full border-2 border-gray-500 flex items-center justify-center mt-0.5">
                  <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                </div>
                <div className="flex-1 mt-0.5">
                  <span className="text-sm font-medium text-gray-400">
                    No to-dos {timeFilter === 'all' ? 'found' : 'due soon'}
                  </span>
                  <div className="text-xs text-gray-500 mt-1">
                    All caught up!
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <SimpleTodosCardModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        timeFilter={timeFilter}
        onFilterChange={setTimeFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        currentTodos={allTodosFiltered}
        undatedTodos={undatedTodos}
        isLoading={isLoading}
        error={error}
        onToggleTodo={handleToggleTodo}
        getEffectiveCompletedState={getEffectiveCompletedState}
        formatDate={formatDate}
        formatTime={formatTime}
      />
    </>
  )
}
