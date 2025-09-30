import { CALENDAR_CONSTANTS } from '../../../lib/utils/constants';
import { startOfWeek, endOfWeek, addMinutes, format, startOfDay, endOfDay, addDays, startOfMonth, endOfMonth } from 'date-fns';

const {
  GRID_HOUR_HEIGHT,
  DEFAULT_SLOT_DURATION,
  SNAP_THRESHOLD,
  WORKING_HOURS,
} = CALENDAR_CONSTANTS;

export interface TimePosition {
  hour: number;
  minute: number;
  y: number;
}

export interface DateRange {
  start: Date;
  end: Date;
}

// Pixel-perfect grid calculations
export class GridMath {
  private static readonly HOUR_HEIGHT = GRID_HOUR_HEIGHT;
  private static readonly SLOT_HEIGHT = GRID_HOUR_HEIGHT / (60 / DEFAULT_SLOT_DURATION);
  
  // Convert time to Y position with pixel precision
  static timeToY(date: Date, startHour = 0): number {
    const hours = date.getHours() - startHour;
    const minutes = date.getMinutes();
    return (hours * this.HOUR_HEIGHT) + (minutes * this.HOUR_HEIGHT / 60);
  }

  // Convert Y position to time with snapping
  static yToTime(y: number, baseDate: Date, startHour = 0): Date {
    const totalMinutes = (y / this.HOUR_HEIGHT) * 60;
    const snappedMinutes = this.snapMinutes(totalMinutes, DEFAULT_SLOT_DURATION);
    
    const result = startOfDay(baseDate);
    return addMinutes(result, (startHour * 60) + snappedMinutes);
  }

  // Snap minutes to nearest interval for perfect alignment
  static snapMinutes(minutes: number, interval: number): number {
    return Math.round(minutes / interval) * interval;
  }

  // Calculate duration in pixels
  static durationToHeight(minutes: number): number {
    return (minutes / 60) * this.HOUR_HEIGHT;
  }

  // Calculate minutes from height
  static heightToDuration(height: number): number {
    return Math.round((height / this.HOUR_HEIGHT) * 60);
  }

  // Get time position with perfect alignment
  static getTimePosition(date: Date, startHour = 0): TimePosition {
    return {
      hour: date.getHours(),
      minute: date.getMinutes(),
      y: this.timeToY(date, startHour),
    };
  }

  // Snap time to grid with configurable intervals
  static snapTime(date: Date, interval: number = DEFAULT_SLOT_DURATION): Date {
    const totalMinutes = date.getHours() * 60 + date.getMinutes();
    const snappedMinutes = this.snapMinutes(totalMinutes, interval);
    
    const result = startOfDay(date);
    return addMinutes(result, snappedMinutes);
  }

  // Check if drag is close enough to snap
  static shouldSnap(currentY: number, targetY: number): boolean {
    const threshold = (SNAP_THRESHOLD / 60) * this.HOUR_HEIGHT;
    return Math.abs(currentY - targetY) <= threshold;
  }

  // Get all time slots for a day with perfect spacing
  static getDayTimeSlots(date: Date, interval: number = DEFAULT_SLOT_DURATION): Date[] {
    const slots: Date[] = [];
    const start = startOfDay(date);
    
    for (let minutes = 0; minutes < 24 * 60; minutes += interval) {
      slots.push(addMinutes(start, minutes));
    }
    
    return slots;
  }

  // Calculate week boundaries
  static getWeekBounds(date: Date): DateRange {
    return {
      start: startOfWeek(date, { weekStartsOn: 1 }), // Monday
      end: endOfWeek(date, { weekStartsOn: 1 }),
    };
  }

  // Calculate month boundaries
  static getMonthBounds(date: Date): DateRange {
    return {
      start: startOfMonth(date),
      end: endOfMonth(date),
    };
  }

  // Get days for week view
  static getWeekDays(date: Date): Date[] {
    const { start } = this.getWeekBounds(date);
    const days: Date[] = [];
    
    for (let i = 0; i < 7; i++) {
      days.push(addDays(start, i));
    }
    
    return days;
  }

  // Calculate working hours bounds
  static getWorkingHoursBounds(): { start: number; end: number; height: number } {
    const height = (WORKING_HOURS.end - WORKING_HOURS.start) * this.HOUR_HEIGHT;
    return {
      start: WORKING_HOURS.start,
      end: WORKING_HOURS.end,
      height,
    };
  }

  // Get visible time range for optimization
  static getVisibleTimeRange(scrollTop: number, viewportHeight: number, startHour = 0): {
    startHour: number;
    endHour: number;
  } {
    const startFromScroll = Math.max(0, Math.floor(scrollTop / this.HOUR_HEIGHT));
    const endFromScroll = Math.ceil((scrollTop + viewportHeight) / this.HOUR_HEIGHT);
    
    return {
      startHour: startHour + startFromScroll,
      endHour: Math.min(24, startHour + endFromScroll + 1),
    };
  }

  // Clamp time to valid bounds
  static clampTime(date: Date, minHour = 0, maxHour = 24): Date {
    const hour = date.getHours();
    const minute = date.getMinutes();
    
    if (hour < minHour) {
      const result = startOfDay(date);
      return addMinutes(result, minHour * 60);
    }
    
    if (hour >= maxHour) {
      const result = startOfDay(date);
      return addMinutes(result, (maxHour - 1) * 60 + 59);
    }
    
    return date;
  }

  // Format time for display
  static formatTime(date: Date, use24Hour = false): string {
    return format(date, use24Hour ? 'HH:mm' : 'h:mm a');
  }

  // Get grid constants for components
  static getConstants() {
    return {
      HOUR_HEIGHT: this.HOUR_HEIGHT,
      SLOT_HEIGHT: this.SLOT_HEIGHT,
      DEFAULT_SLOT_DURATION,
      SNAP_THRESHOLD,
    };
  }
}