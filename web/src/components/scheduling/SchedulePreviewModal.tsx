import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Calendar, Clock, AlertTriangle, Info } from 'lucide-react';

interface TimeblockPreview {
  title: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  color?: string;
  task_id?: string;
  block_type: string;
  description?: string;
}

interface Conflict {
  timeblock_id: string;
  conflict_type: string;
  description: string;
  severity: string;
  suggested_resolution?: string;
}

interface ContextSummary {
  hobbies_count: number;
  preferences_count: number;
  confidence_score: number;
  key_factors: string[];
}

interface SchedulePlan {
  timeblocks: TimeblockPreview[];
  rationale: string;
  conflicts: Conflict[];
  confidence: number;
  context_used: ContextSummary;
}

interface CalendarViewData {
  days: Record<string, TimeblockPreview[]>;
  range: { start: string; end: string };
  timezone: string;
}

interface CompactSummary {
  summary_text: string;
  key_highlights: string[];
  next_steps: string;
}

interface SchedulePreviewData {
  schedule: SchedulePlan;
  calendar_view: CalendarViewData;
  compact_summary: CompactSummary;
  modification_allowed: boolean;
}

interface SchedulingGate {
  gate_token: string;
  action_id: string;
  display_mode: string;
  preview_data: SchedulePreviewData;
  expires_at: string;
}

interface Modification {
  timeblock_id: string;
  new_start_time?: string;
  new_duration_minutes?: number;
}

interface SchedulePreviewModalProps {
  gate: SchedulingGate;
  onConfirm: (modifications?: Modification[]) => Promise<void>;
  onCancel: () => void;
  isOpen: boolean;
}

export const SchedulePreviewModal: React.FC<SchedulePreviewModalProps> = ({
  gate,
  onConfirm,
  onCancel,
  isOpen,
}) => {
  const [modifications, setModifications] = useState<Modification[]>([]);
  const [isConfirming, setIsConfirming] = useState(false);

  const { schedule, calendar_view } = gate.preview_data;

  const handleConfirm = async () => {
    setIsConfirming(true);
    try {
      await onConfirm(modifications.length > 0 ? modifications : undefined);
    } finally {
      setIsConfirming(false);
    }
  };

  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  const getBlockTypeColor = (blockType: string): string => {
    const colors: Record<string, string> = {
      task: 'bg-blue-500',
      hobby: 'bg-green-500',
      break: 'bg-amber-500',
      deep_work: 'bg-purple-500',
      meeting: 'bg-red-500',
    };
    return colors[blockType] || 'bg-gray-500';
  };

  const sortedDays = Object.keys(calendar_view.days).sort();

  return (
    <Dialog open={isOpen} onOpenChange={() => !isConfirming && onCancel()}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Schedule Preview
          </DialogTitle>
          <DialogDescription>{schedule.rationale}</DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-auto space-y-4">
          {/* Confidence Score */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <Badge variant={schedule.confidence >= 0.7 ? 'default' : 'secondary'}>
                {Math.round(schedule.confidence * 100)}% Confidence
              </Badge>
              <span className="text-muted-foreground">
                Using {schedule.context_used.hobbies_count} hobbies and{' '}
                {schedule.context_used.preferences_count} learned preferences
              </span>
            </div>
          </div>

          {/* Conflicts Warning */}
          {schedule.conflicts.length > 0 && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                {schedule.conflicts.length} conflict{schedule.conflicts.length !== 1 ? 's' : ''}{' '}
                detected. Review the schedule below and adjust if needed.
              </AlertDescription>
            </Alert>
          )}

          {/* Calendar Grid */}
          <div className="border rounded-lg p-4 bg-muted/30">
            <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
              {sortedDays.map((day) => (
                <DayColumn
                  key={day}
                  date={day}
                  blocks={calendar_view.days[day]}
                  formatTime={formatTime}
                  formatDate={formatDate}
                  getBlockTypeColor={getBlockTypeColor}
                />
              ))}
            </div>
          </div>

          {/* Conflicts Details */}
          {schedule.conflicts.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-sm flex items-center gap-2">
                <Info className="h-4 w-4" />
                Suggested Adjustments
              </h4>
              {schedule.conflicts.map((conflict, idx) => (
                <Alert key={idx} variant={conflict.severity === 'error' ? 'destructive' : 'default'}>
                  <AlertDescription>
                    <strong>{conflict.conflict_type.replace('_', ' ').toUpperCase()}:</strong>{' '}
                    {conflict.description}
                    {conflict.suggested_resolution && (
                      <span className="block mt-1 text-xs">
                        Suggestion: {conflict.suggested_resolution}
                      </span>
                    )}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          )}

          {/* Key Factors */}
          {schedule.context_used.key_factors.length > 0 && (
            <div className="text-sm text-muted-foreground">
              <span className="font-medium">Considered: </span>
              {schedule.context_used.key_factors.join(', ')}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={isConfirming}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={isConfirming}>
            {isConfirming
              ? 'Confirming...'
              : modifications.length > 0
              ? 'Confirm Changes'
              : 'Approve Schedule'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

interface DayColumnProps {
  date: string;
  blocks: TimeblockPreview[];
  formatTime: (iso: string) => string;
  formatDate: (iso: string) => string;
  getBlockTypeColor: (type: string) => string;
}

const DayColumn: React.FC<DayColumnProps> = ({
  date,
  blocks,
  formatTime,
  formatDate,
  getBlockTypeColor,
}) => {
  return (
    <div className="space-y-2">
      <div className="font-medium text-sm text-center pb-2 border-b">
        {formatDate(date)}
      </div>
      <div className="space-y-2">
        {blocks.map((block, idx) => (
          <div
            key={idx}
            className={`${getBlockTypeColor(
              block.block_type
            )} text-white rounded-md p-2 text-xs shadow-sm`}
          >
            <div className="font-medium truncate">{block.title}</div>
            <div className="flex items-center gap-1 mt-1 opacity-90">
              <Clock className="h-3 w-3" />
              <span>
                {formatTime(block.start_time)} - {formatTime(block.end_time)}
              </span>
            </div>
            <div className="mt-1 text-[10px] opacity-75">
              {block.duration_minutes} min
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
