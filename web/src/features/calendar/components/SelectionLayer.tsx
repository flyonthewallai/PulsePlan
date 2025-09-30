import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { Clock, Plus } from 'lucide-react';
import { cn } from '../../../lib/utils';
import type { SelectionState } from '../calendar-logic/selection';
import { SelectionManager } from '../calendar-logic/selection';

interface SelectionLayerProps {
  selection: SelectionState;
  className?: string;
  onCreateEvent?: (startTime: Date, endTime: Date, dayIndex: number) => void;
}

export const SelectionLayer: React.FC<SelectionLayerProps> = ({
  selection,
  className,
  onCreateEvent,
}) => {
  const visualBounds = SelectionManager.getSelectionVisualBounds(selection);
  
  if (!visualBounds || !selection.isSelecting) {
    return null;
  }

  const duration = SelectionManager.getSelectionDuration(selection);
  const timeString = SelectionManager.getSelectionTimeString(selection);
  const isValid = SelectionManager.isValidSelection(selection);

  const handleCreateClick = () => {
    if (isValid && selection.startTime && selection.endTime && selection.dayIndex !== undefined) {
      onCreateEvent?.(selection.startTime, selection.endTime, selection.dayIndex);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.15 }}
        className={cn(
          'absolute pointer-events-none z-50 rounded-lg border-2 border-dashed',
          'flex flex-col justify-between overflow-hidden',
          isValid 
            ? 'bg-blue-500/20 border-blue-400' 
            : 'bg-yellow-500/20 border-yellow-400',
          className
        )}
        style={{
          left: visualBounds.left + 60, // Offset for hour labels
          top: visualBounds.top + 64,   // Offset for header (64px)
          width: visualBounds.width,
          height: visualBounds.height,
        }}
      >
        {/* Selection content */}
        <div className="flex-1 p-2 flex flex-col justify-center">
          {/* Time indicator */}
          <div className="flex items-center justify-center gap-2 text-sm font-medium">
            <Clock size={14} />
            <span className={isValid ? 'text-blue-200' : 'text-yellow-200'}>
              {timeString}
            </span>
          </div>
          
          {/* Duration */}
          {duration > 0 && (
            <div className={cn(
              'text-xs text-center mt-1',
              isValid ? 'text-blue-300' : 'text-yellow-300'
            )}>
              {duration} minutes
            </div>
          )}

          {/* Create button for valid selections */}
          {isValid && visualBounds.height > 60 && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-2 mx-auto px-3 py-1.5 bg-blue-500 text-white text-xs rounded-md
                       hover:bg-blue-600 transition-colors pointer-events-auto
                       flex items-center gap-1"
              onClick={handleCreateClick}
            >
              <Plus size={12} />
              Create Event
            </motion.button>
          )}

          {/* Warning for invalid selections */}
          {!isValid && visualBounds.height > 40 && (
            <div className="text-xs text-yellow-300 text-center mt-1">
              Minimum 15 minutes
            </div>
          )}
        </div>

        {/* Animated border pulse */}
        <motion.div
          className="absolute inset-0 rounded-lg border-2"
          animate={{
            borderColor: isValid 
              ? ['rgba(59, 130, 246, 0.5)', 'rgba(59, 130, 246, 1)', 'rgba(59, 130, 246, 0.5)']
              : ['rgba(234, 179, 8, 0.5)', 'rgba(234, 179, 8, 1)', 'rgba(234, 179, 8, 0.5)']
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        />

        {/* Corner resize indicators */}
        <div className="absolute -top-1 -left-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white" />
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white" />
        <div className="absolute -bottom-1 -left-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white" />
        <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white" />
      </motion.div>
    </AnimatePresence>
  );
};

// Quick creation overlay that appears on hover over empty time slots
interface QuickCreateOverlayProps {
  isVisible: boolean;
  position: { x: number; y: number };
  timeSlot: Date;
  onQuickCreate?: (startTime: Date) => void;
  className?: string;
}

export const QuickCreateOverlay: React.FC<QuickCreateOverlayProps> = ({
  isVisible,
  position,
  timeSlot,
  onQuickCreate,
  className,
}) => {
  if (!isVisible) return null;

  const handleQuickCreate = () => {
    onQuickCreate?.(timeSlot);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 10 }}
      transition={{ duration: 0.15 }}
      className={cn(
        'absolute z-40 bg-neutral-800 border border-neutral-600 rounded-lg shadow-lg',
        'px-3 py-2 text-sm pointer-events-auto',
        className
      )}
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className="flex items-center gap-2 text-neutral-300 mb-1">
        <Clock size={12} />
        <span>{format(timeSlot, 'h:mm a')}</span>
      </div>
      
      <button
        onClick={handleQuickCreate}
        className="w-full px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded
                 transition-colors flex items-center justify-center gap-1"
      >
        <Plus size={12} />
        Quick Add
      </button>
    </motion.div>
  );
};

// Time slot preview that shows while dragging to create
interface TimeSlotPreviewProps {
  isVisible: boolean;
  startTime: Date;
  endTime: Date;
  position: { x: number; y: number; width: number; height: number };
  className?: string;
}

export const TimeSlotPreview: React.FC<TimeSlotPreviewProps> = ({
  isVisible,
  startTime,
  endTime,
  position,
  className,
}) => {
  if (!isVisible) return null;

  const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60));

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={cn(
        'absolute z-30 bg-blue-500/30 border border-blue-400 rounded border-dashed',
        'flex items-center justify-center text-blue-200 text-xs font-medium',
        className
      )}
      style={{
        left: position.x,
        top: position.y,
        width: position.width,
        height: position.height,
      }}
    >
      <div className="text-center">
        <div>{format(startTime, 'h:mm a')}</div>
        {position.height > 30 && (
          <div className="text-blue-300">
            {duration}m
          </div>
        )}
      </div>
    </motion.div>
  );
};

SelectionLayer.displayName = 'SelectionLayer';
QuickCreateOverlay.displayName = 'QuickCreateOverlay';
TimeSlotPreview.displayName = 'TimeSlotPreview';