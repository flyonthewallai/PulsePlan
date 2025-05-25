import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { Session, User } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabase, getSession, getCurrentUser, resetPassword as supabaseResetPassword, signIn as supabaseSignIn } from '../lib/supabase';
import { API_URL } from '../config/api';

type AuthContextType = {
  user: User | null;
  session: Session | null;
  loading: boolean;
  hasCompletedOnboarding: boolean;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signUp: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<{ error: any }>;
  resetPassword: (email: string) => Promise<{ error: any }>;
  signInWithMagicLink: (email: string) => Promise<{ error: any }>;
  completeOnboarding: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Local storage keys
const USER_STORAGE_KEY = 'pulseplan_user';
const SESSION_STORAGE_KEY = 'pulseplan_session';
const ONBOARDING_STORAGE_KEY = 'pulseplan_onboarding_completed';

// Helper functions for local storage
const clearLocalAuth = async () => {
  try {
    await AsyncStorage.multiRemove([USER_STORAGE_KEY, SESSION_STORAGE_KEY, ONBOARDING_STORAGE_KEY]);
  } catch (error) {
    console.warn('Error clearing local auth storage:', error);
  }
};

const saveLocalAuth = async (user: User | null, session: Session | null) => {
  try {
    if (user && session) {
      await AsyncStorage.multiSet([
        [USER_STORAGE_KEY, JSON.stringify(user)],
        [SESSION_STORAGE_KEY, JSON.stringify(session)]
      ]);
    }
  } catch (error) {
    console.warn('Error saving local auth storage:', error);
  }
};

const checkOnboardingStatus = async (userId: string): Promise<boolean> => {
  try {
    const key = `${ONBOARDING_STORAGE_KEY}_${userId}`;
    const completed = await AsyncStorage.getItem(key);
    return completed === 'true';
  } catch (error) {
    console.warn('Error checking onboarding status:', error);
    return false;
  }
};

const setOnboardingCompleted = async (userId: string): Promise<void> => {
  try {
    await AsyncStorage.setItem(`${ONBOARDING_STORAGE_KEY}_${userId}`, 'true');
  } catch (error) {
    console.warn('Error setting onboarding completed:', error);
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);

  const initializeAuth = useCallback(async () => {
    if (initialized) return;
    
    try {
      // Set a timeout for initialization to prevent hanging
      const initPromise = (async () => {
        const { session: currentSession, error: sessionError } = await getSession();
        if (sessionError) throw sessionError;
        
        setSession(currentSession);
        
        if (currentSession) {
          const { user: currentUser, error: userError } = await getCurrentUser();
          if (userError) throw userError;
          setUser(currentUser);
          
          // Check onboarding status for the user
          if (currentUser) {
            const onboardingCompleted = await checkOnboardingStatus(currentUser.id);
            setHasCompletedOnboarding(onboardingCompleted);
          }
        }
      })();
      
      // Timeout after 10 seconds
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Auth initialization timeout')), 10000)
      );
      
      await Promise.race([initPromise, timeoutPromise]);
    } catch (error) {
      console.warn('Error initializing auth (continuing with logged out state):', error);
      // Reset state on error - user will need to log in
      setSession(null);
      setUser(null);
    } finally {
      setLoading(false);
      setInitialized(true);
    }
  }, [initialized]);

  useEffect(() => {
    let mounted = true;
    let subscription: { unsubscribe: () => void } | null = null;

    const setupAuth = async () => {
      if (!mounted) return;

      try {
        await initializeAuth();

        // Set up auth state change listener
        try {
          const { data: authSubscription } = supabase.auth.onAuthStateChange(
            async (event, newSession) => {
              if (!mounted) return;
              
              try {
                if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
                  const { user: currentUser } = await getCurrentUser();
                  setUser(currentUser);
                  setSession(newSession);
                  
                  // Check onboarding status for newly signed in user
                  if (currentUser) {
                    const onboardingCompleted = await checkOnboardingStatus(currentUser.id);
                    setHasCompletedOnboarding(onboardingCompleted);
                  }
                } else if (event === 'SIGNED_OUT') {
                  setUser(null);
                  setSession(null);
                  setHasCompletedOnboarding(false);
                }
              } catch (error) {
                console.warn('Error handling auth state change:', error);
              }
              setLoading(false);
            }
          );
          
          subscription = authSubscription;
        } catch (error) {
          console.warn('Error setting up auth state listener:', error);
          // Continue without the listener - app will still work
        }
      } catch (error) {
        console.warn('Error setting up auth:', error);
        if (mounted) {
          setLoading(false);
        }
      }
    };

    setupAuth();

    // Cleanup subscription on unmount
    return () => {
      mounted = false;
      if (subscription) {
        subscription.unsubscribe();
      }
    };
  }, [initializeAuth]);

  const value = {
    user,
    session,
    loading,
    hasCompletedOnboarding,
    signIn: async (email: string, password: string) => {
      const { error } = await supabaseSignIn(email, password);
      return { error };
    },
    signUp: async (email: string, password: string) => {
      const { error } = await supabase.auth.signUp({ 
        email, 
        password
      });
      return { error };
    },
    signOut: async () => {
      try {
        // Always clear local state first to ensure logout works
        setUser(null);
        setSession(null);
        
        // Clear local storage
        await clearLocalAuth();
        
        // Try to sign out from Supabase, but don't fail if it doesn't work
        const { error } = await supabase.auth.signOut();
        
        // Log the error but don't throw it - we've already logged out locally
        if (error) {
          console.warn('Supabase signOut error (user still logged out locally):', error);
        }
        
        return { error: null }; // Always return success since local logout worked
      } catch (error) {
        // Even if everything fails, we've cleared local state
        console.warn('SignOut error (user still logged out locally):', error);
        
        // Try to clear local storage as a last resort
        try {
          await clearLocalAuth();
        } catch (storageError) {
          console.warn('Error clearing local storage during failed logout:', storageError);
        }
        
        return { error: null }; // Return success since local logout worked
      }
    },
    resetPassword: async (email: string) => {
      const { error } = await supabaseResetPassword(email);
      return { error };
    },
    signInWithMagicLink: async (email: string) => {
      const { error } = await supabase.auth.api.sendMagicLinkEmail(email);
      return { error };
    },
    completeOnboarding: async () => {
      if (user) {
        await setOnboardingCompleted(user.id);
        setHasCompletedOnboarding(true);
      }
    },
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 