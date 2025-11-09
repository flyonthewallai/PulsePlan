import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { Clock, Plus } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { CALENDAR_CONSTANTS } from '../../../lib/utils/constants';
import type { SelectionState } from '../calendar-logic/selection';
import { SelectionManager } from '../calendar-logic/selection';

interface SelectionLayerProps {
  selection: SelectionState;
  className?: string;
  onCreateEvent?: (startTime: Date, endTime: Date, dayIndex: number) => void;
  columnWidth?: number;
}

export const SelectionLayer: React.FC<SelectionLayerProps> = ({
  selection,
  className,
  onCreateEvent,
  columnWidth = 160,
}) => {
  const visualBounds = SelectionManager.getSelectionVisualBounds(selection, columnWidth);
  
  if (!visualBounds || !selection.isSelecting) {
    return null;
  }

  const duration = SelectionManager.getSelectionDuration(selection);
  const timeString = SelectionManager.getSelectionTimeString(selection);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.98 }}
        transition={{ duration: 0.2 }}
        className={cn(
          'absolute pointer-events-none z-50 rounded-lg border-l-4 shadow-lg',
          'flex flex-col justify-between overflow-hidden',
          'bg-blue-500/30 border-blue-500 backdrop-blur-sm',
          className
        )}
        style={{
          // Selection uses the same coordinate system as events
          // visualBounds already calculates relative to time gutter start
          left: visualBounds.left,
          top: visualBounds.top,
          width: visualBounds.width,
          height: visualBounds.height,
        }}
      >
        {/* Subtle gradient overlay matching event blocks */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />

        {/* Selection content */}
        <div className="relative flex-1 p-2 flex flex-col justify-center">
          {/* Time indicator - matching event block style */}
          <div className="flex items-center gap-2 text-sm font-medium text-white">
            <Clock size={14} className="opacity-90" />
            <span>
              {timeString}
            </span>
          </div>

          {/* Duration */}
          {duration > 0 && (
            <div className="text-xs text-white/80 mt-1">
              {duration} minutes
            </div>
          )}
        </div>

        {/* Subtle animated glow effect */}
        <motion.div
          className="absolute inset-0 rounded-lg pointer-events-none"
          style={{
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.3)'
          }}
          animate={{
            opacity: [0.5, 1, 0.5]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        />
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