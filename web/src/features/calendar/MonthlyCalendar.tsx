import React, { useState, useCallback, useMemo } from 'react';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, addDays, isSameMonth, isSameDay } from 'date-fns';
import { CreateEventTaskModal } from './components/CreateEventTaskModal';
import { EditEventModal } from './components/EditEventModal';
import { EventDetailsModal } from './components/EventDetailsModal';
import { cn } from '@/lib/utils';

import type { CalendarEvent } from '@/types';
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
import type { Timeblock } from '@/types';

interface MonthlyCalendarProps {
  onEventClick?: (event: CalendarEvent) => void;
  onCreateEvent?: (eventData: { start: string; end: string; title?: string }) => void;
  onDayClick?: (date: Date) => void;
  className?: string;
  currentDate?: Date;
}

export function MonthlyCalendar({
  onEventClick,
  onCreateEvent,
  onDayClick,
  className,
  currentDate = new Date(),
}: MonthlyCalendarProps) {
  // State management
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [showNewEventModal, setShowNewEventModal] = useState(false);
  const [showEditEventModal, setShowEditEventModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [newEventData, setNewEventData] = useState<{ start: string; end: string; title?: string } | null>(null);

  // Month calculation
  const monthStart = useMemo(() => startOfMonth(currentDate), [currentDate]);
  const monthEnd = useMemo(() => endOfMonth(currentDate), [currentDate]);
  
  const monthStartStr = useMemo(() => format(monthStart, 'yyyy-MM-dd'), [monthStart]);
  const monthEndStr = useMemo(() => format(monthEnd, 'yyyy-MM-dd'), [monthEnd]);
  const monthStartISO = useMemo(() => monthStart.toISOString(), [monthStart]);
  const monthEndISO = useMemo(() => monthEnd.toISOString(), [monthEnd]);

  // Fetch unified timeblocks
  const { items: timeblocks = [], isLoading: timeblocksLoading, error: timeblocksError } = useTimeblocks({
    fromISO: monthStartISO,
    toISO: monthEndISO,
  });

  // Fetch calendar events (fallback)
  const {
    data: taskEvents = [],
    isLoading: tasksLoading,
    error: tasksError
  } = useCalendarEvents(monthStartStr, monthEndStr, {
    enabled: timeblocks.length === 0 && !timeblocksLoading,
  });

  // Convert timeblocks to CalendarEvent format
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

  // Combine both sources
  const events = timeblockEvents.length > 0 ? timeblockEvents : taskEvents;
  const isLoading = timeblocksLoading || tasksLoading;
  const error = timeblocksError && tasksError ? timeblocksError : null;

  // Mutations
  const createEventMutation = useCreateCalendarEvent();
  const updateEventMutation = useUpdateCalendarEvent();
  const deleteEventMutation = useDeleteCalendarEvent();
  const duplicateEventMutation = useDuplicateCalendarEvent();

  // Accessibility
  const { announce } = useScreenReaderAnnouncements();

  // Group events by day
  const eventsByDay = useMemo(() => {
    const grouped = new Map<string, CalendarEvent[]>();
    
    events.forEach(event => {
      let eventDateStr: string;
      
      if (event.allDay && typeof event.start === 'string') {
        eventDateStr = event.start.split('T')[0];
      } else {
        const eventStart = new Date(event.start);
        eventDateStr = format(eventStart, 'yyyy-MM-dd');
      }
      
      const existing = grouped.get(eventDateStr) || [];
      grouped.set(eventDateStr, [...existing, event]);
    });
    
    return grouped;
  }, [events]);

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

  const handleDayClick = useCallback((date: Date) => {
    if (onDayClick) {
      onDayClick(date);
    } else {
      // Create new event on this day
      const startTime = new Date(date);
      startTime.setHours(9, 0, 0, 0);
      const endTime = new Date(date);
      endTime.setHours(10, 0, 0, 0);
      
      setNewEventData({
        start: startTime.toISOString(),
        end: endTime.toISOString(),
        title: 'New Event',
      });
      setShowNewEventModal(true);
    }
  }, [onDayClick]);

  return (
    <div className={cn('w-full h-full flex flex-col min-h-0 relative', className)}>
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

      <MonthGridWithEvents
        currentDate={currentDate}
        onDayClick={handleDayClick}
        eventsByDay={eventsByDay}
        onEventClick={handleEventSelect}
        className="flex-1"
      />

      {/* Modals */}
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

// Integrated MonthGrid with inline event rendering
interface MonthGridWithEventsProps {
  currentDate: Date;
  eventsByDay: Map<string, CalendarEvent[]>;
  onDayClick: (date: Date) => void;
  onEventClick: (event: CalendarEvent) => void;
  className?: string;
}

const MonthGridWithEvents: React.FC<MonthGridWithEventsProps> = ({
  currentDate,
  eventsByDay,
  onDayClick,
  onEventClick,
  className,
}) => {
  // Calculate month grid
  const monthStart = useMemo(() => startOfMonth(currentDate), [currentDate]);
  const monthEnd = useMemo(() => endOfMonth(currentDate), [currentDate]);
  const gridStart = useMemo(() => startOfWeek(monthStart, { weekStartsOn: 1 }), [monthStart]);
  const gridEnd = useMemo(() => endOfWeek(monthEnd, { weekStartsOn: 1 }), [monthEnd]);

  // Generate all days in grid
  const daysInGrid = useMemo(() => {
    const days = [];
    let day = gridStart;
    while (day <= gridEnd) {
      days.push(day);
      day = addDays(day, 1);
    }
    return days;
  }, [gridStart, gridEnd]);

  const today = new Date();
  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div
      className={cn('relative w-full h-full flex flex-col', className)}
      style={{ backgroundColor: '#111111' }}
    >
      {/* Week day headers */}
      <div className="grid grid-cols-7 border-b" style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}>
        {weekDays.map((day, index) => (
          <div
            key={index}
            className="flex items-center justify-center py-2 text-xs font-medium uppercase tracking-wide"
            style={{
              color: 'rgba(229, 229, 229, 0.5)',
              borderRight: index < 6 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none'
            }}
          >
            {day}
          </div>
        ))}
      </div>

      {/* Days grid */}
      <div className="flex-1 grid grid-cols-7 gap-0">
        {daysInGrid.map((day, index) => {
          const isToday = isSameDay(day, today);
          const isCurrentMonth = isSameMonth(day, currentDate);
          const dateStr = format(day, 'yyyy-MM-dd');
          const dayEvents = eventsByDay.get(dateStr) || [];
          const visibleEvents = dayEvents.slice(0, 3);
          const remainingCount = dayEvents.length - 3;

          return (
            <div
              key={day.toISOString()}
              onClick={() => onDayClick(day)}
              className={cn(
                'relative border-b border-r cursor-pointer hover:bg-white/[0.03] transition-colors flex flex-col',
                !isCurrentMonth && 'opacity-40',
                isToday && 'bg-white/[0.02]'
              )}
              style={{
                borderColor: 'rgba(255, 255, 255, 0.05)',
                borderRight: (index + 1) % 7 === 0 ? 'none' : '1px solid rgba(255, 255, 255, 0.05)',
                borderBottom: index >= daysInGrid.length - 7 ? 'none' : '1px solid rgba(255, 255, 255, 0.05)',
                minHeight: '100px',
              }}
            >
              {/* Day number */}
              <div className="p-2">
                <div
                  className={cn(
                    'inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-medium transition-all',
                    isToday
                      ? 'bg-[#3B82F6] text-white'
                      : isCurrentMonth
                      ? 'text-[#E5E5E5]'
                      : 'text-[#E5E5E5]/40'
                  )}
                >
                  {format(day, 'd')}
                </div>
              </div>

              {/* Events list */}
              <div className="flex flex-col gap-0.5 px-1 pb-1">
                {visibleEvents.map((event) => (
                  <button
                    key={event.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      onEventClick(event);
                    }}
                    className="text-left text-xs px-1.5 py-0.5 rounded truncate transition-colors hover:brightness-110"
                    style={{
                      backgroundColor: event.color || '#3b82f6',
                      color: 'white',
                      fontSize: '10px',
                    }}
                    title={event.title}
                  >
                    {event.title}
                  </button>
                ))}
                {remainingCount > 0 && (
                  <div className="text-xs px-1.5 text-gray-400" style={{ fontSize: '10px' }}>
                    +{remainingCount} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

