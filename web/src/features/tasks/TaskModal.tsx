import { useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X, Calendar, Clock, Flag, Tag } from 'lucide-react'
import { cn } from '@/lib/utils'
import { typography, components, spacing } from '@/lib/design-tokens'
import { useTaskMutations } from '@/hooks/tasks'
import type { Task, CreateTaskData } from '@/types'
import { format, parseISO } from 'date-fns'
import { DateTimePicker } from '@/components/ui/DateTimePicker'

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
        status: task.status as 'pending' | 'in_progress' | 'completed',
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

  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose()
  }

  const handleDelete = () => {
    if (task && window.confirm('Are you sure you want to delete this task?')) {
      deleteTask.mutate(task.id)
      onClose()
    }
  }

  const isLoading = createTask.isPending || updateTask.isPending || deleteTask.isPending

  return (
    <div
      className={cn(
        components.modal.overlay,
        task || initialData ? 'opacity-100' : 'opacity-0 pointer-events-none'
      )}
      onClick={handleBackdrop}
    >
      <div
        className={cn(
          components.modal.container,
          "max-w-lg transition-all duration-300",
          task || initialData ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {(task || initialData) ? (
          <>
            {/* Header */}
            <div className={components.modal.header}>
              <div className="flex items-center justify-between w-full">
                <h2 className={components.modal.title}>
                  {isEditing ? 'Edit Task' : 'Create Task'}
                </h2>
                <button
                  onClick={onClose}
                  disabled={isLoading}
                  className={cn(components.modal.closeButton, isLoading && "opacity-50")}
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Form */}
            <div className={cn(components.modal.content, "max-h-[70vh] overflow-y-auto")}
              style={{
                scrollbarWidth: 'auto',
                scrollbarColor: 'rgba(75, 85, 99, 0.5) transparent'
              }}>
              <form id="task-form" onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
                {/* Title */}
                <div>
                  <label className={cn(components.input.label, "flex items-center gap-1.5")}>
                    <Tag className="w-3.5 h-3.5" />
                    Title
                  </label>
                  <input
                    {...form.register('title')}
                    placeholder="Enter task title"
                    disabled={isLoading}
                    className={cn(components.input.base, "w-full")}
                  />
                  {form.formState.errors.title && (
                    <p className="text-red-400 text-xs mt-1">{form.formState.errors.title.message}</p>
                  )}
                </div>

                {/* Description */}
                <div>
                  <label className={components.input.label}>
                    Description
                  </label>
                  <textarea
                    {...form.register('description')}
                    placeholder="Enter task description (optional)"
                    disabled={isLoading}
                    rows={3}
                    className={cn(components.textarea.base, "w-full")}
                  />
                  {form.formState.errors.description && (
                    <p className="text-red-400 text-xs mt-1">{form.formState.errors.description.message}</p>
                  )}
                </div>

                {/* Subject */}
                <div>
                  <label className={cn(components.input.label, "flex items-center gap-1.5")}>
                    <Tag className="w-3.5 h-3.5" />
                    Subject
                  </label>
                  <select
                    {...form.register('subject')}
                    disabled={isLoading}
                    className={cn(components.select.base, "w-full")}
                  >
                    {subjects.map(subject => (
                      <option key={subject} value={subject}>
                        {subject}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Due Date & Duration Row */}
                <div className="grid grid-cols-2 gap-3">
                  {/* Due Date */}
                  <div>
                    <label className={cn(components.input.label, "flex items-center gap-1.5")}>
                      <Calendar className="w-3.5 h-3.5" />
                      Due Date
                    </label>
                    <Controller
                      name="due_date"
                      control={form.control}
                      render={({ field }) => (
                        <DateTimePicker
                          value={field.value}
                          onChange={field.onChange}
                          disabled={isLoading}
                          placeholder="Select date and time"
                        />
                      )}
                    />
                    {form.formState.errors.due_date && (
                      <p className="text-red-400 text-xs mt-1">{form.formState.errors.due_date.message}</p>
                    )}
                  </div>

                  {/* Estimated Duration */}
                  <div>
                    <label className={cn(components.input.label, "flex items-center gap-1.5")}>
                      <Clock className="w-3.5 h-3.5" />
                      Duration (min)
                    </label>
                    <input
                      {...form.register('estimated_minutes', { valueAsNumber: true })}
                      type="number"
                      min={15}
                      max={480}
                      step={15}
                      disabled={isLoading}
                      className={cn(components.input.base, "w-full")}
                    />
                    {form.formState.errors.estimated_minutes && (
                      <p className="text-red-400 text-xs mt-1">{form.formState.errors.estimated_minutes.message}</p>
                    )}
                  </div>
                </div>

                {/* Priority */}
                <div>
                  <label className={cn(components.input.label, "flex items-center gap-1.5")}>
                    <Flag className="w-3.5 h-3.5" />
                    Priority
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['low', 'medium', 'high'] as const).map(priority => (
                      <label key={priority} className="relative cursor-pointer">
                        <input
                          {...form.register('priority')}
                          type="radio"
                          value={priority}
                          disabled={isLoading}
                          className="sr-only peer"
                        />
                        <div
                          className={cn(
                            'text-center py-2.5 px-3 rounded-lg border transition-all text-sm font-medium',
                            form.watch('priority') === priority
                              ? priority === 'high'
                                ? 'border-red-500 bg-red-500/20 text-red-400'
                                : priority === 'medium'
                                ? 'border-yellow-500 bg-yellow-500/20 text-yellow-400'
                                : 'border-green-500 bg-green-500/20 text-green-400'
                              : 'border-gray-700/50 bg-neutral-800/40 text-gray-400 hover:border-gray-600 hover:text-gray-300'
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
                    <label className={components.input.label}>
                      Status
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['pending', 'in_progress', 'completed'] as const).map(status => (
                        <label key={status} className="relative cursor-pointer">
                          <input
                            {...form.register('status')}
                            type="radio"
                            value={status}
                            disabled={isLoading}
                            className="sr-only peer"
                          />
                          <div
                            className={cn(
                              'text-center py-2.5 px-2 rounded-lg border transition-all text-xs font-medium',
                              form.watch('status') === status
                                ? status === 'completed'
                                  ? 'border-green-500 bg-green-500/20 text-green-400'
                                  : status === 'in_progress'
                                  ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                                  : 'border-gray-500 bg-gray-500/20 text-gray-300'
                                : 'border-gray-700/50 bg-neutral-800/40 text-gray-400 hover:border-gray-600 hover:text-gray-300'
                            )}
                          >
                            {status.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </form>
            </div>

            {/* Actions */}
            <div className={components.modal.footer}>
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className={cn(
                  components.button.base,
                  components.button.secondary,
                  isLoading && "opacity-50 cursor-not-allowed"
                )}
              >
                Cancel
              </button>
              <button
                type="submit"
                form="task-form"
                disabled={isLoading || !form.formState.isValid}
                className={cn(
                  components.button.base,
                  components.button.primary,
                  (isLoading || !form.formState.isValid) && 'opacity-50 cursor-not-allowed'
                )}
              >
                {isLoading ? 'Saving...' : isEditing ? 'Update Task' : 'Create Task'}
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
