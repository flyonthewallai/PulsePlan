import { useQuery } from '@tanstack/react-query';
import type { Timeblock, TimeblocksResponse } from '@/types';
import { API_BASE_URL } from '@/config/api';
import { supabase } from '@/lib/supabase';

// Cache keys for consistent invalidation
export const TIMEBLOCKS_CACHE_KEYS = {
  TIMEBLOCKS: ['timeblocks'],
  TIMEBLOCKS_BY_RANGE: (fromISO: string, toISO: string) => ['timeblocks', 'range', fromISO, toISO],
} as const;

interface UseTimeblocksParams {
  fromISO: string;
  toISO: string;
  enabled?: boolean;
}

interface UseTimeblocksResult {
  items: Timeblock[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

async function fetchTimeblocks(fromISO: string, toISO: string): Promise<Timeblock[]> {
  const url = `${API_BASE_URL}/api/v1/timeblocks?from=${encodeURIComponent(fromISO)}&to=${encodeURIComponent(toISO)}`;

  // Get authentication token from Supabase
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (response.status === 304) {
    return [];
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  const data: TimeblocksResponse = await response.json();

  return data.items || [];
}

export function useTimeblocks({
  fromISO,
  toISO,
  enabled = true,
}: UseTimeblocksParams): UseTimeblocksResult {
  const {
    data: items = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: TIMEBLOCKS_CACHE_KEYS.TIMEBLOCKS_BY_RANGE(fromISO, toISO),
    queryFn: () => fetchTimeblocks(fromISO, toISO),
    enabled: enabled && !!fromISO && !!toISO,
    staleTime: 1 * 60 * 1000, // 1 minute - same as tasks
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: true, // Refetch when returning to tab - same as tasks
    refetchOnMount: true, // Always refetch on mount to catch updates - same as tasks
    retry: 2,
  });

  return {
    items,
    isLoading,
    error: error as Error | null,
    refetch,
  };
}
