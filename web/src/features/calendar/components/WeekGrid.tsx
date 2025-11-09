import React, { useMemo, useRef } from 'react';
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
  const minDayWidth = CALENDAR_CONSTANTS.GRID_DAY_WIDTH;


  return (
    <div
      ref={actualGridRef}
      className={cn('relative w-full', className)}
      style={{
        height: totalHeight + 48, // Extra space for all-day row (header moved to parent)
        minHeight: totalHeight + 48,
        minWidth: `${CALENDAR_CONSTANTS.GRID_MARGIN_LEFT + 7 * minDayWidth}px`,
        backgroundColor: '#111111'
      }}
    >
      {/* All-day row - sits directly below day header divider */}
      <div className="flex">
        {/* All-day label column */}
        <div className="flex items-center justify-end pr-3 text-xs font-medium" style={{ width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT, backgroundColor: '#111111', color: 'rgba(229, 229, 229, 0.7)' }}>
          all-day
        </div>
        {/* All-day event columns */}
        <div className="flex-1 h-12">
          <div className="grid h-full" style={{ gridTemplateColumns: 'repeat(7, 1fr)' }}>
            {weekDays.map((day, index) => {
              const isToday = format(day, 'yyyy-MM-dd') === todayDateString;
              return (
                <div
                  key={day.toISOString()}
                  className={cn(
                    'border-b p-1',
                    isToday ? 'bg-white/[0.02]' : ''
                  )}
                  style={{
                    backgroundColor: isToday ? undefined : '#111111',
                    borderRight: index < 6 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    borderBottomColor: 'rgba(255, 255, 255, 0.05)'
                  }}
                >
                  {/* All-day events would go here */}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main grid content - Notion Style */}
      <div className="relative flex" style={{ backgroundColor: '#111111' }}>
        {/* Hour labels column - right-aligned */}
        <div className="relative" style={{ width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT, height: totalHeight, backgroundColor: '#111111' }}>
          {timeSlots.filter((slot) => slot.getMinutes() === 0).map((slot, hourIndex) => {
            return (
              <div
                key={hourIndex}
                className="absolute text-xs font-medium flex items-start justify-end pr-3"
                style={{ 
                  top: hourIndex * hourHeight - 6,
                  width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT,
                  color: 'rgba(229, 229, 229, 0.7)'
                }}
              >
                {format(slot, 'ha')}
              </div>
            );
          })}
        </div>

        {/* Day columns with subtle grid lines */}
        <div className="flex-1 relative">
          <div className="grid h-full" style={{ gridTemplateColumns: 'repeat(7, 1fr)' }}>
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
                    'relative transition-colors overflow-hidden',
                    isToday && 'bg-white/[0.02]'
                  )}
                  style={{ 
                    borderRight: dayIndex < 6 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    backgroundColor: isToday ? undefined : '#111111'
                  }}
                >
                  {timeSlots.map((slot, slotIndex) => {
                    const isHourStart = slot.getMinutes() === 0;
                    
                    return (
                      <div
                        key={slotIndex}
                        className="border-b hover:brightness-110 transition-all"
                        style={{ 
                          height: slotHeight,
                          borderColor: isHourStart ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.05)'
                        }}
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
            gridRef={actualGridRef}
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
  gridRef: React.RefObject<HTMLDivElement | null>;
}> = ({ currentDate, startHour, weekDays, gridRef }) => {
  const [dayWidth, setDayWidth] = React.useState<number>(CALENDAR_CONSTANTS.GRID_DAY_WIDTH);
  
  React.useEffect(() => {
    const calculateDayWidth = () => {
      if (gridRef.current) {
        const gridWidth = gridRef.current.offsetWidth;
        const availableWidth = gridWidth - CALENDAR_CONSTANTS.GRID_MARGIN_LEFT;
        const calculatedWidth = availableWidth / 7;
        setDayWidth(calculatedWidth);
      }
    };
    
    calculateDayWidth();
    window.addEventListener('resize', calculateDayWidth);
    return () => window.removeEventListener('resize', calculateDayWidth);
  }, [gridRef]);

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