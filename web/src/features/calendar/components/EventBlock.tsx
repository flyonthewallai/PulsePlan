import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useDraggable, useDroppable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { format } from 'date-fns';
import { Clock, GripVertical, MoreHorizontal } from 'lucide-react';
import { cn } from '../../../lib/utils';
import type { CalendarEvent } from '@/types';
import type { EventLayout } from '../calendar-logic/overlaps';
import { GridMath } from '../calendar-logic/gridMath';
import { colors, CALENDAR_CONSTANTS } from '../../../lib/utils/constants';

// Local type definition for PanInfo since it's not exported in newer framer-motion versions
interface PanInfo {
  point: { x: number; y: number };
  offset: { x: number; y: number };
  velocity: { x: number; y: number };
  delta: { x: number; y: number };
}

interface EventBlockProps {
  event: CalendarEvent;
  layout: EventLayout;
  isSelected?: boolean;
  isDragging?: boolean;
  isResizing?: boolean;
  onSelect?: (event: CalendarEvent) => void;
  onEdit?: (event: CalendarEvent) => void;
  onDelete?: (event: CalendarEvent) => void;
  onDragStart?: (event: CalendarEvent) => void;
  onDragEnd?: (event: CalendarEvent, newStart: Date, newEnd: Date) => void;
  onResizeStart?: (event: CalendarEvent) => void;
  onResizeEnd?: (event: CalendarEvent, newStart: Date, newEnd: Date) => void;
  className?: string;
  style?: React.CSSProperties;
}

