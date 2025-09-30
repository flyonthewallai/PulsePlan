import type { CalendarEvent } from '@/types';
import { GridMath } from './gridMath';

export interface EventLayout {
  id: string;
  event: CalendarEvent;
  x: number;
  y: number;
  width: number;
  height: number;
  laneIndex: number;
  laneCount: number;
  zIndex: number;
}

export interface EventGroup {
  events: CalendarEvent[];
  lanes: CalendarEvent[][];
}

export class OverlapCalculator {
  // Main function to calculate perfect lane layout for overlapping events
  static calculateEventLayouts(events: CalendarEvent[], dayWidth: number = 160): EventLayout[] {
    if (events.length === 0) return [];

    // Sort events by start time, then by duration (shorter first for better packing)
    const sortedEvents = [...events].sort((a, b) => {
      const startDiff = new Date(a.start).getTime() - new Date(b.start).getTime();
      if (startDiff !== 0) return startDiff;
      
      // If same start time, shorter events first
      const aDuration = new Date(a.end).getTime() - new Date(a.start).getTime();
      const bDuration = new Date(b.end).getTime() - new Date(b.start).getTime();
      return aDuration - bDuration;
    });

    // Group overlapping events together
    const groups = this.groupOverlappingEvents(sortedEvents);
    
    // Calculate layout for each group independently
    const layouts: EventLayout[] = [];
    
    groups.forEach((group) => {
      const groupLayouts = this.calculateGroupLayout(group, dayWidth);
      layouts.push(...groupLayouts);
    });

    return layouts;
  }

  // Group events that overlap in time
  private static groupOverlappingEvents(events: CalendarEvent[]): EventGroup[] {
    const groups: EventGroup[] = [];
    
    for (const event of events) {
      const eventStart = new Date(event.start).getTime();
      const eventEnd = new Date(event.end).getTime();
      
      // Find a group this event overlaps with
      let foundGroup = false;
      
      for (const group of groups) {
        const hasOverlap = group.events.some(existingEvent => {
          const existingStart = new Date(existingEvent.start).getTime();
          const existingEnd = new Date(existingEvent.end).getTime();
          
          // Check if events overlap (not just touch)
          return eventStart < existingEnd && eventEnd > existingStart;
        });
        
        if (hasOverlap) {
          group.events.push(event);
          foundGroup = true;
          break;
        }
      }
      
      // If no overlapping group found, create new group
      if (!foundGroup) {
        groups.push({
          events: [event],
          lanes: []
        });
      }
    }
    
    return groups;
  }

  // Calculate layout for a single group of overlapping events
  private static calculateGroupLayout(group: EventGroup, dayWidth: number): EventLayout[] {
    if (group.events.length === 1) {
      // Single event takes full width
      const event = group.events[0];
      return [this.createEventLayout(event, 0, dayWidth, 0, 1, 1)];
    }

    // Use lane packing algorithm for multiple events
    const lanes = this.packEventsIntoLanes(group.events);
    const laneCount = lanes.length;
    const laneWidth = dayWidth / laneCount;
    const GAP = 2; // 2px gap between lanes
    const actualLaneWidth = laneWidth - GAP;
    
    const layouts: EventLayout[] = [];
    
    lanes.forEach((lane, laneIndex) => {
      lane.forEach(event => {
        const layout = this.createEventLayout(
          event,
          laneIndex * laneWidth,
          actualLaneWidth,
          laneIndex,
          laneCount,
          laneIndex + 1 // Higher z-index for later lanes
        );
        layouts.push(layout);
      });
    });

    return layouts;
  }

  // Pack events into lanes using greedy algorithm
  private static packEventsIntoLanes(events: CalendarEvent[]): CalendarEvent[][] {
    const lanes: CalendarEvent[][] = [];
    
    // Sort by start time for lane assignment
    const sortedEvents = [...events].sort((a, b) => 
      new Date(a.start).getTime() - new Date(b.start).getTime()
    );

    for (const event of sortedEvents) {
      const eventStart = new Date(event.start).getTime();
      const eventEnd = new Date(event.end).getTime();
      
      // Find the first lane where this event can fit
      let assignedLane = false;
      
      for (const lane of lanes) {
        // Check if event can fit in this lane (doesn't overlap with any event in lane)
        const canFit = lane.every(laneEvent => {
          const laneStart = new Date(laneEvent.start).getTime();
          const laneEnd = new Date(laneEvent.end).getTime();
          
          // Events don't overlap if one ends before or at the moment the other starts
          return eventEnd <= laneStart || eventStart >= laneEnd;
        });
        
        if (canFit) {
          lane.push(event);
          assignedLane = true;
          break;
        }
      }
      
      // If no existing lane can fit this event, create a new lane
      if (!assignedLane) {
        lanes.push([event]);
      }
    }

    return lanes;
  }

