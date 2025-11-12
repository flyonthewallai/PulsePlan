import { Calendar, Clock, BookOpen } from 'lucide-react'
import type { EnhancedTask } from './hooks/useTaskFormatting'

interface TaskListItemProps {
  task: EnhancedTask
  onToggle: (taskId: string) => void
  variant?: 'card' | 'modal'
  showDateDivider?: boolean
  dateLabel?: string
}

export function TaskListItem({
  task,
  onToggle,
  variant = 'card',
  showDateDivider = false,
  dateLabel,
}: TaskListItemProps) {
  if (variant === 'card') {
    return (
      <div className="flex items-start gap-3 relative">
        <button
          className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
            task.isCompleted ? 'bg-blue-500 border-blue-500' : ''
          }`}
          style={{
            backgroundColor: task.isCompleted ? '#3B82F6' : 'transparent',
            borderColor: task.isCompleted ? '#3B82F6' : task.taskColor
          }}
          onClick={(e) => {
            e.stopPropagation()
            onToggle(task.id)
          }}
        >
          {task.isCompleted && (
            <span className="text-white text-xs font-semibold">✓</span>
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
        <button
          className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
            task.isCompleted ? 'bg-blue-500 border-blue-500' : 'border-2'
          }`}
          style={{
            backgroundColor: task.isCompleted ? '#3B82F6' : 'transparent',
            borderColor: task.isCompleted ? '#3B82F6' : task.taskColor
          }}
          onClick={(e) => {
            e.stopPropagation()
            onToggle(task.id)
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
    </>
  )
}

