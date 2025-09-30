import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { X, Calendar, Clock, Loader2, Check, List, Search } from 'lucide-react'
import { useTodos, useToggleTodo } from '../hooks/useTodos'
import { TODO_CACHE_KEYS } from '../hooks/cacheKeys'
import { useTodoUpdates, pendingTodoMutations } from '../hooks/useTodoUpdates'
import { useQueryClient } from '@tanstack/react-query'
import type { Todo } from '../services/todosService'

export function SimpleTodosCard() {
  const [showModal, setShowModal] = useState(false)
  const [timeFilter, setTimeFilter] = useState<'all' | 'due_soon'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  // Local state for immediate visual feedback
  const [localTodoStates, setLocalTodoStates] = useState<Record<string, boolean>>({})

  const allRef = useRef<HTMLButtonElement>(null);
  const dueSoonRef = useRef<HTMLButtonElement>(null);

  const [highlightStyle, setHighlightStyle] = useState({});

  const tabRefs = {
    all: allRef,
    due_soon: dueSoonRef,
  };

  // Enable real-time todo updates
  useTodoUpdates()
  
  // Use React Query for caching and data fetching
  const queryClient = useQueryClient()
  const { data: todosResponse, isLoading, error, refetch } = useTodos()
  const toggleTodo = useToggleTodo()


  // Prefetch to-dos data on component mount for instant modal opening
  useEffect(() => {
    queryClient.prefetchQuery({
      queryKey: TODO_CACHE_KEYS.TODOS,
      queryFn: () => queryClient.getQueryData(TODO_CACHE_KEYS.TODOS) || todosResponse,
      staleTime: 5 * 60 * 1000,
    })
  }, [queryClient, todosResponse])

  // Update highlight position when filter changes
  useEffect(() => {
    const activeTabRef = tabRefs[timeFilter];
    if (activeTabRef.current) {
      setHighlightStyle({
        left: activeTabRef.current.offsetLeft,
        width: activeTabRef.current.offsetWidth,
      });
    }
  }, [timeFilter]);

  // Ensure highlight is positioned when modal opens
  useEffect(() => {
    if (showModal) {
      // Use a small delay to ensure DOM is fully rendered
      const timer = setTimeout(() => {
        const activeTabRef = tabRefs[timeFilter];
        if (activeTabRef.current) {
          setHighlightStyle({
            left: activeTabRef.current.offsetLeft,
            width: activeTabRef.current.offsetWidth,
          });
        }
      }, 10);
      
      return () => clearTimeout(timer);
    }
  }, [showModal, timeFilter]);
  
  // Extract to-dos from response
  const allTodos = (todosResponse as any)?.data || []

  // Helper function to get effective completed state (local state takes precedence)
  const getEffectiveCompletedState = useCallback((todo: Todo) => {
    return localTodoStates.hasOwnProperty(todo.id) ? localTodoStates[todo.id] : todo.completed
  }, [localTodoStates])

  // Date calculations
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const endOfWeek = new Date(today)
  endOfWeek.setDate(endOfWeek.getDate() + 7)

  // Filter and sort to-dos based on timeFilter
  const { allTodosFiltered, undatedTodos } = useMemo(() => {
    let filtered = allTodos

    // Apply time filter
    if (timeFilter === 'all') {
      // Show all to-dos (no filtering by date)
      filtered = allTodos
    } else if (timeFilter === 'due_soon') {
      filtered = allTodos.filter((todo: Todo) => {
        if (!todo.due_date) return false
        const todoDate = new Date(todo.due_date)
        return todoDate >= today && todoDate <= endOfWeek
      })
    }

    // Separate undated todos for "all" filter
    const undatedTodos = timeFilter === 'all' ? allTodos.filter((todo: Todo) => !todo.due_date) : []

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim()
      filtered = filtered.filter((todo: Todo) =>
        todo.title.toLowerCase().includes(query) ||
        todo.description?.toLowerCase().includes(query) ||
        todo.tags?.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // For "all" filter, exclude undated todos from the main list since they're shown separately
    if (timeFilter === 'all') {
      filtered = filtered.filter((todo: Todo) => todo.due_date)
    }

    // Sort to-dos
    const sorted = filtered.sort((a: Todo, b: Todo) => {
      const aCompleted = getEffectiveCompletedState(a)
      const bCompleted = getEffectiveCompletedState(b)
      
      // Incomplete to-dos first
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

    return { allTodosFiltered: sorted, undatedTodos }
  }, [allTodos, timeFilter, searchQuery, getEffectiveCompletedState, today, endOfWeek])

  // Get current to-dos to display - always show all todos on the card
  const currentTodos = allTodosFiltered

  // Card todos - always show all todos regardless of filter (like tasks card)
  const cardTodos = useMemo(() => {
    // Always use all todos for the card, not filtered by timeFilter
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

  // Ultra-fast todo toggle handler
  const handleToggleTodo = useCallback((todoId: string) => {
    // Optimistic update - flip state immediately
    setLocalTodoStates(prev => {
      const currentTodo = allTodos.find((todo: Todo) => todo.id === todoId)
      if (!currentTodo) return prev

      const currentState = prev[todoId] ?? currentTodo.completed
      return { ...prev, [todoId]: !currentState }
    })

    // Fire-and-forget API call
    toggleTodo.mutate(todoId)
  }, [allTodos, toggleTodo])

  // Clean up local states when to-dos data changes (sync with server)
  useEffect(() => {
    if (allTodos.length > 0) {
      // Clear local states for to-dos that no longer exist or have been updated
      setLocalTodoStates(prev => {
        const newStates: Record<string, boolean> = {}
        Object.keys(prev).forEach(todoId => {
          const todo = allTodos.find((t: Todo) => t.id === todoId)
          if (todo) {
            // Keep local state if there's a pending mutation OR if it differs from server state
            const hasPendingMutation = pendingTodoMutations.has(todoId)
            
            if (hasPendingMutation || prev[todoId] !== todo.completed) {
              // Keep local state if there's a pending mutation or it differs from server state
              newStates[todoId] = prev[todoId]
            }
          }
        })
        return newStates
      })
    }
  }, [allTodos])

  const handleModalClose = useCallback(() => {
    setShowModal(false)
  }, [])

  const handleModalBackdropClick = useCallback((e: React.MouseEvent) => {
    // Only close if clicking the background overlay itself, not its children
    if (e.target === e.currentTarget) {
      e.preventDefault()
      e.stopPropagation()
      setShowModal(false)
    }
  }, [])

  // Handle escape key to close modal
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
    <div 
      className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-4 cursor-pointer hover:bg-neutral-800 transition-colors"
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
      
      <div className="space-y-3">
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
          <div className="space-y-3">
            {/* Show filtered to-dos */}
            {cardTodos.slice(0, 3).map((todo: Todo, index: number) => (
              <div key={todo.id} className="flex items-start gap-3 relative">
                <button
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                    getEffectiveCompletedState(todo)
                      ? 'bg-green-500 border-green-500' 
                      : 'border-gray-500'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleToggleTodo(todo.id)
                  }}
                >
                  {getEffectiveCompletedState(todo) && (
                    <Check size={8} className="text-white" strokeWidth={3} />
                  )}
                </button>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium leading-tight ${
                    getEffectiveCompletedState(todo) 
                      ? 'line-through text-gray-400' 
                      : 'text-white'
                  }`}>
                    {todo.title}
                  </div>
                  {todo.due_date && (
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      <div className="flex items-center gap-1">
                        <Calendar size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {formatDate(todo.due_date)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {formatTime(todo.due_date)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
                {/* Show "more" count on the last todo */}
                {index === 2 && cardTodos.length > 3 && (
                  <div className="absolute bottom-0 right-0 text-xs text-gray-500">
                    +{cardTodos.length - 3} more
                  </div>
                )}
              </div>
            ))}
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

      {/* Persistent Modal - Always Mounted, Visibility Controlled */}
      <div
        className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300 cursor-default ${
          showModal ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={handleModalBackdropClick}
      >
          <div 
            className={`bg-neutral-800 border border-gray-700/50 w-full max-w-2xl rounded-2xl h-[80vh] min-h-[600px] flex flex-col cursor-default transition-all duration-300 ${
              showModal ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            {showModal ? (
              <>
                {/* Header */}
                <div className="p-6">
                  {/* Top row: Title and Close button */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <List size={20} className="text-gray-400" />
                      <h2 className="text-xl font-semibold text-white">
                        {timeFilter === 'all' ? 'All To-dos' : 'Due Soon'}
                      </h2>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        handleModalClose()
                      }}
                      className="p-2 hover:bg-neutral-800 rounded-lg transition-colors"
                      aria-label="Close modal"
                      type="button"
                    >
                      <X size={24} className="text-gray-400 hover:text-white" />
                    </button>
                  </div>

                  {/* Count Display - Context Aware */}
                  <div className="flex items-baseline justify-center gap-2 mb-6">
                    {timeFilter === 'all' ? (
                      // Large numbers for "All"
                      <>
                        <div className="flex items-baseline gap-1">
                          <span className="text-4xl font-bold text-white">
                            {currentTodos.length + undatedTodos.length}
                          </span>
                          <span className="text-sm text-gray-300">total to-dos</span>
                        </div>
                      </>
                    ) : (
                      // Small overview for "Due Soon"
                      <div className="text-sm text-gray-400">
                        Due soon: {currentTodos.length} to-dos
                      </div>
                    )}
                  </div>
                </div>

            {/* Search and Toggle Controls */}
            <div className="px-6 pt-2 pb-6">
              <div className="bg-neutral-800 rounded-lg p-5 mb-6">
                <div className="flex items-center gap-4">
                  {/* Search Bar */}
                  <div className="relative flex-1">
                    <Search size={16} className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search to-dos..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-8 pr-3 py-2 bg-neutral-700 rounded-lg text-white placeholder-gray-400 focus:outline-none text-sm"
                    />
                  </div>

                  {/* Time Filter Buttons */}
                  <div className="relative flex bg-neutral-700 rounded-lg p-1.5">
                    <div 
                      className="absolute top-1 bottom-1 bg-white rounded-md transition-all duration-300 ease-out"
                      style={highlightStyle}
                    />
                    <button
                      ref={allRef}
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); setTimeFilter('all'); }}
                      className={`relative px-2 py-1 text-xs font-medium rounded-md transition-colors duration-200 z-10 ${
                        timeFilter === 'all'
                          ? 'text-neutral-900'
                          : 'text-gray-300 hover:text-white'
                      }`}
                    >
                      All
                    </button>
                    <button
                      ref={dueSoonRef}
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); setTimeFilter('due_soon'); }}
                      className={`relative px-2 py-1 text-xs font-medium rounded-md transition-colors duration-200 z-10 ${
                        timeFilter === 'due_soon'
                          ? 'text-neutral-900'
                          : 'text-gray-300 hover:text-white'
                      }`}
                    >
                      Due Soon
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* To-dos list */}
            <div
              className="flex-1 overflow-y-auto"
              style={{
                scrollbarWidth: 'auto',
                scrollbarColor: 'rgba(75, 85, 99, 0.5) transparent'
              }}
            >
              {isLoading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Loader2 size={24} className="text-gray-400 animate-spin" />
                    </div>
                    <div className="text-base font-semibold text-gray-400 mb-2">
                      Loading to-dos...
                    </div>
                    <div className="text-sm text-gray-400">
                      Please wait
                    </div>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-red-500 text-xl font-semibold">!</span>
                    </div>
                    <div className="text-base font-semibold text-red-400 mb-2">
                      Error loading to-dos
                    </div>
                    <div className="text-sm text-gray-400">
                      {error instanceof Error ? error.message : 'Failed to load to-dos'}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="px-6 pt-2 pb-6">
                  {/* To-dos Section */}
                  {currentTodos.length > 0 || (timeFilter === 'all' && undatedTodos.length > 0) ? (
                    <div className="space-y-3">
                      {/* Show dated todos first */}
                      {currentTodos.map((todo: Todo, index: number) => {
                        // Check if we should show a date divider
                        const showDateDivider = index === 0 || (() => {
                          const currentDate = new Date(todo.due_date!)
                          const previousDate = new Date(currentTodos[index - 1].due_date!)
                          return currentDate.toDateString() !== previousDate.toDateString()
                        })()

                        return (
                          <React.Fragment key={todo.id}>
                            {showDateDivider && (
                              <div className="flex items-center gap-2 mb-3 mt-4 first:mt-0">
                                <div className="h-px bg-gray-600 flex-1"></div>
                                <span className="text-xs font-medium text-gray-500 px-2">
                                  {(() => {
                                    if (!todo.due_date) {
                                      return 'No due date'
                                    }
                                    
                                    const taskDate = new Date(todo.due_date)
                                    const today = new Date()
                                    today.setHours(0, 0, 0, 0)
                                    const tomorrow = new Date(today)
                                    tomorrow.setDate(tomorrow.getDate() + 1)
                                    
                                    if (taskDate.toDateString() === today.toDateString()) {
                                      return 'Today'
                                    } else if (taskDate.toDateString() === tomorrow.toDateString()) {
                                      return 'Tomorrow'
                                    } else {
                                      return taskDate.toLocaleDateString('en-US', { 
                                        weekday: 'short', 
                                        month: 'short', 
                                        day: 'numeric' 
                                      })
                                    }
                                  })()}
                                </span>
                                <div className="h-px bg-gray-600 flex-1"></div>
                              </div>
                            )}
                            <div className="flex items-start gap-3 p-4 bg-neutral-700/50 rounded-lg hover:bg-neutral-700/60 transition-colors duration-150">
                              <button
                                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                                  getEffectiveCompletedState(todo)
                                    ? 'bg-green-500 border-green-500' 
                                    : 'border-gray-500'
                                }`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleToggleTodo(todo.id)
                                }}
                              >
                                {getEffectiveCompletedState(todo) && (
                                  <Check size={12} className="text-white" strokeWidth={3} />
                                )}
                              </button>
                              <div className="flex-1 min-w-0">
                                <div className={`text-base font-medium leading-tight ${
                                  getEffectiveCompletedState(todo) 
                                    ? 'line-through text-gray-400' 
                                    : 'text-white'
                                }`}>
                                  {todo.title}
                                </div>
                                {todo.due_date && (
                                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                                    <div className="flex items-center gap-1">
                                      <Calendar size={12} className="text-gray-400" />
                                      <span className="text-xs font-medium text-gray-400">
                                        {formatDate(todo.due_date)}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <Clock size={12} className="text-gray-400" />
                                      <span className="text-xs font-medium text-gray-400">
                                        {formatTime(todo.due_date)}
                                      </span>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </React.Fragment>
                        )
                      })}
                      
                      {/* Show undated todos at bottom for "all" filter */}
                      {timeFilter === 'all' && undatedTodos.length > 0 && (
                        <>
                          {/* No due date divider */}
                          <div className="flex items-center gap-2 mb-3 mt-4">
                            <div className="h-px bg-gray-600 flex-1"></div>
                            <span className="text-xs font-medium text-gray-500 px-2">
                              No due date
                            </span>
                            <div className="h-px bg-gray-600 flex-1"></div>
                          </div>
                          
                          {/* Undated todos */}
                          {undatedTodos.map((todo: Todo) => (
                            <div key={todo.id} className="flex items-start gap-3 p-4 bg-neutral-700/50 rounded-lg hover:bg-neutral-700/60 transition-colors duration-150">
                              <button
                                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                                  getEffectiveCompletedState(todo)
                                    ? 'bg-green-500 border-green-500' 
                                    : 'border-gray-500'
                                }`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleToggleTodo(todo.id)
                                }}
                              >
                                {getEffectiveCompletedState(todo) && (
                                  <Check size={12} className="text-white" strokeWidth={3} />
                                )}
                              </button>
                              <div className="flex-1 min-w-0">
                                <div className={`text-base font-medium leading-tight ${
                                  getEffectiveCompletedState(todo) 
                                    ? 'line-through text-gray-400' 
                                    : 'text-white'
                                }`}>
                                  {todo.title}
                                </div>
                              </div>
                            </div>
                          ))}
                        </>
                      )}
                    </div>
                  ) : (
                    // No to-dos message
                    <div className="text-center py-20">
                      <div className="text-base font-semibold text-gray-400 mb-2">
                        {(() => {
                          if (searchQuery.trim()) {
                            return `No results for "${searchQuery}"`
                          } else if (timeFilter === 'all') {
                            return 'No to-dos found'
                          } else {
                            return 'No to-dos due soon'
                          }
                        })()}
                      </div>
                      <div className="text-sm text-gray-400">
                        {(() => {
                          if (searchQuery.trim()) {
                            return 'Try a different search term or check your spelling.'
                          } else if (timeFilter === 'all') {
                            return 'You\'re all caught up!'
                          } else {
                            return 'Nothing due in the next week!'
                          }
                        })()}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
              </>
            ) : null}
          </div>
      </div>
    </div>
  )
}
