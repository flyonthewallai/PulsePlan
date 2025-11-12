import React, { useState, useMemo } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, isSameDay, isAfter } from 'date-fns';
import { ChevronLeft, ChevronRight, Eye, EyeOff, Calendar as CalendarIcon, BookOpen, ListTodo } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { useTimeblocks } from '@/hooks/calendar';
import { useTimeblockUpdates } from '@/hooks/calendar';
import type { Timeblock } from '../../../types';

interface CalendarAccount {
  id: string;
  name: string;
  email: string;
  color: string;
  icon: 'google' | 'outlook' | 'apple' | 'default';
  isVisible: boolean;
  isDefault?: boolean;
}

interface CalendarRightSidebarProps {
  currentDate: Date;
  onDateSelect: (date: Date) => void;
  calendars?: CalendarAccount[];
  onCalendarToggle?: (calendarId: string) => void;
}

const CalendarIcon_Google = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

const CalendarIcon_Default = ({ color }: { color: string }) => (
  <div className="w-4 h-4 rounded flex items-center justify-center" style={{ backgroundColor: color }}>
    <CalendarIcon size={10} className="text-white" />
  </div>
);

export const CalendarRightSidebar: React.FC<CalendarRightSidebarProps> = ({
  currentDate,
  onDateSelect,
  calendars = [],
  onCalendarToggle,
}) => {
  const [miniCalendarDate, setMiniCalendarDate] = useState(currentDate);

  // Enable real-time timeblock updates
  useTimeblockUpdates();

  // Fetch upcoming events
  const dateRange = useMemo(() => {
    const now = new Date();
    const fromDate = new Date(now.getFullYear(), now.getMonth(), 1);
    const toDate = new Date(now.getFullYear(), now.getMonth() + 4, 0);
    
    return {
      fromISO: fromDate.toISOString(),
      toISO: toDate.toISOString()
    }
  }, [Math.floor(Date.now() / (1000 * 60 * 60 * 24 * 30))]);

  const { items: allEvents = [] } = useTimeblocks({
    fromISO: dateRange.fromISO,
    toISO: dateRange.toISO,
  });

  // Process events similar to UpcomingCalendarCard
  const upcomingEvents = useMemo(() => {
    const futureEvents: Timeblock[] = [];
    
    allEvents.forEach(event => {
      const eventDate = new Date(event.start);
      if (isAfter(eventDate, new Date())) {
        futureEvents.push(event);
      }
    });
    
    futureEvents.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
    
    return futureEvents.slice(0, 5); // Show up to 5 upcoming events
  }, [allEvents]);

  const formatEventTime = (event: Timeblock) => {
    if (event.isAllDay) {
      return 'All day';
    }
    
    const start = new Date(event.start);
    const end = new Date(event.end);
    
    const startTime = format(start, 'h:mm a');
    const endTime = format(end, 'h:mm a');
    
    return `${startTime} - ${endTime}`;
  };

  const formatEventDate = (event: Timeblock) => {
    const dateStr = event.start.split('T')[0];
    const eventDate = new Date(dateStr + 'T00:00:00');
    
    if (isToday(eventDate)) {
      return 'Today';
    } else {
      return format(eventDate, 'MMM d');
    }
  };

  // Generate days for mini calendar
  const monthStart = startOfMonth(miniCalendarDate);
  const monthEnd = endOfMonth(miniCalendarDate);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

  // Get starting day of week (0 = Sunday)
  const startingDayOfWeek = monthStart.getDay();

  // Fill in empty cells at start
  const emptyCells = Array.from({ length: startingDayOfWeek }, (_, i) => i);

  const handlePrevMonth = () => {
    const newDate = new Date(miniCalendarDate);
    newDate.setMonth(newDate.getMonth() - 1);
    setMiniCalendarDate(newDate);
  };

  const handleNextMonth = () => {
    const newDate = new Date(miniCalendarDate);
    newDate.setMonth(newDate.getMonth() + 1);
    setMiniCalendarDate(newDate);
  };

  const handleDayClick = (day: Date) => {
    onDateSelect(day);
  };

  return (
    <div className="w-[370px] h-full border-l border-white/10 flex flex-col overflow-y-auto" style={{ backgroundColor: '#111111' }}>
      {/* Mini Calendar - Moved to top */}
      <div className="p-6 border-b border-gray-800/50">
        {/* Month Navigation */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-white">
            {format(miniCalendarDate, 'MMMM yyyy')}
          </h3>
          <div className="flex items-center gap-1">
            <button
              onClick={handlePrevMonth}
              className="p-1 hover:bg-white/5 rounded transition-colors"
              aria-label="Previous month"
            >
              <ChevronLeft size={16} className="text-gray-400" />
            </button>
            <button
              onClick={handleNextMonth}
              className="p-1 hover:bg-white/5 rounded transition-colors"
              aria-label="Next month"
            >
              <ChevronRight size={16} className="text-gray-400" />
            </button>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1">
          {/* Weekday headers */}
          {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map((day) => (
            <div
              key={day}
              className="text-xs font-medium text-gray-500 text-center py-1"
            >
              {day}
            </div>
          ))}

          {/* Empty cells for alignment */}
          {emptyCells.map((i) => (
            <div key={`empty-${i}`} className="aspect-square" />
          ))}

          {/* Days */}
          {days.map((day) => {
            const isCurrentMonth = isSameMonth(day, miniCalendarDate);
            const isCurrentDay = isToday(day);
            const isSelected = isSameDay(day, currentDate);

            return (
              <button
                key={day.toISOString()}
                onClick={() => handleDayClick(day)}
                className={cn(
                  'aspect-square flex items-center justify-center rounded-lg text-sm transition-all',
                  'hover:bg-white/5',
                  !isCurrentMonth && 'text-gray-600',
                  isCurrentMonth && !isCurrentDay && !isSelected && 'text-gray-300',
                  isCurrentDay && !isSelected && 'bg-blue-500/20 text-blue-400 font-medium',
                  isSelected && 'bg-white text-black font-medium'
                )}
              >
                {format(day, 'd')}
              </button>
            );
          })}
        </div>
      </div>

      {/* Scheduling Section */}
      <div className="p-6 border-b border-gray-800/50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-white">Calendars</h3>
          <button className="p-1 hover:bg-white/5 rounded transition-colors">
            <Eye size={14} className="text-gray-400" />
          </button>
        </div>

        {/* Calendar List */}
        <div className="space-y-2">
          {calendars.length === 0 ? (
            <div className="text-sm text-gray-500">No calendars connected</div>
          ) : (
            calendars.map((calendar) => (
              <div
                key={calendar.id}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
                onClick={() => onCalendarToggle?.(calendar.id)}
              >
                {/* Calendar Icon */}
                <div className="shrink-0">
                  {calendar.icon === 'google' ? (
                    <CalendarIcon_Google />
                  ) : (
                    <CalendarIcon_Default color={calendar.color} />
                  )}
                </div>

                {/* Calendar Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-white truncate">
                      {calendar.name}
                    </span>
                    {calendar.isDefault && (
                      <span className="text-xs text-gray-500 shrink-0">
                        Default
                      </span>
                    )}
                  </div>
                  {calendar.email && (
                    <div className="text-xs text-gray-500 truncate">
                      {calendar.email}
                    </div>
                  )}
                </div>

                {/* Visibility Toggle */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onCalendarToggle?.(calendar.id);
                  }}
                  className="shrink-0 p-1 hover:bg-white/10 rounded transition-colors"
                >
                  {calendar.isVisible ? (
                    <Eye size={14} className="text-gray-400" />
                  ) : (
                    <EyeOff size={14} className="text-gray-600" />
                  )}
                </button>
              </div>
            ))
          )}
        </div>

        {/* Add Calendar Button */}
        <button className="w-full mt-4 text-sm text-gray-400 hover:text-white text-left px-2 py-1 rounded hover:bg-white/5 transition-colors">
          + Add calendar account
        </button>
      </div>

      {/* Upcoming Events Section */}
      {upcomingEvents.length > 0 && (
        <div className="p-6 border-b border-gray-800/50">
          <div>
            <div className="text-sm font-medium text-white mb-3">Upcoming</div>
            <div className="space-y-2">
              {upcomingEvents.map((event) => (
                <div key={event.id} className="relative">
                  <div className="flex items-center py-2">
                    {/* Vertical blue line for timed events */}
                    {!event.isAllDay && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-full"></div>
                    )}
                    
                    {/* Blue dot for all-day events */}
                    {event.isAllDay && (
                      <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full"></div>
                    )}
                    
                    <div className="flex-1 ml-6">
                      <div className="text-sm text-white font-medium">{event.title}</div>
                      <div className="text-xs text-gray-400">
                        {formatEventDate(event)} • {formatEventTime(event)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Assignments & Todos Section */}
      <div className="p-6">
        <h3 className="text-sm font-medium text-white mb-4">Assignments & Todos</h3>
        
        <div className="space-y-2">
          <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
            <div className="w-4 h-4 rounded flex items-center justify-center" style={{ backgroundColor: '#4285F4' }}>
              <BookOpen size={10} className="text-white" />
            </div>
            <span className="text-sm text-white">Assignments</span>
          </div>
          
          <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
            <div className="w-4 h-4 rounded flex items-center justify-center" style={{ backgroundColor: '#8b5cf6' }}>
              <ListTodo size={10} className="text-white" />
            </div>
            <span className="text-sm text-white">Todos</span>
          </div>
        </div>
      </div>
    </div>
  );
};

