import { useMemo } from 'react'
import type { Task } from '../../../lib/utils/types'

type ExamTimeFilter = 'week' | 'month' | 'all' | 'past'

interface UseExamFilteringProps {
  examTasks: Task[]
  timeFilter: ExamTimeFilter
  searchQuery: string
}

export function useExamFiltering({
  examTasks,
  timeFilter,
  searchQuery,
}: UseExamFilteringProps) {
  const { today, endOfWeek, endOfMonth } = useMemo(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const endOfWeek = new Date(today)
    endOfWeek.setDate(endOfWeek.getDate() + 7)
    const endOfMonth = new Date(today)
    endOfMonth.setMonth(endOfMonth.getMonth() + 1)
    return { today, endOfWeek, endOfMonth }
  }, [new Date().toDateString()])

  const { sortedCurrentExams, sortedPastExams, upcomingExams } = useMemo(() => {
    // Filter exams based on time filter
    let filteredExams = examTasks.filter(exam => {
      if (!exam.due_date) return false
      const examDate = new Date(exam.due_date)
      examDate.setHours(0, 0, 0, 0)
      
      switch (timeFilter) {
        case 'week':
          return examDate >= today && examDate <= endOfWeek
        case 'month':
          return examDate >= today && examDate <= endOfMonth
        case 'all':
          return examDate >= today
        case 'past':
          return examDate < today
        default:
          return examDate >= today && examDate <= endOfWeek
      }
    })

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filteredExams = filteredExams.filter(exam => 
        exam.title?.toLowerCase().includes(query) ||
        exam.courses?.canvas_course_code?.toLowerCase().includes(query)
      )
    }

    // Sort by due date
    const sorted = filteredExams.sort((a, b) => {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA.getTime() - dateB.getTime()
    })

    // Split into current and past
    const current = sorted.filter(exam => {
      const examDate = new Date(exam.due_date)
      examDate.setHours(0, 0, 0, 0)
      return examDate >= today
    })

    const past = sorted.filter(exam => {
      const examDate = new Date(exam.due_date)
      examDate.setHours(0, 0, 0, 0)
      return examDate < today
    })

    // Get upcoming exams for card preview (this week + next week, max 4)
    const endOfNextWeek = new Date(today)
    endOfNextWeek.setDate(endOfNextWeek.getDate() + 14)
    const upcoming = examTasks
      .filter(exam => {
        if (!exam.due_date) return false
        const examDate = new Date(exam.due_date)
        examDate.setHours(0, 0, 0, 0)
        return examDate >= today && examDate <= endOfNextWeek
      })
      .sort((a, b) => {
        const dateA = new Date(a.due_date)
        const dateB = new Date(b.due_date)
        return dateA.getTime() - dateB.getTime()
      })
      .slice(0, 4)

    return {
      sortedCurrentExams: current,
      sortedPastExams: past,
      upcomingExams: upcoming,
    }
  }, [examTasks, timeFilter, searchQuery, today, endOfWeek, endOfMonth])

  return {
    sortedCurrentExams,
    sortedPastExams,
    upcomingExams,
    today,
    endOfWeek,
    endOfMonth,
  }
}

