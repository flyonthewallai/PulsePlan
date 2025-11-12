import { useState, useMemo, useEffect, useRef } from 'react'
import { usePageTitle } from '@/hooks/ui'
import {
  Search,
  Plus,
  CheckCircle2,
  Circle,
  ChevronRight,
  Calendar,
  Clock,
  Check,
  List,
  LayoutGrid
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { components } from '@/lib/design-tokens'
import { useTasks } from '@/hooks/tasks'
import { useTodos } from '@/hooks/todos'
import { useToggleTask } from '@/hooks/tasks'
import { useToggleTodo } from '@/hooks/todos'
import { TaskModal } from '@/features/tasks/TaskModal'
import { TaskboardAIModal } from '@/features/tasks/components/TaskboardAIModal'
import { KanbanView } from '@/features/tasks/components/KanbanView'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { PulseTrace } from '@/components/ui/common'
import type { Task } from '@/types'
import { format, parseISO } from 'date-fns'
import { useProfile } from '@/hooks/profile'
import { useUpdateTask } from '@/hooks/tasks'

type ViewMode = 'all' | 'todos' | 'assignments'
type DisplayMode = 'list' | 'kanban'

interface TaskboardItem {
  id: string
  type: 'task' | 'todo'
  title: string
  description?: string
  dueDate?: string
  priority: 'low' | 'medium' | 'high'
  status?: string
  courseName?: string
  courseColor?: string
  tags?: string[]
  isCompleted: boolean
  estimatedMinutes?: number
  originalData: any // Use any to avoid type conflicts between different Task definitions
}

function TaskboardPageCore() {
  usePageTitle('Taskboard')
  const [viewMode, setViewMode] = useState<ViewMode>('all')
  const [displayMode, setDisplayMode] = useState<DisplayMode>('list')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [showAIModal, setShowAIModal] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)
  const tooltipTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // Profile for greeting personalization
  const { data: profile } = useProfile()
  const displayName = profile?.full_name?.split(' ')[0] || 'there'

  // Fetch tasks and todos
  const { data: tasks = [], isLoading: tasksLoading } = useTasks()
  const { data: todosResponse, isLoading: todosLoading } = useTodos()
  
  // Toggle mutations
  const toggleTask = useToggleTask()
  const toggleTodo = useToggleTodo()
  const updateTask = useUpdateTask()

  // Extract todos from response structure
  const todos = todosResponse?.data || []

  const isLoading = tasksLoading || todosLoading

  // Transform data into unified format
  const taskboardItems: TaskboardItem[] = useMemo(() => {
    const items: TaskboardItem[] = []

    // Add tasks (Canvas assignments)
    if (viewMode === 'all' || viewMode === 'assignments') {
      tasks.forEach((task: any) => {
        const isCompleted = ['completed', 'done', 'finished'].includes(task.status)

        items.push({
          id: task.id,
          type: 'task',
          title: task.title,
          description: task.description,
          dueDate: task.due_date,
          priority: task.priority,
          status: task.status,
          courseName: task.courses?.name || task.courses?.canvas_course_code,
          courseColor: task.courses?.color || task.color,
          isCompleted,
          estimatedMinutes: task.estimated_minutes,
          originalData: task
        })
      })
    }

    // Add todos
    if (viewMode === 'all' || viewMode === 'todos') {
      todos.forEach((todo: any) => {
        items.push({
          id: todo.id,
          type: 'todo',
          title: todo.title,
          description: todo.description,
          dueDate: todo.due_date,
          priority: todo.priority,
          tags: todo.tags,
          isCompleted: todo.completed,
          estimatedMinutes: todo.estimated_minutes,
          originalData: todo
        })
      })
    }

    // Sort by due date (soonest first), then by priority
    return items.sort((a, b) => {
      if (!a.dueDate && !b.dueDate) return 0
      if (!a.dueDate) return 1
      if (!b.dueDate) return -1

      const dateCompare = new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
      if (dateCompare !== 0) return dateCompare

      const priorityOrder = { high: 0, medium: 1, low: 2 }
      return priorityOrder[a.priority] - priorityOrder[b.priority]
    })
  }, [tasks, todos, viewMode])

  // Filter by search query
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return taskboardItems

    const query = searchQuery.toLowerCase()
    return taskboardItems.filter(item =>
      item.title.toLowerCase().includes(query) ||
      item.description?.toLowerCase().includes(query) ||
      item.courseName?.toLowerCase().includes(query) ||
      item.tags?.some(tag => tag.toLowerCase().includes(query))
    )
  }, [taskboardItems, searchQuery])

  const handleItemClick = (item: TaskboardItem) => {
    if (item.type === 'task') {
      setSelectedTask(item.originalData as Task)
      setShowTaskModal(true)
    }
  }

  const handleCreateTask = () => {
    setSelectedTask(null)
    setShowTaskModal(true)
  }

  const handleToggleCompletion = (e: React.MouseEvent, item: TaskboardItem) => {
    e.stopPropagation() // Prevent opening the modal
    
    if (item.type === 'task') {
      toggleTask.mutate(item.id)
    } else {
      toggleTodo.mutate(item.id)
    }
  }

  const handleStatusChange = (itemId: string, newStatus: 'todo' | 'in_progress' | 'done') => {
    const item = filteredItems.find(i => i.id === itemId)
    if (!item) return

    // Map kanban status to task status
    let statusUpdate: string
    if (newStatus === 'done') {
      statusUpdate = 'completed'
    } else if (newStatus === 'in_progress') {
      statusUpdate = 'in_progress'
    } else {
      statusUpdate = 'pending'
    }

    if (item.type === 'task') {
      updateTask.mutate({
        id: itemId,
        updates: { status: statusUpdate as any }
      })
    } else {
      // For todos, we can only mark as completed/pending
      if (newStatus === 'done') {
        toggleTodo.mutate(itemId)
      } else {
        // Toggle from completed back to pending
        toggleTodo.mutate(itemId)
      }
    }
  }

  const formatCourseCode = (courseCode: string): string => {
    const match = courseCode.match(/^([A-Za-z]+)\s*(\d{4})/)
    if (match) return `${match[1]} ${match[2]}`

    const match3 = courseCode.match(/^([A-Za-z]+)\s*(\d{3})/)
    if (match3) return `${match3[1]} ${match3[2]}`

    return courseCode
  }

  const formatDueDate = (dateStr?: string) => {
    if (!dateStr) return null
    try {
      const date = parseISO(dateStr)
      const now = new Date()
      const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

      if (diffDays < 0) return <span className="text-gray-500">Overdue</span>
      if (diffDays === 0) return <span className="text-gray-500">Today</span>
      if (diffDays === 1) return <span className="text-gray-500">Tomorrow</span>
      if (diffDays <= 7) return <span className="text-gray-500">{format(date, 'EEE, MMM d')}</span>

      return <span className="text-gray-500">{format(date, 'MMM d, yyyy')}</span>
    } catch {
      return null
    }
  }

  // Handle tooltip hover with delay
  const handleMouseEnter = () => {
    tooltipTimeoutRef.current = setTimeout(() => {
      setShowTooltip(true)
    }, 1500) // 1.5 second delay
  }

  const handleMouseLeave = () => {
    if (tooltipTimeoutRef.current) {
      clearTimeout(tooltipTimeoutRef.current)
      tooltipTimeoutRef.current = null
    }
    setShowTooltip(false)
  }

  // Handle 'P' key to open/close AI modal
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'p' || e.key === 'P') {
        // Don't trigger if user is typing in an input/textarea
        const target = e.target as HTMLElement
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
          return
        }
        e.preventDefault()
        
        if (showAIModal) {
          setShowAIModal(false)
        } else {
          setShowAIModal(true)
        }
      }
    }

    document.addEventListener('keydown', handleKeyPress)
    return () => {
      document.removeEventListener('keydown', handleKeyPress)
    }
  }, [showAIModal])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current)
      }
    }
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center" style={{ backgroundColor: '#0f0f0f' }}>
      <div className="w-full max-w-5xl px-6 pt-24 pb-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-white">Taskboard</h1>

          {/* View Toggle (List/Kanban) */}
          <div className="flex items-center bg-neutral-800/40 border border-gray-700/50 rounded-lg p-0.5">
            <button
              onClick={() => setDisplayMode('list')}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5',
                displayMode === 'list'
                  ? 'bg-white text-black'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              <List size={14} />
              List
            </button>
            <button
              onClick={() => setDisplayMode('kanban')}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5',
                displayMode === 'kanban'
                  ? 'bg-white text-black'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              <LayoutGrid size={14} />
              Kanban
            </button>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => setViewMode('all')}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              viewMode === 'all'
                ? 'bg-neutral-800/60 border border-gray-700/50 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            All
          </button>
          <button
            onClick={() => setViewMode('assignments')}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              viewMode === 'assignments'
                ? 'bg-neutral-800/60 border border-gray-700/50 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            Assignments
          </button>
          <button
            onClick={() => setViewMode('todos')}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              viewMode === 'todos'
                ? 'bg-neutral-800/60 border border-gray-700/50 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            Todos
          </button>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search taskboard..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-2 bg-neutral-800/40 border border-gray-700/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-gray-600 text-sm min-w-[300px]"
              />
            </div>
          </div>

          {/* Add Button */}
          <button
            onClick={handleCreateTask}
            className={cn(
              components.button.base,
              components.button.primary,
              'flex items-center gap-2'
            )}
          >
            <Plus size={16} />
            New Task
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-400">Loading taskboard...</div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredItems.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="text-gray-400 text-lg mb-2">
              {searchQuery ? 'No items match your search' : 'No items to display'}
            </div>
            <div className="text-gray-500 text-sm">
              Add a new task to get started
            </div>
          </div>
        )}

        {/* Taskboard Items - List or Kanban View */}
        {!isLoading && filteredItems.length > 0 && (
          displayMode === 'kanban' ? (
            <KanbanView
              items={filteredItems}
              onStatusChange={handleStatusChange}
              onItemClick={handleItemClick}
              onToggleCompletion={handleToggleCompletion}
              toggleTaskPending={toggleTask.isPending}
              toggleTodoPending={toggleTodo.isPending}
              formatCourseCode={formatCourseCode}
            />
          ) : (
            <div className="space-y-2">
              {filteredItems.map((item) => {
              const taskColor = item.courseColor || '#6B7280'
              const dueDateFormatted = item.dueDate ? parseISO(item.dueDate) : null
              const timeFormatted = dueDateFormatted ? format(dueDateFormatted, 'h:mm a') : null
              
              // Format date for display
              let dateFormatted: string | null = null
              if (item.dueDate && dueDateFormatted) {
                const now = new Date()
                const diffDays = Math.ceil((dueDateFormatted.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
                
                if (diffDays < 0) {
                  dateFormatted = 'Overdue'
                } else if (diffDays === 0) {
                  dateFormatted = 'Today'
                } else if (diffDays === 1) {
                  dateFormatted = 'Tomorrow'
                } else if (diffDays <= 7) {
                  dateFormatted = format(dueDateFormatted, 'EEE, MMM d')
                } else {
                  dateFormatted = format(dueDateFormatted, 'MMM d, yyyy')
                }
              }

              return (
                <div
                  key={`${item.type}-${item.id}`}
                  onClick={() => handleItemClick(item)}
                  className="flex items-start gap-3 p-3 rounded-xl bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/50 transition-colors group cursor-pointer"
                >
                  {/* Circular Checkbox */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleToggleCompletion(e, item)
                    }}
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-colors duration-150 ${
                      item.isCompleted
                        ? 'bg-blue-500 border-blue-500'
                        : 'border-2'
                    }`}
                    style={{
                      backgroundColor: item.isCompleted ? '#3B82F6' : 'transparent',
                      borderColor: item.isCompleted ? '#3B82F6' : taskColor
                    }}
                    disabled={toggleTask.isPending || toggleTodo.isPending}
                  >
                    {item.isCompleted && (
                      <Check size={12} className="text-white" strokeWidth={3} />
                    )}
                  </button>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-3">
                      <div className={cn(
                        'text-base font-medium leading-tight',
                        item.isCompleted ? 'line-through text-gray-400' : 'text-white'
                      )}>
                        {item.title}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {/* Course Code */}
                        {item.courseName && (
                          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-neutral-800/50">
                            <span className="text-xs font-medium text-gray-300">
                              {formatCourseCode(item.courseName)}
                            </span>
                          </div>
                        )}
                        {/* Date */}
                        {dateFormatted && (
                          <div className="flex items-center gap-1.5">
                            <Calendar size={11} className="text-gray-500" />
                            <span className="text-xs text-gray-400">
                              {dateFormatted}
                            </span>
                          </div>
                        )}
                        {/* Time */}
                        {timeFormatted && (
                          <div className="flex items-center gap-1.5">
                            <Clock size={11} className="text-gray-500" />
                            <span className="text-xs text-gray-400">
                              {timeFormatted}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
              })}
            </div>
          )
        )}
      </div>

      {/* Task Modal */}
      {showTaskModal && (
        <TaskModal
          task={selectedTask}
          onClose={() => {
            setShowTaskModal(false)
            setSelectedTask(null)
          }}
        />
      )}

      {/* Floating Pulse Button */}
      {!showAIModal && (
        <div className="fixed bottom-6 right-6 z-50">
          <button
            onClick={() => setShowAIModal(true)}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            className="w-16 h-16 bg-neutral-800/80 border border-gray-700/50 rounded-full flex items-center justify-center shadow-lg backdrop-blur-sm hover:bg-neutral-700/80 transition-colors"
          >
            <PulseTrace active={true} width={32} height={32} />
          </button>
          
          {/* Tooltip */}
          <div className={`absolute bottom-full right-0 mb-2 transition-opacity duration-200 pointer-events-none ${
            showTooltip ? 'opacity-100' : 'opacity-0'
          }`}>
            <div className="bg-neutral-800/90 border border-gray-600/50 rounded-lg px-3 py-2 shadow-lg backdrop-blur-sm">
              <p className="text-white text-sm whitespace-nowrap">Press 'P' anywhere to summon Pulse</p>
            </div>
            {/* Arrow pointing down */}
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-neutral-800/90"></div>
          </div>
        </div>
      )}

      {/* AI Modal */}
      <TaskboardAIModal
        visible={showAIModal}
        onClose={() => setShowAIModal(false)}
        userName={displayName}
      />
    </div>
  )
}

// Wrap with ErrorBoundary to prevent taskboard errors from breaking the entire app
export function TaskboardPage() {
  return (
    <ErrorBoundary>
      <TaskboardPageCore />
    </ErrorBoundary>
  )
}
