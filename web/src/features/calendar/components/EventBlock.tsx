import React, { useRef } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { format } from 'date-fns';
import { Clock, Repeat } from 'lucide-react';
import { cn } from '../../../lib/utils';
import type { CalendarEvent } from '@/types';
import type { EventLayout } from '../calendar-logic/overlaps';
import { colors } from '../../../lib/utils/constants';
import { calculateEventPosition } from '../calendar-logic/positioning';

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
    return computed;
  }, [event, dayIndex, startHour, layout, columnWidth]);
  const eventRef = useRef<HTMLDivElement>(null);

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

  // Check if event is in the past
  const isPastEvent = endTime < new Date();

  // Determine if this event is draggable (disabled for now - user request)
  const isReadonly = true; // Disable dragging for all events
  const isDraggableEvent = false;

  // Draggable setup - DISABLED for now per user request
  const {
    attributes,
    listeners,
    setNodeRef: setDraggableRef,
    transform,
  } = useDraggable({
    id: event.id,
    data: { event, layout },
    disabled: true, // Disable dragging for all events
  });

  const draggableStyle = {}; // No drag transform

  // Determine what to show based on event type and size
  const isAllDay = event.allDay;
  const shouldShowFullText = layout.height > 40;
  const shouldShowTime = !isAllDay && layout.height > 60; // Never show time for all-day events

  // Check if event is recurring
  const isRecurring = Boolean(event.recurrence || event.timeblock?.recurrence);

  return (
    <div
      ref={(node) => {
        setDraggableRef(node);
        eventRef.current = node;
      }}
      data-event-block // This prevents drag-to-create from triggering on events
      className={cn(
        'absolute select-none cursor-pointer',
        'rounded-lg overflow-hidden',
        'flex flex-col justify-between',
        'hover:brightness-110 transition-all duration-150',
        isSelected && 'ring-2 ring-blue-400',
        isPastEvent && 'opacity-50', // Gray out past events
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
        ...style,
      }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect?.(event);
      }}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onEdit?.(event);
      }}
    >
      {/* Event content */}
      <div className={cn(
        "flex-1 p-2 min-h-0 flex flex-col",
        isAllDay ? "justify-center" : "justify-start" // All-day centered, timed from top
      )}>
        {/* All-Day Event: Compact single-line layout */}
        {isAllDay ? (
          <div className="flex items-center justify-between w-full gap-1">
            <div className="flex items-center gap-1.5 flex-1 min-w-0">
              <h3
                className="text-sm font-medium text-white truncate"
                title={event.title}
              >
                {event.title}
              </h3>
              {isRecurring && (
                <Repeat size={12} className="text-white/70 shrink-0" aria-label="Recurring event" />
              )}
            </div>
          </div>
        ) : (
          /* Timed Event: Full layout with time and description */
          <>
            {/* Header with title */}
            <div className="flex items-start justify-between gap-1 mb-0.5">
              <h3
                className="text-sm font-medium text-white truncate flex-1 leading-tight"
                title={event.title}
              >
                {event.title}
              </h3>
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
                {isRecurring && (
                  <Repeat size={10} className="text-white/70 shrink-0 ml-0.5" aria-label="Recurring event" />
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
    </div>
  );
};

EventBlock.displayName = 'EventBlock';