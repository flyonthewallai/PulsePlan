/**
 * TimeblocksOverlay - Renders unified timeblocks (tasks + calendar events + busy blocks)
 *
 * This component demonstrates how to integrate the unified calendar feed.
 * It fetches timeblocks using the useTimeblocks hook and renders them as blue blocks
 * overlaid on the calendar grid.
 *
 * Integration with WeeklyCalendar:
 * 1. Import this component in WeeklyCalendar.tsx
 * 2. Add it as a child of the grid container, positioned absolutely
 * 3. Ensure z-index layering is correct (timeblocks under draggable events)
 *
 * Example usage in WeeklyCalendar:
 * ```tsx
 * <WeekGrid ...>
 *   <TimeblocksOverlay weekStart={weekStart} weekEnd={weekEnd} />
 *   {/* existing event rendering *\/}
 * </WeekGrid>
 * ```
 */

import React from 'react';
import { useTimeblocks } from '@/hooks/calendar';
import type { Timeblock } from '@/types';

interface TimeblocksOverlayProps {
  weekStart: Date;
  weekEnd: Date;
  className?: string;
}

export function TimeblocksOverlay({
  weekStart,
  weekEnd,
  className = '',
}: TimeblocksOverlayProps) {
  // Fetch timeblocks for the week
  const { items, isLoading, error } = useTimeblocks({
    fromISO: weekStart.toISOString(),
    toISO: weekEnd.toISOString(),
  });

  if (isLoading) {
    return (
      <div className={`absolute inset-0 flex items-center justify-center ${className}`}>
        <div className="text-blue-400 text-sm">Loading timeblocks...</div>
      </div>
    );
  }

  if (error) {
    console.error('Failed to load timeblocks:', error);
    return null; // Fail silently to not disrupt calendar
  }

  return (
    <div className={`absolute inset-0 pointer-events-none ${className}`} style={{ zIndex: 5 }}>
      {items.map((block: Timeblock) => (
        <TimeblockItem key={block.id} block={block} />
      ))}
    </div>
  );
}

interface TimeblockItemProps {
  block: Timeblock;
}

function TimeblockItem({ block }: TimeblockItemProps) {
  // Calculate position and dimensions based on time
  // NOTE: This is a simplified example. In production, you'd use the same
  // layout calculation logic as EventBlock (OverlapCalculator, etc.)

  const start = new Date(block.start);
  const end = new Date(block.end);

  // Simple positioning (needs to match WeekGrid constants)
  const START_HOUR = 6;
  const HOUR_HEIGHT = 60; // pixels per hour
  const DAY_WIDTH = 160; // pixels per day
  const GRID_MARGIN_LEFT = 60; // hour gutter width

  const dayOfWeek = start.getDay(); // 0 = Sunday
  const mondayOffset = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // Convert to Monday-based (0-6)

  const startHour = start.getHours() + start.getMinutes() / 60;
  const endHour = end.getHours() + end.getMinutes() / 60;

  const top = (startHour - START_HOUR) * HOUR_HEIGHT;
  const height = (endHour - startHour) * HOUR_HEIGHT;
  const left = GRID_MARGIN_LEFT + (mondayOffset * DAY_WIDTH);

  // Skip if outside visible range
  if (top < 0 || startHour > 22) return null;

  // Determine color based on source
  const getBlockColor = () => {
    switch (block.source) {
      case 'task':
        return 'bg-blue-500/30 border-blue-500/50';
      case 'calendar':
        if (block.provider === 'google') return 'bg-green-500/20 border-green-500/40';
        if (block.provider === 'outlook') return 'bg-purple-500/20 border-purple-500/40';
        return 'bg-gray-500/20 border-gray-500/40';
      case 'busy':
        return 'bg-red-500/20 border-red-500/40';
      default:
        return 'bg-gray-500/20 border-gray-500/40';
    }
  };

  return (
    <div
      className={`absolute rounded border pointer-events-auto cursor-pointer hover:opacity-80 transition-opacity ${getBlockColor()}`}
      style={{
        top: `${top}px`,
        left: `${left}px`,
        width: `${DAY_WIDTH - 4}px`, // Slight padding
        height: `${Math.max(height, 20)}px`, // Min height
      }}
      title={`${block.title} (${block.source})`}
    >
      <div className="px-2 py-1 text-xs text-white truncate">
        {block.title}
      </div>
      {block.readonly && (
        <div className="absolute top-1 right-1 w-2 h-2 bg-gray-400 rounded-full" title="Read-only" />
      )}
    </div>
  );
}
