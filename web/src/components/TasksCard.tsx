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

    // Calculate upcoming tasks (next 7 days, excluding today)
    const upcomingTasks = allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate > today && taskDate <= new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000)
    }).sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    }).slice(0, 3) // Show next 3 upcoming tasks

    return {
      today: sortedTodaysTasks.map(processTask),
      upcoming: upcomingTasks.map(processTask),
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
      className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-5 cursor-pointer hover:bg-neutral-800/60 transition-colors h-full flex flex-col"
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
      <div className="space-y-3 flex-1 flex flex-col">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="w-8 h-8 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <Loader2 size={16} className="text-gray-400 animate-spin" />
              </div>
              <div className="text-sm font-medium text-gray-400 mb-1">
                Loading assignments...
              </div>
              <div className="text-xs text-gray-400">
                Please wait
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
        ) : cardTasks.today.length > 0 ? (
          <div className="space-y-2">
            {/* Show today's assignments */}
            {cardTasks.today.map((task, index) => (
              <div key={task.id} className="flex items-start gap-3 relative">
                <button
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                    task.isCompleted
                      ? 'bg-blue-500 border-blue-500'
                      : ''
                  }`}
                  style={{
                    backgroundColor: task.isCompleted ? '#3B82F6' : 'transparent',
                    borderColor: task.isCompleted ? '#3B82F6' : task.taskColor
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
        ) : cardTasks.upcoming.length > 0 ? (
          <div className="space-y-2">
            {/* Show upcoming assignments when no assignments due today */}
            {cardTasks.upcoming.map((task, index) => (
              <div key={task.id} className="flex items-start gap-3 relative">
                <button
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                    task.isCompleted
                      ? 'bg-blue-500 border-blue-500'
                      : ''
                  }`}
                  style={{
                    backgroundColor: task.isCompleted ? '#3B82F6' : 'transparent',
                    borderColor: task.isCompleted ? '#3B82F6' : task.taskColor
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
                      Assignments
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
                        {sortedTodaysTasks?.length || 0}
                      </span>
                      <span className="text-gray-400 font-medium">today</span>
                    </div>
                    <div className="h-3 w-px bg-gray-700/50"></div>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-lg font-semibold text-white tabular-nums">
                        {currentTasks.length + pastTasks.length}
                      </span>
                      <span className="text-gray-400 font-medium">
                        {timeFilter === 'week' ? 'this week' :
                         timeFilter === 'month' ? 'this month' :
                         timeFilter === 'past' ? 'completed' :
                         'total'}
                      </span>
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
                    placeholder="Search assignments..."
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
                    ref={weekRef}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setTimeFilter('week')
                    }}
                    className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                      timeFilter === 'week'
                        ? 'text-neutral-900'
                        : 'text-gray-400 hover:text-white'
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
                    className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                      timeFilter === 'month'
                        ? 'text-neutral-900'
                        : 'text-gray-400 hover:text-white'
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
                    className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                      timeFilter === 'all'
                        ? 'text-neutral-900'
                        : 'text-gray-400 hover:text-white'
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
                    className={`relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors duration-200 z-10 ${
                      timeFilter === 'past'
                        ? 'text-neutral-900'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Past
                  </button>
                </div>
              </div>
            </div>

            {/* Tasks list */}
            <div
              className="flex-1 overflow-y-auto px-5 py-3"
              style={{
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgba(75, 85, 99, 0.3) transparent'
              }}
            >
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <Loader2 size={20} className="text-gray-400 animate-spin mx-auto mb-3" />
                    <div className="text-sm font-medium text-gray-400">
                      Loading assignments...
                    </div>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="w-10 h-10 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-red-400 text-lg">!</span>
                    </div>
                    <div className="text-sm font-semibold text-red-400 mb-1">
                      Error loading assignments
                    </div>
                    <div className="text-xs text-gray-500">
                      {error instanceof Error ? error.message : 'Failed to load assignments'}
                    </div>
                  </div>
                </div>
              ) : (
                <div>

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
                      <div className="space-y-2">
                        {tasksToShow.map((task, index) => {
                          const currentDate = task.due_date ? new Date(task.due_date).toDateString() : null
                          const previousDate = index > 0 && tasksToShow[index - 1].due_date
                            ? new Date(tasksToShow[index - 1].due_date).toDateString()
                            : null
                          const showDateDivider = showDateDividers && currentDate && currentDate !== previousDate

                          return (
                            <React.Fragment key={task.id}>
                              {showDateDivider && (
                                <div className="flex items-center gap-3 py-3 first:pt-0">
                                  <div className="h-px bg-gray-700/50 flex-1"></div>
                                  <span className="text-xs font-semibold text-gray-400">
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
                                  <div className="h-px bg-gray-700/50 flex-1"></div>
                                </div>
                              )}
                              <div className="flex items-start gap-3 p-3 rounded-xl bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/50 transition-colors group">
                                <button
                                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                                    task.isCompleted
                                      ? 'bg-blue-500 border-blue-500'
                                      : 'border-2'
                                  }`}
                                  style={{
                                    backgroundColor: task.isCompleted ? '#3B82F6' : 'transparent',
                                    borderColor: task.isCompleted ? '#3B82F6' : task.taskColor
                                  }}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleToggleTask(task.id)
                                  }}
                                >
                                  {task.isCompleted && (
                                    <span className="text-white text-xs font-bold">✓</span>
                                  )}
                                </button>

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between gap-3">
                                    <div className={task.textClasses}>
                                      {task.title}
                                    </div>
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                      {task.formattedCourseCode && (
                                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-neutral-800/50">
                                          <span className="text-xs font-medium text-gray-300">
                                            {task.formattedCourseCode}
                                          </span>
                                        </div>
                                      )}
                                      <div className="flex items-center gap-1.5">
                                        <Calendar size={11} className="text-gray-500" />
                                        <span className="text-xs text-gray-400">
                                          {task.formattedDate}
                                        </span>
                                      </div>
                                      {task.formattedTime && (
                                        <div className="flex items-center gap-1.5">
                                          <Clock size={11} className="text-gray-500" />
                                          <span className="text-xs text-gray-400">
                                            {task.formattedTime}
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </React.Fragment>
                          )
                        })}
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
                        message = `No results for "${searchQuery}"`
                        subMessage = 'Try a different search term'
                      } else if (timeFilter === 'week') {
                        tasksToShow = sortedCurrentTasks
                        message = `No results for "${searchQuery}"`
                        subMessage = 'Try a different search term'
                      } else if (timeFilter === 'month') {
                        tasksToShow = sortedCurrentTasks
                        message = `No results for "${searchQuery}"`
                        subMessage = 'Try a different search term'
                      } else {
                        tasksToShow = sortedCurrentTasks
                        message = `No results for "${searchQuery}"`
                        subMessage = 'Try a different search term'
                      }
                    } else {
                      // No search query - show filter-specific messages
                      if (timeFilter === 'past') {
                        tasksToShow = sortedPastTasks
                        message = 'No completed assignments'
                        subMessage = 'All caught up!'
                      } else if (timeFilter === 'week') {
                        tasksToShow = sortedCurrentTasks
                        message = 'No assignments this week'
                        subMessage = 'Looking good!'
                      } else if (timeFilter === 'month') {
                        tasksToShow = sortedCurrentTasks
                        message = 'No assignments this month'
                        subMessage = 'Looking good!'
                      } else {
                        tasksToShow = sortedCurrentTasks
                        message = 'No assignments'
                        subMessage = 'All caught up!'
                      }
                    }

                    return tasksToShow.length === 0 && (
                      <div className="text-center py-16">
                        <div className="text-sm font-medium text-gray-400 mb-1">
                          {message}
                        </div>
                        <div className="text-xs text-gray-500">
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
