import React from 'react'
import { X, Search, Loader2 } from 'lucide-react'
import { TodoFilterTabs } from './TodoFilterTabs'
import { TodoListItem } from './TodoListItem'
import type { Todo } from '../../services/tasks'

type TodoTimeFilter = 'all' | 'due_soon'

interface SimpleTodosCardModalProps {
  isOpen: boolean
  onClose: () => void
  timeFilter: TodoTimeFilter
  onFilterChange: (filter: TodoTimeFilter) => void
  searchQuery: string
  onSearchChange: (query: string) => void
  currentTodos: Todo[]
  undatedTodos: Todo[]
  isLoading: boolean
  error: Error | null
  onToggleTodo: (todoId: string) => void
  getEffectiveCompletedState: (todo: Todo) => boolean
  formatDate: (dateString: string) => string
  formatTime: (dateString: string) => string
}

export function SimpleTodosCardModal({
  isOpen,
  onClose,
  timeFilter,
  onFilterChange,
  searchQuery,
  onSearchChange,
  currentTodos,
  undatedTodos,
  isLoading,
  error,
  onToggleTodo,
  getEffectiveCompletedState,
  formatDate,
  formatTime,
}: SimpleTodosCardModalProps) {
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      e.preventDefault()
      e.stopPropagation()
      onClose()
    }
  }

  const getDateLabel = (dateString: string): string => {
    const taskDate = new Date(dateString)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (taskDate.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (taskDate.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow'
    } else {
      return taskDate.toLocaleDateString('en-US', {
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
    } else if (timeFilter === 'all') {
      return {
        message: 'No to-dos found',
        subMessage: 'All caught up!'
      }
    } else {
      return {
        message: 'No to-dos due soon',
        subMessage: 'Nothing due in the next week!'
      }
    }
  }

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
                  To-Dos
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
                    {currentTodos.length + (undatedTodos.length || 0)}
                  </span>
                  <span className="text-gray-400 font-medium">
                    {timeFilter === 'all' ? 'total' : 'due soon'}
                  </span>
                </div>
                <div className="h-3 w-px bg-gray-700/50"></div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-lg font-semibold text-white tabular-nums">
                    {currentTodos.filter((t: Todo) => !getEffectiveCompletedState(t)).length}
                  </span>
                  <span className="text-gray-400 font-medium">incomplete</span>
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
                    placeholder="Search to-dos..."
                    value={searchQuery}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-neutral-900/50 border border-gray-700/50 text-white placeholder-gray-500 focus:outline-none focus:border-gray-600 transition-colors text-sm"
                  />
                </div>

                {/* Time Filter Tabs */}
                <TodoFilterTabs timeFilter={timeFilter} onFilterChange={onFilterChange} />
              </div>
            </div>

            {/* To-dos list */}
            <div
              className="flex-1 overflow-y-auto px-5 py-3"
              style={{
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgba(75, 85, 99, 0.3) transparent'
              }}
            >
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="w-8 h-8 bg-gray-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                      <Loader2 size={16} className="text-gray-400 animate-spin" />
                    </div>
                    <div className="text-sm font-medium text-gray-400 mb-1">
                      Loading to-dos...
                    </div>
                    <div className="text-xs text-gray-400">
                      Please wait
                    </div>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-red-500 text-xl font-semibold">!</span>
                    </div>
                    <div className="text-base font-semibold text-red-400 mb-2">
                      Error loading to-dos
                    </div>
                    <div className="text-sm text-gray-400">
                      {error instanceof Error ? error.message : 'Failed to load to-dos'}
                    </div>
                  </div>
                </div>
              ) : currentTodos.length > 0 || (timeFilter === 'all' && undatedTodos.length > 0) ? (
                <div className="space-y-2">
                  {/* Show dated todos first */}
                  {currentTodos.map((todo: Todo, index: number) => {
                    const showDateDivider = index === 0 || (() => {
                      if (!todo.due_date || !currentTodos[index - 1].due_date) return false
                      const currentDate = new Date(todo.due_date)
                      const previousDate = new Date(currentTodos[index - 1].due_date!)
                      return currentDate.toDateString() !== previousDate.toDateString()
                    })()

                    return (
                      <TodoListItem
                        key={todo.id}
                        todo={todo}
                        isCompleted={getEffectiveCompletedState(todo)}
                        onToggle={onToggleTodo}
                        variant="modal"
                        showDateDivider={showDateDivider}
                        dateLabel={showDateDivider && todo.due_date ? getDateLabel(todo.due_date) : undefined}
                        formatDate={formatDate}
                        formatTime={formatTime}
                      />
                    )
                  })}
                  
                  {/* Show undated todos at bottom for "all" filter */}
                  {timeFilter === 'all' && undatedTodos.length > 0 && (
                    <>
                      <div className="flex items-center gap-3 py-3">
                        <div className="h-px bg-gray-700/50 flex-1"></div>
                        <span className="text-xs font-semibold text-gray-400">
                          No due date
                        </span>
                        <div className="h-px bg-gray-700/50 flex-1"></div>
                      </div>

                      {undatedTodos.map((todo: Todo) => (
                        <div key={todo.id} className="flex items-start gap-3 p-3 rounded-lg bg-neutral-900/30 hover:bg-neutral-900/50 transition-colors group">
                          <button
                            className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                              getEffectiveCompletedState(todo)
                                ? 'bg-blue-500 border-blue-500'
                                : 'border-gray-500'
                            }`}
                            onClick={(e) => {
                              e.stopPropagation()
                              onToggleTodo(todo.id)
                            }}
                          >
                            {getEffectiveCompletedState(todo) && (
                              <span className="text-white text-xs font-bold">✓</span>
                            )}
                          </button>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-3">
                              <div className={`text-base font-medium leading-tight flex-shrink ${
                                getEffectiveCompletedState(todo)
                                  ? 'line-through text-gray-400'
                                  : 'text-white'
                              }`}>
                                {todo.title}
                              </div>
                              {todo.tags && todo.tags.length > 0 && (
                                <div className="flex items-center gap-1">
                                  <div className="flex items-center gap-1 bg-neutral-800/60 rounded px-2 py-0.5">
                                    <span className="text-xs text-gray-400">{todo.tags[0]}</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
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

