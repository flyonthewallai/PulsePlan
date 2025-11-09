import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DndContext, DragOverlay } from '@dnd-kit/core';
import type { DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { format, addDays, startOfWeek, endOfWeek } from 'date-fns';

import { WeekGrid } from './components/WeekGrid';
import { EventBlock } from './components/EventBlock';
import { CreateEventTaskModal } from './components/CreateEventTaskModal';
import { AIEventPrompt } from './components/AIEventPrompt';
import { EditEventModal } from './components/EditEventModal';
import { EventDetailsModal } from './components/EventDetailsModal';
import { SelectionLayer } from './components/SelectionLayer';
import { SelectionManager } from './calendar-logic/selection';
import { OverlapCalculator, type EventLayout } from './calendar-logic/overlaps';
import { CALENDAR_CONSTANTS } from '../../lib/utils/constants';
import { ErrorBoundary } from '../../components/ui/ErrorBoundary';

import type { CalendarEvent, CreateTaskData } from '@/types';
import {
  useCalendarEvents,
  useCreateCalendarEvent,
  useUpdateCalendarEvent,
  useDeleteCalendarEvent,
  useDuplicateCalendarEvent,
} from '../../hooks/useCalendarEvents';
import { useTimeblocks } from '../../hooks/useTimeblocks';
import {
  useScreenReaderAnnouncements
} from '../../hooks/useKeyboardNavigation';
import { cn } from '../../lib/utils';
import type { Timeblock } from '../../types';
import { useQueryClient } from '@tanstack/react-query';

interface WeeklyCalendarProps {
  onEventClick?: (event: CalendarEvent) => void;
  onCreateEvent?: (eventData: { start: string; end: string; title?: string }) => void;
  className?: string;
  currentDate?: Date;
}

function WeeklyCalendarCore({
  onEventClick,
  onCreateEvent,
  className,
  currentDate = new Date(),
}: WeeklyCalendarProps) {
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

  // Week calculation - memoize to prevent unnecessary refetches
  const weekStart = React.useMemo(() => startOfWeek(currentDate, { weekStartsOn: 1 }), [currentDate]);
  const weekEnd = React.useMemo(() => endOfWeek(currentDate, { weekStartsOn: 1 }), [currentDate]);

  // Memoize date strings to prevent query key changes on every render
  const weekStartStr = React.useMemo(() => format(weekStart, 'yyyy-MM-dd'), [weekStart]);
  const weekEndStr = React.useMemo(() => format(weekEnd, 'yyyy-MM-dd'), [weekEnd]);
  const weekStartISO = React.useMemo(() => weekStart.toISOString(), [weekStart]);
  const weekEndISO = React.useMemo(() => weekEnd.toISOString(), [weekEnd]);

  // Fetch unified timeblocks (tasks + external calendar events + busy blocks)
  // This is our PRIMARY data source - no need for separate task fetch
  const { items: timeblocks = [], isLoading: timeblocksLoading, error: timeblocksError } = useTimeblocks({
    fromISO: weekStartISO,
    toISO: weekEndISO,
  });

  // Fetch calendar events using custom hook (tasks only) - ONLY as fallback if timeblocks fail
  const {
    data: taskEvents = [],
    isLoading: tasksLoading,
    error: tasksError
  } = useCalendarEvents(weekStartStr, weekEndStr, {
    enabled: timeblocks.length === 0 && !timeblocksLoading, // Only fetch if timeblocks empty
  });

  // Convert timeblocks to CalendarEvent format for rendering
  const timeblockEvents: CalendarEvent[] = timeblocks.map((block: Timeblock) => {
    // DEBUG: Log all-day status
    if (block.title.includes('Halloween') || block.title.includes('Daylight')) {
      console.log(`[Timeblock] ${block.title}:`, {
        isAllDay: block.isAllDay,
        start: block.start,
        end: block.end
      });
    }

    return {
      id: block.id,
      title: block.title,
      description: block.description || undefined,
      start: block.start,
      end: block.end,
      allDay: block.isAllDay, // Map isAllDay from timeblock to allDay for CalendarEvent
      color: block.color || (block.source === 'task' ? '#3b82f6' : block.source === 'calendar' ? '#3b82f6' : '#ef4444'),
      priority: block.priority || 'medium',
      task: block.source === 'task' ? taskEvents.find(e => e.id === block.id)?.task : undefined,
      timeblock: block, // Pass through full timeblock data for metadata modal
    } as CalendarEvent & { timeblock: Timeblock };
  });

  // Combine both sources (prefer timeblocks for complete view)
  const events = timeblockEvents.length > 0 ? timeblockEvents : taskEvents;
  const isLoading = timeblocksLoading || tasksLoading;
  // Only show error if both sources fail - be more resilient
  const error = timeblocksError && tasksError ? timeblocksError : null;


  // Mutations
  const createEventMutation = useCreateCalendarEvent();
  const updateEventMutation = useUpdateCalendarEvent();
  const deleteEventMutation = useDeleteCalendarEvent();
  const duplicateEventMutation = useDuplicateCalendarEvent();

  // Accessibility hooks
  const { announce } = useScreenReaderAnnouncements();

  // Calendar configuration - match WeekGrid constants
  const START_HOUR = 6;
  const END_HOUR = 24; // Show full day including late evening events
  const SLOT_INTERVAL = 30; // minutes
  const MIN_COLUMN_WIDTH = 160; // minimum pixels from CALENDAR_CONSTANTS.GRID_DAY_WIDTH
  const GRID_MARGIN_LEFT = CALENDAR_CONSTANTS.GRID_MARGIN_LEFT; // 60px hour gutter

  // Refs for grid elements
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const gridInnerRef = useRef<HTMLDivElement | null>(null);
  const dayColumnsRef = useRef<HTMLDivElement[]>([]);
  
  // Dynamic column width based on actual rendered size
  const [columnWidth, setColumnWidth] = useState(MIN_COLUMN_WIDTH);
  
  // Calculate actual column width from rendered grid
  useEffect(() => {
    const calculateColumnWidth = () => {
      if (gridInnerRef.current) {
        const gridWidth = gridInnerRef.current.offsetWidth;
        const availableWidth = gridWidth - GRID_MARGIN_LEFT;
        const calculatedWidth = Math.max(MIN_COLUMN_WIDTH, availableWidth / 7);
        setColumnWidth(calculatedWidth);
      }
    };
    
    calculateColumnWidth();
    window.addEventListener('resize', calculateColumnWidth);
    
    // Use ResizeObserver for more accurate tracking
    const resizeObserver = new ResizeObserver(calculateColumnWidth);
    if (gridInnerRef.current) {
      resizeObserver.observe(gridInnerRef.current);
    }
    
    return () => {
      window.removeEventListener('resize', calculateColumnWidth);
      resizeObserver.disconnect();
    };
  }, [GRID_MARGIN_LEFT, MIN_COLUMN_WIDTH]);

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

    weekDays.forEach((day, dayIndex) => {
      // Format day as YYYY-MM-DD for consistent comparison
      const dayDateStr = format(day, 'yyyy-MM-dd');

      const dayEvents = events.filter(event => {
        // For all-day events, extract date from ISO string directly to avoid timezone issues
        // For regular events, use the local date
        let eventDateStr: string;

        if (event.allDay && typeof event.start === 'string') {
          // Extract YYYY-MM-DD from ISO string (e.g., "2025-10-31T00:00:00Z" -> "2025-10-31")
          eventDateStr = event.start.split('T')[0];
        } else {
          // For timed events, use local timezone interpretation
          const eventStart = new Date(event.start);
          eventDateStr = format(eventStart, 'yyyy-MM-dd');
        }

        // Simple string comparison - event is on this day if dates match
        return eventDateStr === dayDateStr;
      });

      if (dayEvents.length > 0) {
        // Separate all-day events from timed events
        const timedEvents = dayEvents.filter(e => !e.allDay);
        const allDayEvents = dayEvents.filter(e => e.allDay);

        // DEBUG: Log event categorization
        console.log(`[Day ${dayIndex}] Total: ${dayEvents.length}, Timed: ${timedEvents.length}, All-Day: ${allDayEvents.length}`);
        allDayEvents.forEach(e => console.log(`  All-Day: ${e.title}, allDay=${e.allDay}`));

        // Process timed events (go in the time grid)
        if (timedEvents.length > 0) {
          const dayLayouts = OverlapCalculator.calculateEventLayouts(timedEvents, columnWidth, START_HOUR);

          // Apply day offset to each layout's X position
          dayLayouts.forEach(layout => {
            // Adjust X position to place event in correct day column
            const adjustedLayout = {
              ...layout,
              x: layout.x + (dayIndex * columnWidth),
            };
            layouts.set(layout.id, adjustedLayout);
          });
        }

        // Process all-day events (go in the all-day row)
        if (allDayEvents.length > 0) {
          const EVENT_HEIGHT = 32; // Must match positioning.ts
          const VERTICAL_GAP = 4;

          allDayEvents.forEach((event, index) => {
            const allDayLayout: EventLayout = {
              id: event.id,
              event,
              x: GRID_MARGIN_LEFT + (dayIndex * columnWidth), // Account for time gutter
              y: (index * (EVENT_HEIGHT + VERTICAL_GAP)) + 4, // Stack with proper spacing
              width: columnWidth - 8, // Account for p-1 padding (4px each side)
              height: EVENT_HEIGHT, // Increased height for better visibility
              laneIndex: 0,
              laneCount: 1,
              zIndex: 10, // Higher z-index so they appear above time grid
            };
            console.log(`[All-Day Layout] Setting ${event.title} to y=${allDayLayout.y}px (height=${EVENT_HEIGHT}px)`);

            // Check if this ID already exists
            if (layouts.has(allDayLayout.id)) {
              console.warn(`⚠️ OVERWRITING layout for ${event.title}! Old:`, layouts.get(allDayLayout.id));
            }

            layouts.set(allDayLayout.id, allDayLayout);

            console.log(`[All-Day Layout] After set, y=${layouts.get(allDayLayout.id)?.y}px`);
          });
        }
      }
    });

    return layouts;
  }, [events, weekStart, columnWidth, GRID_MARGIN_LEFT, START_HOUR]);

  // Navigation handlers removed - now handled in CalendarPage

  // Event mutation handlers
  const handleCreateEvent = useCallback(async (eventData: any) => {
    // Handle both old CreateTaskData format and new EventTaskData format
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
    // Don't call onEventClick here - let the details modal handle it
  }, []);

  const handleEventEdit = useCallback((event: CalendarEvent) => {
    setSelectedEvent(event);
    setShowEditEventModal(true);
  }, []);

  // Selection rendering handled by SelectionLayer

  // Convert client coordinates to grid coordinates
  const clientToGridCoords = useCallback((clientX: number, clientY: number) => {
    if (!scrollerRef.current) return null;

    const scroller = scrollerRef.current;
    const rect = scroller.getBoundingClientRect();

    // Use constants from centralized config
    const ALL_DAY_ROW_HEIGHT = CALENDAR_CONSTANTS.ALL_DAY_ROW_HEIGHT; // 48px
    const TIME_COLUMN_WIDTH = CALENDAR_CONSTANTS.GRID_MARGIN_LEFT; // 60px
    const DAY_COLUMN_WIDTH = columnWidth; // Use dynamic column width
    const HOUR_HEIGHT = CALENDAR_CONSTANTS.GRID_HOUR_HEIGHT; // 120px
    const MINUTES_PER_PIXEL = 60 / HOUR_HEIGHT; // 0.5 minutes per pixel
    
    // Calculate position relative to the calendar container
    const relativeX = clientX - rect.left + scroller.scrollLeft;
    const relativeY = clientY - rect.top + scroller.scrollTop;
    
    // Calculate position within the day columns area (excluding time column)
    const dayAreaX = relativeX - TIME_COLUMN_WIDTH;
    
    // Calculate position within the time grid (excluding all-day row)
    // Note: The header is now outside the scroller, so we only need to subtract the all-day row
    const gridY = relativeY - ALL_DAY_ROW_HEIGHT;
    
    // Guard: click is outside the day columns
    if (dayAreaX < 0 || gridY < 0) return null;
    
    // Calculate which day column (0-6)
    const dayIndex = Math.floor(dayAreaX / DAY_COLUMN_WIDTH);
    if (dayIndex < 0 || dayIndex > 6) return null;
    
    // Calculate X position within the specific day column
    const xInDay = dayAreaX % DAY_COLUMN_WIDTH;
    
    // Calculate the time in minutes from START_HOUR (not from midnight)
    // gridY is pixels from top of time grid, which starts at START_HOUR
    const minutesFromStart = gridY * MINUTES_PER_PIXEL;

    // Snap to nearest 15-minute interval
    const snappedMinutes = Math.round(minutesFromStart / 15) * 15;

    // Convert back to Y pixel position (for rendering)
    // This Y is relative to START_HOUR, matching how events are positioned
    const snappedY = snappedMinutes / MINUTES_PER_PIXEL;
    
    if (debugEnabled) {
      setDebugInfo({
        clientX,
        clientY,
        x: xInDay,
        y: snappedY,
        dayIndex,
        headerHeight: ALL_DAY_ROW_HEIGHT,
        scrollTop: scroller.scrollTop,
      });
    }
    
    return { 
      x: xInDay, 
      y: snappedY, 
      dayIndex, 
      headerHeight: ALL_DAY_ROW_HEIGHT 
    };
  }, [debugEnabled, columnWidth]);

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

    // DEBUG: Log click coordinates
    console.group('🖱️ CLICK DEBUG');
    console.log('Client coords:', { x: e.clientX, y: e.clientY });
    console.log('Grid coords:', coords);
    console.log('Day index:', coords.dayIndex);
    console.log('Base date:', getBaseDateForDay(coords.dayIndex).toDateString());
    console.groupEnd();

    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    const baseDate = getBaseDateForDay(coords.dayIndex);
    const next = SelectionManager.startSelection(coords.x, coords.y, coords.dayIndex, baseDate, START_HOUR);

    // DEBUG: Log selection state
    console.group('📐 SELECTION START');
    console.log('Selection state:', next);
    console.log('Start time:', next.startTime?.toLocaleString());
    console.log('Start Y:', next.startY);
    console.groupEnd();

    setSelection(next);
    setIsSelecting(true);
    document.body.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';
  }, [getBaseDateForDay, clientToGridCoords, START_HOUR]);

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

  // Memoize AI prompt handlers to prevent re-renders
  const handleAIPromptClose = useCallback(() => {
    setShowAIPrompt(false);
    setNewEventData(null);
  }, []);

  const handleAIPromptSubmit = useCallback(async (prompt: string) => {
    if (!newEventData) return;
    // Use API service to create event with AI extraction
    const { apiService } = await import('../../services/apiService');
    const newEvent = await apiService.createEventWithAI(prompt, {
      start: newEventData.start,
      end: newEventData.end,
    });
    // Refresh calendar data
    queryClient.invalidateQueries({ queryKey: ['timeblocks'] });
  }, [newEventData, queryClient]);

  // Don't block calendar display on loading/error states

  return (
    <div className={cn('w-full h-full flex flex-col min-h-0', className)}>
      {/* Calendar grid - Full page, no header */}
      <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div 
          ref={scrollerRef}
          className="relative flex-1"
          data-calendar-container
          tabIndex={0}
          role="grid"
          aria-label={`Calendar for week of ${format(weekStart, 'MMMM d, yyyy')}`}
          aria-rowcount={48}
          aria-colcount={7}
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(156, 163, 175, 0.3) transparent',
            overflow: 'visible'
          }}
        >
          {/* Full-width background grid layer */}
          <WeekGrid 
            currentDate={currentDate}
            startHour={START_HOUR}
            endHour={END_HOUR}
            slotInterval={SLOT_INTERVAL}
            className="absolute inset-0 pointer-events-none"
            gridInnerRef={gridInnerRef}
            dayColumnsRef={dayColumnsRef}
          />
          {/* Selection overlay - captures drag-to-create on empty spaces */}
          {/* Events have higher z-index and stopPropagation to prevent this from triggering */}
          <div
            ref={selectionOverlayRef}
            className="absolute inset-0"
            style={{
              pointerEvents: 'auto',
              zIndex: 1, // Lower than events so events are clickable
            }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerCancel}
          />
          
          <div className="relative w-full h-full">
            {/* Show loading indicator if tasks are loading */}
            {isLoading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-neutral-900/50">
                <div className="flex items-center gap-3 bg-neutral-800 px-4 py-2 rounded-lg">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
                  <span className="text-white text-sm">Loading tasks...</span>
                </div>
              </div>
            )}

            {/* Show error notification if both data sources failed */}
            {error && (
              <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
                <div className="bg-error border border-error text-white px-4 py-2 rounded-lg text-sm">
                  Unable to load calendar data. Some events may not be visible.
                </div>
              </div>
            )}

            {/* Render events */}
            {!error && events.map((event) => {
              const layout = eventLayouts.get(event.id);
              if (!layout) return null;

              // Calculate which day this event is on
              const eventStart = new Date(event.start);
              const eventDateStr = event.allDay && typeof event.start === 'string'
                ? event.start.split('T')[0]
                : format(eventStart, 'yyyy-MM-dd');

              // Find matching day index (0-6)
              const dayIndex = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))
                .findIndex(day => format(day, 'yyyy-MM-dd') === eventDateStr);

              if (dayIndex === -1) return null; // Event not in this week

              return (
                <EventBlock
                  key={event.id}
                  event={event}
                  layout={layout}
                  dayIndex={dayIndex}
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

            {/* Debug marker showing exact computed position */}
            {debugEnabled && debugInfo && (
              <div className="pointer-events-none" style={{ position: 'absolute', zIndex: 50 }}>
                {/* Dot at computed position */}
                <div
                  style={{
                    position: 'absolute',
                    left: GRID_MARGIN_LEFT + (debugInfo.dayIndex * columnWidth) + debugInfo.x - 4,
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
        onClose={handleAIPromptClose}
        onSubmit={handleAIPromptSubmit}
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

// Wrap with ErrorBoundary to prevent calendar crashes from breaking the entire app
export function WeeklyCalendar(props: WeeklyCalendarProps) {
  return (
    <ErrorBoundary>
      <WeeklyCalendarCore {...props} />
    </ErrorBoundary>
  );
}
