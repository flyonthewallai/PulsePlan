import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from '../../lib/toast';

interface Modification {
  timeblock_id: string;
  new_start_time?: string;
  new_duration_minutes?: number;
}

interface SchedulingGate {
  gate_token: string;
  action_id: string;
  display_mode: string;
  preview_data: unknown;
  expires_at: string;
}

/**
 * Hook to fetch gate status
 */
export const useGate = (gateToken: string) => {
  return useQuery<SchedulingGate>({
    queryKey: ['gate', gateToken],
    queryFn: async () => {
      const response = await fetch(`/api/v1/gates/${gateToken}/status`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch gate');
      }

      return response.json();
    },
    staleTime: 30000, // 30 seconds
    retry: 1,
  });
};

/**
 * Hook to confirm a gate with optional modifications
 */
export const useConfirmGate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      gateToken,
      modifications,
    }: {
      gateToken: string;
      modifications?: Modification[];
    }) => {
      const response = await fetch(`/api/v1/gates/${gateToken}/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ modifications }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to confirm gate');
      }

      return response.json();
    },
    onSuccess: () => {
      toast.success('Schedule Confirmed', 'Your schedule has been successfully created!');

      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['timeblocks'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
    },
    onError: (error: Error) => {
      toast.error('Confirmation Failed', error.message);
    },
  });
};

/**
 * Hook to cancel a gate
 */
export const useCancelGate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      gateToken,
      reason,
    }: {
      gateToken: string;
      reason?: string;
    }) => {
      const response = await fetch(`/api/v1/gates/${gateToken}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to cancel gate');
      }

      return response.json();
    },
    onSuccess: () => {
      toast.success('Schedule Cancelled', 'The schedule has been cancelled.');

      // Invalidate gate query
      queryClient.invalidateQueries({ queryKey: ['gate'] });
    },
    onError: (error: Error) => {
      toast.error('Cancellation Failed', error.message);
    },
  });
};

/**
 * Combined hook for gate operations
 */
export const useSchedulingGate = (gateToken: string) => {
  const gateQuery = useGate(gateToken);
  const confirmMutation = useConfirmGate();
  const cancelMutation = useCancelGate();

  return {
    gate: gateQuery.data,
    isLoading: gateQuery.isLoading,
    error: gateQuery.error,
    confirm: (modifications?: Modification[]) =>
      confirmMutation.mutateAsync({ gateToken, modifications }),
    cancel: (reason?: string) => cancelMutation.mutateAsync({ gateToken, reason }),
    isConfirming: confirmMutation.isPending,
    isCancelling: cancelMutation.isPending,
  };
};
