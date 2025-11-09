import React from 'react';
import { format, addDays, startOfWeek } from 'date-fns';
import { cn } from '../../../lib/utils';
import { CALENDAR_CONSTANTS } from '../../../lib/utils/constants';

export interface CalendarDayHeaderProps {
  currentDate: Date;
  className?: string;
  viewMode?: 'day' | 'week';
}

export const CalendarDayHeader: React.FC<CalendarDayHeaderProps> = ({
  currentDate,
  className,
  viewMode = 'week',
}) => {
  // Calculate days to display based on view mode
  const displayDays = React.useMemo(() => {
    if (viewMode === 'day') {
      return [currentDate];
    } else {
      const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
      return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
    }
  }, [currentDate, viewMode]);

  // Get today for highlighting
  const today = new Date();
  const todayDateString = format(today, 'yyyy-MM-dd');

  return (
    <div
      className={cn(
        'relative',
        className
      )}
      style={{ backgroundColor: '#111111' }}
    >
      {/* Container with divider line */}
      <div className="flex relative">
        {/* Time column gutter - empty space */}
        <div
          className="flex items-end justify-center pb-2"
          style={{ width: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT }}
        />

        {/* Day headers positioned on divider line */}
        <div className="flex-1 flex relative">
          {displayDays.map((day, index) => {
            const isToday = format(day, 'yyyy-MM-dd') === todayDateString;
            const isLastDay = index === displayDays.length - 1;

            return (
              <div
                key={day.toISOString()}
                className="flex-1 flex items-end justify-center pb-2 relative"
                style={{
                  borderRight: !isLastDay ? '1px solid rgba(255, 255, 255, 0.05)' : 'none'
                }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="text-xs font-medium tracking-wide text-[#E5E5E5]/50"
                  >
                    {format(day, 'EEE').charAt(0) + format(day, 'EEE').slice(1).toLowerCase()}
                  </span>
                  <span
                    className={cn(
                      'text-sm font-semibold transition-all duration-200',
                      isToday 
                        ? 'bg-[#3B82F6] text-white px-2 py-0.5 rounded-md' 
                        : 'text-[#E5E5E5]'
                    )}
                  >
                    {format(day, 'd')}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Divider line that sits below day labels */}
      <div 
        className="w-full h-px" 
        style={{ 
          background: 'rgba(255, 255, 255, 0.05)',
          marginLeft: CALENDAR_CONSTANTS.GRID_MARGIN_LEFT
        }}
      />
    </div>
  );
};

