import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase, getSession, getCurrentUser, resetPassword as supabaseResetPassword } from '../lib/supabase';

type AuthContextType = {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signUp: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<{ error: any }>;
  resetPassword: (email: string) => Promise<{ error: any }>;
  signInWithMagicLink: (email: string) => Promise<{ error: any }>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  const initializeAuth = useCallback(async () => {
    if (initialized) return;
    
    try {
      const { session: currentSession, error: sessionError } = await getSession();
      if (sessionError) throw sessionError;
      
      setSession(currentSession);
      
      if (currentSession) {
        const { user: currentUser, error: userError } = await getCurrentUser();
        if (userError) throw userError;
        setUser(currentUser);
      }
    } catch (error) {
      console.error('Error initializing auth:', error);
      // Reset state on error
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
        const { data: { subscription: authSubscription } } = supabase.auth.onAuthStateChange(
          async (event, newSession) => {
            if (!mounted) return;
            
            setSession(newSession);
            setUser(newSession?.user ?? null);
            setLoading(false);
          }
        );
        
        subscription = authSubscription;
      } catch (error) {
        console.error('Error setting up auth:', error);
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
    signIn: async (email: string, password: string) => {
      const { error } = await supabase.auth.signIn({ email, password });
      return { error };
    },
    signUp: async (email: string, password: string) => {
      // Sign up without email verification
      const { error } = await supabase.auth.signUp({ 
        email, 
        password,
        options: {
          data: {
            email_confirmed: true // Mark email as confirmed
          }
        }
      });
      return { error };
    },
    signOut: async () => {
      const { error } = await supabase.auth.signOut();
      return { error };
    },
    resetPassword: async (email: string) => {
      const { error } = await supabaseResetPassword(email);
      return { error };
    },
    signInWithMagicLink: async (email: string) => {
      const { error } = await supabase.auth.signIn({
        email,
        options: {
          shouldCreateUser: true
        }
      });
      return { error };
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