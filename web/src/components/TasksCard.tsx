import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { X, Calendar, Clock, Loader2, BookOpen, Search } from 'lucide-react'
import { useTasks, useToggleTask } from '../hooks/useTasks'
import { TASK_CACHE_KEYS } from '../hooks/cacheKeys'
import { useTaskUpdates, pendingTaskMutations } from '../hooks/useTaskUpdates'
import { useQueryClient } from '@tanstack/react-query'
import type { Task } from '../lib/utils/types'

// Enhanced task type with pre-computed values
type EnhancedTask = Task & {
  effectiveStatus: string
  taskColor: string
  formattedDate: string
  formattedTime: string | null
  formattedCourseCode: string | null
  isCompleted: boolean
  textClasses: string
  buttonClasses: string
}

export function TasksCard() {
  const [showModal, setShowModal] = useState(false)
  const [timeFilter, setTimeFilter] = useState<'week' | 'month' | 'all' | 'past'>('week')
  const [searchQuery, setSearchQuery] = useState('')
  // Local state for immediate visual feedback
  const [localTaskStates, setLocalTaskStates] = useState<Record<string, string>>({})

  const weekRef = useRef<HTMLButtonElement>(null);
  const monthRef = useRef<HTMLButtonElement>(null);
  const pastRef = useRef<HTMLButtonElement>(null);
  const allRef = useRef<HTMLButtonElement>(null);

  const [highlightStyle, setHighlightStyle] = useState({});

  const tabRefs = {
    week: weekRef,
    month: monthRef,
    past: pastRef,
    all: allRef,
  };

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

  // Enable real-time task updates
  useTaskUpdates()
  
  // Use React Query for caching and data fetching
  const queryClient = useQueryClient()
  const { data: allTasksData = [], isLoading, error } = useTasks()
  const toggleTask = useToggleTask()

  // Prefetch tasks data on component mount for instant modal opening
  useEffect(() => {
    queryClient.prefetchQuery({
      queryKey: TASK_CACHE_KEYS.TASKS,
      queryFn: () => queryClient.getQueryData(TASK_CACHE_KEYS.TASKS) || allTasksData,
      staleTime: 5 * 60 * 1000,
    })
  }, [queryClient, allTasksData])


  // Memoized task filtering - show all assignments, quizzes, and exams (including completed)
  const allRelevantTasks = useMemo(() =>
    allTasksData.filter(task =>
      task.status !== 'cancelled' &&
      (task.task_type === 'assignment' || task.task_type === 'quiz' || task.task_type === 'exam')
    ), [allTasksData]
  )
  
  // Memoized date calculations to prevent unnecessary re-renders
  const { today, tomorrow, endOfWeek, endOfMonth } = useMemo(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    const endOfWeek = new Date(today)
    endOfWeek.setDate(endOfWeek.getDate() + 7)
    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0)
    endOfMonth.setHours(23, 59, 59, 999)
    return { today, tomorrow, endOfWeek, endOfMonth }
  }, [new Date().toDateString()]) // Only recalculate when the date changes

  // Filter and search tasks based on user selections
  const { currentTasks, pastTasks } = useMemo(() => {
    let filtered = allRelevantTasks

    // Apply time filter
    if (timeFilter === 'week') {
      filtered = filtered.filter(task => {
        if (!task.due_date) return false
        const taskDate = new Date(task.due_date)
        return taskDate >= today && taskDate <= endOfWeek
      })
    } else if (timeFilter === 'month') {
      filtered = filtered.filter(task => {
        if (!task.due_date) return false
        const taskDate = new Date(task.due_date)
        return taskDate >= today && taskDate <= endOfMonth
      })
    } else if (timeFilter === 'past') {
      filtered = filtered.filter(task => {
        if (!task.due_date) return false
        const taskDate = new Date(task.due_date)
        return taskDate < today
      })
    }
    // 'all' shows everything (no additional filtering)

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim()
      filtered = filtered.filter(task =>
        task.title.toLowerCase().includes(query) ||
        task.description?.toLowerCase().includes(query) ||
        task.courses?.canvas_course_code?.toLowerCase().includes(query)
      )
    }

    // Split filtered tasks into categories
    const currentTasks = filtered.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate >= today
    })

    const pastTasks = filtered.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate < today
    })

    return { currentTasks, pastTasks }
  }, [allRelevantTasks, timeFilter, searchQuery, today, endOfWeek, endOfMonth])

  // Helper function to get effective status (local state takes precedence)
  const getEffectiveStatus = useCallback((task: Task) => {
    return localTaskStates.hasOwnProperty(task.id) ? localTaskStates[task.id] : task.status
  }, [localTaskStates])

  // Memoized helper functions for performance
  const getTaskColor = useCallback((task: Task): string => {
    // Use course color if available (from joined course data)
    if (task.courses?.color) {
      return task.courses.color
    }
    
    // Fallback to direct color field (for backward compatibility)
    if (task.color) {
      return task.color
    }
    
    // Fallback to priority-based colors
    switch (task.priority) {
      case 'high': return '#EF4444'
      case 'medium': return '#F59E0B'
      case 'low': return '#10B981'
      default: return '#666666'
    }
  }, [])

  const formatCourseCode = useCallback((courseCode: string): string => {
    // Extract text and first 4 numbers from course code
    const match = courseCode.match(/^([A-Za-z]+)\s*(\d{4})/)
    if (match) {
      return `${match[1]} ${match[2]}`
    }
    
    // Try 3-digit numbers
    const match3 = courseCode.match(/^([A-Za-z]+)\s*(\d{3})/)
    if (match3) {
      return `${match3[1]} ${match3[2]}`
    }
    
    // If no 4-digit number found, return as-is
    return courseCode
  }, [])

  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow'
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric' 
      })
    }
  }, [])

  const formatTime = useCallback((dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }, [])



  // Only compute minimal data needed for card view
  const cardTasks = useMemo(() => {
    // Calculate today's tasks from ALL tasks (not filtered by timeFilter)
    const todaysTasks = allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate >= today && taskDate < tomorrow
    })

    // Sort today's tasks: incomplete first, then completed, then by due time
    const sortedTodaysTasks = todaysTasks.sort((a, b) => {
      const aIsCompleted = getEffectiveStatus(a) === 'completed'
      const bIsCompleted = getEffectiveStatus(b) === 'completed'
      
      // Incomplete tasks first
      if (!aIsCompleted && bIsCompleted) return -1
      if (aIsCompleted && !bIsCompleted) return 1

      // Within same completion status, sort by due time
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    })

    const processTask = (task: Task): EnhancedTask => {
      const isCompleted = getEffectiveStatus(task) === 'completed'
      const taskColor = getTaskColor(task)
      return {
        ...task,
        effectiveStatus: getEffectiveStatus(task),
        taskColor,
        formattedDate: task.due_date ? formatDate(task.due_date) : 'No due date',
        formattedTime: task.due_date ? formatTime(task.due_date) : null,
        formattedCourseCode: task.courses?.canvas_course_code ? formatCourseCode(task.courses.canvas_course_code) : null,
        isCompleted,
        textClasses: `text-sm font-medium leading-tight ${
          isCompleted ? 'line-through text-gray-400' : 'text-white'
        }`,
        buttonClasses: `w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
          isCompleted ? 'bg-green-500 border-green-500' : ''
        }`
      }
    }

    // Calculate counts from ALL tasks (not filtered)
    const allCurrentTasks = allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate >= today
    })
    
    const allPastTasks = allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate < today
    })

    // Calculate this week's tasks (excluding today)
    const thisWeekTasks = allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate > tomorrow && taskDate <= endOfWeek
    })

    return {
      today: sortedTodaysTasks.map(processTask),
      counts: {
        todaysTotal: todaysTasks.length,
        currentTotal: allCurrentTasks.length,
        pastTotal: allPastTasks.length,
        thisWeekTotal: thisWeekTasks.length
      }
    }
  }, [allRelevantTasks, today, tomorrow, endOfWeek, getEffectiveStatus, getTaskColor, formatDate, formatTime, formatCourseCode])

  // Always precompute modal tasks for instant opening
  const { visibleTasks } = useMemo(() => {

    const processTask = (task: Task): EnhancedTask => {
      const isCompleted = getEffectiveStatus(task) === 'completed'
      const taskColor = getTaskColor(task)
      return {
        ...task,
        effectiveStatus: getEffectiveStatus(task),
        taskColor,
        formattedDate: task.due_date ? formatDate(task.due_date) : 'No due date',
        formattedTime: task.due_date ? formatTime(task.due_date) : null,
        formattedCourseCode: task.courses?.canvas_course_code ? formatCourseCode(task.courses.canvas_course_code) : null,
        isCompleted,
        textClasses: `text-base font-medium leading-tight ${
          isCompleted ? 'line-through text-gray-400' : 'text-white'
        }`,
        buttonClasses: `w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
          isCompleted ? 'bg-green-500 border-green-500' : 'border-2 hover:border-opacity-80'
        }`
      }
    }

    // Calculate today's tasks from current tasks
    const todaysTasks = currentTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate >= today && taskDate < tomorrow
    })

    // Sort tasks to prioritize visible ones
    const sortedCurrentTasks = currentTasks.sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      const aIsToday = dateA >= today && dateA < tomorrow
      const bIsToday = dateB >= today && dateB < tomorrow

      if (aIsToday && !bIsToday) return -1
      if (!aIsToday && bIsToday) return 1
      if (!getEffectiveStatus(a).includes('completed') && getEffectiveStatus(b).includes('completed')) return -1
      if (getEffectiveStatus(a).includes('completed') && !getEffectiveStatus(b).includes('completed')) return 1
      return dateA.getTime() - dateB.getTime()
    })

    // Process ALL tasks immediately - no progressive loading limits
    return {
      visibleTasks: {
        current: sortedCurrentTasks.map(processTask),
        past: pastTasks.map(processTask),
        today: todaysTasks.map(processTask)
      }
    }
  }, [currentTasks, pastTasks, today, tomorrow, getEffectiveStatus, getTaskColor, formatDate, formatTime, formatCourseCode])

  // Use pre-computed tasks directly - no progressive loading needed
  const memoizedTasks = visibleTasks

  // Sorted tasks only computed when modal is visible
  const sortedCurrentTasks = useMemo((): EnhancedTask[] => {
    if (!memoizedTasks) return []
    return memoizedTasks.current.sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)

      // Check if tasks are due today
      const aIsToday = dateA >= today && dateA < tomorrow
      const bIsToday = dateB >= today && dateB < tomorrow

      // Today's tasks first
      if (aIsToday && !bIsToday) return -1
      if (!aIsToday && bIsToday) return 1

      // Within same day category, incomplete first
      if (!a.isCompleted && b.isCompleted) return -1
      if (a.isCompleted && !b.isCompleted) return 1

      // Then by due time
      return dateA.getTime() - dateB.getTime()
    })
  }, [memoizedTasks, today, tomorrow])


  // Sort past tasks by date (most recent first)
  const sortedPastTasks = useMemo((): EnhancedTask[] => {
    if (!memoizedTasks) return []
    return memoizedTasks.past.sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateB.getTime() - dateA.getTime() // Most recent first
    })
  }, [memoizedTasks])

  // Sort today's tasks: incomplete first, then completed, then by due time
  const sortedTodaysTasks = useMemo((): EnhancedTask[] => {
    if (!memoizedTasks) return []
    return memoizedTasks.today.sort((a, b) => {
      if (!a.isCompleted && b.isCompleted) return -1
      if (a.isCompleted && !b.isCompleted) return 1

      // Within same completion status, sort by due time
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    })
  }, [memoizedTasks])



  // Ultra-fast task toggle handler - minimal synchronous work
  const handleToggleTask = useCallback((taskId: string) => {
    // Skip heavy lookups - just toggle the optimistic state immediately
    setLocalTaskStates(prev => {
      const currentTask = allTasksData.find(task => task.id === taskId)
      if (!currentTask) return prev

      const currentStatus = prev[taskId] ?? currentTask.status
      const newStatus = currentStatus === 'completed' ? 'pending' : 'completed'

      return { ...prev, [taskId]: newStatus }
    })

    // Fire-and-forget API call - don't block UI
    toggleTask.mutate(taskId)
  }, [allTasksData, toggleTask])

  // Clean up local states when tasks data changes (sync with server)
  useEffect(() => {
    if (allTasksData.length > 0) {
      // Clear local states for tasks that no longer exist or have been updated
      setLocalTaskStates(prev => {
        const newStates: Record<string, string> = {}
        Object.keys(prev).forEach(taskId => {
          const task = allTasksData.find((t: Task) => t.id === taskId)
          if (task) {
            // Keep local state if there's a pending mutation OR if it differs from server state
            const hasPendingMutation = pendingTaskMutations.has(taskId)
            
            if (hasPendingMutation || prev[taskId] !== task.status) {
              // Keep local state if there's a pending mutation or it differs from server state
              newStates[taskId] = prev[taskId]
            }
          }
        })
        return newStates
      })
    }
  }, [allTasksData])

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



  // Ultra-fast click handler - just flips boolean
  const handleCardClick = useCallback(() => {
    setShowModal(true)
  }, [])

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

  return (
    <div 
      className="bg-neutral-800/80 border border-gray-700/50 rounded-xl p-5 cursor-pointer hover:bg-neutral-800 transition-colors"
      onClick={handleCardClick}
    >
      <div className="flex items-center justify-between mb-4 px-1">
        <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
          ASSIGNMENTS
        </span>
        <div className="w-4 h-4 flex items-center justify-center">
          <BookOpen size={16} className="text-gray-400" />
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
                  Loading assignments...
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
                  Error loading assignments
                </span>
                <div className="text-xs text-gray-500 mt-1">
                  {error instanceof Error ? error.message : 'Failed to load assignments'}
                </div>
              </div>
            </div>
          </div>
        ) : cardTasks.today.length > 0 || cardTasks.counts.pastTotal > 0 ? (
          <div className="space-y-3">
            {/* Show today's assignments only */}
            {cardTasks.today.map((task, index) => (
              <div key={task.id} className="flex items-start gap-3 relative">
                <button
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                    task.isCompleted
                      ? 'bg-green-500 border-green-500'
                      : ''
                  }`}
                  style={{
                    backgroundColor: task.isCompleted ? '#10B981' : 'transparent',
                    borderColor: task.isCompleted ? '#10B981' : task.taskColor
                  }}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleToggleTask(task.id)
                  }}
                >
                  {task.isCompleted && (
                    <span className="text-white text-xs font-semibold">✓</span>
                  )}
                </button>
                <div className="flex-1 min-w-0">
                  <div className={task.textClasses}>
                    {task.title}
                  </div>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    <div className="flex items-center gap-1">
                      <Calendar size={10} className="text-gray-400" />
                      <span className="text-xs text-gray-400">
                        {task.formattedDate}
                      </span>
                    </div>
                    {task.formattedTime && (
                      <div className="flex items-center gap-1">
                        <Clock size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {task.formattedTime}
                        </span>
                      </div>
                    )}
                    {task.formattedCourseCode && (
                      <div className="flex items-center gap-1">
                        <BookOpen size={10} className="text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {task.formattedCourseCode}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                {/* Show "this week" count on the last task */}
                {index === cardTasks.today.length - 1 && cardTasks.counts.thisWeekTotal > 0 && (
                  <div className="absolute bottom-0 right-0 text-xs text-gray-500">
                    +{cardTasks.counts.thisWeekTotal} this week
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
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-400">
                  No assignments due today
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
                      <Calendar size={20} className="text-gray-400" />
                      <h2 className="text-xl font-semibold text-white">
                        {timeFilter === 'week' ? 'This Week' : 
                         timeFilter === 'month' ? new Date().toLocaleDateString('en-US', { month: 'long' }) : 
                         timeFilter === 'past' ? 'Completed Assignments' :
                         'All Assignments'}
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
                    {timeFilter === 'week' ? (
                      // Large numbers for "This Week"
                      <>
                        <div className="flex items-baseline gap-1">
                          <span className="text-4xl font-bold text-white">
                            {currentTasks.length + pastTasks.length}
                          </span>
                          <span className="text-sm text-gray-300">total</span>
                        </div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-4xl font-bold text-white">
                            {sortedTodaysTasks?.length || 0}
                          </span>
                          <span className="text-sm text-gray-300">due today</span>
                        </div>
                      </>
                    ) : (
                      // Small overview for other filters
                      <div className="text-sm text-gray-400">
                        {timeFilter === 'month' && `${new Date().toLocaleDateString('en-US', { month: 'long' })}: ${currentTasks.length} due (${sortedTodaysTasks?.length || 0} today)`}
                        {timeFilter === 'past' && `Completed: ${pastTasks.length} assignments`}
                        {timeFilter === 'all' && `All: ${currentTasks.length + pastTasks.length} total (${sortedTodaysTasks?.length || 0} today)`}
                      </div>
                    )}
                  </div>
                </div>

            {/* Tasks list */}
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
                      Loading assignments...
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
                      Error loading assignments
                    </div>
                    <div className="text-sm text-gray-400">
                      {error instanceof Error ? error.message : 'Failed to load assignments'}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="px-6 pt-2 pb-6">
                  {/* Search and Toggle Controls */}
                  {(
                    <div className="bg-neutral-800 rounded-lg p-5 mb-6">
                      <div className="flex items-center gap-4">
                        {/* Search Bar */}
                        <div className="relative flex-1">
                          <Search size={16} className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
                          <input
                            type="text"
                            placeholder="Search assignments..."
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
                          ref={weekRef}
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            setTimeFilter('week')
                          }}
                          className={`relative px-2 py-1 text-xs font-medium rounded-md transition-colors duration-200 z-10 ${
                            timeFilter === 'week'
                              ? 'text-neutral-900'
                              : 'text-gray-300 hover:text-white'
                          }`}
                        >
                          Week
                        </button>
                        <button
                          ref={monthRef}
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            setTimeFilter('month')
                          }}
                          className={`relative px-2 py-1 text-xs font-medium rounded-md transition-colors duration-200 z-10 ${
                            timeFilter === 'month'
                              ? 'text-neutral-900'
                              : 'text-gray-300 hover:text-white'
                          }`}
                        >
                          Month
                        </button>
                        <button
                          ref={allRef}
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            setTimeFilter('all')
                          }}
                          className={`relative px-2 py-1 text-xs font-medium rounded-md transition-colors duration-200 z-10 ${
                            timeFilter === 'all'
                              ? 'text-neutral-900'
                              : 'text-gray-300 hover:text-white'
                          }`}
                        >
                          All
                        </button>
                        <button
                          ref={pastRef}
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            setTimeFilter('past')
                          }}
                          className={`relative px-2 py-1 text-xs font-medium rounded-md transition-colors duration-200 z-10 ${
                            timeFilter === 'past'
                              ? 'text-neutral-900'
                              : 'text-gray-300 hover:text-white'
                          }`}
                        >
                          Past
                        </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tasks Section */}
                  {(() => {
                    let tasksToShow: EnhancedTask[] = []
                    let showDateDividers = false
                    
                    if (timeFilter === 'past') {
                      tasksToShow = sortedPastTasks
                    } else {
                      tasksToShow = sortedCurrentTasks
                      showDateDividers = true
                    }
                    
                    return tasksToShow.length > 0 && (
                      <div className="mb-8">
                        <div className="space-y-3">
                          {tasksToShow.map((task, index) => {
                          const currentDate = task.due_date ? new Date(task.due_date).toDateString() : null
                          const previousDate = index > 0 && tasksToShow[index - 1].due_date 
                            ? new Date(tasksToShow[index - 1].due_date).toDateString() 
                            : null
                          const showDateDivider = showDateDividers && currentDate && currentDate !== previousDate
                          
                          return (
                            <React.Fragment key={task.id}>
                              {showDateDivider && (
                                <div className="flex items-center gap-2 mb-3 mt-4 first:mt-0">
                                  <div className="h-px bg-gray-600 flex-1"></div>
                                  <span className="text-xs font-medium text-gray-500 px-2">
                                    {(() => {
                                      const taskDate = new Date(task.due_date)
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
                              <div
                                className="flex items-start gap-3 p-4 bg-neutral-700/50 rounded-lg hover:bg-neutral-700/60 transition-colors duration-150"
                              >
                            <button
                              className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                                task.isCompleted
                                  ? 'bg-green-500 border-green-500' 
                                  : `border-2 hover:border-opacity-80`
                              }`}
                              style={{
                                backgroundColor: task.isCompleted ? '#10B981' : 'transparent',
                                borderColor: task.isCompleted ? '#10B981' : task.taskColor
                              }}
                              onClick={(e) => {
                                e.stopPropagation()
                                handleToggleTask(task.id)
                              }}
                            >
                              {task.isCompleted && (
                                <span className="text-white text-xs font-semibold">✓</span>
                              )}
                            </button>
                            <div className="flex-1 min-w-0">
                              <div className={task.textClasses}>
                                {task.title}
                              </div>
                              <div className="flex items-center gap-3 mt-2 flex-wrap">
                                <div className="flex items-center gap-1">
                                  <Calendar size={12} className="text-gray-400" />
                                  <span className="text-xs font-medium text-gray-400">
                                    {task.formattedDate}
                                  </span>
                                </div>
                                {task.formattedTime && (
                                  <div className="flex items-center gap-1">
                                    <Clock size={12} className="text-gray-400" />
                                    <span className="text-xs font-medium text-gray-400">
                                      {task.formattedTime}
                                    </span>
                                  </div>
                                )}
                                {task.formattedCourseCode && (
                                  <div className="flex items-center gap-1">
                                    <BookOpen size={12} className="text-gray-400" />
                                    <span className="text-xs font-medium text-gray-400">
                                      {task.formattedCourseCode}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                            </div>
                            </React.Fragment>
                          )
                        })}
                      </div>
                    </div>
                    )
                  })()}


                  {/* No tasks message */}
                  {(() => {
                    let tasksToShow: EnhancedTask[] = []
                    let message = ''
                    let subMessage = ''
                    
                    // Check if there's an active search query first
                    if (searchQuery.trim()) {
                      if (timeFilter === 'past') {
                        tasksToShow = sortedPastTasks
                        message = `No results for "${searchQuery}" in completed assignments`
                        subMessage = 'Try a different search term or check your spelling.'
                      } else if (timeFilter === 'week') {
                        tasksToShow = sortedCurrentTasks
                        message = `No results for "${searchQuery}" this week`
                        subMessage = 'Try a different search term or check your spelling.'
                      } else if (timeFilter === 'month') {
                        tasksToShow = sortedCurrentTasks
                        message = `No results for "${searchQuery}" this month`
                        subMessage = 'Try a different search term or check your spelling.'
                      } else {
                        tasksToShow = sortedCurrentTasks
                        message = `No results for "${searchQuery}"`
                        subMessage = 'Try a different search term or check your spelling.'
                      }
                    } else {
                      // No search query - show filter-specific messages
                      if (timeFilter === 'past') {
                        tasksToShow = sortedPastTasks
                        message = 'No completed assignments'
                        subMessage = 'You\'re all caught up with completed work!'
                      } else if (timeFilter === 'week') {
                        tasksToShow = sortedCurrentTasks
                        message = 'No assignments this week'
                        subMessage = 'You\'re all set for the week ahead!'
                      } else if (timeFilter === 'month') {
                        tasksToShow = sortedCurrentTasks
                        message = 'No assignments this month'
                        subMessage = 'You\'re all set for the month ahead!'
                      } else {
                        tasksToShow = sortedCurrentTasks
                        message = 'No assignments'
                        subMessage = 'All caught up! Great job.'
                      }
                    }
                    
                    return tasksToShow.length === 0 && (
                      <div className="text-center py-20">
                        <div className="text-base font-semibold text-gray-400 mb-2">
                          {message}
                        </div>
                        <div className="text-sm text-gray-400">
                          {subMessage}
                        </div>
                      </div>
                    )
                  })()}
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
