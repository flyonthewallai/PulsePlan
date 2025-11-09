import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { X, Calendar, Clock, Loader2, Check, List, Search, Tag } from 'lucide-react'
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
  const { data: todosResponse, isLoading, error } = useTodos()
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
            {/* Show filtered to-dos */}
            {cardTodos.slice(0, 4).map((todo: Todo, index: number) => (
              <div key={todo.id} className="flex items-start gap-3 relative">
                <button
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                    getEffectiveCompletedState(todo)
                      ? 'bg-blue-500 border-blue-500' 
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
                  <div className="flex items-center justify-between gap-2">
                    <div className={`text-sm font-medium leading-tight ${
                      getEffectiveCompletedState(todo) 
                        ? 'line-through text-gray-400' 
                        : 'text-white'
                    }`}>
                      {todo.title}
                    </div>
                    {todo.tags && todo.tags.length > 0 && (
                      <div className="flex items-center gap-1">
                        <div className="flex items-center gap-1 bg-neutral-800/60 rounded px-1.5 py-0.5">
                          <Tag size={8} className="text-gray-500" />
                          <span className="text-xs text-gray-400">{todo.tags[0]}</span>
                        </div>
                      </div>
                    )}
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
                {index === 3 && cardTodos.length > 4 && (
                  <div className="absolute bottom-0 right-0 text-xs text-gray-500">
                    +{cardTodos.length - 4} more
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
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300 cursor-default ${
          showModal ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={handleModalBackdropClick}
      >
          <div
            className={`border border-gray-700/50 w-full max-w-3xl rounded-xl h-[75vh] flex flex-col cursor-default transition-all duration-300 shadow-2xl ${
              showModal ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
            }`}
            style={{ backgroundColor: '#121212' }}
            onClick={(e) => e.stopPropagation()}
          >
            {showModal ? (
              <>
                {/* Header - Matching Card Style */}
                <div className="p-5 border-b border-gray-700/30">
                  {/* Title Row */}
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-white tracking-tight">
                      To-Dos
                    </h2>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        handleModalClose()
                      }}
                      className="p-1.5 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-neutral-800/60"
                      aria-label="Close modal"
                      type="button"
                    >
                      <X size={18} />
                    </button>
                  </div>

                  {/* Stats Bar - Clean Inline */}
                  <div className="flex items-center gap-5 text-sm">
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-2xl font-bold text-white tabular-nums">
                        {currentTodos.length + (undatedTodos.length || 0)}
                      </span>
                      <span className="text-gray-400 font-medium">
                        {timeFilter === 'all' ? 'total' : 'due soon'}
                      </span>
                    </div>
                    <div className="h-3 w-px bg-gray-700/50"></div>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-lg font-semibold text-white tabular-nums">
                        {currentTodos.filter((t: Todo) => !getEffectiveCompletedState(t)).length}
                      </span>
                      <span className="text-gray-400 font-medium">incomplete</span>
                    </div>
                  </div>
                </div>

            {/* Controls Bar - Clean Inline Layout */}
            <div className="px-5 py-3 border-b border-gray-700/30">
              <div className="flex items-center gap-3">
                {/* Search Bar */}
                <div className="relative flex-1">
                  <Search size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search to-dos..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-neutral-900/50 border border-gray-700/50 text-white placeholder-gray-500 focus:outline-none focus:border-gray-600 transition-colors text-sm"
                  />
                </div>

                {/* Time Filter Buttons - Sleek Segmented Control */}
                <div className="relative flex rounded-lg p-1 bg-neutral-900/50 border border-gray-700/50">
                  <div
                    className="absolute top-1 bottom-1 bg-white rounded-md transition-all duration-300 ease-out shadow-sm"
                    style={highlightStyle}
                  />
                  <button
                    ref={allRef}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); setTimeFilter('all'); }}
                    className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                      timeFilter === 'all'
                        ? 'text-neutral-900'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    All
                  </button>
                  <button
                    ref={dueSoonRef}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); setTimeFilter('due_soon'); }}
                    className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                      timeFilter === 'due_soon'
                        ? 'text-neutral-900'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Due Soon
                  </button>
                </div>
              </div>
            </div>

            {/* To-dos list */}
            <div
              className="flex-1 overflow-y-auto px-5 py-3"
              style={{
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgba(75, 85, 99, 0.3) transparent'
              }}
            >
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="w-8 h-8 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                      <Loader2 size={16} className="text-gray-400 animate-spin" />
                    </div>
                    <div className="text-sm font-medium text-gray-400 mb-1">
                      Loading to-dos...
                    </div>
                    <div className="text-xs text-gray-400">
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
                <div>
                  {/* To-dos Section */}
                  {currentTodos.length > 0 || (timeFilter === 'all' && undatedTodos.length > 0) ? (
                    <div className="space-y-2">
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
                              <div className="flex items-center gap-3 py-3 first:pt-0">
                                <div className="h-px bg-gray-700/50 flex-1"></div>
                                <span className="text-xs font-semibold text-gray-400">
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
                                <div className="h-px bg-gray-700/50 flex-1"></div>
                              </div>
                            )}
                            <div className="flex items-start gap-3 p-3 rounded-xl bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/50 transition-colors group">
                              <button
                                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                                  getEffectiveCompletedState(todo)
                                    ? 'bg-blue-500 border-blue-500'
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
                                <div className="flex items-start justify-between gap-3">
                                  <div className={`text-base font-medium leading-tight flex-shrink ${
                                    getEffectiveCompletedState(todo)
                                      ? 'line-through text-gray-400'
                                      : 'text-white'
                                  }`}>
                                    {todo.title}
                                  </div>
                                  <div className="flex items-center gap-2 flex-shrink-0">
                                    {todo.tags && todo.tags.length > 0 && (
                                      <div className="flex items-center gap-1">
                                        <div className="flex items-center gap-1 bg-neutral-800/60 rounded px-2 py-0.5">
                                          <Tag size={9} className="text-gray-500" />
                                          <span className="text-xs text-gray-400">{todo.tags[0]}</span>
                                        </div>
                                      </div>
                                    )}
                                    {todo.due_date && (
                                      <>
                                        <div className="flex items-center gap-1.5">
                                          <Calendar size={11} className="text-gray-500" />
                                          <span className="text-xs text-gray-400">
                                            {formatDate(todo.due_date)}
                                          </span>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                          <Clock size={11} className="text-gray-500" />
                                          <span className="text-xs text-gray-400">
                                            {formatTime(todo.due_date)}
                                          </span>
                                        </div>
                                      </>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </React.Fragment>
                        )
                      })}
                      
                      {/* Show undated todos at bottom for "all" filter */}
                      {timeFilter === 'all' && undatedTodos.length > 0 && (
                        <>
                          {/* No due date divider */}
                          <div className="flex items-center gap-3 py-3">
                            <div className="h-px bg-gray-700/50 flex-1"></div>
                            <span className="text-xs font-semibold text-gray-400">
                              No due date
                            </span>
                            <div className="h-px bg-gray-700/50 flex-1"></div>
                          </div>

                          {/* Undated todos */}
                          {undatedTodos.map((todo: Todo) => (
                            <div key={todo.id} className="flex items-start gap-3 p-3 rounded-lg bg-neutral-900/30 hover:bg-neutral-900/50 transition-colors group">
                              <button
                                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                                  getEffectiveCompletedState(todo)
                                    ? 'bg-blue-500 border-blue-500'
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
                                <div className="flex items-start justify-between gap-3">
                                  <div className={`text-base font-medium leading-tight flex-shrink ${
                                    getEffectiveCompletedState(todo)
                                      ? 'line-through text-gray-400'
                                      : 'text-white'
                                  }`}>
                                    {todo.title}
                                  </div>
                                  {todo.tags && todo.tags.length > 0 && (
                                    <div className="flex items-center gap-1">
                                      <div className="flex items-center gap-1 bg-neutral-800/60 rounded px-2 py-0.5">
                                        <Tag size={9} className="text-gray-500" />
                                        <span className="text-xs text-gray-400">{todo.tags[0]}</span>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </>
                      )}
                    </div>
                  ) : (
                    // No to-dos message
                    <div className="text-center py-16">
                      <div className="text-sm font-medium text-gray-400 mb-1">
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
                      <div className="text-xs text-gray-500">
                        {(() => {
                          if (searchQuery.trim()) {
                            return 'Try a different search term'
                          } else if (timeFilter === 'all') {
                            return 'All caught up!'
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
