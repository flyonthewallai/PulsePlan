import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { useRouter, useSegments } from 'expo-router';
import { supabaseAuth, onAuthStateChange, getSession } from '@/lib/supabase-rn';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  isAuthenticated: false,
  error: null,
  refreshAuth: async () => {},
});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const router = useRouter();
  const segments = useSegments();
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshAuth = async () => {
    try {
      const { session, error: sessionError } = await getSession();
      
      if (sessionError) {
        console.error('Error refreshing session:', sessionError);
        setError('Failed to refresh authentication session');
        setSession(null);
        setUser(null);
      } else if (!session) {
        setSession(null);
        setUser(null);
        setError(null);
      } else if (!session.user) {
        setSession(null);
        setUser(null);
        setError(null);
      } else {
        // Session is valid - we have a session with user data
        setSession(session);
        setUser(session.user);
        setError(null);
      }
    } catch (error) {
      console.error('Error refreshing auth:', error);
      setError('Authentication refresh failed');
      setSession(null);
      setUser(null);
    }
  };

  // Navigation logic in auth context
  useEffect(() => {
    if (loading) {
      return;
    }

    const isInAuthGroup = segments[0] === '(tabs)';
    const isOnAuthPage = segments[0] === 'auth';
    const isOnIndexPage = segments.length === 0;

    if (!user) {
      // User not authenticated
      if (isInAuthGroup) {
        router.replace('/auth');
      } else if (isOnIndexPage) {
        // If user is on index page and not authenticated, redirect to auth
        setTimeout(() => {
          router.replace('/auth');
        }, 500); // Small delay to ensure auth state is settled
      } else if (!isOnAuthPage) {
        router.replace('/auth');
      }
    } else {
      // User is authenticated
      if (!isInAuthGroup && !isOnIndexPage) {
        router.replace('/(tabs)/home');
      } else if (isOnIndexPage) {
        // Special case: if user is on index page and authenticated, immediately redirect
        setTimeout(() => {
          router.replace('/(tabs)/home');
        }, 100); // Small delay to ensure routing is ready
      }
    }
  }, [user, loading, segments, router]);

  useEffect(() => {
    // Validate Supabase client
    if (!supabaseAuth) {
      console.error('Supabase client not properly initialized');
      setError('Authentication service not available. Please check your configuration.');
      setLoading(false);
      return;
    }

    // Get initial session
    const getInitialSession = async () => {
      setLoading(true);
      
      try {
        await refreshAuth();
      } catch (error) {
        console.error('❌ Error getting initial session:', error);
        setError('Authentication initialization failed');
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    // Set up periodic session refresh to catch any stale sessions
    const refreshInterval = setInterval(() => {
      if (!loading && user) {
        refreshAuth().catch(error => {
          console.error('Periodic refresh failed:', error);
        });
      }
    }, 5 * 60 * 1000); // Refresh every 5 minutes

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  const value = {
    user,
    session,
    loading,
    isAuthenticated: !!user,
    error,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 