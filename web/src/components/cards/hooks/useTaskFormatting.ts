import { useMemo, useCallback } from 'react'
import type { Task } from '../../../lib/utils/types'
import { formatCourseCode } from '../../../lib/utils/formatters'

export type EnhancedTask = Task & {
  effectiveStatus: string
  taskColor: string
  formattedDate: string
  formattedTime: string | null
  formattedCourseCode: string | null
  isCompleted: boolean
  textClasses: string
  buttonClasses: string
}

interface UseTaskFormattingProps {
  tasks: Task[]
  localTaskStates: Record<string, string>
  today: Date
  tomorrow: Date
}

export function useTaskFormatting({
  tasks,
  localTaskStates,
  today,
  tomorrow,
}: UseTaskFormattingProps) {
  const getEffectiveStatus = useCallback((task: Task): string => {
    return localTaskStates[task.id] ?? task.status
  }, [localTaskStates])

  const getTaskColor = useCallback((task: Task): string => {
    if (task.courses?.color) {
      return task.courses.color
    }
    if (task.color) {
      return task.color
    }
    switch (task.priority) {
      case 'high': return '#EF4444'
      case 'medium': return '#F59E0B'
      case 'low': return '#10B981'
      default: return '#666666'
    }
  }, [])

  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString)
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
  }, [today, tomorrow])

  const formatTime = useCallback((dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }, [])

  const enhancedTasks = useMemo((): EnhancedTask[] => {
    return tasks.map(task => {
      const effectiveStatus = getEffectiveStatus(task)
      const isCompleted = effectiveStatus === 'completed'
      const taskColor = getTaskColor(task)
      
      const textClasses = isCompleted
        ? 'text-sm font-medium text-gray-500 line-through'
        : 'text-sm font-medium text-white'
      
      const buttonClasses = isCompleted
        ? 'bg-blue-500 border-blue-500'
        : 'border-2'

      return {
        ...task,
        effectiveStatus,
        taskColor,
        formattedDate: task.due_date ? formatDate(task.due_date) : '',
        formattedTime: task.due_date ? formatTime(task.due_date) : null,
        formattedCourseCode: task.courses?.canvas_course_code
          ? formatCourseCode(task.courses.canvas_course_code)
          : null,
        isCompleted,
        textClasses,
        buttonClasses,
      }
    })
  }, [tasks, localTaskStates, getEffectiveStatus, getTaskColor, formatDate, formatTime])

  return { enhancedTasks }
}

