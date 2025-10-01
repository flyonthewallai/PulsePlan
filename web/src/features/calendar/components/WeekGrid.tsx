import React, { useMemo, useState, useRef, useEffect } from 'react';
import { format, addDays, startOfWeek } from 'date-fns';
import { cn } from '../../../lib/utils';
import { GridMath } from '../calendar-logic/gridMath';
import { CALENDAR_CONSTANTS } from '../../../lib/utils/constants';

interface WeekGridProps {
  currentDate: Date;
  startHour?: number;
  endHour?: number;
  slotInterval?: number;
  className?: string;
  children?: React.ReactNode;
  gridInnerRef?: React.RefObject<HTMLDivElement | null>;
  headerRef?: React.RefObject<HTMLDivElement | null>;
  gutterRef?: React.RefObject<HTMLDivElement | null>;
  dayColumnsRef?: React.MutableRefObject<HTMLDivElement[]>;
}

export const WeekGrid: React.FC<WeekGridProps> = ({
  currentDate,
  startHour = 6,
  endHour = 22,
  slotInterval = 30,
  className,
  children,
  gridInnerRef,
  headerRef,
  gutterRef,
  dayColumnsRef,
}) => {
  // Calculate week days (Monday to Sunday)
  const weekDays = useMemo(() => {
    const start = startOfWeek(currentDate, { weekStartsOn: 1 });
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }, [currentDate]);

  // Generate time slots
  const timeSlots = useMemo(() => {
    const slots = [];
    for (let hour = startHour; hour < endHour; hour++) {
      for (let minutes = 0; minutes < 60; minutes += slotInterval) {
        const time = new Date();
        time.setHours(hour, minutes, 0, 0);
        slots.push(time);
      }
    }
    return slots;
  }, [startHour, endHour, slotInterval]);

  // Get today for highlighting
  const today = new Date();
  const todayDateString = format(today, 'yyyy-MM-dd');

  const internalGridRef = useRef<HTMLDivElement>(null);
  const actualGridRef = gridInnerRef || internalGridRef;

  // Grid dimensions
  const hourHeight = CALENDAR_CONSTANTS.GRID_HOUR_HEIGHT;
  const slotHeight = hourHeight / (60 / slotInterval);
  const totalHeight = (endHour - startHour) * hourHeight;
  const dayWidth = CALENDAR_CONSTANTS.GRID_DAY_WIDTH;


  return (
    <div
      ref={actualGridRef}
      className={cn('relative bg-neutral-900', className)}
      style={{
        height: totalHeight + 60 + 48, // Extra space for header + all-day row
      }}
    >
      {/* Header with day labels - Dates next to weekdays */}
      <div ref={headerRef} className="sticky top-0 z-20 bg-neutral-900 flex">
        {/* Time column header - empty space */}
        <div ref={gutterRef} className="flex items-center justify-center text-gray-500 text-xs font-medium" style={{ width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT }}>
          
        </div>
        
        {/* Day headers with dates inline */}
        <div className="flex-1 border-l border-r border-b border-white/5">
          <div className="grid h-14" style={{ gridTemplateColumns: `repeat(7, ${dayWidth}px)` }}>
            {weekDays.map((day) => {
              const isToday = format(day, 'yyyy-MM-dd') === todayDateString;
              
              return (
                <div
                  key={day.toISOString()}
                  className={cn(
                    'flex items-center justify-center border-r border-white/5 last:border-r-0',
                    'transition-colors duration-200'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      'text-xs font-semibold uppercase tracking-wider',
                      isToday ? 'text-blue-400' : 'text-gray-500'
                    )}>
                      {format(day, 'EEE')}
                    </div>
                    <div className={cn(
                      'text-sm font-semibold',
                      isToday 
                        ? 'text-white bg-blue-500 w-6 h-6 rounded-full flex items-center justify-center' 
                        : 'text-white'
                    )}>
                      {format(day, 'd')}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* All-day row */}
      <div className="flex">
        {/* All-day label column */}
        <div className="flex items-center justify-end pr-3 text-gray-500 text-xs font-medium" style={{ width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT }}>
          all-day
        </div>
        {/* All-day event columns */}
        <div className="flex-1 border-l border-r border-b border-white/5 h-12 bg-neutral-900/50">
          <div className="grid h-full" style={{ gridTemplateColumns: `repeat(7, ${dayWidth}px)` }}>
            {weekDays.map((day) => (
              <div
                key={day.toISOString()}
                className="border-r border-white/5 last:border-r-0 p-1"
              >
                {/* All-day events would go here */}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main grid content - Clean & Minimal */}
      <div className="relative flex">
        {/* Hour labels column - aligned with grid lines */}
        <div className="relative" style={{ width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT, height: totalHeight }}>
          {timeSlots.filter((slot) => slot.getMinutes() === 0).map((slot, hourIndex) => {
            return (
              <div
                key={hourIndex}
                className="absolute text-gray-500 text-xs font-medium flex items-start justify-end pr-3"
                style={{ 
                  top: hourIndex * hourHeight - 6, // Position text slightly above the line
                  width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT
                }}
              >
                {format(slot, 'ha')}
              </div>
            );
          })}
        </div>

        {/* Day columns with grid lines */}
        <div className="flex-1 relative border-l border-r border-white/5">
          <div className="grid h-full" style={{ gridTemplateColumns: `repeat(7, ${dayWidth}px)` }}>
            {weekDays.map((day, dayIndex) => {
              const isToday = format(day, 'yyyy-MM-dd') === todayDateString;
              
              return (
                <div
                  key={day.toISOString()}
                  ref={(el) => {
                    if (el && dayColumnsRef) {
                      dayColumnsRef.current[dayIndex] = el;
                    }
                  }}
                  className={cn(
                    'relative border-r border-white/5 last:border-r-0 transition-colors',
                    isToday && 'bg-white/[0.02]'
                  )}
                >
                  {timeSlots.map((slot, slotIndex) => {
                    const isHourStart = slot.getMinutes() === 0;
                    
                    return (
                      <div
                        key={slotIndex}
                        className={cn(
                          'border-b hover:bg-white/[0.02] transition-colors',
                          isHourStart 
                            ? 'border-white/10' 
                            : 'border-white/5'
                        )}
                        style={{ height: slotHeight }}
                        data-day-index={dayIndex}
                        data-slot-index={slotIndex}
                        data-time={format(slot, 'HH:mm')}
                      />
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>

        {/* Current time indicator */}
        {weekDays.some(day => format(day, 'yyyy-MM-dd') === todayDateString) && (
          <CurrentTimeIndicator
            currentDate={today}
            startHour={startHour}
            weekDays={weekDays}
            dayWidth={dayWidth}
          />
        )}

        {/* Content overlay - events, selections, etc. */}
        <div className="absolute inset-0 pointer-events-none">
          {children}
        </div>
      </div>
    </div>
  );
};

// Current time indicator component
const CurrentTimeIndicator: React.FC<{
  currentDate: Date;
  startHour: number;
  weekDays: Date[];
  dayWidth: number;
}> = ({ currentDate, startHour, weekDays, dayWidth }) => {
  const todayIndex = weekDays.findIndex(
    day => format(day, 'yyyy-MM-dd') === format(currentDate, 'yyyy-MM-dd')
  );

  if (todayIndex === -1) return null;

  const currentY = GridMath.timeToY(currentDate, startHour);
  const leftOffset = CALENDAR_CONSTANTS.GRID_MARGIN_LEFT + (todayIndex * dayWidth);

  return (
    <>
      {/* Time indicator dot */}
      <div
        className="absolute w-3 h-3 bg-red-500 rounded-full z-30 -translate-y-1/2"
        style={{
          top: currentY,
          left: leftOffset - 6,
        }}
      />
      
      {/* Time indicator line */}
      <div
        className="absolute h-0.5 bg-red-500 z-20"
        style={{
          top: currentY,
          left: leftOffset,
          width: dayWidth,
        }}
      />
    </>
  );
};

WeekGrid.displayName = 'WeekGrid';