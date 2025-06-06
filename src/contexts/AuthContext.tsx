import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { useRouter, useSegments } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabaseAuth, onAuthStateChange, getSession } from '@/lib/supabase-rn';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  refreshAuth: () => Promise<void>;
  needsOnboarding: boolean;
  markOnboardingComplete: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  isAuthenticated: false,
  error: null,
  refreshAuth: async () => {},
  needsOnboarding: false,
  markOnboardingComplete: async () => {},
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

const ONBOARDING_KEY = 'onboarding_completed';

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const router = useRouter();
  const segments = useSegments();
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  const checkOnboardingStatus = async (userId: string) => {
    try {
      const onboardingData = await AsyncStorage.getItem(`${ONBOARDING_KEY}_${userId}`);
      return onboardingData === 'true';
    } catch (error) {
      console.error('Error checking onboarding status:', error);
      return false;
    }
  };

  const markOnboardingComplete = async () => {
    if (!user?.id) return;
    
    try {
      await AsyncStorage.setItem(`${ONBOARDING_KEY}_${user.id}`, 'true');
      setNeedsOnboarding(false);
      console.log('✅ Onboarding marked as complete');
    } catch (error) {
      console.error('Error marking onboarding complete:', error);
    }
  };

  const refreshAuth = async () => {
    console.log('🔄 AuthContext: Starting refreshAuth...');
    try {
      const { session, error: sessionError } = await getSession();
      console.log('📊 AuthContext: Session check result:', {
        hasSession: !!session,
        hasUser: !!session?.user,
        userEmail: session?.user?.email,
        error: sessionError?.message
      });
      
      if (sessionError) {
        console.error('❌ AuthContext: Error refreshing session:', sessionError);
        setError('Failed to refresh authentication session');
        setSession(null);
        setUser(null);
        setNeedsOnboarding(false);
        console.log('🚪 AuthContext: Cleared user state due to session error');
      } else if (!session) {
        console.log('🚪 AuthContext: No session found, clearing user state');
        setSession(null);
        setUser(null);
        setError(null);
        setNeedsOnboarding(false);
      } else if (!session.user) {
        console.log('🚪 AuthContext: Session exists but no user, clearing state');
        setSession(null);
        setUser(null);
        setError(null);
        setNeedsOnboarding(false);
      } else {
        // Session is valid - we have a session with user data
        console.log('✅ AuthContext: Valid session found, updating user state');
        setSession(session);
        setUser(session.user);
        setError(null);
        
        // Check if user needs onboarding
        const hasCompletedOnboarding = await checkOnboardingStatus(session.user.id);
        setNeedsOnboarding(!hasCompletedOnboarding);
        
        console.log('🔍 AuthContext: Auth refresh complete:', {
          userId: session.user.id,
          email: session.user.email,
          needsOnboarding: !hasCompletedOnboarding
        });
      }
    } catch (error) {
      console.error('❌ AuthContext: Unexpected error refreshing auth:', error);
      setError('Authentication refresh failed');
      setSession(null);
      setUser(null);
      setNeedsOnboarding(false);
      console.log('🚪 AuthContext: Cleared user state due to unexpected error');
    }
  };

  // Navigation logic in auth context
  useEffect(() => {
    if (loading) {
      return;
    }

    const isInAuthGroup = segments[0] === '(tabs)';
    const isOnAuthPage = segments[0] === 'auth';
    const isOnOnboardingPage = segments[0] === 'onboarding';
    const isOnIndexPage = segments.length === 0;

    console.log('🧭 Navigation check:', {
      segments,
      user: !!user,
      needsOnboarding,
      isInAuthGroup,
      isOnAuthPage,
      isOnOnboardingPage,
      isOnIndexPage
    });

    if (!user) {
      // User not authenticated
      if (isInAuthGroup || isOnOnboardingPage) {
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
      if (needsOnboarding) {
        // User needs onboarding
        if (!isOnOnboardingPage) {
          console.log('🎯 Redirecting to onboarding...');
          router.replace('/onboarding');
        }
      } else {
        // User has completed onboarding
        if (!isInAuthGroup && !isOnIndexPage) {
          console.log('🏠 Redirecting to main app...');
          router.replace('/(tabs)/home');
        } else if (isOnIndexPage || isOnOnboardingPage) {
          // Special case: if user is on index page or onboarding and authenticated with completed onboarding
          setTimeout(() => {
            router.replace('/(tabs)/home');
          }, 100); // Small delay to ensure routing is ready
        }
      }
    }
  }, [user, needsOnboarding, loading, segments, router]);

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
    needsOnboarding,
    markOnboardingComplete,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 