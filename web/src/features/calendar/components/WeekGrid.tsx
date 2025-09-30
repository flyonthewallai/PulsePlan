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
      className={cn('relative bg-neutral-900 rounded-lg border border-neutral-700', className)}
      style={{
        height: totalHeight + 60, // Extra space for header
      }}
    >
      {/* Header with day labels */}
      <div ref={headerRef} className="sticky top-0 z-20 bg-neutral-800 border-b border-neutral-700 rounded-t-lg">
        <div className="grid grid-cols-8 h-16">
          {/* Time column header */}
          <div ref={gutterRef} className="flex items-center justify-center text-neutral-400 text-sm font-medium border-r border-neutral-700">
            Time
          </div>
          
          {/* Day headers */}
          {weekDays.map((day) => {
            const isToday = format(day, 'yyyy-MM-dd') === todayDateString;
            
            return (
              <div
                key={day.toISOString()}
                className={cn(
                  'flex flex-col items-center justify-center border-r border-neutral-700 last:border-r-0',
                  'transition-colors duration-200',
                  isToday 
                    ? 'bg-neutral-600/20 text-white' 
                    : 'text-neutral-300 hover:text-white hover:bg-neutral-700/30'
                )}
              >
                <div className={cn(
                  'text-xs font-medium uppercase tracking-wide mb-1',
                  isToday ? 'text-blue-400' : 'text-neutral-400'
                )}>
                  {format(day, 'EEE')}
                </div>
                <div className={cn(
                  'text-lg font-semibold',
                  isToday 
                    ? 'text-white bg-blue-500 w-7 h-7 rounded-full flex items-center justify-center' 
                    : ''
                )}>
                  {format(day, 'd')}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main grid content */}
      <div className="relative">
        {/* Time slots grid */}
        <div className="grid grid-cols-8">
          {/* Hour labels column */}
          <div className="relative border-r border-neutral-700">
            {timeSlots.map((slot, index) => {
              const isHourStart = slot.getMinutes() === 0;
              
              return (
                <div
                  key={index}
                  className={cn(
                    'relative border-b border-neutral-800/50 text-neutral-400 text-xs',
                    'flex items-start justify-end pr-3 pt-1'
                  )}
                  style={{ height: slotHeight }}
                >
                  {isHourStart && (
                    <span className="font-medium">
                      {format(slot, 'ha')}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Day columns */}
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
                  'relative border-r border-neutral-700 last:border-r-0',
                  isToday && 'bg-neutral-800/30'
                )}
              >
                {timeSlots.map((slot, slotIndex) => {
                  const isHourStart = slot.getMinutes() === 0;
                  
                  return (
                    <div
                      key={slotIndex}
                      className={cn(
                        'border-b',
                        isHourStart 
                          ? 'border-neutral-700/60' 
                          : 'border-neutral-800/30'
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
  const leftOffset = 60 + (todayIndex * dayWidth); // 60px for hour labels

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