  // Create EventLayout object with precise positioning
  private static createEventLayout(
    event: CalendarEvent,
    x: number,
    width: number,
    laneIndex: number,
    laneCount: number,
    zIndex: number
  ): EventLayout {
    const startDate = new Date(event.start);
    const endDate = new Date(event.end);
    const durationMs = endDate.getTime() - startDate.getTime();
    const durationMinutes = durationMs / (1000 * 60);
    
    return {
      id: event.id,
      event,
      x: Math.round(x), // Pixel-perfect positioning
      y: GridMath.timeToY(startDate),
      width: Math.round(width),
      height: Math.max(
        GridMath.durationToHeight(durationMinutes),
        20 // Minimum height for visibility
      ),
      laneIndex,
      laneCount,
      zIndex
    };
  }

  // Get all overlapping events for a specific event (used for highlighting)
  static getOverlappingEvents(targetEvent: CalendarEvent, allEvents: CalendarEvent[]): CalendarEvent[] {
    const targetStart = new Date(targetEvent.start).getTime();
    const targetEnd = new Date(targetEvent.end).getTime();
    
    return allEvents.filter(event => {
      if (event.id === targetEvent.id) return false;
      
      const eventStart = new Date(event.start).getTime();
      const eventEnd = new Date(event.end).getTime();
      
      // Check for overlap
      return targetStart < eventEnd && targetEnd > eventStart;
    });
  }

  // Check if two events overlap
  static eventsOverlap(event1: CalendarEvent, event2: CalendarEvent): boolean {
    const start1 = new Date(event1.start).getTime();
    const end1 = new Date(event1.end).getTime();
    const start2 = new Date(event2.start).getTime();
    const end2 = new Date(event2.end).getTime();
    
    return start1 < end2 && end1 > start2;
  }

  // Calculate optimal width for a day column based on max concurrent events
  static calculateOptimalDayWidth(events: CalendarEvent[], minWidth: number = 120): number {
    const layouts = this.calculateEventLayouts(events, 200); // Use reference width
    const maxLaneCount = Math.max(...layouts.map(layout => layout.laneCount), 1);
    
    // Ensure minimum width per lane while respecting minimum day width
    const minWidthPerLane = 80;
    const calculatedWidth = maxLaneCount * minWidthPerLane;
    
    return Math.max(calculatedWidth, minWidth);
  }
}

// Utility functions for common overlap operations
export const OverlapUtils = {
  // Check if a time range is free of events
  isTimeSlotFree(
    startTime: Date,
    endTime: Date,
    existingEvents: CalendarEvent[],
    excludeEventId?: string
  ): boolean {
    const slotStart = startTime.getTime();
    const slotEnd = endTime.getTime();
    
    return !existingEvents.some(event => {
      if (excludeEventId && event.id === excludeEventId) return false;
      
      const eventStart = new Date(event.start).getTime();
      const eventEnd = new Date(event.end).getTime();
      
      return slotStart < eventEnd && slotEnd > eventStart;
    });
  },

  // Find next available time slot
  findNextFreeSlot(
    preferredStart: Date,
    duration: number, // in minutes
    existingEvents: CalendarEvent[],
    maxHour: number = 22
  ): Date | null {
    const slotDuration = duration * 60 * 1000; // Convert to milliseconds
    let currentStart = new Date(preferredStart);
    
    // Try every 30-minute increment until maxHour
    while (currentStart.getHours() < maxHour) {
      const currentEnd = new Date(currentStart.getTime() + slotDuration);
      
      if (this.isTimeSlotFree(currentStart, currentEnd, existingEvents)) {
        return currentStart;
      }
      
      // Move to next 30-minute slot
      currentStart = new Date(currentStart.getTime() + 30 * 60 * 1000);
    }
    
    return null;
  },

  // Get conflict information for an event
  getEventConflicts(
    event: CalendarEvent,
    existingEvents: CalendarEvent[]
  ): {
    hasConflicts: boolean;
    conflictingEvents: CalendarEvent[];
    conflictSeverity: 'none' | 'minor' | 'major';
  } {
    const conflictingEvents = OverlapCalculator.getOverlappingEvents(event, existingEvents);
    const hasConflicts = conflictingEvents.length > 0;
    
    let conflictSeverity: 'none' | 'minor' | 'major' = 'none';
    
    if (hasConflicts) {
      // Determine severity based on number of conflicts and overlap percentage
      const eventDuration = new Date(event.end).getTime() - new Date(event.start).getTime();
      const maxOverlapDuration = Math.max(...conflictingEvents.map(conflictEvent => {
        const overlapStart = Math.max(
          new Date(event.start).getTime(),
          new Date(conflictEvent.start).getTime()
        );
        const overlapEnd = Math.min(
          new Date(event.end).getTime(),
          new Date(conflictEvent.end).getTime()
        );
        return Math.max(0, overlapEnd - overlapStart);
      }));
      
      const overlapPercentage = maxOverlapDuration / eventDuration;
      
      if (overlapPercentage > 0.75 || conflictingEvents.length > 2) {
        conflictSeverity = 'major';
      } else {
        conflictSeverity = 'minor';
      }
    }
    
    return {
      hasConflicts,
      conflictingEvents,
      conflictSeverity
    };
  }
};