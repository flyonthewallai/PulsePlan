import { useMemo } from 'react'
import type { Task } from '../../../lib/utils/types'

type TimeFilter = 'week' | 'month' | 'all' | 'past'

interface UseTaskFilteringProps {
  tasks: Task[]
  timeFilter: TimeFilter
  searchQuery: string
}

export function useTaskFiltering({ tasks, timeFilter, searchQuery }: UseTaskFilteringProps) {
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
  }, [new Date().toDateString()])

  const { currentTasks, pastTasks } = useMemo(() => {
    let filtered = tasks

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
  }, [tasks, timeFilter, searchQuery, today, endOfWeek, endOfMonth])

  return {
    currentTasks,
    pastTasks,
    today,
    tomorrow,
    endOfWeek,
    endOfMonth,
  }
}

