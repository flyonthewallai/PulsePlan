import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DndContext, DragOverlay } from '@dnd-kit/core';
import type { DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { format } from 'date-fns';

import { DayGrid } from './components/DayGrid';
import { EventBlock } from './components/EventBlock';
import { CreateEventTaskModal } from './components/CreateEventTaskModal';
import { AIEventPrompt } from './components/AIEventPrompt';
import { EditEventModal } from './components/EditEventModal';
import { EventDetailsModal } from './components/EventDetailsModal';
import { SelectionLayer } from './components/SelectionLayer';
import { SelectionManager } from './calendar-logic/selection';
import { OverlapCalculator, type EventLayout } from './calendar-logic/overlaps';
import { CALENDAR_CONSTANTS } from '@/lib/utils/constants';

import type { CalendarEvent, CreateTaskData } from '@/types';
import {
  useCalendarEvents,
  useCreateCalendarEvent,
  useUpdateCalendarEvent,
  useDeleteCalendarEvent,
  useDuplicateCalendarEvent,
} from '@/hooks/calendar';
import { useTimeblocks } from '@/hooks/calendar';
import {
  useScreenReaderAnnouncements
} from '@/hooks/ui';
import { cn } from '@/lib/utils';
import type { Timeblock } from '@/types';
import { useQueryClient } from '@tanstack/react-query';

interface DailyCalendarProps {
  onEventClick?: (event: CalendarEvent) => void;
  onCreateEvent?: (eventData: { start: string; end: string; title?: string }) => void;
  className?: string;
  currentDate?: Date;
}

export function DailyCalendar({
  onEventClick,
  onCreateEvent,
  className,
  currentDate = new Date(),
}: DailyCalendarProps) {
  // Query client for cache invalidation
  const queryClient = useQueryClient();
  
  // State management
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [draggedEvent, setDraggedEvent] = useState<CalendarEvent | null>(null);
  const [showNewEventModal, setShowNewEventModal] = useState(false);
  const [showAIPrompt, setShowAIPrompt] = useState(false);
  const [showEditEventModal, setShowEditEventModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [newEventData, setNewEventData] = useState<{ start: string; end: string; title?: string } | null>(null);
  
  // Pointer selection state
  const [isSelecting, setIsSelecting] = useState(false);
  const [selection, setSelection] = useState(SelectionManager.cancelSelection());
  
  // Refs
  const selectionOverlayRef = useRef<HTMLDivElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Day calculation - memoize to prevent unnecessary refetches
  const dayStartStr = React.useMemo(() => format(currentDate, 'yyyy-MM-dd'), [currentDate]);
  const dayStartISO = React.useMemo(() => {
    const start = new Date(currentDate);
    start.setHours(0, 0, 0, 0);
    return start.toISOString();
  }, [currentDate]);
  const dayEndISO = React.useMemo(() => {
    const end = new Date(currentDate);
    end.setHours(23, 59, 59, 999);
    return end.toISOString();
  }, [currentDate]);

  // Fetch unified timeblocks (tasks + external calendar events + busy blocks)
  const { items: timeblocks = [], isLoading: timeblocksLoading, error: timeblocksError } = useTimeblocks({
    fromISO: dayStartISO,
    toISO: dayEndISO,
  });

  // Fetch calendar events using custom hook (tasks only) - ONLY as fallback if timeblocks fail
  const {
    data: taskEvents = [],
    isLoading: tasksLoading,
    error: tasksError
  } = useCalendarEvents(dayStartStr, dayStartStr, {
    enabled: timeblocks.length === 0 && !timeblocksLoading,
  });

  // Convert timeblocks to CalendarEvent format for rendering
  const timeblockEvents: CalendarEvent[] = timeblocks.map((block: Timeblock) => {
    return {
      id: block.id,
      title: block.title,
      description: block.description || undefined,
      start: block.start,
      end: block.end,
      allDay: block.isAllDay,
      color: block.color || (block.source === 'task' ? '#3b82f6' : block.source === 'calendar' ? '#3b82f6' : '#ef4444'),
      priority: block.priority || 'medium',
      task: block.source === 'task' ? taskEvents.find(e => e.id === block.id)?.task : undefined,
      timeblock: block,
    } as CalendarEvent & { timeblock: Timeblock };
  });

  // Combine both sources (prefer timeblocks for complete view)
  const events = timeblockEvents.length > 0 ? timeblockEvents : taskEvents;
  const isLoading = timeblocksLoading || tasksLoading;
  const error = timeblocksError && tasksError ? timeblocksError : null;

  // Mutations
  const createEventMutation = useCreateCalendarEvent();
  const updateEventMutation = useUpdateCalendarEvent();
  const deleteEventMutation = useDeleteCalendarEvent();
  const duplicateEventMutation = useDuplicateCalendarEvent();

  // Accessibility hooks
  const { announce } = useScreenReaderAnnouncements();

  // Calendar configuration
  const START_HOUR = 6;
  const END_HOUR = 24;
  const SLOT_INTERVAL = 30;
  const GRID_MARGIN_LEFT = CALENDAR_CONSTANTS.GRID_MARGIN_LEFT;

  // Refs for grid elements
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const gridInnerRef = useRef<HTMLDivElement | null>(null);
  const dayColumnRef = useRef<HTMLDivElement | null>(null);
  
  // Dynamic column width based on actual rendered size
  const [columnWidth, setColumnWidth] = useState(CALENDAR_CONSTANTS.GRID_DAY_WIDTH);
  
  // Calculate actual column width from rendered grid
  useEffect(() => {
    const calculateColumnWidth = () => {
      if (gridInnerRef.current) {
        const gridWidth = gridInnerRef.current.offsetWidth;
        const availableWidth = gridWidth - GRID_MARGIN_LEFT;
        setColumnWidth(availableWidth);
      }
    };
    
    calculateColumnWidth();
    window.addEventListener('resize', calculateColumnWidth);
    
    const resizeObserver = new ResizeObserver(calculateColumnWidth);
    if (gridInnerRef.current) {
      resizeObserver.observe(gridInnerRef.current);
    }
    
    return () => {
      window.removeEventListener('resize', calculateColumnWidth);
      resizeObserver.disconnect();
    };
  }, [GRID_MARGIN_LEFT]);

  // Calculate event layouts for overlap handling
  const eventLayouts = React.useMemo(() => {
    const layouts = new Map();
    const dayDateStr = format(currentDate, 'yyyy-MM-dd');

    const dayEvents = events.filter(event => {
      let eventDateStr: string;

      if (event.allDay && typeof event.start === 'string') {
        eventDateStr = event.start.split('T')[0];
      } else {
        const eventStart = new Date(event.start);
        eventDateStr = format(eventStart, 'yyyy-MM-dd');
      }

      return eventDateStr === dayDateStr;
    });

    if (dayEvents.length > 0) {
      // Separate all-day events from timed events
      const timedEvents = dayEvents.filter(e => !e.allDay);
      const allDayEvents = dayEvents.filter(e => e.allDay);

      // Process timed events
      if (timedEvents.length > 0) {
        const dayLayouts = OverlapCalculator.calculateEventLayouts(timedEvents, columnWidth, START_HOUR);
        dayLayouts.forEach(layout => {
          layouts.set(layout.id, layout);
        });
      }

      // Process all-day events
      if (allDayEvents.length > 0) {
        const EVENT_HEIGHT = 32;
        const VERTICAL_GAP = 4;

        allDayEvents.forEach((event, index) => {
          const allDayLayout: EventLayout = {
            id: event.id,
            event,
            x: GRID_MARGIN_LEFT,
            y: (index * (EVENT_HEIGHT + VERTICAL_GAP)) + 4,
            width: columnWidth - 8,
            height: EVENT_HEIGHT,
            laneIndex: 0,
            laneCount: 1,
            zIndex: 10,
          };
          layouts.set(allDayLayout.id, allDayLayout);
        });
      }
    }

    return layouts;
  }, [events, currentDate, columnWidth, GRID_MARGIN_LEFT, START_HOUR]);

  // Event mutation handlers
  const handleCreateEvent = useCallback(async (eventData: any) => {
    const startIso = eventData.start || eventData.dueDate;
    const endIso = eventData.end || new Date(new Date(startIso).getTime() + (eventData.estimatedDuration || 60) * 60 * 1000).toISOString();

    const { title, description, priority, subject, allDay } = eventData;
    await createEventMutation.mutateAsync({
      start: startIso,
      end: endIso,
      title,
      description,
      priority,
      subject,
      allDay,
    });
    setShowNewEventModal(false);
    setNewEventData(null);
    announce(`Event "${title}" created successfully`);
  }, [createEventMutation, announce]);

  const handleUpdateEvent = useCallback(async (eventId: string, updates: Partial<CalendarEvent>) => {
    await updateEventMutation.mutateAsync({ eventId, updates });
    setShowEditEventModal(false);
    setSelectedEvent(null);
    announce(`Event updated successfully`);
  }, [updateEventMutation, announce]);

  const handleDeleteEvent = useCallback(async (eventId: string) => {
    const event = events.find(e => e.id === eventId);
    await deleteEventMutation.mutateAsync(eventId);
    setShowEditEventModal(false);
    setSelectedEvent(null);
    announce(`Event "${event?.title || 'Unknown event'}" deleted`);
  }, [deleteEventMutation, events, announce]);

  const handleDuplicateEvent = useCallback(async (event: CalendarEvent) => {
    await duplicateEventMutation.mutateAsync(event);
  }, [duplicateEventMutation]);

  // Event handlers
  const handleEventSelect = useCallback((event: CalendarEvent) => {
    setSelectedEvent(event);
    setShowDetailsModal(true);
  }, []);

  const handleEventEdit = useCallback((event: CalendarEvent) => {
    setSelectedEvent(event);
    setShowEditEventModal(true);
  }, []);

  // Convert client coordinates to grid coordinates
  const clientToGridCoords = useCallback((clientX: number, clientY: number) => {
    if (!scrollerRef.current) return null;

    const scroller = scrollerRef.current;
    const rect = scroller.getBoundingClientRect();

    const ALL_DAY_ROW_HEIGHT = CALENDAR_CONSTANTS.ALL_DAY_ROW_HEIGHT;
    const TIME_COLUMN_WIDTH = CALENDAR_CONSTANTS.GRID_MARGIN_LEFT;
    const HOUR_HEIGHT = CALENDAR_CONSTANTS.GRID_HOUR_HEIGHT;
    const MINUTES_PER_PIXEL = 60 / HOUR_HEIGHT;
    
    const relativeX = clientX - rect.left + scroller.scrollLeft;
    const relativeY = clientY - rect.top + scroller.scrollTop;
    
    const dayAreaX = relativeX - TIME_COLUMN_WIDTH;
    const gridY = relativeY - ALL_DAY_ROW_HEIGHT;
    
    if (dayAreaX < 0 || gridY < 0) return null;
    
    const xInDay = dayAreaX;
    const minutesFromStart = gridY * MINUTES_PER_PIXEL;
    const snappedMinutes = Math.round(minutesFromStart / 15) * 15;
    const snappedY = snappedMinutes / MINUTES_PER_PIXEL;
    
    return { 
      x: xInDay, 
      y: snappedY, 
      dayIndex: 0, // Always 0 for day view
      headerHeight: ALL_DAY_ROW_HEIGHT 
    };
  }, [columnWidth]);

  // Drag and drop handlers
  const handleDragStart = useCallback((event: DragStartEvent) => {
    const eventData = event.active.data.current?.event as CalendarEvent;
    if (eventData) {
      setDraggedEvent(eventData);
    }
  }, []);

  const handleDragEnd = useCallback((_event: DragEndEvent) => {
    setDraggedEvent(null);
  }, []);

  // Pointer event handlers for drag-to-create
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest('[data-event-block]')) {
      return;
    }
    const coords = clientToGridCoords(e.clientX, e.clientY);
    if (!coords) return;

    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    const next = SelectionManager.startSelection(coords.x, coords.y, 0, currentDate, START_HOUR);

    setSelection(next);
    setIsSelecting(true);
    document.body.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';
  }, [currentDate, clientToGridCoords, START_HOUR]);

  const updateSelection = useCallback((e: React.PointerEvent) => {
    if (!isSelecting || !selection.isSelecting || selection.dayIndex === undefined) return;
    const coords = clientToGridCoords(e.clientX, e.clientY);
    if (!coords) return;
    const next = SelectionManager.updateSelection(selection, coords.x, coords.y, currentDate, START_HOUR);
    setSelection(next);
  }, [isSelecting, selection, currentDate, clientToGridCoords]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isSelecting) return;
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    animationFrameRef.current = requestAnimationFrame(() => {
      updateSelection(e);
    });
  }, [isSelecting, updateSelection]);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (!isSelecting || !selection.isSelecting) return;
    e.currentTarget.releasePointerCapture(e.pointerId);
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    const finalBounds = SelectionManager.endSelection(selection, START_HOUR);
    if (finalBounds) {
      const payload = { start: finalBounds.startTime.toISOString(), end: finalBounds.endTime.toISOString(), title: 'New Event' };
      if (onCreateEvent) {
        onCreateEvent(payload);
      } else {
        setNewEventData(payload);
        // Show AI prompt instead of traditional modal
        setShowAIPrompt(true);
      }
    }
    setIsSelecting(false);
    setSelection(SelectionManager.cancelSelection());
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, [isSelecting, selection, onCreateEvent]);

  const handlePointerCancel = useCallback(() => {
    setIsSelecting(false);
    setSelection(SelectionManager.cancelSelection());
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, []);

  return (
    <div className={cn('w-full h-full flex flex-col min-h-0', className)}>
      <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div 
          ref={scrollerRef}
          className="relative flex-1"
          data-calendar-container
          tabIndex={0}
          role="grid"
          aria-label={`Calendar for ${format(currentDate, 'MMMM d, yyyy')}`}
          aria-rowcount={48}
          aria-colcount={1}
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(156, 163, 175, 0.3) transparent',
            overflow: 'visible'
          }}
        >
          <DayGrid 
            currentDate={currentDate}
            startHour={START_HOUR}
            endHour={END_HOUR}
            slotInterval={SLOT_INTERVAL}
            className="absolute inset-0 pointer-events-none"
            gridInnerRef={gridInnerRef}
            dayColumnRef={dayColumnRef}
          />
          
          {/* Selection overlay */}
          <div
            ref={selectionOverlayRef}
            className="absolute inset-0"
            style={{
              pointerEvents: 'auto',
              zIndex: 1,
            }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerCancel}
          />
          
          <div className="relative w-full h-full">
            {isLoading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-neutral-900/50">
                <div className="flex items-center gap-3 bg-neutral-800 px-4 py-2 rounded-lg">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
                  <span className="text-white text-sm">Loading tasks...</span>
                </div>
              </div>
            )}

            {error && (
              <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
                <div className="bg-error border border-error text-white px-4 py-2 rounded-lg text-sm">
                  Unable to load calendar data. Some events may not be visible.
                </div>
              </div>
            )}

            {!error && events.map((event) => {
              const layout = eventLayouts.get(event.id);
              if (!layout) return null;

              return (
                <EventBlock
                  key={event.id}
                  event={event}
                  layout={layout}
                  dayIndex={0}
                  startHour={START_HOUR}
                  columnWidth={columnWidth}
                  isSelected={selectedEvent?.id === event.id}
                  isDragging={draggedEvent?.id === event.id}
                  onSelect={handleEventSelect}
                  onEdit={handleEventEdit}
                  onDragStart={(e) => setDraggedEvent(e)}
                  onDragEnd={(event, newStart, newEnd) => {
                    handleUpdateEvent(event.id, {
                      start: newStart.toISOString(),
                      end: newEnd.toISOString(),
                    });
                    setDraggedEvent(null);
                  }}
                  onResizeEnd={(event, newStart, newEnd) => {
                    handleUpdateEvent(event.id, {
                      start: newStart.toISOString(),
                      end: newEnd.toISOString(),
                    });
                  }}
                  data-event-block
                />
              );
            })}
            
            {/* Selection overlay visualization */}
            <SelectionLayer
              selection={selection}
              columnWidth={columnWidth}
              onCreateEvent={(startTime, endTime) => {
                const payload = { start: startTime.toISOString(), end: endTime.toISOString(), title: 'New Event' };
                if (onCreateEvent) {
                  onCreateEvent(payload);
                } else {
                  setNewEventData(payload);
                  // Show AI prompt instead of traditional modal
                  setShowAIPrompt(true);
                }
              }}
            />
          </div>
        </div>

        {/* Drag overlay */}
        <DragOverlay>
          {draggedEvent && eventLayouts.get(draggedEvent.id) && (
            <EventBlock
              event={draggedEvent}
              layout={eventLayouts.get(draggedEvent.id)!}
              dayIndex={0}
              startHour={START_HOUR}
              columnWidth={columnWidth}
              isDragging={true}
              className="opacity-90"
            />
          )}
        </DragOverlay>
      </DndContext>

      {/* Modals and AI Prompt */}
      <AIEventPrompt
        isOpen={showAIPrompt}
        onClose={() => {
          setShowAIPrompt(false);
          setNewEventData(null);
        }}
        onSubmit={async (prompt) => {
          if (!newEventData) return;
          // Use API service to create event with AI extraction
          const { apiService } = await import('@/services/core/apiService');
          const newEvent = await apiService.createEventWithAI(prompt, {
            start: newEventData.start,
            end: newEventData.end,
          });
          // Refresh calendar data
          queryClient.invalidateQueries({ queryKey: ['timeblocks'] });
        }}
        timeSlot={newEventData}
      />
      
      <CreateEventTaskModal
        isOpen={showNewEventModal}
        initialData={newEventData ?? undefined}
        onClose={() => {
          setShowNewEventModal(false);
          setNewEventData(null);
        }}
        onCreate={handleCreateEvent}
      />

      <EventDetailsModal
        isOpen={showDetailsModal}
        event={selectedEvent}
        onClose={() => {
          setShowDetailsModal(false);
          setSelectedEvent(null);
        }}
      />

      <EditEventModal
        isOpen={showEditEventModal}
        event={selectedEvent}
        onClose={() => {
          setShowEditEventModal(false);
          setSelectedEvent(null);
        }}
        onUpdate={handleUpdateEvent}
        onDelete={handleDeleteEvent}
        onDuplicate={handleDuplicateEvent}
      />
    </div>
  );
}




