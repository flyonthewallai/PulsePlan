import { GridMath } from './gridMath';

export interface SelectionState {
  isSelecting: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
  startTime?: Date;
  endTime?: Date;
  dayIndex?: number;
}

export interface SelectionBounds {
  left: number;
  top: number;
  width: number;
  height: number;
  startTime: Date;
  endTime: Date;
  dayIndex: number;
}

export class SelectionManager {
  private static readonly MIN_SELECTION_HEIGHT = 30; // pixels
  private static readonly SNAP_INTERVAL = 15; // minutes

  // Start a new selection
  static startSelection(
    x: number,
    y: number,
    dayIndex: number,
    baseDate: Date,
    startHour: number = 6
  ): SelectionState {
    const startTime = GridMath.yToTime(y, baseDate, startHour);
    
    return {
      isSelecting: true,
      startX: x,
      startY: y,
      currentX: x,
      currentY: y,
      startTime,
      endTime: startTime,
      dayIndex
    };
  }

  // Update selection during drag
  static updateSelection(
    selection: SelectionState,
    x: number,
    y: number,
    baseDate: Date,
    startHour: number = 6
  ): SelectionState {
    if (!selection.isSelecting) return selection;

    const currentTime = GridMath.yToTime(y, baseDate, startHour);
    const startTime = selection.startTime!;
    
    // Determine which time is earlier and which is later
    const earlierTime = currentTime < startTime ? currentTime : startTime;
    const laterTime = currentTime < startTime ? startTime : currentTime;
    
    // Snap to intervals
    const snappedStartTime = GridMath.snapTime(earlierTime, this.SNAP_INTERVAL);
    const snappedEndTime = GridMath.snapTime(laterTime, this.SNAP_INTERVAL);
    
    // Ensure minimum duration of 30 minutes
    let finalEndTime = snappedEndTime;
    const minDuration = 30 * 60 * 1000; // 30 minutes in milliseconds
    if (finalEndTime.getTime() - snappedStartTime.getTime() < minDuration) {
      finalEndTime = new Date(snappedStartTime.getTime() + minDuration);
    }

    return {
      ...selection,
      currentX: x,
      currentY: y,
      startTime: snappedStartTime,
      endTime: finalEndTime
    };
  }

  // End selection and return final bounds
  static endSelection(selection: SelectionState, startHour: number = 6): SelectionBounds | null {
    if (!selection.isSelecting || !selection.startTime || !selection.endTime || selection.dayIndex === undefined) {
      return null;
    }

    // Calculate visual bounds (relative to startHour)
    const startY = GridMath.timeToY(selection.startTime, startHour);
    const endY = GridMath.timeToY(selection.endTime, startHour);
    
    const top = Math.min(startY, endY);
    const height = Math.max(Math.abs(endY - startY), this.MIN_SELECTION_HEIGHT);
    
    // Calculate horizontal position (assuming day columns)
    const dayWidth = 160; // From constants
    const left = selection.dayIndex * dayWidth;
    const width = dayWidth - 4; // Small margin for visual clarity

    return {
      left: Math.round(left),
      top: Math.round(top),
      width: Math.round(width),
      height: Math.round(height),
      startTime: selection.startTime,
      endTime: selection.endTime,
      dayIndex: selection.dayIndex
    };
  }

  // Cancel selection
  static cancelSelection(): SelectionState {
    return {
      isSelecting: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0
    };
  }

  // Check if selection is valid (meets minimum requirements)
  static isValidSelection(selection: SelectionState): boolean {
    if (!selection.isSelecting || !selection.startTime || !selection.endTime) {
      return false;
    }

    const duration = selection.endTime.getTime() - selection.startTime.getTime();
    const minDuration = 15 * 60 * 1000; // 15 minutes minimum
    
    return duration >= minDuration;
  }

  // Get visual bounds for current selection (for rendering selection rectangle)
  static getSelectionVisualBounds(selection: SelectionState, columnWidth: number = 160): {
    left: number;
    top: number;
    width: number;
    height: number;
  } | null {
    if (!selection.isSelecting || !selection.startTime || !selection.endTime || selection.dayIndex === undefined) {
      return null;
    }

    const ALL_DAY_ROW_HEIGHT = 48; // Match CALENDAR_CONSTANTS.ALL_DAY_ROW_HEIGHT
    const TIME_GUTTER_WIDTH = 60; // Match CALENDAR_CONSTANTS.GRID_MARGIN_LEFT
    
    const startY = GridMath.timeToY(selection.startTime, 6);
    const endY = GridMath.timeToY(selection.endTime, 6);
    
    // Add ALL_DAY_ROW_HEIGHT offset to match event positioning
    const top = ALL_DAY_ROW_HEIGHT + Math.min(startY, endY);
    const height = Math.max(Math.abs(endY - startY), this.MIN_SELECTION_HEIGHT);
    
    // Add TIME_GUTTER_WIDTH offset to match event positioning
    const left = TIME_GUTTER_WIDTH + (selection.dayIndex * columnWidth);
    const width = columnWidth - 4; // 4px margin for visual clarity

    return {
      left: Math.round(left + 2), // Small offset for visual clarity
      top: Math.round(top),
      width: Math.round(width),
      height: Math.round(height)
    };
  }

