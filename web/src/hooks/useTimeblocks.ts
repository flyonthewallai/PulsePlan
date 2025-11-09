import { useQuery } from '@tanstack/react-query';
import type { Timeblock, TimeblocksResponse } from '../types';
import { API_BASE_URL } from '../config/api';
import { supabase } from '../lib/supabase';

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

  console.log('[useTimeblocks] Fetching timeblocks:', { fromISO, toISO, url });

  // Get authentication token from Supabase
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  if (!token) {
    console.error('[useTimeblocks] No authentication token');
    throw new Error('Not authenticated');
  }

  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  console.log('[useTimeblocks] Response status:', response.status);

  if (response.status === 304) {
    console.log('[useTimeblocks] 304 Not Modified - returning empty');
    return [];
  }

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[useTimeblocks] Error response:', errorText);
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  const data: TimeblocksResponse = await response.json();
  console.log('[useTimeblocks] Received data:', {
    totalItems: data.items?.length || 0,
    items: data.items,
    sources: data.items?.reduce((acc, item) => {
      acc[item.source] = (acc[item.source] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  });

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

  console.log('[useTimeblocks] Hook result:', {
    itemsCount: items.length,
    isLoading,
    error: error?.message,
    fromISO,
    toISO,
  });

  return {
    items,
    isLoading,
    error: error as Error | null,
    refetch,
  };
}
