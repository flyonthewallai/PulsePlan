import { useMemo } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import {
  useDroppable,
} from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { Calendar, Clock, Check } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { cn } from '../../../lib/utils'

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
  originalData: any
}

type KanbanStatus = 'todo' | 'in_progress' | 'done'

interface KanbanColumn {
  id: KanbanStatus
  title: string
  items: TaskboardItem[]
}

interface KanbanViewProps {
  items: TaskboardItem[]
  onStatusChange: (itemId: string, newStatus: KanbanStatus) => void
  onItemClick: (item: TaskboardItem) => void
  onToggleCompletion: (e: React.MouseEvent, item: TaskboardItem) => void
  toggleTaskPending: boolean
  toggleTodoPending: boolean
  formatCourseCode: (code: string) => string
}

// Sortable task card component
function SortableTaskCard({
  item,
  onItemClick,
  onToggleCompletion,
  toggleTaskPending,
  toggleTodoPending,
  formatCourseCode,
}: {
  item: TaskboardItem
  onItemClick: (item: TaskboardItem) => void
  onToggleCompletion: (e: React.MouseEvent, item: TaskboardItem) => void
  toggleTaskPending: boolean
  toggleTodoPending: boolean
  formatCourseCode: (code: string) => string
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

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
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => onItemClick(item)}
      className="flex items-start gap-3 p-3 rounded-xl bg-neutral-800/40 border border-gray-700/50 hover:bg-neutral-800/50 transition-colors group cursor-grab active:cursor-grabbing"
    >
      {/* Circular Checkbox */}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onToggleCompletion(e, item)
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
        disabled={toggleTaskPending || toggleTodoPending}
      >
        {item.isCompleted && (
          <Check size={12} className="text-white" strokeWidth={3} />
        )}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className={cn(
          'text-base font-medium leading-tight mb-2',
          item.isCompleted ? 'line-through text-gray-400' : 'text-white'
        )}>
          {item.title}
        </div>
        
        {/* Metadata */}
        <div className="flex flex-wrap items-center gap-2">
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
  )
}

export function KanbanView({
  items,
  onStatusChange,
  onItemClick,
  onToggleCompletion,
  toggleTaskPending,
  toggleTodoPending,
  formatCourseCode,
}: KanbanViewProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // Map task statuses to kanban columns
  const mapStatusToKanban = (status?: string, isCompleted?: boolean): KanbanStatus => {
    if (isCompleted) return 'done'
    if (status === 'in_progress' || status === 'in-progress') return 'in_progress'
    if (status === 'completed' || status === 'done' || status === 'finished') return 'done'
    return 'todo' // pending, todo, or undefined
  }

  // Group items by status
  const columns: KanbanColumn[] = useMemo(() => {
    const todo: TaskboardItem[] = []
    const inProgress: TaskboardItem[] = []
    const done: TaskboardItem[] = []

    items.forEach((item) => {
      const kanbanStatus = mapStatusToKanban(item.status, item.isCompleted)
      if (kanbanStatus === 'todo') {
        todo.push(item)
      } else if (kanbanStatus === 'in_progress') {
        inProgress.push(item)
      } else {
        done.push(item)
      }
    })

    return [
      { id: 'todo', title: 'Todo', items: todo },
      { id: 'in_progress', title: 'In Progress', items: inProgress },
      { id: 'done', title: 'Done', items: done },
    ]
  }, [items])

  const handleDragEnd = (event: any) => {
    const { active, over } = event

    if (!over) return

    const itemId = active.id as string
    const overId = over.id as string

    // Check if dropped on a column (column ID matches)
    const isDroppingOnColumn = ['todo', 'in_progress', 'done'].includes(overId)
    
    if (isDroppingOnColumn) {
      // Find the item and its current column
      let currentColumn: KanbanStatus | null = null
      for (const column of columns) {
        if (column.items.some(item => item.id === itemId)) {
          currentColumn = column.id
          break
        }
      }

      // If dragging within the same column, just return (reordering not implemented)
      if (currentColumn === overId) return

      // Update status
      onStatusChange(itemId, overId as KanbanStatus)
    } else {
      // Dropping on another item - check if it's in a different column
      let sourceColumn: KanbanStatus | null = null
      let targetColumn: KanbanStatus | null = null
      
      for (const column of columns) {
        if (column.items.some(item => item.id === itemId)) {
          sourceColumn = column.id
        }
        if (column.items.some(item => item.id === overId)) {
          targetColumn = column.id
        }
      }

      // If dropped on an item in a different column, move to that column
      if (sourceColumn && targetColumn && sourceColumn !== targetColumn) {
        onStatusChange(itemId, targetColumn)
      }
    }
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((column) => (
          <DroppableColumn
            key={column.id}
            column={column}
            onItemClick={onItemClick}
            onToggleCompletion={onToggleCompletion}
            toggleTaskPending={toggleTaskPending}
            toggleTodoPending={toggleTodoPending}
            formatCourseCode={formatCourseCode}
          />
        ))}
      </div>
    </DndContext>
  )
}

// Droppable Column Component
function DroppableColumn({
  column,
  onItemClick,
  onToggleCompletion,
  toggleTaskPending,
  toggleTodoPending,
  formatCourseCode,
}: {
  column: KanbanColumn
  onItemClick: (item: TaskboardItem) => void
  onToggleCompletion: (e: React.MouseEvent, item: TaskboardItem) => void
  toggleTaskPending: boolean
  toggleTodoPending: boolean
  formatCourseCode: (code: string) => string
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
  })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex-shrink-0 w-80 flex flex-col",
        isOver && "bg-neutral-800/20 rounded-lg"
      )}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <h3 className="text-sm font-semibold text-white">
          {column.title}
        </h3>
        <span className="text-xs text-gray-400 bg-neutral-800/50 px-2 py-0.5 rounded">
          {column.items.length}
        </span>
      </div>

      {/* Column Content */}
      <div className="flex-1 min-h-[400px]">
        <SortableContext
          items={column.items.map(item => item.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-2">
            {column.items.length === 0 ? (
              <div className="p-8 text-center border-2 border-dashed border-gray-700/50 rounded-xl">
                <p className="text-sm text-gray-500">No tasks</p>
              </div>
            ) : (
              column.items.map((item) => (
                <SortableTaskCard
                  key={item.id}
                  item={item}
                  onItemClick={onItemClick}
                  onToggleCompletion={onToggleCompletion}
                  toggleTaskPending={toggleTaskPending}
                  toggleTodoPending={toggleTodoPending}
                  formatCourseCode={formatCourseCode}
                />
              ))
            )}
          </div>
        </SortableContext>
      </div>
    </div>
  )
}

