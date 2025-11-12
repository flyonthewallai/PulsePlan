import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { X, Clock, Type, FileText, AlertCircle, Save, Trash2 } from 'lucide-react';
import { cn } from '../../../lib/utils';
import type { CalendarEvent, Task } from '@/types';
import { VALIDATION } from '../../../lib/utils/constants';
import { components, typography, colors, spacing, layout } from '../../../lib/design-tokens';

interface EditEventModalProps {
  isOpen: boolean;
  event: CalendarEvent | null;
  onClose: () => void;
  onUpdate: (eventId: string, updates: Partial<CalendarEvent>) => void;
  onDelete: (eventId: string) => void;
  onDuplicate?: (event: CalendarEvent) => void;
  className?: string;
}

export const EditEventModal: React.FC<EditEventModalProps> = ({
  isOpen,
  event,
  onClose,
  onUpdate,
  onDelete,
  onDuplicate,
  className,
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    start: '',
    end: '',
    status: 'todo' as 'todo' | 'in_progress' | 'completed',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form data when event changes
  useEffect(() => {
    if (isOpen && event) {
      setFormData({
        title: event.title,
        description: event.description || '',
        start: event.start,
        end: event.end,
        status: event.task?.status || 'todo',
      });
      setErrors({});
    }
  }, [isOpen, event]);

  // Calculate duration
  const duration = React.useMemo(() => {
    if (!formData.start || !formData.end) return 0;
    const start = new Date(formData.start);
    const end = new Date(formData.end);
    return Math.round((end.getTime() - start.getTime()) / (1000 * 60));
  }, [formData.start, formData.end]);

  // Check if form has changes
  const hasChanges = React.useMemo(() => {
    if (!event) return false;
    return (
      formData.title !== event.title ||
      formData.description !== (event.description || '') ||
      formData.start !== event.start ||
      formData.end !== event.end ||
      formData.status !== (event.task?.status || 'todo')
    );
  }, [formData, event]);

  // Validation
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length > VALIDATION.MAX_TASK_TITLE_LENGTH) {
      newErrors.title = `Title must be less than ${VALIDATION.MAX_TASK_TITLE_LENGTH} characters`;
    }

    if (formData.description && formData.description.length > VALIDATION.MAX_TASK_DESCRIPTION_LENGTH) {
      newErrors.description = `Description must be less than ${VALIDATION.MAX_TASK_DESCRIPTION_LENGTH} characters`;
    }

    if (!formData.start) {
      newErrors.start = 'Start time is required';
    }

    if (!formData.end) {
      newErrors.end = 'End time is required';
    }

    if (formData.start && formData.end) {
      const start = new Date(formData.start);
      const end = new Date(formData.end);
      
      if (end <= start) {
        newErrors.end = 'End time must be after start time';
      }

      if (duration < 15) {
        newErrors.duration = 'Event must be at least 15 minutes long';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!event || !validateForm()) return;

    setIsSubmitting(true);

    try {
      const updates: Partial<CalendarEvent> = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        start: formData.start,
        end: formData.end,
      };

      // If event has a task, update task-specific fields
      if (event.task) {
        updates.task = {
          ...event.task,
          title: formData.title.trim(),
          description: formData.description.trim(),
          dueDate: formData.start,
          status: formData.status,
          estimatedDuration: duration,
        };
      }

      onUpdate(event.id, updates);
      onClose();
    } catch (error) {
      console.error('Error updating event:', error);
      setErrors({ submit: 'Failed to update event. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!event) return;

    setIsSubmitting(true);
    try {
      onDelete(event.id);
      onClose();
    } catch (error) {
      console.error('Error deleting event:', error);
      setErrors({ submit: 'Failed to delete event. Please try again.' });
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (isSubmitting) return;
    onClose();
  };

  // Status color mapping
  const statusColors = {
    todo: '#6B7280',
    in_progress: '#3B82F6',
    completed: '#10B981',
  };

  if (!event || !isOpen) return null;

  return (
    <div
      className={cn(
        components.modal.overlay,
        'z-[60]', // Higher z-index to overlay on top of EventDetailsModal (z-50)
        'p-4',
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      )}
      onClick={handleClose}
    >
      <div
        className={cn(
          components.modal.container,
          'max-w-md max-h-[80vh] overflow-auto',
          isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4',
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {isOpen ? (
          <>
            {/* Header */}
            <div className={cn(components.modal.header, layout.flex.between)}>
              <h2 className={cn(components.modal.title)}>
                Edit Event
              </h2>
              <div className="flex items-center gap-1 shrink-0 ml-2">
                <button
                  onClick={() => {
                    handleDelete();
                  }}
                  disabled={isSubmitting}
                  className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete event"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="p-1.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className={cn(spacing.modal.content, spacing.stack.sm)}>
              {/* Title */}
              <div>
                <label className={cn(components.input.label, 'flex items-center', spacing.gap.sm)}>
                  <Type size={16} />
                  Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="What are you working on?"
                  className={cn(
                    components.input.base,
                    'w-full',
                    errors.title && components.input.error
                  )}
                  disabled={isSubmitting}
                />
                {errors.title && (
                  <p className={cn(components.input.helper, colors.text.error, 'flex items-center', spacing.gap.xs)}>
                    <AlertCircle size={14} />
                    {errors.title}
                  </p>
                )}
              </div>

              {/* Time Range */}
              <div className={cn(layout.grid.cols2, spacing.gap.md)}>
                <div>
                  <label className={components.input.label}>
                    Start Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.start ? format(new Date(formData.start), "yyyy-MM-dd'T'HH:mm") : ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, start: e.target.value ? new Date(e.target.value).toISOString() : '' }))}
                    className={cn(
                      components.input.base,
                      'w-full',
                      errors.start && components.input.error
                    )}
                    disabled={isSubmitting}
                  />
                  {errors.start && (
                    <p className={cn(components.input.helper, colors.text.error)}>{errors.start}</p>
                  )}
                </div>

                <div>
                  <label className={components.input.label}>
                    End Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.end ? format(new Date(formData.end), "yyyy-MM-dd'T'HH:mm") : ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, end: e.target.value ? new Date(e.target.value).toISOString() : '' }))}
                    className={cn(
                      components.input.base,
                      'w-full',
                      errors.end && components.input.error
                    )}
                    disabled={isSubmitting}
                  />
                  {errors.end && (
                    <p className={cn(components.input.helper, colors.text.error)}>{errors.end}</p>
                  )}
                </div>
              </div>

              {/* Duration Display */}
              {duration > 0 && (
                <div className={cn(
                  'flex items-center',
                  spacing.gap.sm,
                  typography.body.small,
                  colors.text.secondary,
                  colors.bg.input,
                  'px-3 py-2 rounded-lg'
                )}>
                  <Clock size={14} />
                  Duration: {duration} minutes
                  {duration >= 60 && (
                    <span>({Math.floor(duration / 60)}h {duration % 60}m)</span>
                  )}
                </div>
              )}
              {errors.duration && (
                <p className={cn(components.input.helper, colors.text.error, 'flex items-center', spacing.gap.xs)}>
                  <AlertCircle size={14} />
                  {errors.duration}
                </p>
              )}

              {/* Status */}
              {event.task && (
                <div>
                  <label className={components.input.label}>
                    Status
                  </label>
                  <div className={spacing.stack.xs}>
                    {(['todo', 'in_progress', 'completed'] as const).map((status) => (
                      <button
                        key={status}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, status }))}
                        disabled={isSubmitting}
                        className={cn(
                          'w-full p-2 rounded-lg border transition-all text-sm font-medium flex items-center gap-2',
                          formData.status === status
                            ? 'border-current text-white'
                            : cn(colors.border.default, colors.text.secondary, 'hover:text-white hover:border-gray-600'),
                          'disabled:opacity-50 disabled:cursor-not-allowed'
                        )}
                        style={{
                          borderColor: formData.status === status ? statusColors[status] : undefined,
                          backgroundColor: formData.status === status ? `${statusColors[status]}20` : undefined,
                        }}
                      >
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: statusColors[status] }}
                        />
                        {status === 'todo' ? 'To Do' : status === 'in_progress' ? 'In Progress' : 'Completed'}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Description */}
              <div>
                <label className={cn(components.input.label, 'flex items-center', spacing.gap.sm)}>
                  <FileText size={16} />
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Add notes or details..."
                  rows={3}
                  className={cn(
                    components.textarea.base,
                    'w-full',
                    errors.description && components.input.error
                  )}
                  disabled={isSubmitting}
                />
                {errors.description && (
                  <p className={cn(components.input.helper, colors.text.error)}>{errors.description}</p>
                )}
              </div>

              {/* Submit Error */}
              {errors.submit && (
                <div className={cn('p-3 rounded-lg', colors.bg.buttonDanger, colors.border.error)}>
                  <p className={cn(typography.body.small, colors.text.error, 'flex items-center', spacing.gap.sm)}>
                    <AlertCircle size={16} />
                    {errors.submit}
                  </p>
                </div>
              )}
            </form>

            {/* Actions Footer */}
            <div className={cn(
              spacing.modal.footer,
              components.divider.horizontal,
              'flex justify-end'
            )}>
              {/* Save/Cancel */}
              <div className={cn('flex items-center', spacing.gap.md)}>
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className={cn(
                    components.button.base,
                    components.button.secondary,
                    'disabled:opacity-50'
                  )}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={isSubmitting || !formData.title.trim() || !hasChanges}
                  className={cn(
                    components.button.base,
                    components.button.primary,
                    'flex items-center',
                    spacing.gap.sm,
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save size={16} />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};

EditEventModal.displayName = 'EditEventModal';