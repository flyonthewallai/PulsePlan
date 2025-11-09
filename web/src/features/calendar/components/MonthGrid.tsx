import React, { useMemo } from 'react';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, addDays, isSameMonth, isSameDay } from 'date-fns';
import { cn } from '../../../lib/utils';

interface MonthGridProps {
  currentDate: Date;
  className?: string;
  children?: React.ReactNode;
  onDayClick?: (date: Date) => void;
}

export const MonthGrid: React.FC<MonthGridProps> = ({
  currentDate,
  className,
  children,
  onDayClick,
}) => {
  // Calculate month grid (6 weeks x 7 days)
  const monthStart = useMemo(() => startOfMonth(currentDate), [currentDate]);
  const monthEnd = useMemo(() => endOfMonth(currentDate), [currentDate]);
  const gridStart = useMemo(() => startOfWeek(monthStart, { weekStartsOn: 1 }), [monthStart]);
  const gridEnd = useMemo(() => endOfWeek(monthEnd, { weekStartsOn: 1 }), [monthEnd]);

  // Generate all days in grid (typically 35 or 42 days)
  const daysInGrid = useMemo(() => {
    const days = [];
    let day = gridStart;
    while (day <= gridEnd) {
      days.push(day);
      day = addDays(day, 1);
    }
    return days;
  }, [gridStart, gridEnd]);

  // Get today for highlighting
  const today = new Date();

  // Week days header
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

      {/* Days grid - fill remaining height */}
      <div className="flex-1 grid grid-cols-7 gap-0">
        {daysInGrid.map((day, index) => {
          const isToday = isSameDay(day, today);
          const isCurrentMonth = isSameMonth(day, currentDate);
          const dayOfWeek = day.getDay();
          const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

          return (
            <div
              key={day.toISOString()}
              onClick={() => onDayClick?.(day)}
              className={cn(
                'relative border-b border-r cursor-pointer hover:bg-white/[0.03] transition-colors',
                !isCurrentMonth && 'opacity-40',
                isToday && 'bg-white/[0.02]'
              )}
              style={{
                borderColor: 'rgba(255, 255, 255, 0.05)',
                borderRight: (index + 1) % 7 === 0 ? 'none' : '1px solid rgba(255, 255, 255, 0.05)',
                borderBottom: index >= daysInGrid.length - 7 ? 'none' : '1px solid rgba(255, 255, 255, 0.05)',
                minHeight: '100px',
              }}
              data-date={format(day, 'yyyy-MM-dd')}
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

              {/* Events container - positioned absolutely to allow overflow */}
              <div className="absolute top-10 left-1 right-1 bottom-1 overflow-hidden">
                {/* Events will be rendered here by parent component */}
              </div>
            </div>
          );
        })}
      </div>

      {/* Overlay for events */}
      <div className="absolute inset-0 pointer-events-none" style={{ top: '42px' }}>
        {children}
      </div>
    </div>
  );
};

MonthGrid.displayName = 'MonthGrid';




