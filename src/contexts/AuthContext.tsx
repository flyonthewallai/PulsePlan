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
      console.log('🔄 Refreshing auth state...');
      const { session, error: sessionError } = await getSession();
      
      if (sessionError) {
        console.error('Error refreshing session:', sessionError);
        setError('Failed to refresh authentication session');
        setSession(null);
        setUser(null);
        console.log('🔄 Auth state set to unauthenticated due to error');
      } else {
        console.log('🔄 Auth refresh result:', { 
          hasSession: !!session, 
          userEmail: session?.user?.email || 'none',
          sessionKeys: session ? Object.keys(session) : []
        });
        setSession(session);
        setUser(session?.user ?? null);
        setError(null);
        console.log('🔄 Auth state updated:', {
          hasUser: !!(session?.user),
          userEmail: session?.user?.email || 'none'
        });
      }
    } catch (error) {
      console.error('Error refreshing auth:', error);
      setError('Authentication refresh failed');
      setSession(null);
      setUser(null);
      console.log('🔄 Auth state set to unauthenticated due to exception');
    }
  };

  // Navigation logic in auth context
  useEffect(() => {
    if (loading) {
      console.log('⏳ Auth still loading, skipping navigation...');
      return;
    }

    const isInAuthGroup = segments[0] === '(tabs)';
    const isOnAuthPage = segments[0] === 'auth';
    const isOnIndexPage = segments.length === 0;
    
    console.log('🔀 Auth Context Navigation Check:', { 
      hasUser: !!user, 
      isAuthenticated: !!user,
      segments,
      isInAuthGroup,
      isOnAuthPage,
      isOnIndexPage,
      userEmail: user?.email || 'none'
    });

    if (!user) {
      // User not authenticated
      if (isInAuthGroup) {
        console.log('🔒 User not authenticated, redirecting from tabs to auth...');
        router.replace('/auth');
      } else if (!isOnAuthPage && !isOnIndexPage) {
        console.log('🔒 User not authenticated, redirecting to auth...');
        router.replace('/auth');
      } else {
        console.log('👤 User not authenticated but already on auth/index page');
      }
    } else {
      // User is authenticated
      if (!isInAuthGroup) {
        console.log('✅ User authenticated, redirecting to home...');
        router.replace('/(tabs)/home');
      } else {
        console.log('🏠 User authenticated and already in tabs');
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
      try {
        console.log('Getting initial session...');
        await refreshAuth();
      } catch (error) {
        console.error('Error getting initial session:', error);
        setError('Authentication initialization failed');
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    // For now, we'll skip the auth state listener since it's not implemented in our RN client
    // This can be added later with a polling mechanism if needed
    console.log('Auth context initialized with React Native client');
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