  // Convert client coordinates to grid coordinates
  static clientToGridCoords(
    clientX: number,
    clientY: number,
    gridElement: HTMLElement,
    hourLabelWidth: number = 60
  ): { x: number; y: number; dayIndex: number } | null {
    const rect = gridElement.getBoundingClientRect();
    const headerHeight = 64; // Height of the day header
    const dayWidth = 160; // GRID_DAY_WIDTH from constants
    
    // Calculate relative coordinates
    const x = clientX - rect.left - hourLabelWidth;
    const y = clientY - rect.top - headerHeight;

    // Check bounds
    if (x < 0 || y < 0) return null;
    if (x >= (dayWidth * 7)) return null; // Beyond 7 days

    // Calculate which day column
    const dayIndex = Math.floor(x / dayWidth);
    
    // Clamp to valid day range (0-6 for week view)
    if (dayIndex < 0 || dayIndex > 6) return null;

    // Calculate position within the day column
    const dayX = x - (dayIndex * dayWidth);

    return { x: dayX, y, dayIndex };
  }

  // Check if coordinates are within a valid selection area
  static isInSelectableArea(
    x: number,
    y: number,
    workingHours: { start: number; end: number } = { start: 6, end: 22 }
  ): boolean {
    const maxY = (workingHours.end - workingHours.start) * 60; // 60px per hour
    return x >= 0 && y >= 0 && y <= maxY;
  }

  // Get time range string for display
  static getSelectionTimeString(selection: SelectionState): string {
    if (!selection.startTime || !selection.endTime) return '';

    const formatTime = (date: Date) => {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    };

    return `${formatTime(selection.startTime)} - ${formatTime(selection.endTime)}`;
  }

  // Calculate selection duration in minutes
  static getSelectionDuration(selection: SelectionState): number {
    if (!selection.startTime || !selection.endTime) return 0;
    
    return Math.round(
      (selection.endTime.getTime() - selection.startTime.getTime()) / (1000 * 60)
    );
  }

  // Validate selection against existing events
  static validateSelectionAgainstEvents(
    selection: SelectionState,
    existingEvents: any[]
  ): {
    isValid: boolean;
    conflicts: any[];
    warning?: string;
  } {
    if (!selection.startTime || !selection.endTime) {
      return { isValid: false, conflicts: [] };
    }

    const selectionStart = selection.startTime.getTime();
    const selectionEnd = selection.endTime.getTime();

    const conflicts = existingEvents.filter(event => {
      const eventStart = new Date(event.start).getTime();
      const eventEnd = new Date(event.end).getTime();
      
      // Check for overlap
      return selectionStart < eventEnd && selectionEnd > eventStart;
    });

    let warning: string | undefined;
    if (conflicts.length > 0) {
      warning = `This time slot overlaps with ${conflicts.length} existing event${conflicts.length > 1 ? 's' : ''}`;
    }

    return {
      isValid: conflicts.length === 0,
      conflicts,
      warning
    };
  }
}

// Utility types for drag-to-create functionality
export interface DragToCreateState {
  selection: SelectionState;
  isCreating: boolean;
  previewEvent?: {
    title: string;
    startTime: Date;
    endTime: Date;
    dayIndex: number;
  };
}

// Helper functions for common selection operations
export const SelectionUtils = {
  // Create a preview event from selection
  createPreviewFromSelection(
    selection: SelectionState,
    defaultTitle: string = 'New Event'
  ): DragToCreateState['previewEvent'] | null {
    if (!SelectionManager.isValidSelection(selection)) return null;

    return {
      title: defaultTitle,
      startTime: selection.startTime!,
      endTime: selection.endTime!,
      dayIndex: selection.dayIndex!
    };
  },

  // Check if selection spans multiple days
  selectionSpansMultipleDays(selection: SelectionState): boolean {
    if (!selection.startTime || !selection.endTime) return false;
    
    return selection.startTime.getDate() !== selection.endTime.getDate();
  },

  // Round selection to common time increments
  roundSelectionToIncrement(
    selection: SelectionState,
    increment: 15 | 30 | 60 = 30
  ): SelectionState {
    if (!selection.startTime || !selection.endTime) return selection;

    const roundedStart = GridMath.snapTime(selection.startTime, increment);
    const roundedEnd = GridMath.snapTime(selection.endTime, increment);

    return {
      ...selection,
      startTime: roundedStart,
      endTime: roundedEnd
    };
  }
};