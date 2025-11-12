import React, { useMemo, useState, useCallback, useEffect } from 'react'
import { GraduationCap, X, Loader2 } from 'lucide-react'
import { useTasks } from '@/hooks/tasks'
import { format, isToday, isTomorrow } from 'date-fns'
import type { Task } from '../../lib/utils/types'
import { useExamFiltering } from './hooks/useExamFiltering'
import { ExamListItem } from './ExamListItem'
import { UpcomingExamsCardModal } from './UpcomingExamsCardModal'

type ExamTimeFilter = 'week' | 'month' | 'all' | 'past'

export function UpcomingExamsCard() {
  const [showModal, setShowModal] = useState(false)
  const [timeFilter, setTimeFilter] = useState<ExamTimeFilter>('week')
  const [searchQuery, setSearchQuery] = useState('')
  
  const { data: allTasksData = [], isLoading, error } = useTasks()

  // Filter for quizzes and exams only
  const examTasks = useMemo(() => {
    return allTasksData.filter(task => {
      const taskType = task.task_type?.toLowerCase()
      if (taskType === 'quiz' || taskType === 'exam') {
        return true
      }
      
      const title = task.title?.toLowerCase() || ''
      const examKeywords = [
        'exam', 'quiz', 'test', 'midterm', 'assessment', 
        'examination', 'mid-term', 'final exam', 'quiz exam',
        'unit test', 'chapter test', 'pop quiz', 'surprise quiz'
      ]
      
      return examKeywords.some(keyword => title.includes(keyword))
    })
  }, [allTasksData])

  // Use filtering hook
  const { sortedCurrentExams, sortedPastExams, upcomingExams } = useExamFiltering({
    examTasks,
    timeFilter,
    searchQuery,
  })

  // Format date for display
  const formatExamDate = (dueDate: string) => {
    const examDate = new Date(dueDate)
    
    if (isToday(examDate)) {
      return 'Today'
    } else if (isTomorrow(examDate)) {
      return 'Tomorrow'
    } else {
      return format(examDate, 'MMM d')
    }
  }

  // Format time for display
  const formatExamTime = (dueDate: string) => {
    const examDate = new Date(dueDate)
    return format(examDate, 'h:mm a')
  }

  // Get task color
  const getTaskColor = (task: Task) => {
    if (task.color) return task.color
    if (task.courses?.color) return task.courses.color
    return '#3B82F6' // Default blue
  }

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

  if (isLoading) {
    return (
      <div className="w-full">
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 min-h-[200px] flex flex-col">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              UPCOMING EXAMS
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <GraduationCap size={16} className="text-gray-400" />
            </div>
          </div>
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="w-8 h-8 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <Loader2 size={16} className="text-gray-400 animate-spin" />
              </div>
              <div className="text-sm font-medium text-gray-400 mb-1">
                Loading exams...
              </div>
              <div className="text-xs text-gray-400">
                Please wait
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full">
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 min-h-[200px] flex flex-col">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              UPCOMING EXAMS
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <GraduationCap size={16} className="text-gray-400" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-4 h-4 rounded-full border-2 border-red-500 flex items-center justify-center mt-0.5">
                <X size={10} className="text-red-400" />
              </div>
              <div className="flex-1">
                <span className="text-sm font-medium text-red-400">
                  Error loading exams
                </span>
                <div className="text-xs text-gray-500 mt-1">
                  {error instanceof Error ? error.message : 'Failed to load exams'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="w-full">
        <div 
          className="bg-neutral-800/40 border border-gray-700/50 rounded-xl p-4 cursor-pointer hover:bg-neutral-800/60 transition-colors h-full flex flex-col"
          onClick={() => setShowModal(true)}
        >
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gray-400">
              UPCOMING EXAMS
            </span>
            <div className="w-4 h-4 flex items-center justify-center">
              <GraduationCap size={16} className="text-gray-400" />
            </div>
          </div>
          
          <div className="space-y-2.5 flex-1 flex flex-col">
            {upcomingExams.length > 0 ? (
              <div className="space-y-2">
                {upcomingExams.map((exam) => (
                  <ExamListItem
                    key={exam.id}
                    exam={exam}
                    variant="card"
                    formatExamDate={formatExamDate}
                    formatExamTime={formatExamTime}
                    getTaskColor={getTaskColor}
                  />
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-400 text-center py-4">
                No upcoming exams
              </div>
            )}
          </div>
        </div>
      </div>

      <UpcomingExamsCardModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        timeFilter={timeFilter}
        onFilterChange={setTimeFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        sortedCurrentExams={sortedCurrentExams}
        sortedPastExams={sortedPastExams}
        isLoading={isLoading}
        error={error}
        formatExamDate={formatExamDate}
        formatExamTime={formatExamTime}
        getTaskColor={getTaskColor}
      />
    </>
  )
}
