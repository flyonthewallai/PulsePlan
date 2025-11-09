import React, { useState, useEffect } from 'react'
import { X, Calendar, Clock, Type, FileText, Tag, Flag, Save } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { cn } from '../../../lib/utils'
import { colors, VALIDATION } from '../../../lib/utils/constants'

interface CreateEventTaskModalProps {
  isOpen: boolean
  onClose: () => void
  onCreate: (data: EventTaskData) => void
  initialData?: {
    start: string
    end: string
    title?: string
  }
  className?: string
}

export interface EventTaskData {
  title: string
  description?: string
  start: string
  end: string
  priority: 'high' | 'medium' | 'low'
  subject?: string
  allDay?: boolean
}

const subjects = [
  'Work', 'Study', 'Personal', 'Health', 'Finance', 'Projects', 'Meeting', 'Review'
]

export function CreateEventTaskModal({
  isOpen,
  onClose,
  onCreate,
  initialData,
  className,
}: CreateEventTaskModalProps) {
  const [formData, setFormData] = useState<EventTaskData>({
    title: '',
    description: '',
    start: '',
    end: '',
    priority: 'medium',
    subject: 'Personal',
    allDay: false,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Initialize form data when modal opens with initial data
  useEffect(() => {
    if (isOpen && initialData) {
      const startDate = new Date(initialData.start)
      const endDate = new Date(initialData.end)

      setFormData({
        title: initialData.title || '',
        description: '',
        start: initialData.start,
        end: initialData.end,
        priority: 'medium',
        subject: 'Personal',
        allDay: false,
      })
      setErrors({})
    } else if (!isOpen) {
      // Reset form when modal closes
      setFormData({
        title: '',
        description: '',
        start: '',
        end: '',
        priority: 'medium',
        subject: 'Personal',
        allDay: false,
      })
      setErrors({})
    }
  }, [isOpen, initialData])

  // Calculate duration in minutes
  const duration = React.useMemo(() => {
    if (!formData.start || !formData.end) return 0
    const start = new Date(formData.start)
    const end = new Date(formData.end)
    return Math.round((end.getTime() - start.getTime()) / (1000 * 60))
  }, [formData.start, formData.end])

  // Validation
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required'
    } else if (formData.title.length > VALIDATION.MAX_TASK_TITLE_LENGTH) {
      newErrors.title = `Title must be less than ${VALIDATION.MAX_TASK_TITLE_LENGTH} characters`
    }

    if (formData.description && formData.description.length > VALIDATION.MAX_TASK_DESCRIPTION_LENGTH) {
      newErrors.description = `Description must be less than ${VALIDATION.MAX_TASK_DESCRIPTION_LENGTH} characters`
    }

    if (!formData.start) {
      newErrors.start = 'Start time is required'
    }

    if (!formData.end) {
      newErrors.end = 'End time is required'
    }

    if (formData.start && formData.end) {
      const start = new Date(formData.start)
      const end = new Date(formData.end)

      if (end <= start) {
        newErrors.end = 'End time must be after start time'
      }

      if (duration < 15) {
        newErrors.duration = 'Event must be at least 15 minutes long'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setIsSubmitting(true)

    try {
      onCreate({
        title: formData.title.trim(),
        description: formData.description?.trim(),
        start: formData.start,
        end: formData.end,
        priority: formData.priority,
        subject: formData.subject,
        allDay: formData.allDay,
      })
      onClose()
    } catch (error) {
      console.error('Error creating event:', error)
      setErrors({ submit: 'Failed to create event. Please try again.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (isSubmitting) return
    onClose()
  }

  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) handleClose()
  }

  // Priority color mapping
  const priorityColors = {
    high: colors.taskColors.high,
    medium: colors.taskColors.medium,
    low: colors.taskColors.low,
  }

  if (!isOpen) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300',
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      )}
      onClick={handleBackdrop}
    >
      <div
        className={cn(
          'border border-gray-700/50 w-full max-w-lg rounded-2xl max-h-[80vh] flex flex-col transition-all duration-300',
          isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4',
          className
        )}
        style={{ backgroundColor: '#181818' }}
        onClick={(e) => e.stopPropagation()}
      >
        {isOpen ? (
          <>
            {/* Header */}
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-neutral-700 flex items-center justify-center">
              <Calendar size={20} className="text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold text-white">Create Event</h2>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={isSubmitting}
            className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-neutral-800/60 disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Content */}
        <div className="p-4 overflow-y-auto flex-1">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                <Type size={16} />
                Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="What are you working on?"
                className="w-full px-3 py-2 bg-neutral-800/40 border border-gray-700/50 rounded-lg text-white
                         placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                         focus:outline-none transition-colors"
                disabled={isSubmitting}
                autoFocus
              />
              {errors.title && (
                <p className="mt-2 text-sm text-red-400 flex items-center gap-1">
                  {errors.title}
                </p>
              )}
            </div>

            {/* Time Range */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                  <Clock size={16} />
                  Start Time *
                </label>
                <input
                  type="datetime-local"
                  value={formData.start ? format(new Date(formData.start), "yyyy-MM-dd'T'HH:mm") : ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    start: e.target.value ? new Date(e.target.value).toISOString() : ''
                  }))}
                  className="w-full px-3 py-2 bg-neutral-800/40 border border-gray-700/50 rounded-lg text-white
                           focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
                  disabled={isSubmitting}
                />
                {errors.start && (
                  <p className="mt-2 text-sm text-red-400">{errors.start}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  End Time *
                </label>
                <input
                  type="datetime-local"
                  value={formData.end ? format(new Date(formData.end), "yyyy-MM-dd'T'HH:mm") : ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    end: e.target.value ? new Date(e.target.value).toISOString() : ''
                  }))}
                  className="w-full px-3 py-2 bg-neutral-800/40 border border-gray-700/50 rounded-lg text-white
                           focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
                  disabled={isSubmitting}
                />
                {errors.end && (
                  <p className="mt-2 text-sm text-red-400">{errors.end}</p>
                )}
              </div>
            </div>

            {/* Duration Display */}
            {duration > 0 && (
              <div className="bg-neutral-800/40 border border-gray-700/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Clock size={14} />
                  <span>Duration: {duration} minutes</span>
                  {duration >= 60 && (
                    <span className="text-gray-500">
                      ({Math.floor(duration / 60)}h {duration % 60}m)
                    </span>
                  )}
                </div>
              </div>
            )}
            {errors.duration && (
              <p className="text-sm text-red-400">{errors.duration}</p>
            )}

            {/* Subject */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                <Tag size={16} />
                Subject
              </label>
              <select
                value={formData.subject}
                onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                className="w-full px-3 py-2 bg-neutral-800/40 border border-gray-700/50 rounded-lg text-white
                         focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
                disabled={isSubmitting}
              >
                {subjects.map(subject => (
                  <option key={subject} value={subject}>
                    {subject}
                  </option>
                ))}
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                <Flag size={16} />
                Priority
              </label>
              <div className="space-y-2">
                {(['high', 'medium', 'low'] as const).map((priority) => (
                  <button
                    key={priority}
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, priority }))}
                    disabled={isSubmitting}
                    className={cn(
                      'w-full p-3 rounded-lg border transition-all capitalize text-sm font-medium flex items-center gap-3',
                      formData.priority === priority
                        ? 'border-current text-white bg-neutral-800/40'
                        : 'border-gray-700/50 text-gray-400 hover:text-white hover:border-gray-600 bg-neutral-800/20',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                    style={{
                      borderColor: formData.priority === priority ? priorityColors[priority] : undefined,
                    }}
                  >
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: priorityColors[priority] }}
                    />
                    {priority}
                  </button>
                ))}
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                <FileText size={16} />
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Add notes or details..."
                rows={3}
                className="w-full px-3 py-2 bg-neutral-800/40 border border-gray-700/50 rounded-lg text-white
                         placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                         focus:outline-none transition-colors resize-none"
                disabled={isSubmitting}
              />
              {errors.description && (
                <p className="mt-2 text-sm text-red-400">{errors.description}</p>
              )}
            </div>

            {/* Submit Error */}
            {errors.submit && (
              <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                <p className="text-sm text-red-400">{errors.submit}</p>
              </div>
            )}
          </form>
        </div>

        {/* Footer */}
        <div className="p-4 flex justify-end gap-3">
          <button
            type="button"
            onClick={handleClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={isSubmitting || !formData.title.trim()}
            className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium
                     transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Save size={16} />
                Create Event
              </>
            )}
          </button>
        </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

CreateEventTaskModal.displayName = 'CreateEventTaskModal'
