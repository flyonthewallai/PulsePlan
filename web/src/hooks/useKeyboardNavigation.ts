import { useEffect, useRef, useCallback } from 'react';
import type { CalendarEvent } from '@/types';
import { GridMath } from '../features/calendar/calendar-logic/gridMath';

interface UseKeyboardNavigationProps {
  events: CalendarEvent[];
  selectedEvent: CalendarEvent | null;
  onEventSelect: (event: CalendarEvent) => void;
  onEventEdit: (event: CalendarEvent) => void;
  onEventDelete: (eventId: string) => void;
  onNewEvent: () => void;
  currentDate: Date;
  setCurrentDate: (date: Date) => void;
  isModalOpen?: boolean;
}

export function useKeyboardNavigation({
  events,
  selectedEvent,
  onEventSelect,
  onEventEdit,
  onEventDelete,
  onNewEvent,
  currentDate,
  setCurrentDate,
  isModalOpen = false,
}: UseKeyboardNavigationProps) {
  const lastActiveElement = useRef<Element | null>(null);

  // Get events sorted by date and time for navigation
  const sortedEvents = events.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Don't handle keyboard events when modal is open or when typing in inputs
    if (isModalOpen || (e.target as Element)?.tagName === 'INPUT' || (e.target as Element)?.tagName === 'TEXTAREA') {
      return;
    }

    const currentIndex = selectedEvent ? sortedEvents.findIndex(event => event.id === selectedEvent.id) : -1;

    switch (e.key) {
      case 'ArrowLeft':
        e.preventDefault();
        if (e.shiftKey) {
          // Move to previous week
          setCurrentDate(new Date(currentDate.getTime() - 7 * 24 * 60 * 60 * 1000));
        } else if (selectedEvent && currentIndex > 0) {
          // Select previous event
          onEventSelect(sortedEvents[currentIndex - 1]);
        }
        break;

      case 'ArrowRight':
        e.preventDefault();
        if (e.shiftKey) {
          // Move to next week
          setCurrentDate(new Date(currentDate.getTime() + 7 * 24 * 60 * 60 * 1000));
        } else if (selectedEvent && currentIndex < sortedEvents.length - 1) {
          // Select next event
          onEventSelect(sortedEvents[currentIndex + 1]);
        } else if (!selectedEvent && sortedEvents.length > 0) {
          // Select first event if none selected
          onEventSelect(sortedEvents[0]);
        }
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (selectedEvent) {
          // Move selected event 15 minutes earlier
          const newStart = new Date(new Date(selectedEvent.start).getTime() - 15 * 60 * 1000);
          const newEnd = new Date(new Date(selectedEvent.end).getTime() - 15 * 60 * 1000);
          // This would need to be wired to the update handler
          // For now, we'll just prevent the default
        }
        break;

      case 'ArrowDown':
        e.preventDefault();
        if (selectedEvent) {
          // Move selected event 15 minutes later
          const newStart = new Date(new Date(selectedEvent.start).getTime() + 15 * 60 * 1000);
          const newEnd = new Date(new Date(selectedEvent.end).getTime() + 15 * 60 * 1000);
          // This would need to be wired to the update handler
          // For now, we'll just prevent the default
        }
        break;

      case 'Enter':
        e.preventDefault();
        if (selectedEvent) {
          // Edit selected event
          onEventEdit(selectedEvent);
        } else {
          // Create new event
          onNewEvent();
        }
        break;

      case 'Delete':
      case 'Backspace':
        e.preventDefault();
        if (selectedEvent) {
          // Delete selected event
          onEventDelete(selectedEvent.id);
        }
        break;

      case 'Escape':
        e.preventDefault();
        if (selectedEvent) {
          // Deselect event
          onEventSelect(null as any); // This is a bit of a hack for the type system
        }
        break;

      case 'n':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          onNewEvent();
        }
        break;

      case 't':
        e.preventDefault();
        // Go to today
        setCurrentDate(new Date());
        break;

      case 'j':
        e.preventDefault();
        // Select next event (vim-style navigation)
        if (currentIndex < sortedEvents.length - 1) {
          onEventSelect(sortedEvents[currentIndex + 1]);
        }
        break;

      case 'k':
        e.preventDefault();
        // Select previous event (vim-style navigation)
        if (currentIndex > 0) {
          onEventSelect(sortedEvents[currentIndex - 1]);
        }
        break;

      case '?':
        e.preventDefault();
        // Show keyboard shortcuts help (could be implemented later)
        console.log('Keyboard shortcuts help would go here');
        break;

      default:
        break;
    }
  }, [
    isModalOpen,
    selectedEvent,
    sortedEvents,
    currentDate,
    onEventSelect,
    onEventEdit,
    onEventDelete,
    onNewEvent,
    setCurrentDate,
  ]);

  // Focus management for accessibility
  const focusCalendar = useCallback(() => {
    const calendarElement = document.querySelector('[data-calendar-container]') as HTMLElement;
    if (calendarElement) {
      calendarElement.focus();
    }
  }, []);

  const restoreFocus = useCallback(() => {
    if (lastActiveElement.current && document.contains(lastActiveElement.current)) {
      (lastActiveElement.current as HTMLElement).focus?.();
    } else {
      focusCalendar();
    }
  }, [focusCalendar]);

  const storeFocus = useCallback(() => {
    lastActiveElement.current = document.activeElement;
  }, []);

  // Keyboard event listeners
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  return {
    focusCalendar,
    restoreFocus,
    storeFocus,
  };
}

// Hook for announcing changes to screen readers
export function useScreenReaderAnnouncements() {
  const announceRef = useRef<HTMLDivElement | null>(null);

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!announceRef.current) {
      // Create announcement element if it doesn't exist
      const announcer = document.createElement('div');
      announcer.setAttribute('aria-live', priority);
      announcer.setAttribute('aria-atomic', 'true');
      announcer.className = 'sr-only';
      announcer.style.position = 'absolute';
      announcer.style.left = '-10000px';
      announcer.style.width = '1px';
      announcer.style.height = '1px';
      announcer.style.overflow = 'hidden';
      document.body.appendChild(announcer);
      announceRef.current = announcer;
    }

    // Clear previous announcement and set new one
    announceRef.current.textContent = '';
    setTimeout(() => {
      if (announceRef.current) {
        announceRef.current.textContent = message;
      }
    }, 100);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (announceRef.current && document.body.contains(announceRef.current)) {
        document.body.removeChild(announceRef.current);
      }
    };
  }, []);

  return { announce };
}

// Helper hook to get keyboard shortcut descriptions
export function useKeyboardShortcuts() {
  return {
    shortcuts: [
      { key: '←/→', description: 'Navigate between events' },
      { key: 'Shift + ←/→', description: 'Navigate between weeks' },
      { key: '↑/↓', description: 'Move selected event by 15 minutes' },
      { key: 'Enter', description: 'Edit selected event or create new event' },
      { key: 'Delete/Backspace', description: 'Delete selected event' },
      { key: 'Escape', description: 'Deselect event' },
      { key: 'Ctrl/Cmd + N', description: 'Create new event' },
      { key: 'T', description: 'Go to today' },
      { key: 'J/K', description: 'Navigate events (vim-style)' },
      { key: '?', description: 'Show keyboard shortcuts' },
    ],
  };
}