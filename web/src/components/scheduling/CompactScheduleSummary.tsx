import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, Check, X, Eye } from 'lucide-react';

interface CompactSummary {
  summary_text: string;
  key_highlights: string[];
  next_steps: string;
}

interface SchedulePlan {
  rationale: string;
  confidence: number;
  conflicts: unknown[];
  timeblocks: unknown[];
}

interface SchedulePreviewData {
  compact_summary: CompactSummary;
  schedule: SchedulePlan;
}

interface SchedulingGate {
  gate_token: string;
  preview_data: SchedulePreviewData;
}

interface CompactScheduleSummaryProps {
  gate: SchedulingGate;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  onViewFull?: () => void;
}

export const CompactScheduleSummary: React.FC<CompactScheduleSummaryProps> = ({
  gate,
  onConfirm,
  onCancel,
  onViewFull,
}) => {
  const [isConfirming, setIsConfirming] = useState(false);

  const handleConfirm = async () => {
    setIsConfirming(true);
    try {
      await onConfirm();
    } finally {
      setIsConfirming(false);
    }
  };

  const { compact_summary, schedule } = gate.preview_data;

  return (
    <div className="border rounded-lg p-4 bg-muted/50 space-y-3">
      {/* Header with confidence badge */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-sm">Schedule Ready</span>
        </div>
        <Badge variant={schedule.confidence >= 0.7 ? 'default' : 'secondary'} className="text-xs">
          {Math.round(schedule.confidence * 100)}% match
        </Badge>
      </div>

      {/* Rationale */}
      <p className="text-sm leading-relaxed">{schedule.rationale}</p>

      {/* Summary */}
      <div className="space-y-2">
        <p className="font-medium text-sm">{compact_summary.summary_text}</p>
        {compact_summary.key_highlights.length > 0 && (
          <ul className="text-sm text-muted-foreground space-y-1 ml-4">
            {compact_summary.key_highlights.map((highlight, idx) => (
              <li key={idx} className="list-disc">
                {highlight}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Conflicts warning */}
      {schedule.conflicts.length > 0 && (
        <div className="text-xs text-amber-600 dark:text-amber-500 flex items-center gap-1">
          <span className="font-medium">
            ⚠️ {schedule.conflicts.length} adjustment{schedule.conflicts.length !== 1 ? 's' : ''}{' '}
            recommended
          </span>
        </div>
      )}

      {/* Next steps */}
      <p className="text-sm text-muted-foreground">{compact_summary.next_steps}</p>

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        <Button
          size="sm"
          onClick={handleConfirm}
          disabled={isConfirming}
          className="flex items-center gap-1"
        >
          <Check className="h-3 w-3" />
          {isConfirming ? 'Confirming...' : 'Approve'}
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={onCancel}
          disabled={isConfirming}
          className="flex items-center gap-1"
        >
          <X className="h-3 w-3" />
          Cancel
        </Button>
        {onViewFull && (
          <Button
            size="sm"
            variant="ghost"
            onClick={onViewFull}
            className="flex items-center gap-1"
          >
            <Eye className="h-3 w-3" />
            View Calendar
          </Button>
        )}
      </div>
    </div>
  );
};
