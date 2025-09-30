import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DndContext, DragOverlay } from '@dnd-kit/core';
import type { DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { format, addDays, startOfWeek, endOfWeek } from 'date-fns';
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react';

import { WeekGrid } from './components/WeekGrid';
import { EventBlock } from './components/EventBlock';
import { NewEventModal } from './components/NewEventModal';
import { EditEventModal } from './components/EditEventModal';
import { SelectionLayer } from './components/SelectionLayer';
import { SelectionManager } from './calendar-logic/selection';
import { OverlapCalculator } from './calendar-logic/overlaps';
import { CALENDAR_CONSTANTS } from '../../lib/utils/constants';

import type { CalendarEvent, CreateTaskData } from '@/types';
import {
  useCalendarEvents,
  useCreateCalendarEvent,
  useUpdateCalendarEvent,
  useDeleteCalendarEvent,
  useDuplicateCalendarEvent,
} from '../../hooks/useCalendarEvents';
import { 
  useScreenReaderAnnouncements 
} from '../../hooks/useKeyboardNavigation';
import { cn } from '../../lib/utils';

interface WeeklyCalendarProps {
  onEventClick?: (event: CalendarEvent) => void;
  onCreateEvent?: (eventData: { start: string; end: string; title?: string }) => void;
  className?: string;
}

export function WeeklyCalendar({
  onEventClick,
  onCreateEvent,
  className,
}: WeeklyCalendarProps) {
  // State management
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [draggedEvent, setDraggedEvent] = useState<CalendarEvent | null>(null);
  const [showNewEventModal, setShowNewEventModal] = useState(false);
  const [showEditEventModal, setShowEditEventModal] = useState(false);
  const [newEventData, setNewEventData] = useState<{ start: string; end: string; title?: string } | null>(null);
  
  // Pointer selection state
  const [isSelecting, setIsSelecting] = useState(false);
  const [selection, setSelection] = useState(SelectionManager.cancelSelection());
  
  // Refs
  const selectionOverlayRef = useRef<HTMLDivElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Week calculation
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 });

  // Fetch calendar events using custom hook
  const { data: events = [], isLoading, error } = useCalendarEvents(
    format(weekStart, 'yyyy-MM-dd'),
    format(weekEnd, 'yyyy-MM-dd')
  );

  // Mutations
  const createEventMutation = useCreateCalendarEvent();
  const updateEventMutation = useUpdateCalendarEvent();
  const deleteEventMutation = useDeleteCalendarEvent();
  const duplicateEventMutation = useDuplicateCalendarEvent();

  // Accessibility hooks
  const { announce } = useScreenReaderAnnouncements();

  // Calendar configuration - match WeekGrid constants
  const START_HOUR = 6;
  const END_HOUR = 22;
  const SLOT_INTERVAL = 30; // minutes
  const COLUMN_WIDTH = 160; // pixels from CALENDAR_CONSTANTS.GRID_DAY_WIDTH
  const GRID_MARGIN_LEFT = CALENDAR_CONSTANTS.GRID_MARGIN_LEFT; // 60px hour gutter

  // Refs for grid elements
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const gridInnerRef = useRef<HTMLDivElement | null>(null);
  const headerRef = useRef<HTMLDivElement | null>(null);
  const gutterRef = useRef<HTMLDivElement | null>(null);
  const dayColumnsRef = useRef<HTMLDivElement[]>([]);

  // Debug state
  const [debugEnabled, setDebugEnabled] = useState<boolean>(() => {
    try {
      return localStorage.getItem('calendarDebug') === '1';
    } catch {
      return false;
    }
  });
  const [debugInfo, setDebugInfo] = useState<{
    clientX: number;
    clientY: number;
    x: number;
    y: number;
    dayIndex: number;
    headerHeight: number;
    scrollTop: number;
  } | null>(null);

  // Utility: base date for a given day index
  const getBaseDateForDay = useCallback((dayIndex: number) => addDays(weekStart, dayIndex), [weekStart]);

  // Calculate event layouts for overlap handling
  const eventLayouts = React.useMemo(() => {
    const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
    const layouts = new Map();
    
    weekDays.forEach((day) => {
      const dayEvents = events.filter(event => {
        const eventDate = new Date(event.start);
        return format(eventDate, 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd');
      });
      
      if (dayEvents.length > 0) {
        const dayLayouts = OverlapCalculator.calculateEventLayouts(dayEvents, COLUMN_WIDTH);
        dayLayouts.forEach(layout => {
          layouts.set(layout.id, layout);
        });
      }
    });
    
    return layouts;
  }, [events, weekStart]);

  // Navigation handlers
  const handlePreviousWeek = useCallback(() => {
    setCurrentDate(prev => addDays(prev, -7));
  }, []);

  const handleNextWeek = useCallback(() => {
    setCurrentDate(prev => addDays(prev, 7));
  }, []);

  const handleToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  // Event mutation handlers
  const handleCreateEvent = useCallback(async (eventData: CreateTaskData) => {
    const startIso = eventData.dueDate;
    const durationMinutes = Math.max(eventData.estimatedDuration || 30, 15);
    const endIso = new Date(new Date(startIso).getTime() + durationMinutes * 60 * 1000).toISOString();

    const { title, ...rest } = eventData;
    await createEventMutation.mutateAsync({
      start: startIso,
      end: endIso,
      title,
      ...rest,
    });
    setShowNewEventModal(false);
    setNewEventData(null);
    announce(`Event "${eventData.title}" created successfully`);
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

  const handleNewEventClick = useCallback(() => {
    const now = new Date();
    const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);
    
    setNewEventData({
      start: now.toISOString(),
      end: oneHourLater.toISOString(),
      title: 'New Event',
    });
    setShowNewEventModal(true);
  }, []);

  // Event handlers
  const handleEventSelect = useCallback((event: CalendarEvent) => {
    setSelectedEvent(event);
    onEventClick?.(event);
  }, [onEventClick]);

  const handleEventEdit = useCallback((event: CalendarEvent) => {
    setSelectedEvent(event);
    setShowEditEventModal(true);
  }, []);

  // Selection rendering handled by SelectionLayer

  // Robust client -> grid coords using scroller scroll and dynamic header height
  const clientToGridCoords = useCallback((clientX: number, clientY: number) => {
    if (!scrollerRef.current) return null;
    const scroller = scrollerRef.current;
    const rect = scroller.getBoundingClientRect();
    const headerHeight = headerRef.current?.getBoundingClientRect().height ?? 64;

    // Position within scrollable content area (top-left of content is 0,0 at start of grid rows)
    const contentX = clientX - rect.left + scroller.scrollLeft - GRID_MARGIN_LEFT;
    const contentY = clientY - rect.top + scroller.scrollTop - headerHeight;

    // Guard: outside selectable area
    if (contentX < 0) return null;

    const dayWidth = CALENDAR_CONSTANTS.GRID_DAY_WIDTH;
    const dayIndex = Math.max(0, Math.min(6, Math.floor(contentX / dayWidth)));
    const xInDay = contentX - dayIndex * dayWidth;

    if (xInDay < 0) return null;

    if (debugEnabled) {
      setDebugInfo({
        clientX,
        clientY,
        x: xInDay,
        y: contentY,
        dayIndex,
        headerHeight,
        scrollTop: scroller.scrollTop,
      });
    }

    return { x: xInDay, y: Math.max(0, contentY), dayIndex, headerHeight };
  }, [debugEnabled]);

  // Toggle debug via keyboard: Ctrl/Cmd+Shift+D
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key.toLowerCase() === 'd')) {
        e.preventDefault();
        setDebugEnabled(prev => {
          const next = !prev;
          try { localStorage.setItem('calendarDebug', next ? '1' : '0'); } catch {}
          return next;
        });
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // Drag and drop handlers
  const handleDragStart = useCallback((event: DragStartEvent) => {
    const eventData = event.active.data.current?.event as CalendarEvent;
    if (eventData) {
      setDraggedEvent(eventData);
    }
  }, []);

  const handleDragEnd = useCallback((_event: DragEndEvent) => {
    setDraggedEvent(null);
    // Drag and drop updates are handled by EventBlock component directly
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
    const baseDate = getBaseDateForDay(coords.dayIndex);
    const next = SelectionManager.startSelection(coords.x, coords.y, coords.dayIndex, baseDate, START_HOUR);
    setSelection(next);
    setIsSelecting(true);
    document.body.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';
  }, [getBaseDateForDay, clientToGridCoords]);

  const updateSelection = useCallback((e: React.PointerEvent) => {
    if (!isSelecting || !selection.isSelecting || selection.dayIndex === undefined) return;
    const coords = clientToGridCoords(e.clientX, e.clientY);
    if (!coords) return;
    const baseDate = getBaseDateForDay(selection.dayIndex);
    const next = SelectionManager.updateSelection(selection, coords.x, coords.y, baseDate, START_HOUR);
    setSelection(next);
  }, [isSelecting, selection, getBaseDateForDay, clientToGridCoords]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isSelecting) return;
    
    // Throttle with requestAnimationFrame
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
    const finalBounds = SelectionManager.endSelection(selection);
    if (finalBounds) {
      const payload = { start: finalBounds.startTime.toISOString(), end: finalBounds.endTime.toISOString(), title: 'New Event' };
      if (onCreateEvent) {
        onCreateEvent(payload);
      } else {
        setNewEventData(payload);
        setShowNewEventModal(true);
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


  // Don't block calendar display on loading/error states

  return (
    <div className={cn('w-full max-w-full', className)}>
      {/* Header with navigation */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-white">
            {format(currentDate, 'MMMM yyyy')}
          </h2>
          
          <div className="flex items-center gap-1 bg-neutral-800 rounded-lg p-1">
            <button
              onClick={handlePreviousWeek}
              className="p-2 hover:bg-neutral-700 rounded-md transition-colors text-neutral-300 hover:text-white"
            >
              <ChevronLeft size={18} />
            </button>
            
            <button
              onClick={handleToday}
              className="px-3 py-2 hover:bg-neutral-700 rounded-md transition-colors text-neutral-300 hover:text-white text-sm font-medium"
            >
              Today
            </button>
            
            <button
              onClick={handleNextWeek}
              className="p-2 hover:bg-neutral-700 rounded-md transition-colors text-neutral-300 hover:text-white"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleNewEventClick}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm font-medium"
          >
            <Plus size={16} />
            New Event
          </button>
        </div>
      </div>

      {/* Calendar grid */}
      <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div 
          ref={scrollerRef}
          className="relative overflow-auto"
          data-calendar-container
          tabIndex={0}
          role="grid"
          aria-label={`Calendar for week of ${format(weekStart, 'MMMM d, yyyy')}`}
          aria-rowcount={48}
          aria-colcount={7}
        >
          {/* Selection overlay - transparent layer for pointer events */}
          <div
            ref={selectionOverlayRef}
            className="absolute inset-0 z-30"
            style={{ pointerEvents: 'auto' }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerCancel}
          />
          
          <WeekGrid 
            currentDate={currentDate}
            startHour={START_HOUR}
            endHour={END_HOUR}
            slotInterval={SLOT_INTERVAL}
            className="overflow-hidden"
            gridInnerRef={gridInnerRef}
            headerRef={headerRef}
            gutterRef={gutterRef}
            dayColumnsRef={dayColumnsRef}
          >
            {/* Show loading indicator if tasks are loading */}
            {isLoading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-neutral-900/50">
                <div className="flex items-center gap-3 bg-neutral-800 px-4 py-2 rounded-lg">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
                  <span className="text-white text-sm">Loading tasks...</span>
                </div>
              </div>
            )}

            {/* Show error notification if tasks failed to load */}
            {error && (
              <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
                <div className="bg-error border border-error text-white px-4 py-2 rounded-lg text-sm">
                  Tasks failed to load. Calendar functionality may be limited.
                </div>
              </div>
            )}

            {/* Render events */}
            {!error && events.map((event) => {
              const layout = eventLayouts.get(event.id);
              if (!layout) return null;

              return (
                <EventBlock
                  key={event.id}
                  event={event}
                  layout={layout}
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
              onCreateEvent={(startTime, endTime) => {
                const payload = { start: startTime.toISOString(), end: endTime.toISOString(), title: 'New Event' };
                if (onCreateEvent) {
                  onCreateEvent(payload);
                } else {
                  setNewEventData(payload);
                  setShowNewEventModal(true);
                }
              }}
            />

            {/* Debug marker showing exact computed position */}
            {debugEnabled && debugInfo && (
              <div className="pointer-events-none" style={{ position: 'absolute', zIndex: 50 }}>
                {/* Dot at computed position */}
                <div
                  style={{
                    position: 'absolute',
                    left: GRID_MARGIN_LEFT + (debugInfo.dayIndex * CALENDAR_CONSTANTS.GRID_DAY_WIDTH) + debugInfo.x - 4,
                    top: (debugInfo.headerHeight) + Math.max(0, debugInfo.y) - 4,
                    width: 8,
                    height: 8,
                    borderRadius: 9999,
                    backgroundColor: '#22c55e',
                    border: '2px solid white',
                  }}
                />
                {/* Info panel */}
                <div
                  style={{
                    position: 'absolute',
                    right: 8,
                    top: 8,
                    background: 'rgba(17,24,39,0.9)',
                    color: 'white',
                    border: '1px solid #374151',
                    padding: '6px 8px',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                >
                  <div>dayIndex: {debugInfo.dayIndex}</div>
                  <div>x: {Math.round(debugInfo.x)} px, y: {Math.round(debugInfo.y)} px</div>
                  <div>scrollTop: {Math.round(debugInfo.scrollTop)} px</div>
                  <div>header: {Math.round(debugInfo.headerHeight)} px</div>
                  <div>client: {Math.round(debugInfo.clientX)}, {Math.round(debugInfo.clientY)}</div>
                  <div>Press Ctrl/Cmd+Shift+D to toggle</div>
                </div>
              </div>
            )}
          </WeekGrid>

          {/* Drag overlay */}
          <DragOverlay>
            {draggedEvent && eventLayouts.get(draggedEvent.id) && (
              <EventBlock
                event={draggedEvent}
                layout={eventLayouts.get(draggedEvent.id)!}
                isDragging={true}
                className="opacity-90"
              />
            )}
          </DragOverlay>
        </div>
      </DndContext>

      {/* Week indicator */}
      <div className="mt-4 text-center text-sm text-neutral-400">
        Week of {format(weekStart, 'MMM d')} - {format(weekEnd, 'MMM d, yyyy')}
      </div>

      {/* Modals */}
      <NewEventModal
        isOpen={showNewEventModal}
        initialData={newEventData ?? undefined}
        onClose={() => {
          setShowNewEventModal(false);
          setNewEventData(null);
        }}
        onCreate={handleCreateEvent}
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
