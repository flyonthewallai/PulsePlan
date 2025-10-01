import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionContextProvider } from '@supabase/auth-helpers-react';
import { supabase } from '../lib/supabase';
import { ThemeProvider } from './theme-provider';
import { Toaster } from '../components/ui/toaster';
import { ErrorBoundary } from './error-boundary';
import { TaskSuccessProvider } from '../contexts/TaskSuccessContext';
import { TaskSuccessOverlay } from '../components/TaskSuccessOverlay';
import { WebSocketProvider } from '../contexts/WebSocketContext';
import type { ReactNode } from 'react';

// Create a client instance with optimized settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount, error) => {
        // Don't retry on auth errors
        if (error instanceof Error && error.message.includes('Authentication')) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Custom persistence implementation
const CACHE_KEY = 'pulseplan-query-cache';
const CACHE_EXPIRY_KEY = 'pulseplan-query-cache-expiry';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

// Save cache to localStorage before page unload
const saveCache = () => {
  try {
    const cache = queryClient.getQueryCache().getAll();
    const serializedCache = JSON.stringify(cache.map(query => ({
      queryKey: query.queryKey,
      queryHash: query.queryHash,
      state: query.state,
      dataUpdatedAt: query.state.dataUpdatedAt,
    })));
    
    localStorage.setItem(CACHE_KEY, serializedCache);
    localStorage.setItem(CACHE_EXPIRY_KEY, Date.now().toString());
  } catch (error) {
    console.warn('Failed to save query cache:', error);
  }
};

// Restore cache from localStorage on page load
const restoreCache = () => {
  try {
    const cachedData = localStorage.getItem(CACHE_KEY);
    const cacheExpiry = localStorage.getItem(CACHE_EXPIRY_KEY);
    
    if (!cachedData || !cacheExpiry) return;
    
    const now = Date.now();
    const expiry = parseInt(cacheExpiry);
    
    // Check if cache is expired
    if (now - expiry > CACHE_DURATION) {
      localStorage.removeItem(CACHE_KEY);
      localStorage.removeItem(CACHE_EXPIRY_KEY);
      return;
    }
    
    const cache = JSON.parse(cachedData);
    
    // Restore each query to the cache
    cache.forEach((queryData: any) => {
      if (queryData.state.data !== undefined) {
        queryClient.setQueryData(queryData.queryKey, queryData.state.data);
      }
    });
  } catch (error) {
    console.warn('Failed to restore query cache:', error);
    // Clear corrupted cache
    localStorage.removeItem(CACHE_KEY);
    localStorage.removeItem(CACHE_EXPIRY_KEY);
  }
};

// Set up persistence
if (typeof window !== 'undefined') {
  // Restore cache on initialization
  restoreCache();
  
  // Save cache before page unload
  window.addEventListener('beforeunload', saveCache);
  
  // Save cache periodically (every 5 minutes)
  setInterval(saveCache, 5 * 60 * 1000);
}

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <SessionContextProvider
          supabaseClient={supabase}
          initialSession={null}
        >
          <QueryClientProvider client={queryClient}>
            <ThemeProvider
              attribute="class"
              defaultTheme="dark"
              enableSystem
              disableTransitionOnChange={false}
            >
              <WebSocketProvider>
                <TaskSuccessProvider>
                  {children}
                  <Toaster />
                  <TaskSuccessOverlay />
                </TaskSuccessProvider>
              </WebSocketProvider>
            </ThemeProvider>
          </QueryClientProvider>
        </SessionContextProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export { queryClient };
export default Providers;