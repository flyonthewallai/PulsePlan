import { Calendar, Clock, Tag, Check } from 'lucide-react'
import type { Todo } from '../../services/tasks'

interface TodoListItemProps {
  todo: Todo
  isCompleted: boolean
  onToggle: (todoId: string) => void
  variant?: 'card' | 'modal'
  showDateDivider?: boolean
  dateLabel?: string
  formatDate: (dateString: string) => string
  formatTime: (dateString: string) => string
}

export function TodoListItem({
  todo,
  isCompleted,
  onToggle,
  variant = 'card',
  showDateDivider = false,
  dateLabel,
  formatDate,
  formatTime,
}: TodoListItemProps) {
  if (variant === 'card') {
    return (
      <div className="flex items-start gap-3 relative">
        <button
          className={`w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
            isCompleted
              ? 'bg-blue-500 border-blue-500' 
              : 'border-gray-500'
          }`}
          onClick={(e) => {
            e.stopPropagation()
            onToggle(todo.id)
          }}
        >
          {isCompleted && (
            <Check size={8} className="text-white" strokeWidth={3} />
          )}
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className={`text-sm font-medium leading-tight ${
              isCompleted 
                ? 'line-through text-gray-400' 
                : 'text-white'
            }`}>
              {todo.title}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {todo.tags && todo.tags.length > 0 && (
                <div className="flex items-center gap-1 bg-neutral-800/60 rounded px-1.5 py-0.5">
                  <Tag size={8} className="text-gray-500" />
                  <span className="text-xs text-gray-400">{todo.tags[0]}</span>
                </div>
              )}
              {todo.due_date && (
                <>
                  <div className="flex items-center gap-1">
                    <Calendar size={10} className="text-gray-400" />
                    <span className="text-xs text-gray-400">
                      {formatDate(todo.due_date)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock size={10} className="text-gray-400" />
                    <span className="text-xs text-gray-400">
                      {formatTime(todo.due_date)}
                    </span>
                  </div>
                </>
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
            isCompleted
              ? 'bg-blue-500 border-blue-500'
              : 'border-gray-500'
          }`}
          onClick={(e) => {
            e.stopPropagation()
            onToggle(todo.id)
          }}
        >
          {isCompleted && (
            <Check size={12} className="text-white" strokeWidth={3} />
          )}
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className={`text-base font-medium leading-tight flex-shrink ${
              isCompleted
                ? 'line-through text-gray-400'
                : 'text-white'
            }`}>
              {todo.title}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {todo.tags && todo.tags.length > 0 && (
                <div className="flex items-center gap-1">
                  <div className="flex items-center gap-1 bg-neutral-800/60 rounded px-2 py-0.5">
                    <Tag size={9} className="text-gray-500" />
                    <span className="text-xs text-gray-400">{todo.tags[0]}</span>
                  </div>
                </div>
              )}
              {todo.due_date && (
                <>
                  <div className="flex items-center gap-1.5">
                    <Calendar size={11} className="text-gray-500" />
                    <span className="text-xs text-gray-400">
                      {formatDate(todo.due_date)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock size={11} className="text-gray-500" />
                    <span className="text-xs text-gray-400">
                      {formatTime(todo.due_date)}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

