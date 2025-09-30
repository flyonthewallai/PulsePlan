import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { X, Calendar, Clock, Type, FileText, Tag, AlertCircle, Save } from 'lucide-react';
import { cn } from '../../../lib/utils';
import type { CalendarEvent, CreateTaskData } from '@/types';
import { colors, VALIDATION } from '../../../lib/utils/constants';

interface NewEventModalProps {
  isOpen: boolean;
  initialData?: {
    start: string;
    end: string;
    title?: string;
  };
  onClose: () => void;
  onCreate: (eventData: CreateTaskData) => void;
  className?: string;
}

export const NewEventModal: React.FC<NewEventModalProps> = ({
  isOpen,
  initialData,
  onClose,
  onCreate,
  className,
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    start: '',
    end: '',
    priority: 'medium' as 'high' | 'medium' | 'low',
    tags: [] as string[],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form data when modal opens or initial data changes
  useEffect(() => {
    if (isOpen && initialData) {
      setFormData({
        title: initialData.title || '',
        description: '',
        start: initialData.start,
        end: initialData.end,
        priority: 'medium',
        tags: [],
      });
      setErrors({});
    }
  }, [isOpen, initialData]);

  // Calculate duration
  const duration = React.useMemo(() => {
    if (!formData.start || !formData.end) return 0;
    const start = new Date(formData.start);
    const end = new Date(formData.end);
    return Math.round((end.getTime() - start.getTime()) / (1000 * 60));
  }, [formData.start, formData.end]);

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
    
    if (!validateForm()) return;

    setIsSubmitting(true);

    try {
      const eventData: CreateTaskData = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        dueDate: formData.start,
        priority: formData.priority,
        status: 'todo',
        estimatedDuration: duration,
        tags: formData.tags,
      };

      onCreate(eventData);
      onClose();
    } catch (error) {
      console.error('Error creating event:', error);
      setErrors({ submit: 'Failed to create event. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
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

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.3 }}
            className={cn(
              'fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50',
              'w-full max-w-md max-h-[90vh] overflow-auto',
              'bg-neutral-900 border border-neutral-700 rounded-xl shadow-2xl',
              className
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-neutral-700">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Calendar size={20} />
                New Event
              </h2>
              <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="p-2 hover:bg-neutral-700 rounded-lg transition-colors text-neutral-400 hover:text-white disabled:opacity-50"
              >
                <X size={18} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
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
                  autoFocus
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

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2 flex items-center gap-2">
                  <Tag size={16} />
                  Priority
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['high', 'medium', 'low'] as const).map((priority) => (
                    <button
                      key={priority}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, priority }))}
                      disabled={isSubmitting}
                      className={cn(
                        'p-3 rounded-lg border-2 transition-all capitalize text-sm font-medium',
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
                        className="w-3 h-3 rounded-full mx-auto mb-1"
                        style={{ backgroundColor: priorityColors[priority] }}
                      />
                      {priority}
                    </button>
                  ))}
                </div>
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
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-neutral-700">
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
                  disabled={isSubmitting || !formData.title.trim()}
                  className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg 
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
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

NewEventModal.displayName = 'NewEventModal';