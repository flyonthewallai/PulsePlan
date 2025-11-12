import React from 'react'
import { X, Search, Loader2 } from 'lucide-react'
import { TaskFilterTabs } from './TaskFilterTabs'
import { ExamListItem } from './ExamListItem'
import type { Task } from '../../lib/utils/types'

type ExamTimeFilter = 'week' | 'month' | 'all' | 'past'

interface UpcomingExamsCardModalProps {
  isOpen: boolean
  onClose: () => void
  timeFilter: ExamTimeFilter
  onFilterChange: (filter: ExamTimeFilter) => void
  searchQuery: string
  onSearchChange: (query: string) => void
  sortedCurrentExams: Task[]
  sortedPastExams: Task[]
  isLoading: boolean
  error: Error | null
  formatExamDate: (dateString: string) => string
  formatExamTime: (dateString: string) => string
  getTaskColor: (exam: Task) => string
}

export function UpcomingExamsCardModal({
  isOpen,
  onClose,
  timeFilter,
  onFilterChange,
  searchQuery,
  onSearchChange,
  sortedCurrentExams,
  sortedPastExams,
  isLoading,
  error,
  formatExamDate,
  formatExamTime,
  getTaskColor,
}: UpcomingExamsCardModalProps) {
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      e.preventDefault()
      e.stopPropagation()
      onClose()
    }
  }

  const getDateLabel = (dateString: string): string => {
    const examDate = new Date(dateString)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (examDate.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (examDate.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow'
    } else {
      return examDate.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      })
    }
  }

  const getEmptyMessage = () => {
    if (searchQuery.trim()) {
      return {
        message: `No results for "${searchQuery}"`,
        subMessage: 'Try a different search term'
      }
    }

    if (timeFilter === 'past') {
      return {
        message: 'No completed exams',
        subMessage: 'All caught up!'
      }
    } else if (timeFilter === 'week') {
      return {
        message: 'No exams this week',
        subMessage: 'Looking good!'
      }
    } else if (timeFilter === 'month') {
      return {
        message: 'No exams this month',
        subMessage: 'Looking good!'
      }
    } else {
      return {
        message: 'No upcoming exams',
        subMessage: 'All caught up!'
      }
    }
  }

  const examsToShow = timeFilter === 'past' ? sortedPastExams : sortedCurrentExams
  const showDateDividers = timeFilter !== 'past'
  const emptyMessage = getEmptyMessage()

  return (
    <div
      className={`fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300 cursor-default ${
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
      onClick={handleBackdropClick}
    >
      <div
        className={`border border-gray-700/50 w-full max-w-3xl rounded-xl h-[75vh] flex flex-col cursor-default transition-all duration-300 shadow-2xl ${
          isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        style={{ backgroundColor: '#121212' }}
        onClick={(e) => e.stopPropagation()}
      >
        {isOpen ? (
          <>
            {/* Header */}
            <div className="p-5 border-b border-gray-700/30">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white tracking-tight">
                  Upcoming Exams
                </h2>
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onClose()
                  }}
                  className="p-1.5 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-neutral-800/60"
                  aria-label="Close modal"
                  type="button"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Stats Bar */}
              <div className="flex items-center gap-5 text-sm">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-bold text-white tabular-nums">
                    {timeFilter === 'past' ? sortedPastExams.length : sortedCurrentExams.length}
                  </span>
                  <span className="text-gray-400 font-medium">
                    {timeFilter === 'past' ? 'completed' : 'upcoming'}
                  </span>
                </div>
                <div className="h-3 w-px bg-gray-700/50"></div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-lg font-semibold text-white tabular-nums">
                    {sortedCurrentExams.length + sortedPastExams.length}
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

            {/* Controls Bar */}
            <div className="px-5 py-3 border-b border-gray-700/30">
              <div className="flex items-center gap-3">
                {/* Search Bar */}
                <div className="relative flex-1">
                  <Search size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search exams..."
                    value={searchQuery}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-neutral-900/50 border border-gray-700/50 text-white placeholder-gray-500 focus:outline-none focus:border-gray-600 transition-colors text-sm"
                  />
                </div>

                {/* Time Filter Tabs */}
                <TaskFilterTabs timeFilter={timeFilter} onFilterChange={onFilterChange} />
              </div>
            </div>

            {/* Exams list */}
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
                      Loading exams...
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
                      Error loading exams
                    </div>
                    <div className="text-xs text-gray-500">
                      {error instanceof Error ? error.message : 'Failed to load exams'}
                    </div>
                  </div>
                </div>
              ) : examsToShow.length > 0 ? (
                <div className="space-y-2">
                  {examsToShow.map((exam, index) => {
                    const currentDate = exam.due_date ? new Date(exam.due_date).toDateString() : null
                    const previousDate = index > 0 && examsToShow[index - 1].due_date
                      ? new Date(examsToShow[index - 1].due_date).toDateString()
                      : null
                    const showDateDivider = showDateDividers && currentDate && currentDate !== previousDate

                    return (
                      <ExamListItem
                        key={exam.id}
                        exam={exam}
                        variant="modal"
                        showDateDivider={showDateDivider}
                        dateLabel={showDateDivider && exam.due_date ? getDateLabel(exam.due_date) : undefined}
                        formatExamDate={formatExamDate}
                        formatExamTime={formatExamTime}
                        getTaskColor={getTaskColor}
                      />
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-16">
                  <div className="text-sm font-medium text-gray-400 mb-1">
                    {emptyMessage.message}
                  </div>
                  <div className="text-xs text-gray-500">
                    {emptyMessage.subMessage}
                  </div>
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

