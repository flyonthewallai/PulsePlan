import React from 'react'
import { CheckSquare, Square, Calendar, Clock, Flag } from 'lucide-react'
import { useTaskMutations } from '@/hooks/tasks'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'
import type { Task } from '../../types'

interface TaskItemProps {
  task: Task
  onEdit?: (task: Task) => void
}

export function TaskItem({ task, onEdit }: TaskItemProps) {
  const { toggleTaskStatus } = useTaskMutations()

  const handleToggleStatus = () => {
    toggleTaskStatus.mutate(task)
  }

  const handleEdit = () => {
    onEdit?.(task)
  }

  const isCompleted = task.status === 'completed'
  const isOverdue = new Date(task.due_date) < new Date() && !isCompleted

  const priorityColors = {
    high: 'text-error',
    medium: 'text-warning', 
    low: 'text-success'
  }

  const statusColors = {
    pending: 'text-textSecondary',
    in_progress: 'text-primary',
    completed: 'text-success'
  }

  return (
    <div className={cn(
      'flex items-center gap-3 p-4 rounded-xl transition-all',
      isCompleted ? 'opacity-70' : '',
      isOverdue ? 'border border-error/30' : ''
    )}
    style={{ 
      backgroundColor: isOverdue ? '#2a1a1a' : '#2a2a2a'
    }}>
      <button
        onClick={handleToggleStatus}
        disabled={toggleTaskStatus.isPending}
        className={cn(
          'flex-shrink-0 transition-colors',
          toggleTaskStatus.isPending && 'opacity-50 cursor-not-allowed'
        )}
      >
        {isCompleted ? (
          <CheckSquare className="w-5 h-5 text-success" />
        ) : (
          <Square className="w-5 h-5 text-textSecondary hover:text-primary" />
        )}
      </button>

      <div 
        className="flex-1 min-w-0 cursor-pointer" 
        onClick={handleEdit}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className={cn(
              'text-sm font-medium truncate',
              isCompleted ? 'line-through text-textSecondary' : 'text-textPrimary'
            )}>
              {task.title}
            </h3>
            
            {task.description && (
              <p className={cn(
                'text-xs mt-1 truncate',
                isCompleted ? 'line-through text-textSecondary' : 'text-textSecondary'
              )}>
                {task.description}
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-2 flex-shrink-0 ml-2">
            <div className={cn(
              'flex items-center gap-1 text-xs px-2 py-1 rounded',
              statusColors[task.status],
              task.status === 'completed' ? 'bg-success/10' :
              task.status === 'in_progress' ? 'bg-primary/10' :
              'bg-textSecondary/10'
            )}>
              <span className="capitalize">{task.status.replace('_', ' ')}</span>
            </div>
            
            <Flag className={cn('w-3 h-3', priorityColors[task.priority])} />
          </div>
        </div>

        <div className="flex items-center gap-4 mt-2">
          <div className="flex items-center gap-1 text-xs text-textSecondary">
            <Calendar className="w-3 h-3" />
            <span className={cn(isOverdue && !isCompleted && 'text-error')}>
              {format(new Date(task.due_date), 'MMM dd, HH:mm')}
            </span>
          </div>
          
          {task.estimated_minutes && (
            <div className="flex items-center gap-1 text-xs text-textSecondary">
              <Clock className="w-3 h-3" />
              <span>{task.estimated_minutes}min</span>
            </div>
          )}
          
          <div className="text-xs text-textSecondary">
            {task.subject}
          </div>
        </div>
      </div>
    </div>
  )
}