import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SchedulePreviewModal } from './SchedulePreviewModal';
import { CompactScheduleSummary } from './CompactScheduleSummary';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { toast } from '@/lib/toast';

interface SchedulingGate {
  gate_token: string;
  action_id: string;
  display_mode: string;
  preview_data: {
    schedule: {
      timeblocks: unknown[];
      rationale: string;
      conflicts: unknown[];
      confidence: number;
      context_used: {
        hobbies_count: number;
        preferences_count: number;
        confidence_score: number;
        key_factors: string[];
      };
    };
    calendar_view: {
      days: Record<string, unknown[]>;
      range: { start: string; end: string };
      timezone: string;
    };
    compact_summary: {
      summary_text: string;
      key_highlights: string[];
      next_steps: string;
    };
    modification_allowed: boolean;
  };
  expires_at: string;
}

interface Modification {
  timeblock_id: string;
  new_start_time?: string;
  new_duration_minutes?: number;
}

interface ScheduleGateRendererProps {
  gateToken: string;
  displayContext?: 'chat' | 'full-screen' | 'auto';
}

export const ScheduleGateRenderer: React.FC<ScheduleGateRendererProps> = ({
  gateToken,
  displayContext = 'auto',
}) => {
  const queryClient = useQueryClient();
  const [showFullView, setShowFullView] = useState(false);

  // Fetch gate data
  const {
    data: gate,
    isLoading,
    error,
  } = useQuery<SchedulingGate>({
    queryKey: ['gate', gateToken],
    queryFn: async () => {
      const response = await fetch(`/api/v1/gates/${gateToken}/status`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch gate');
      }

      return response.json();
    },
  });

  // Confirm mutation
  const confirmMutation = useMutation({
    mutationFn: async (modifications?: Modification[]) => {
      const response = await fetch(`/api/v1/gates/${gateToken}/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ modifications }),
      });

      if (!response.ok) {
        throw new Error('Failed to confirm gate');
      }

      return response.json();
    },
    onSuccess: () => {
      toast.success('Schedule Confirmed', 'Your schedule has been successfully created!');

      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['timeblocks'] });
    },
    onError: (error: Error) => {
      toast.error('Confirmation Failed', error.message || 'Failed to confirm schedule');
    },
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/v1/gates/${gateToken}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to cancel gate');
      }

      return response.json();
    },
    onSuccess: () => {
      toast.success('Schedule Cancelled', 'The schedule has been cancelled.');
    },
    onError: (error: Error) => {
      toast.error('Cancellation Failed', error.message || 'Failed to cancel schedule');
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-20 w-full" />
        <div className="flex gap-2">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-24" />
        </div>
      </div>
    );
  }

  if (error || !gate) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          {error instanceof Error ? error.message : 'Gate not found or expired'}
        </AlertDescription>
      </Alert>
    );
  }

  // Detect display context
  const effectiveContext =
    displayContext === 'auto' ? detectDisplayContext() : displayContext;

  // Show full view modal if requested or if context is full-screen
  const shouldShowModal =
    showFullView || effectiveContext === 'full-screen' || gate.display_mode === 'visual';

  // Route to appropriate component
  if (shouldShowModal) {
    return (
      <SchedulePreviewModal
        gate={gate}
        onConfirm={(mods) => confirmMutation.mutateAsync(mods)}
        onCancel={() => cancelMutation.mutate()}
        isOpen={true}
      />
    );
  }

  return (
    <CompactScheduleSummary
      gate={gate}
      onConfirm={() => confirmMutation.mutateAsync()}
      onCancel={() => cancelMutation.mutate()}
      onViewFull={() => setShowFullView(true)}
    />
  );
};

/**
 * Detect display context based on viewport and route
 */
function detectDisplayContext(): 'chat' | 'full-screen' {
  // Check viewport size
  const isMobile = window.innerWidth < 768;

  // Check if in chat context
  const isInChat =
    window.location.pathname.includes('/chat') ||
    window.location.pathname.includes('/conversation');

  // Mobile or chat = compact mode
  if (isMobile || isInChat) {
    return 'chat';
  }

  // Desktop planning page = full-screen mode
  return 'full-screen';
}

export default ScheduleGateRenderer;
