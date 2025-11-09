import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { X, Calendar, Clock, Type, FileText, Tag, AlertCircle, Save, Trash2, Copy } from 'lucide-react';
import { cn } from '../../../lib/utils';
import type { CalendarEvent, Task } from '@/types';
import { colors, VALIDATION } from '../../../lib/utils/constants';

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
    priority: 'medium' as 'high' | 'medium' | 'low',
    status: 'todo' as 'todo' | 'in_progress' | 'completed',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Initialize form data when event changes
  useEffect(() => {
    if (isOpen && event) {
      setFormData({
        title: event.title,
        description: event.description || '',
        start: event.start,
        end: event.end,
        priority: event.priority || 'medium',
        status: event.task?.status || 'todo',
      });
      setErrors({});
      setShowDeleteConfirm(false);
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
      formData.priority !== (event.priority || 'medium') ||
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
        priority: formData.priority,
      };

      // If event has a task, update task-specific fields
      if (event.task) {
        updates.task = {
          ...event.task,
          title: formData.title.trim(),
          description: formData.description.trim(),
          dueDate: formData.start,
          priority: formData.priority,
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

  const handleDuplicate = () => {
    if (!event || !onDuplicate) return;
    onDuplicate(event);
    onClose();
  };

  const handleClose = () => {
    if (isSubmitting) return;
    onClose();
  };

  // Priority color mapping
  const priorityColors = {
    high: colors.taskColors.high,
    medium: colors.taskColors.medium,
    low: colors.taskColors.low,
  };

  // Status color mapping
  const statusColors = {
    todo: '#6B7280',
    in_progress: '#3B82F6',
    completed: '#10B981',
  };

  if (!event || !isOpen) return null;

  return (
    <div className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300 ${
      isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
    }`} onClick={handleClose}>
      <div
        className={cn(
          `border border-neutral-700 rounded-xl shadow-2xl w-full max-w-md max-h-[80vh] overflow-auto transition-all duration-300 ${
            isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
          }`,
          'bg-neutral-900',
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {isOpen ? (
          <>
            {/* Header */}
            <div className="flex items-center justify-between p-4">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Calendar size={20} />
                Edit Event
              </h2>
              <div className="flex items-center gap-1">
                {onDuplicate && (
                  <button
                    onClick={handleDuplicate}
                    disabled={isSubmitting}
                    className="p-2 hover:bg-neutral-700 rounded-lg transition-colors text-neutral-400 hover:text-white disabled:opacity-50"
                    title="Duplicate event"
                  >
                    <Copy size={18} />
                  </button>
                )}
                <button
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-neutral-800/60 disabled:opacity-50"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-4 space-y-3">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2 flex items-center gap-2">
                  <Type size={16} />
                  Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="What are you working on?"
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white 
                           placeholder-neutral-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 
                           focus:outline-none transition-colors"
                  disabled={isSubmitting}
                />
                {errors.title && (
                  <p className="mt-1 text-sm bg-error text-white px-2 py-1 rounded flex items-center gap-1">
                    <AlertCircle size={14} />
                    {errors.title}
                  </p>
                )}
              </div>

              {/* Time Range */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Start Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.start ? format(new Date(formData.start), "yyyy-MM-dd'T'HH:mm") : ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, start: e.target.value ? new Date(e.target.value).toISOString() : '' }))}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white 
                             focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
                    disabled={isSubmitting}
                  />
                  {errors.start && (
                    <p className="mt-1 text-sm bg-error text-white px-2 py-1 rounded">{errors.start}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    End Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.end ? format(new Date(formData.end), "yyyy-MM-dd'T'HH:mm") : ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, end: e.target.value ? new Date(e.target.value).toISOString() : '' }))}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white 
                             focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
                    disabled={isSubmitting}
                  />
                  {errors.end && (
                    <p className="mt-1 text-sm bg-error text-white px-2 py-1 rounded">{errors.end}</p>
                  )}
                </div>
              </div>

              {/* Duration Display */}
              {duration > 0 && (
                <div className="flex items-center gap-2 text-sm text-neutral-400 bg-neutral-800/50 px-3 py-2 rounded-lg">
                  <Clock size={14} />
                  Duration: {duration} minutes
                  {duration >= 60 && (
                    <span>({Math.floor(duration / 60)}h {duration % 60}m)</span>
                  )}
                </div>
              )}
              {errors.duration && (
                <p className="text-sm bg-error text-white px-2 py-1 rounded flex items-center gap-1">
                  <AlertCircle size={14} />
                  {errors.duration}
                </p>
              )}

              {/* Priority and Status */}
              <div className="grid grid-cols-2 gap-4">
                {/* Priority */}
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2 flex items-center gap-2">
                    <Tag size={16} />
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
                          'w-full p-2 rounded-lg border transition-all capitalize text-sm font-medium flex items-center gap-2',
                          formData.priority === priority
                            ? 'border-current text-white'
                            : 'border-neutral-600 text-neutral-400 hover:text-white hover:border-neutral-500',
                          'disabled:opacity-50 disabled:cursor-not-allowed'
                        )}
                        style={{
                          borderColor: formData.priority === priority ? priorityColors[priority] : undefined,
                          backgroundColor: formData.priority === priority ? `${priorityColors[priority]}20` : undefined,
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

                {/* Status */}
                {event.task && (
                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Status
                    </label>
                    <div className="space-y-2">
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
                              : 'border-neutral-600 text-neutral-400 hover:text-white hover:border-neutral-500',
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
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2 flex items-center gap-2">
                  <FileText size={16} />
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Add notes or details..."
                  rows={3}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white 
                           placeholder-neutral-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 
                           focus:outline-none transition-colors resize-none"
                  disabled={isSubmitting}
                />
                {errors.description && (
                  <p className="mt-1 text-sm bg-error text-white px-2 py-1 rounded">{errors.description}</p>
                )}
              </div>

              {/* Submit Error */}
              {errors.submit && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                  <p className="text-sm bg-error text-white px-2 py-1 rounded flex items-center gap-2">
                    <AlertCircle size={16} />
                    {errors.submit}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-neutral-700/30">
                {/* Delete Button */}
                <div>
                  {!showDeleteConfirm ? (
                    <button
                      type="button"
                      onClick={() => setShowDeleteConfirm(true)}
                      disabled={isSubmitting}
                      className="px-4 py-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg 
                               transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      <Trash2 size={16} />
                      Delete
                    </button>
                  ) : (
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleDelete}
                        disabled={isSubmitting}
                        className="px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white text-sm rounded 
                                 transition-colors disabled:opacity-50"
                      >
                        Confirm
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowDeleteConfirm(false)}
                        disabled={isSubmitting}
                        className="px-3 py-1.5 text-neutral-400 hover:text-white text-sm transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>

                {/* Save/Cancel */}
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleClose}
                    disabled={isSubmitting}
                    className="px-4 py-2 text-neutral-400 hover:text-white transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !formData.title.trim() || !hasChanges}
                    className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg 
                             transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                             flex items-center gap-2"
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
            </form>
          </>
        ) : null}
      </div>
    </div>
  );
};

EditEventModal.displayName = 'EditEventModal';