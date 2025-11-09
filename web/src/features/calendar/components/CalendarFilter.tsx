import React, { useState, useEffect } from 'react';
import { cn } from '../../../lib/utils';
import { useOAuthConnections } from '../../../hooks/useOAuthConnections';

interface CalendarFilterProps {
  onFilterChange?: (selectedCalendars: string[]) => void;
  className?: string;
}

export const CalendarFilter: React.FC<CalendarFilterProps> = ({
  onFilterChange,
  className,
}) => {
  const { isConnected } = useOAuthConnections();
  const [selectedCalendars, setSelectedCalendars] = useState<string[]>([]);

  // Define calendar providers in order
  const calendars = [
    {
      id: 'google-calendar',
      name: 'Google Calendar',
      icon: '/googlecalendar.png',
      provider: 'google' as const,
      service: 'calendar' as const,
    },
    {
      id: 'outlook-calendar',
      name: 'Outlook Calendar',
      icon: '/assets/integrations/OutlookCalendar.svg',
      provider: 'microsoft' as const,
      service: 'calendar' as const,
    },
    {
      id: 'apple-calendar',
      name: 'Apple Calendar',
      icon: '/assets/integrations/AppleCalendar.svg',
      provider: null,
      service: null,
      comingSoon: true,
    },
  ];

  // Filter to only show connected calendars
  const connectedCalendars = calendars.filter(cal => {
    if (cal.comingSoon || !cal.provider || !cal.service) return false;
    return isConnected(cal.provider, cal.service);
  });

  // Initialize all connected calendars as selected
  useEffect(() => {
    const allConnectedIds = connectedCalendars.map(cal => cal.id);
    setSelectedCalendars(allConnectedIds);
    onFilterChange?.(allConnectedIds);
  }, [connectedCalendars.length]);

  const toggleCalendar = (calendarId: string) => {
    setSelectedCalendars(prev => {
      const newSelection = prev.includes(calendarId)
        ? prev.filter(id => id !== calendarId)
        : [...prev, calendarId];

      onFilterChange?.(newSelection);
      return newSelection;
    });
  };

  // Don't render if no calendars are connected
  if (connectedCalendars.length === 0) {
    return null;
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {connectedCalendars.map(calendar => {
        const isSelected = selectedCalendars.includes(calendar.id);

        return (
          <button
            key={calendar.id}
            onClick={() => toggleCalendar(calendar.id)}
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden transition-all',
              'border-2',
              isSelected
                ? 'bg-white border-white opacity-100'
                : 'bg-neutral-700 border-neutral-600 opacity-40 hover:opacity-60'
            )}
            title={calendar.name}
          >
            <img
              src={calendar.icon}
              alt={calendar.name}
              className="w-6 h-6 object-contain"
            />
          </button>
        );
      })}
    </div>
  );
};

CalendarFilter.displayName = 'CalendarFilter';
