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
import { calculateEventPosition } from '../calendar-logic/positioning';

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
  dayIndex: number;
  startHour: number;
  columnWidth?: number; // Dynamic column width
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
  dayIndex,
  startHour,
  columnWidth,
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
  // USE THE NEW POSITIONING SYSTEM - SINGLE SOURCE OF TRUTH
  const position = React.useMemo(() => {
    console.log(`🔍 [EventBlock] Computing position for "${event.title}"`, {
      dayIndex,
      startHour,
      eventStart: event.start,
      eventAllDay: event.allDay,
      layoutFromProps: layout,
      columnWidth
    });

    // For all-day events, extract stack index from layout if available
    let stackIndex = 0;
    if (event.allDay && layout) {
      // The old layout system stored Y position - derive stack index from it
      // Each all-day event is 24px tall with 4px padding
      stackIndex = Math.floor((layout.y - 4) / 24);
    }

    const computed = calculateEventPosition(event, dayIndex, startHour, {
      stackIndex: event.allDay ? stackIndex : undefined,
      columnWidth
    });
    console.log(`✅ [EventBlock] Computed position for "${event.title}":`, computed);
    return computed;
  }, [event, dayIndex, startHour, layout, columnWidth]);
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

  // Track pointer down position to distinguish clicks from drags
  const pointerDownPos = useRef<{ x: number; y: number } | null>(null);
  const CLICK_THRESHOLD = 5; // pixels - movement less than this is considered a click

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

  // Determine if this event is draggable (only non-readonly events)
  const isReadonly = event.timeblock?.readonly ?? true;
  const isDraggableEvent = !isReadonly;

  // Draggable setup - only enable for editable events
  const {
    attributes,
    listeners,
    setNodeRef: setDraggableRef,
    transform,
  } = useDraggable({
    id: event.id,
    data: { event, layout },
    disabled: isReadonly, // Disable dragging for readonly events
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

  // Determine what to show based on event type and size
  const isAllDay = event.allDay;
  const shouldShowFullText = layout.height > 40;
  const shouldShowTime = !isAllDay && layout.height > 60; // Never show time for all-day events

  // VERIFICATION: Log what we're about to render
  console.log(`📍 [EventBlock RENDER] "${event.title}" at:`, {
    position,
    appliedStyle: {
      left: position.left,
      top: position.top,
      width: position.width,
      height: position.height
    },
    layoutFromProps: layout,
    eventStart: event.start,
    eventAllDay: event.allDay
  });

  return (
    <motion.div
      ref={(node) => {
        setDraggableRef(node);
        eventRef.current = node;
      }}
      data-event-block // This prevents drag-to-create from triggering on events
      className={cn(
        'absolute select-none cursor-pointer transition-all duration-200',
        'rounded-lg overflow-hidden',
        'flex flex-col justify-between',
        'hover:brightness-110',
        isSelected && 'ring-2 ring-blue-400',
        isDragging && 'shadow-xl scale-105 rotate-1',
        isResizing && 'shadow-xl',
        className
      )}
      style={{
        // USE NEW POSITIONING - GUARANTEED CORRECT
        left: position.left,
        top: position.top,
        width: position.width,
        height: position.height,
        backgroundColor: 'rgba(59, 130, 246, 0.7)', // Notion-style translucent blue
        borderRadius: '0.5rem',
        zIndex: Math.max(layout.zIndex, 10) + (isSelected ? 10 : 0),
        pointerEvents: 'auto',
        boxShadow: isSelected ? '0 4px 12px rgba(59, 130, 246, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.2)',
        ...draggableStyle,
        ...style,
      }}
      initial={false}
      animate={{
        scale: isDragging ? 1.05 : 1,
        rotate: isDragging ? 1 : 0,
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      onPointerDown={(e) => {
        e.stopPropagation(); // Stop the drag-to-create overlay from capturing this
        // Track starting position for click detection
        pointerDownPos.current = { x: e.clientX, y: e.clientY };
      }}
      onPointerUp={(e) => {
        e.stopPropagation();

        // Calculate movement distance
        if (pointerDownPos.current) {
          const dx = Math.abs(e.clientX - pointerDownPos.current.x);
          const dy = Math.abs(e.clientY - pointerDownPos.current.y);
          const distance = Math.sqrt(dx * dx + dy * dy);

          // If movement was minimal, treat as click
          if (distance < CLICK_THRESHOLD) {
            onSelect?.(event);
          }

          pointerDownPos.current = null;
        }
      }}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onEdit?.(event);
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      {...(isDraggableEvent ? attributes : {})}
      {...(isDraggableEvent ? listeners : {})}
    >
      {/* Resize handle - top (subtle, shows on hover) */}
      <div
        className="absolute top-0 left-0 right-0 h-3 cursor-ns-resize opacity-0 group-hover:opacity-100 
                   bg-gradient-to-b from-white/10 to-transparent z-10 transition-opacity"
        onMouseDown={(e) => {
          e.stopPropagation();
          handleResizeStart('top', e.clientY);
        }}
      />

      {/* Event content */}
      <div className={cn(
        "flex-1 p-2 min-h-0 flex flex-col",
        isAllDay ? "justify-center" : "justify-start" // All-day centered, timed from top
      )}>
        {/* All-Day Event: Compact single-line layout */}
        {isAllDay ? (
          <div className="flex items-center justify-between w-full">
            <h3
              className="text-sm font-medium text-white truncate flex-1"
              title={event.title}
            >
              {event.title}
            </h3>
            {(isHovering || isSelected) && (
              <button
                className="w-4 h-4 flex items-center justify-center rounded ml-2 shrink-0
                         text-neutral-400 hover:text-white hover:bg-black/20"
                onClick={(e) => {
                  e.stopPropagation();
                  // Show context menu or quick actions
                }}
              >
                <MoreHorizontal size={12} />
              </button>
            )}
          </div>
        ) : (
          /* Timed Event: Full layout with time and description */
          <>
            {/* Header with title and actions */}
            <div className="flex items-start justify-between gap-1 mb-0.5">
              <h3
                className="text-sm font-medium text-white truncate flex-1 leading-tight"
                title={event.title}
              >
                {event.title}
              </h3>

              {(isHovering || isSelected) && (
                <button
                  className="w-4 h-4 flex items-center justify-center rounded shrink-0
                           text-neutral-400 hover:text-white hover:bg-black/20"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Show context menu or quick actions
                  }}
                >
                  <MoreHorizontal size={12} />
                </button>
              )}
            </div>

            {/* Time display - always visible for timed events */}
            {!isAllDay && (
              <div className="flex items-center gap-1 text-xs text-white/90 leading-tight">
                <Clock size={10} className="shrink-0" />
                <span className="whitespace-nowrap">
                  {format(startTime, 'h:mm a')}
                </span>
                {shouldShowTime && (
                  <>
                    <span className="text-white/60">-</span>
                    <span className="whitespace-nowrap">{format(endTime, 'h:mm a')}</span>
                  </>
                )}
              </div>
            )}

            {/* Description - only for taller events */}
            {shouldShowFullText && event.description && (
              <p className="text-xs text-white/70 line-clamp-2 mt-1 leading-tight">
                {event.description}
              </p>
            )}

            {/* Priority indicator for small events */}
            {!shouldShowFullText && event.task?.priority && (
              <div
                className="w-2 h-2 rounded-full absolute top-1.5 right-1.5"
                style={{ backgroundColor: priorityColor }}
              />
            )}
          </>
        )}
      </div>

      {/* Resize handle - bottom (shows drag handle on hover) */}
      {(isHovering || isSelected) && !isAllDay && (
        <div
          className="absolute bottom-0 left-0 right-0 h-4 cursor-ns-resize
                     bg-gradient-to-t from-white/10 to-transparent z-10 transition-opacity
                     flex items-end justify-center pb-1"
          onMouseDown={(e) => {
            e.stopPropagation();
            handleResizeStart('bottom', e.clientY);
          }}
        >
          <div className="w-8 h-1 bg-white/40 rounded-full" />
        </div>
      )}

    </motion.div>
  );
};

EventBlock.displayName = 'EventBlock';