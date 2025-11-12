import { Calendar, Clock, BookOpen } from 'lucide-react'
import type { Task } from '../../lib/utils/types'
import { formatCourseCode } from '../../lib/utils/formatters'

interface ExamListItemProps {
  exam: Task
  variant?: 'card' | 'modal'
  showDateDivider?: boolean
  dateLabel?: string
  formatExamDate: (dateString: string) => string
  formatExamTime: (dateString: string) => string
  getTaskColor: (exam: Task) => string
}

export function ExamListItem({
  exam,
  variant = 'card',
  showDateDivider = false,
  dateLabel,
  formatExamDate,
  formatExamTime,
  getTaskColor,
}: ExamListItemProps) {
  if (variant === 'card') {
    return (
      <div className="flex items-start gap-3 relative">
        <div
          className="w-2 h-2 rounded-full flex-shrink-0 mt-1.5"
          style={{ backgroundColor: getTaskColor(exam) }}
        ></div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-white leading-tight">
            {exam.title}
          </div>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            <div className="flex items-center gap-1">
              <Calendar size={10} className="text-gray-400" />
              <span className="text-xs text-gray-400">
                {formatExamDate(exam.due_date)}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Clock size={10} className="text-gray-400" />
              <span className="text-xs text-gray-400">
                {formatExamTime(exam.due_date)}
              </span>
            </div>
            {exam.courses?.canvas_course_code && (
              <div className="flex items-center gap-1">
                <BookOpen size={10} className="text-gray-400" />
                <span className="text-xs text-gray-400">
                  {formatCourseCode(exam.courses.canvas_course_code)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      {showDateDivider && dateLabel && (
        <div className="flex items-center gap-3 py-3 first:pt-0">
          <div className="h-px bg-gray-700/50 flex-1"></div>
          <span className="text-xs font-semibold text-gray-400">
            {dateLabel}
          </span>
          <div className="h-px bg-gray-700/50 flex-1"></div>
        </div>
      )}
      <div className="flex items-start gap-3 p-3 rounded-xl bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/50 transition-colors group">
        <div
          className="w-2 h-2 rounded-full flex-shrink-0 mt-2"
          style={{ backgroundColor: getTaskColor(exam) }}
        ></div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-3">
            <div className="text-base font-medium text-white">
              {exam.title}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {exam.courses?.canvas_course_code && (
                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-neutral-800/50">
                  <span className="text-xs font-medium text-gray-300">
                    {formatCourseCode(exam.courses.canvas_course_code)}
                  </span>
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <Calendar size={11} className="text-gray-500" />
                <span className="text-xs text-gray-400">
                  {formatExamDate(exam.due_date)}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Clock size={11} className="text-gray-500" />
                <span className="text-xs text-gray-400">
                  {formatExamTime(exam.due_date)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

