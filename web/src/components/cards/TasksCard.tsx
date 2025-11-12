import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { X, Calendar, Clock, Loader2, BookOpen } from 'lucide-react'
import { useTasks, useToggleTask } from '@/hooks/tasks'
import { TASK_CACHE_KEYS } from '@/hooks/shared'
import { useTaskUpdates, pendingTaskMutations } from '@/hooks/tasks'
import { useQueryClient } from '@tanstack/react-query'
import type { Task } from '../../lib/utils/types'
import { formatCourseCode } from '../../lib/utils/formatters'
import { useTaskFiltering } from './hooks/useTaskFiltering'
import { useTaskFormatting, type EnhancedTask } from './hooks/useTaskFormatting'
import { TaskListItem } from './TaskListItem'
import { TasksCardModal } from './TasksCardModal'

type TimeFilter = 'week' | 'month' | 'all' | 'past'

export function TasksCard() {
  const [showModal, setShowModal] = useState(false)
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('week')
  const [searchQuery, setSearchQuery] = useState('')
  const [localTaskStates, setLocalTaskStates] = useState<Record<string, string>>({})

  // Enable real-time task updates
  useTaskUpdates()
  
  const queryClient = useQueryClient()
  const { data: allTasksData = [], isLoading, error } = useTasks()
  const toggleTask = useToggleTask()

  // Prefetch tasks data on component mount
  useEffect(() => {
    queryClient.prefetchQuery({
      queryKey: TASK_CACHE_KEYS.TASKS,
      queryFn: () => queryClient.getQueryData(TASK_CACHE_KEYS.TASKS) || allTasksData,
      staleTime: 5 * 60 * 1000,
    })
  }, [queryClient, allTasksData])

  // Filter relevant tasks
  const allRelevantTasks = useMemo(() =>
    allTasksData.filter(task =>
      task.status !== 'cancelled' &&
      (task.task_type === 'assignment' || task.task_type === 'quiz' || task.task_type === 'exam')
    ), [allTasksData]
  )

  // Use filtering hook
  const { currentTasks, pastTasks, today, tomorrow, endOfWeek } = useTaskFiltering({
    tasks: allRelevantTasks,
    timeFilter,
    searchQuery,
  })

  // Use formatting hook
  const { enhancedTasks: allEnhancedTasks } = useTaskFormatting({
    tasks: allRelevantTasks,
    localTaskStates,
    today,
    tomorrow,
  })

  // Card view tasks (today's tasks only)
  const cardTasks = useMemo(() => {
    const todaysTasks = allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate >= today && taskDate < tomorrow
    })

    const sortedTodaysTasks = todaysTasks.sort((a, b) => {
      const aStatus = localTaskStates[a.id] ?? a.status
      const bStatus = localTaskStates[b.id] ?? b.status
      const aIsCompleted = aStatus === 'completed'
      const bIsCompleted = bStatus === 'completed'
      
      if (!aIsCompleted && bIsCompleted) return -1
      if (aIsCompleted && !bIsCompleted) return 1

      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    })

    const thisWeekTasks = allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate > tomorrow && taskDate <= endOfWeek
    })

    const enhancedTodays = sortedTodaysTasks.map(task => {
      const taskEnhanced = allEnhancedTasks.find(t => t.id === task.id)
      return taskEnhanced || {
        ...task,
        effectiveStatus: localTaskStates[task.id] ?? task.status,
        taskColor: task.courses?.color || task.color || '#666666',
        formattedDate: task.due_date ? (task.due_date === today.toISOString().split('T')[0] ? 'Today' : 'Tomorrow') : '',
        formattedTime: task.due_date ? new Date(task.due_date).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : null,
        formattedCourseCode: task.courses?.canvas_course_code ? formatCourseCode(task.courses.canvas_course_code) : null,
        isCompleted: (localTaskStates[task.id] ?? task.status) === 'completed',
        textClasses: (localTaskStates[task.id] ?? task.status) === 'completed' ? 'text-sm font-medium text-gray-500 line-through' : 'text-sm font-medium text-white',
        buttonClasses: '',
      } as EnhancedTask
    })

    return {
      today: enhancedTodays,
      counts: {
        thisWeekTotal: thisWeekTasks.length
      }
    }
  }, [allRelevantTasks, today, tomorrow, endOfWeek, localTaskStates, allEnhancedTasks])

  // Modal view tasks
  const { enhancedTasks: currentEnhancedTasks } = useTaskFormatting({
    tasks: currentTasks,
    localTaskStates,
    today,
    tomorrow,
  })

  const { enhancedTasks: pastEnhancedTasks } = useTaskFormatting({
    tasks: pastTasks,
    localTaskStates,
    today,
    tomorrow,
  })

  const { enhancedTasks: todaysEnhancedTasks } = useTaskFormatting({
    tasks: allRelevantTasks.filter(task => {
      if (!task.due_date) return false
      const taskDate = new Date(task.due_date)
      return taskDate >= today && taskDate < tomorrow
    }),
    localTaskStates,
    today,
    tomorrow,
  })

  // Sort tasks for modal
  const sortedTodaysTasks = useMemo((): EnhancedTask[] => {
    return todaysEnhancedTasks.sort((a, b) => {
      if (!a.isCompleted && b.isCompleted) return -1
      if (a.isCompleted && !b.isCompleted) return 1
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    })
  }, [todaysEnhancedTasks])

  const sortedCurrentTasks = useMemo((): EnhancedTask[] => {
    return currentEnhancedTasks.sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      const aIsToday = dateA >= today && dateA < tomorrow
      const bIsToday = dateB >= today && dateB < tomorrow

      if (aIsToday && !bIsToday) return -1
      if (!aIsToday && bIsToday) return 1
      if (!a.isCompleted && b.isCompleted) return -1
      if (a.isCompleted && !b.isCompleted) return 1
      return dateA.getTime() - dateB.getTime()
    })
  }, [currentEnhancedTasks, today, tomorrow])

  const sortedPastTasks = useMemo((): EnhancedTask[] => {
    return pastEnhancedTasks.sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateB.getTime() - dateA.getTime()
    })
  }, [pastEnhancedTasks])

  // Toggle handler
  const handleToggleTask = useCallback((taskId: string) => {
    setLocalTaskStates(prev => {
      const currentTask = allTasksData.find(task => task.id === taskId)
      if (!currentTask) return prev

      const currentStatus = prev[taskId] ?? currentTask.status
      const newStatus = currentStatus === 'completed' ? 'pending' : 'completed'

      return { ...prev, [taskId]: newStatus }
    })

    toggleTask.mutate(taskId)
  }, [allTasksData, toggleTask])

  // Clean up local states when tasks data changes
  useEffect(() => {
    if (allTasksData.length > 0) {
      setLocalTaskStates(prev => {
        const newStates: Record<string, string> = {}
        Object.keys(prev).forEach(taskId => {
          const task = allTasksData.find((t: Task) => t.id === taskId)
          if (task) {
            const hasPendingMutation = pendingTaskMutations.has(taskId)
            if (hasPendingMutation || prev[taskId] !== task.status) {
              newStates[taskId] = prev[taskId]
            }
          }
        })
        return newStates
      })
    }
  }, [allTasksData])

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

  const handleCardClick = useCallback(() => {
    setShowModal(true)
  }, [])

  return (
    <>
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
              {cardTasks.today.map((task) => (
                <TaskListItem
                  key={task.id}
                  task={task}
                  onToggle={handleToggleTask}
                  variant="card"
                />
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
        {cardTasks.counts.thisWeekTotal > 0 && (
          <div className="mt-2 text-xs text-gray-500 text-right">
            +{cardTasks.counts.thisWeekTotal} this week
          </div>
        )}
      </div>

      <TasksCardModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        timeFilter={timeFilter}
        onFilterChange={setTimeFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        sortedTodaysTasks={sortedTodaysTasks}
        sortedCurrentTasks={sortedCurrentTasks}
        sortedPastTasks={sortedPastTasks}
        currentTasksCount={currentTasks.length}
        pastTasksCount={pastTasks.length}
        isLoading={isLoading}
        error={error}
        onToggleTask={handleToggleTask}
      />
    </>
  )
}
