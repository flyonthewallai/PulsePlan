/**
 * CALENDAR POSITIONING - SINGLE SOURCE OF TRUTH
 *
 * This file contains ALL positioning logic for the calendar.
 * NO other file should calculate positions independently.
 */

import { CALENDAR_CONSTANTS } from '../../../lib/utils/constants';

// Calendar grid constants
const HOUR_HEIGHT = CALENDAR_CONSTANTS.GRID_HOUR_HEIGHT; // 120px per hour
const HEADER_HEIGHT = CALENDAR_CONSTANTS.HEADER_HEIGHT; // 56px
const ALL_DAY_ROW_HEIGHT = CALENDAR_CONSTANTS.ALL_DAY_ROW_HEIGHT; // 48px
const TIME_GUTTER_WIDTH = CALENDAR_CONSTANTS.GRID_MARGIN_LEFT; // 60px
const DAY_WIDTH = CALENDAR_CONSTANTS.GRID_DAY_WIDTH; // 160px
const CONTAINER_PADDING = 32; // px-8 padding from parent container

/**
 * Convert a Date to Y position (pixels from grid start)
 * Grid starts at START_HOUR (e.g., 6 AM)
 */
export function dateToGridY(date: Date, startHour: number): number {
  const hour = date.getHours();
  const minute = date.getMinutes();

  // Minutes from grid start (not from midnight!)
  const minutesFromGridStart = (hour - startHour) * 60 + minute;

  // Convert to pixels
  const y = (minutesFromGridStart / 60) * HOUR_HEIGHT;

  console.log(`[dateToGridY] ${hour}:${String(minute).padStart(2, '0')} with startHour=${startHour} → minutesFromStart=${minutesFromGridStart}, y=${y}px`);

  return y;
}

/**
 * Calculate the final screen position for an event
 */
export interface EventPosition {
  left: number;  // Absolute pixels from container left
  top: number;   // Absolute pixels from container top
  width: number;
  height: number;
}

export function calculateEventPosition(
  event: {
    start: string;
    end: string;
    allDay?: boolean;
  },
  dayIndex: number,  // 0-6 for Mon-Sun
  startHour: number,
  options?: {
    stackIndex?: number; // For stacking multiple all-day events
    columnWidth?: number; // Dynamic column width (defaults to constant)
  }
): EventPosition {
  const startDate = new Date(event.start);
  const endDate = new Date(event.end);

  // Use dynamic column width if provided, otherwise fall back to constant
  const columnWidth = options?.columnWidth ?? DAY_WIDTH;

  // Calculate width and horizontal position
  // Container already has px-8 padding, so events only need time gutter offset
  const left = TIME_GUTTER_WIDTH + (dayIndex * columnWidth);
  const width = columnWidth - 2; // 2px margin for better fit

  if (event.allDay) {
    // ALL-DAY EVENT: Position NEGATIVE to go up into the all-day row
    // The overlay is inside the time grid, so we need negative top to reach the all-day area
    const stackIndex = options?.stackIndex || 0;
    const eventHeight = 32; // Increased from 20px to 32px for better visibility
    const verticalGap = 4; // Gap between stacked events
    const top = -(ALL_DAY_ROW_HEIGHT) + (stackIndex * (eventHeight + verticalGap)) + 4; // Negative offset + stacking
    const height = eventHeight;

    console.log(`🟢 [NEW POSITIONING] All-Day "${(event as any).title}":`, {
      top, left, width, height, dayIndex, stackIndex,
      explanation: 'Negative top positions event in all-day row above time grid'
    });

    return { left, top, width, height };
  }

  // TIMED EVENT: Position based on time RELATIVE TO TIME GRID START
  // Account for ALL_DAY_ROW_HEIGHT since events render below it
  const hour = startDate.getHours();
  const minute = startDate.getMinutes();
  const gridY = dateToGridY(startDate, startHour);
  const top = ALL_DAY_ROW_HEIGHT + gridY; // All-day row offset + grid Y

  // Calculate height from duration
  const durationMs = endDate.getTime() - startDate.getTime();
  const durationMinutes = durationMs / (1000 * 60);
  const height = Math.max((durationMinutes / 60) * HOUR_HEIGHT, 20);

  console.log(`🔵 [NEW POSITIONING] Timed "${(event as any).title}":`, {
    hour, minute, startHour,
    gridY, top, left, width, height, dayIndex,
    explanation: 'Top is relative to time grid start (overlay container)'
  });

  return { left, top, width, height };
}

/**
 * Calculate position for drag-to-create selection
 */
export function calculateSelectionPosition(
  startY: number, // Grid Y coordinate from click
  endY: number,
  dayIndex: number
): EventPosition {
  const top = Math.min(startY, endY) + HEADER_HEIGHT + ALL_DAY_ROW_HEIGHT;
  const height = Math.max(Math.abs(endY - startY), 30); // Min 30px
  const left = TIME_GUTTER_WIDTH + (dayIndex * DAY_WIDTH);
  const width = DAY_WIDTH - 4;

  return { left, top, width, height };
}

/**
 * Convert click coordinates to grid position
 */
export function clickToGridPosition(
  clientX: number,
  clientY: number,
  containerRect: DOMRect,
  scrollTop: number,
  startHour: number
): {
  dayIndex: number;
  gridY: number; // Y position within grid (pixels from grid start)
  time: Date;    // Actual time clicked
  baseDate: Date; // Date for the clicked day
} | null {
  // Calculate position relative to container
  const relativeX = clientX - containerRect.left;
  const relativeY = clientY - containerRect.top + scrollTop;

  // Remove header and gutter offsets
  const gridX = relativeX - TIME_GUTTER_WIDTH;
  const gridY = relativeY - HEADER_HEIGHT - ALL_DAY_ROW_HEIGHT;

  // Guard: outside valid area
  if (gridX < 0 || gridY < 0) return null;

  // Calculate day index (0-6)
  const dayIndex = Math.floor(gridX / DAY_WIDTH);
  if (dayIndex < 0 || dayIndex > 6) return null;

  // Calculate time from gridY
  const minutesFromGridStart = (gridY / HOUR_HEIGHT) * 60;
  const totalMinutes = (startHour * 60) + minutesFromGridStart;

  // Snap to 15-minute intervals
  const snappedMinutes = Math.round(totalMinutes / 15) * 15;
  const hour = Math.floor(snappedMinutes / 60);
  const minute = snappedMinutes % 60;

  // Create time for clicked position
  const baseDate = new Date();
  baseDate.setHours(hour, minute, 0, 0);

  // Recalculate gridY from snapped time
  const snappedGridY = ((hour - startHour) * 60 + minute) / 60 * HOUR_HEIGHT;

  return {
    dayIndex,
    gridY: snappedGridY,
    time: baseDate,
    baseDate,
  };
}

/**
 * DEBUG: Log all positioning calculations
 */
export function debugPosition(
  label: string,
  event: { title: string; start: string; end: string; allDay?: boolean },
  dayIndex: number,
  startHour: number
) {
  const pos = calculateEventPosition(event, dayIndex, startHour);
  const startDate = new Date(event.start);

  console.group(`[POSITION DEBUG] ${label}`);
  console.log('Event:', event.title);
  console.log('Type:', event.allDay ? 'ALL-DAY' : 'TIMED');
  console.log('Start:', event.start);
  console.log('Local time:', `${startDate.getHours()}:${String(startDate.getMinutes()).padStart(2, '0')}`);
  console.log('Day index:', dayIndex);
  console.log('Start hour:', startHour);
  console.log('Calculated position:', pos);
  console.groupEnd();

  return pos;
}
