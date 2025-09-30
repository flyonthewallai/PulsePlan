import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X, Calendar, Clock, Flag, Tag, Trash2 } from 'lucide-react'
import { cn } from '../../lib/utils'
import { useTaskMutations } from '../../hooks/useTaskMutations'
import type { Task, CreateTaskData } from '../../types'
import { format, parseISO } from 'date-fns'

const taskSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100, 'Title too long'),
  description: z.string().max(500, 'Description too long').optional(),
  subject: z.string().min(1, 'Subject is required'),
  due_date: z.string().min(1, 'Due date is required'),
  estimated_minutes: z.number().min(15).max(480),
  priority: z.enum(['low', 'medium', 'high']),
  status: z.enum(['pending', 'in_progress', 'completed']),
})

type TaskFormData = z.infer<typeof taskSchema>

interface TaskModalProps {
  task?: Task | null
  initialData?: { start: string; end: string } | null
  onClose: () => void
}

const subjects = [
  'Work', 'Study', 'Personal', 'Health', 'Finance', 'Projects', 'Meeting', 'Review'
]

export function TaskModal({ task, initialData, onClose }: TaskModalProps) {
  const { createTask, updateTask, deleteTask } = useTaskMutations()
  const isEditing = !!task

  const form = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      title: '',
      description: '',
      subject: 'Personal',
      due_date: '',
      estimated_minutes: 60,
      priority: 'medium',
      status: 'pending',
    },
  })

  // Set initial values
  useEffect(() => {
    if (task) {
      form.reset({
        title: task.title,
        description: task.description || '',
        subject: task.subject,
        due_date: format(parseISO(task.due_date), "yyyy-MM-dd'T'HH:mm"),
        estimated_minutes: task.estimated_minutes || 60,
        priority: task.priority,
        status: task.status,
      })
    } else if (initialData) {
      const startDate = new Date(initialData.start)
      const endDate = new Date(initialData.end)
      const estimatedMinutes = Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60))
      
      form.reset({
        title: '',
        description: '',
        subject: 'Personal',
        due_date: format(startDate, "yyyy-MM-dd'T'HH:mm"),
        estimated_minutes: Math.max(15, estimatedMinutes),
        priority: 'medium',
        status: 'pending',
      })
    }
  }, [task, initialData, form])


  const onSubmit = (data: TaskFormData) => {
    const taskData: CreateTaskData = {
      ...data,
      due_date: new Date(data.due_date).toISOString(),
    }

    if (isEditing && task) {
      updateTask.mutate({
        taskId: task.id,
        updates: taskData,
      })
      onClose()
    } else {
      createTask.mutate(taskData)
      onClose()
    }
  }

  const handleDelete = () => {
    if (task && window.confirm('Are you sure you want to delete this task?')) {
      deleteTask.mutate(task.id)
      onClose()
    }
  }

  const isLoading = createTask.isPending || updateTask.isPending || deleteTask.isPending

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-textPrimary">
            {isEditing ? 'Edit Task' : 'Create Task'}
          </h2>
          <div className="flex items-center gap-2">
            {isEditing && (
              <button
                onClick={handleDelete}
                disabled={isLoading}
                className="p-2 text-error hover:bg-error/20 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={onClose}
              disabled={isLoading}
              className="p-2 text-textSecondary hover:text-textPrimary rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={form.handleSubmit(onSubmit)} className="p-6 space-y-4 overflow-y-auto">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              <Tag className="w-4 h-4 inline mr-1" />
              Title *
            </label>
            <input
              {...form.register('title')}
              placeholder="Enter task title"
              disabled={isLoading}
              className="input w-full"
            />
            {form.formState.errors.title && (
              <p className="bg-error text-white text-sm mt-1 px-2 py-1 rounded">{form.formState.errors.title.message}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              Description
            </label>
            <textarea
              {...form.register('description')}
              placeholder="Enter task description (optional)"
              disabled={isLoading}
              rows={3}
              className="input w-full resize-none"
            />
            {form.formState.errors.description && (
              <p className="bg-error text-white text-sm mt-1 px-2 py-1 rounded">{form.formState.errors.description.message}</p>
            )}
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              <Tag className="w-4 h-4 inline mr-1" />
              Subject *
            </label>
            <select
              {...form.register('subject')}
              disabled={isLoading}
              className="input w-full"
            >
              {subjects.map(subject => (
                <option key={subject} value={subject}>
                  {subject}
                </option>
              ))}
            </select>
          </div>

          {/* Due Date */}
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              <Calendar className="w-4 h-4 inline mr-1" />
              Due Date *
            </label>
            <input
              {...form.register('due_date')}
              type="datetime-local"
              disabled={isLoading}
              className="input w-full"
            />
            {form.formState.errors.due_date && (
              <p className="bg-error text-white text-sm mt-1 px-2 py-1 rounded">{form.formState.errors.due_date.message}</p>
            )}
          </div>

          {/* Estimated Duration */}
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              <Clock className="w-4 h-4 inline mr-1" />
              Estimated Duration (minutes)
            </label>
            <input
              {...form.register('estimated_minutes', { valueAsNumber: true })}
              type="number"
              min={15}
              max={480}
              step={15}
              disabled={isLoading}
              className="input w-full"
            />
            {form.formState.errors.estimated_minutes && (
              <p className="bg-error text-white text-sm mt-1 px-2 py-1 rounded">{form.formState.errors.estimated_minutes.message}</p>
            )}
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              <Flag className="w-4 h-4 inline mr-1" />
              Priority
            </label>
            <div className="flex gap-2">
              {(['low', 'medium', 'high'] as const).map(priority => (
                <label key={priority} className="flex items-center gap-2 flex-1">
                  <input
                    {...form.register('priority')}
                    type="radio"
                    value={priority}
                    disabled={isLoading}
                    className="sr-only"
                  />
                  <div
                    className={cn(
                      'flex-1 text-center py-2 px-3 rounded-lg border cursor-pointer transition-colors',
                      form.watch('priority') === priority
                        ? priority === 'high'
                          ? 'border-error bg-error/20 text-error'
                          : priority === 'medium'
                          ? 'border-warning bg-warning/20 text-warning'
                          : 'border-success bg-success/20 text-success'
                        : 'border-gray-600 text-textSecondary hover:border-gray-500'
                    )}
                  >
                    {priority.charAt(0).toUpperCase() + priority.slice(1)}
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Status (only for editing) */}
          {isEditing && (
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                Status
              </label>
              <div className="flex gap-2">
                {(['pending', 'in_progress', 'completed'] as const).map(status => (
                  <label key={status} className="flex items-center gap-2 flex-1">
                    <input
                      {...form.register('status')}
                      type="radio"
                      value={status}
                      disabled={isLoading}
                      className="sr-only"
                    />
                    <div
                      className={cn(
                        'flex-1 text-center py-2 px-3 rounded-lg border cursor-pointer transition-colors text-xs',
                        form.watch('status') === status
                          ? status === 'completed'
                            ? 'border-success bg-success/20 text-success'
                            : status === 'in_progress'
                            ? 'border-primary bg-primary/20 text-primary'
                            : 'border-textSecondary bg-textSecondary/20 text-textSecondary'
                          : 'border-gray-600 text-textSecondary hover:border-gray-500'
                      )}
                    >
                      {status.replace('_', ' ').charAt(0).toUpperCase() + status.replace('_', ' ').slice(1)}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !form.formState.isValid}
              className={cn(
                'btn-primary flex-1',
                (isLoading || !form.formState.isValid) && 'opacity-50 cursor-not-allowed'
              )}
            >
              {isLoading ? 'Saving...' : isEditing ? 'Update Task' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}