export const EventBlock: React.FC<EventBlockProps> = ({
  event,
  layout,
  isSelected = false,
  isDragging = false,
  isResizing = false,
  onSelect,
  onEdit,
  onDelete,
  onDragStart,
  onDragEnd,
  onResizeStart,
  onResizeEnd,
  className,
  style,
}) => {
  const eventRef = useRef<HTMLDivElement>(null);
  const [isHovering, setIsHovering] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [resizeState, setResizeState] = useState<{
    isResizing: boolean;
    direction: 'top' | 'bottom' | null;
    startHeight: number;
    startY: number;
  }>({
    isResizing: false,
    direction: null,
    startHeight: 0,
    startY: 0,
  });

  // Get priority color
  const priorityColor = React.useMemo(() => {
    if (event.task?.priority) {
      return colors.taskColors[event.task.priority];
    }
    return event.color || colors.taskColors.default;
  }, [event.task?.priority, event.color]);

  // Calculate event times
  const startTime = new Date(event.start);
  const endTime = new Date(event.end);
  const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60));

  // Draggable setup
  const {
    attributes,
    listeners,
    setNodeRef: setDraggableRef,
    transform,
  } = useDraggable({
    id: event.id,
    data: { event, layout },
  });

  const draggableStyle = transform ? {
    transform: CSS.Translate.toString(transform),
    zIndex: 1000,
  } : {};

  // Handle drag operations
  const handleDragStart = (info: PanInfo) => {
    onDragStart?.(event);
    setDragOffset({
      x: info.offset.x,
      y: info.offset.y,
    });
  };

  const handleDrag = (info: PanInfo) => {
    setDragOffset({
      x: info.offset.x,
      y: info.offset.y,
    });
  };

  const handleDragEnd = (info: PanInfo) => {
    const { offset } = info;
    
    // Calculate new start time based on Y offset
    const yDelta = offset.y;
    const timeDelta = GridMath.heightToDuration(yDelta);
    
    const newStart = new Date(startTime.getTime() + timeDelta * 60 * 1000);
    const newEnd = new Date(endTime.getTime() + timeDelta * 60 * 1000);
    
    // Snap to grid
    const snappedStart = GridMath.snapTime(newStart, 15);
    const snappedEnd = GridMath.snapTime(newEnd, 15);
    
    onDragEnd?.(event, snappedStart, snappedEnd);
    setDragOffset({ x: 0, y: 0 });
  };

  // Handle resize operations
  const handleResizeStart = (direction: 'top' | 'bottom', clientY: number) => {
    if (!eventRef.current) return;
    
    const rect = eventRef.current.getBoundingClientRect();
    setResizeState({
      isResizing: true,
      direction,
      startHeight: rect.height,
      startY: clientY,
    });
    onResizeStart?.(event);
  };

  const handleResizeMove = (clientY: number) => {
    if (!resizeState.isResizing || !eventRef.current) return;
    
    const deltaY = clientY - resizeState.startY;
    let newHeight = resizeState.startHeight;
    let newStart = startTime;
    let newEnd = endTime;
    
    if (resizeState.direction === 'bottom') {
      // Resizing from bottom - change end time
      newHeight = Math.max(30, resizeState.startHeight + deltaY);
      const newDuration = GridMath.heightToDuration(newHeight);
      newEnd = new Date(startTime.getTime() + newDuration * 60 * 1000);
    } else if (resizeState.direction === 'top') {
      // Resizing from top - change start time  
      newHeight = Math.max(30, resizeState.startHeight - deltaY);
      const newDuration = GridMath.heightToDuration(newHeight);
      newStart = new Date(endTime.getTime() - newDuration * 60 * 1000);
    }
    
    // Apply visual feedback
    if (eventRef.current) {
      eventRef.current.style.height = `${newHeight}px`;
      if (resizeState.direction === 'top') {
        const topDelta = resizeState.startHeight - newHeight;
        eventRef.current.style.transform = `translateY(${topDelta}px)`;
      }
    }
  };

  const handleResizeEnd = () => {
    if (!resizeState.isResizing || !eventRef.current) return;
    
    const rect = eventRef.current.getBoundingClientRect();
    const newDuration = GridMath.heightToDuration(rect.height);
    
    let newStart = startTime;
    let newEnd = endTime;
    
    if (resizeState.direction === 'bottom') {
      newEnd = new Date(startTime.getTime() + newDuration * 60 * 1000);
    } else if (resizeState.direction === 'top') {
      newStart = new Date(endTime.getTime() - newDuration * 60 * 1000);
    }
    
    // Snap to grid
    const snappedStart = GridMath.snapTime(newStart, 15);
    const snappedEnd = GridMath.snapTime(newEnd, 15);
    
    onResizeEnd?.(event, snappedStart, snappedEnd);
    
    // Reset visual state
    eventRef.current.style.height = '';
    eventRef.current.style.transform = '';
    
    setResizeState({
      isResizing: false,
      direction: null,
      startHeight: 0,
      startY: 0,
    });
  };

  // Truncate text for small events
  const shouldShowFullText = layout.height > 40;
  const shouldShowTime = layout.height > 60;

  return (
    <motion.div
      ref={(node) => {
        setDraggableRef(node);
        eventRef.current = node;
      }}
      className={cn(
        'absolute select-none cursor-pointer transition-all duration-200',
        'rounded-lg border-l-4 shadow-sm hover:shadow-md',
        'flex flex-col justify-between overflow-hidden',
        isSelected && 'ring-2 ring-blue-400 ring-offset-1 ring-offset-neutral-900',
        isDragging && 'shadow-lg scale-105 rotate-1',
        isResizing && 'shadow-lg',
        className
      )}
      style={{
        left: layout.x + CALENDAR_CONSTANTS.GRID_MARGIN_LEFT, // Offset for time label column
        top: layout.y + 60 + 48, // Offset for header + all-day row
        width: layout.width,
        height: layout.height,
        backgroundColor: `${priorityColor}15`,
        borderLeftColor: priorityColor,
        zIndex: layout.zIndex + (isSelected ? 10 : 0),
        ...draggableStyle,
        ...style,
      }}
      initial={false}
      animate={{
        scale: isDragging ? 1.05 : 1,
        rotate: isDragging ? 1 : 0,
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect?.(event);
      }}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onEdit?.(event);
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      {...attributes}
      {...listeners}
    >
      {/* Resize handle - top */}
      <div
        className="absolute top-0 left-0 right-0 h-2 cursor-ns-resize opacity-0 hover:opacity-100 
                   bg-gradient-to-b from-white/20 to-transparent z-10"
        onMouseDown={(e) => {
          e.stopPropagation();
          handleResizeStart('top', e.clientY);
        }}
      />

      {/* Event content */}
      <div className="flex-1 p-2 min-h-0">
        {/* Header with title and actions */}
        <div className="flex items-start justify-between mb-1">
          <h3 
            className="text-sm font-medium text-white truncate flex-1"
            style={{ color: priorityColor }}
            title={event.title}
          >
            {event.title}
          </h3>
          
          {(isHovering || isSelected) && (
            <div className="flex items-center gap-1 ml-2">
              <button
                className="w-4 h-4 flex items-center justify-center rounded 
                         text-neutral-400 hover:text-white hover:bg-black/20"
                onClick={(e) => {
                  e.stopPropagation();
                  // Show context menu or quick actions
                }}
              >
                <MoreHorizontal size={12} />
              </button>
            </div>
          )}
        </div>

        {/* Time display */}
        {shouldShowTime && (
          <div className="flex items-center gap-1 text-xs text-neutral-300 mb-1">
            <Clock size={10} />
            <span>
              {format(startTime, 'h:mm a')} - {format(endTime, 'h:mm a')}
            </span>
            <span className="text-neutral-400">({duration}m)</span>
          </div>
        )}

        {/* Description */}
        {shouldShowFullText && event.description && (
          <p className="text-xs text-neutral-300 line-clamp-2">
            {event.description}
          </p>
        )}

        {/* Priority indicator for small events */}
        {!shouldShowFullText && event.task?.priority && (
          <div 
            className="w-2 h-2 rounded-full absolute top-1 right-1"
            style={{ backgroundColor: priorityColor }}
          />
        )}
      </div>

      {/* Resize handle - bottom */}
      <div
        className="absolute bottom-0 left-0 right-0 h-2 cursor-ns-resize opacity-0 hover:opacity-100
                   bg-gradient-to-t from-white/20 to-transparent z-10"
        onMouseDown={(e) => {
          e.stopPropagation();
          handleResizeStart('bottom', e.clientY);
        }}
      />

      {/* Drag handle indicator */}
      {(isHovering || isDragging) && (
        <div className="absolute left-1 top-1/2 transform -translate-y-1/2 text-neutral-400">
          <GripVertical size={12} />
        </div>
      )}
    </motion.div>
  );
};

EventBlock.displayName = 'EventBlock';