import { useMemo } from 'react'
import { AlertTriangle } from 'lucide-react'
import { useTasks } from '../hooks/useTasks'
import { useTaskUpdates } from '../hooks/useTaskUpdates'
import { format, isToday, isTomorrow, isAfter } from 'date-fns'
import type { Task } from '../lib/utils/types'

export function UpcomingCard() {
  // Enable real-time task updates
  useTaskUpdates()
  
  // Fetch tasks to get quizzes and exams
  const { data: allTasksData = [], isLoading } = useTasks()
  
  // Filter for quizzes and exams only
  const quizzesAndExams = useMemo(() => {
    return allTasksData.filter(task =>
      task.status !== 'cancelled' &&
      (task.task_type === 'quiz' || task.task_type === 'exam')
    )
  }, [allTasksData])
  
  // Get upcoming quizzes and exams (next 7 days)
  const upcomingItems = useMemo(() => {
    const today = new Date()
    const nextWeek = new Date()
    nextWeek.setDate(today.getDate() + 7)
    
    return quizzesAndExams
      .filter(task => {
        if (!task.due_date) return false
        const taskDate = new Date(task.due_date)
        return taskDate >= today && taskDate <= nextWeek
      })
      .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())
      .slice(0, 4) // Show max 4 items
  }, [quizzesAndExams])

  // Format date for display
  const formatItemDate = (dueDate: string) => {
    const taskDate = new Date(dueDate)
    
    if (isToday(taskDate)) {
      return 'Today'
    } else if (isTomorrow(taskDate)) {
      return 'Tomorrow'
    } else {
      return format(taskDate, 'MMM d')
    }
  }

  // Format time for display
  const formatItemTime = (dueDate: string) => {
    const taskDate = new Date(dueDate)
    return format(taskDate, 'h:mm a')
  }

  // Get color based on task type
  const getItemColor = (taskType: string) => {
    switch (taskType) {
      case 'exam':
        return 'border-red-500 bg-red-500'
      case 'quiz':
        return 'border-orange-500 bg-orange-500'
      default:
        return 'border-blue-500 bg-blue-500'
    }
  }

  if (isLoading) {
    return (
      <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4 px-1">
          <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
            UPCOMING 
          </span>
          <div className="w-4 h-4 flex items-center justify-center">
            <AlertTriangle size={16} className="text-gray-400" />
          </div>
        </div>
        <div className="space-y-3">
          <div className="text-sm text-gray-400 text-center py-4">
            Loading upcoming items...
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4">
      <div className="flex items-center justify-between mb-4 px-1">
        <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
          UPCOMING 
        </span>
        <div className="w-4 h-4 flex items-center justify-center">
          <AlertTriangle size={16} className="text-gray-400" />
        </div>
      </div>
      
      {upcomingItems.length > 0 ? (
        <div className="space-y-3">
          {upcomingItems.map((item) => (
            <div key={item.id} className="flex items-start gap-3">
              <div className={`w-4 h-4 rounded-full border-2 ${getItemColor(item.task_type)} flex items-center justify-center mt-0.5 flex-shrink-0`}>
                <div className={`w-2 h-2 ${getItemColor(item.task_type).split(' ')[1]} rounded-full`}></div>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-white">{item.title}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {formatItemDate(item.due_date)} at {formatItemTime(item.due_date)}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-gray-400 text-center py-4">
          No upcoming quizzes or exams
        </div>
      )}
    </div>
  )
}

