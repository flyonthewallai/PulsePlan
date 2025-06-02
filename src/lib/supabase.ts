import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient, SupabaseClient, Session, User } from '@supabase/supabase-js';
import Constants from 'expo-constants';
import { EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY } from '@env';

// Debug: Log environment variables
console.log('Environment variables:', {
  fromEnv: {
    supabaseUrl: EXPO_PUBLIC_SUPABASE_URL,
    supabaseAnonKey: EXPO_PUBLIC_SUPABASE_ANON_KEY,
  }
});

// Initialize Supabase client
const supabaseUrl = EXPO_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = EXPO_PUBLIC_SUPABASE_ANON_KEY;

console.log('Supabase configuration:', {
  supabaseUrl,
  hasAnonKey: !!supabaseAnonKey,
  anonKeyLength: supabaseAnonKey?.length,
});

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase credentials:', { supabaseUrl, supabaseAnonKey });
  throw new Error('Missing Supabase URL or Anon Key. Please check your environment variables.');
}

// Check if we're using the wrong key type
try {
  if (supabaseAnonKey) {
    const payload = JSON.parse(atob(supabaseAnonKey.split('.')[1]));
    console.log('Key payload:', payload);
    if (payload.role === 'service_role') {
      console.error('🚨 CRITICAL: You are using a service_role key! This will NOT work in React Native.');
      console.error('Please update your .env file to use the anon key instead.');
      console.error('Check SUPABASE_SETUP.md for instructions.');
    } else if (payload.role === 'anon') {
      console.log('✅ Correct: Using anon key for client-side authentication.');
    }
  }
} catch (error) {
  console.warn('Could not parse JWT token:', error);
}

// Create a single instance of the Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
    flowType: 'pkce',
  },
  // Completely disable realtime for React Native compatibility
  realtime: {
    params: {
      eventsPerSecond: 0,
    },
    // Use a mock implementation that doesn't try to create WebSocket connections
    encoder: () => '',
    decoder: () => ({}),
  },
  global: {
    headers: {
      'X-Client-Info': 'supabase-js-react-native',
      'X-Supabase-Client': 'react-native',
    },
  },
  // Disable automatic connection attempts
  db: {
    schema: 'public',
  },
});

// Override realtime to prevent any connection attempts
if (supabase.realtime) {
  // Stub out realtime methods to prevent errors
  supabase.realtime.connect = () => Promise.resolve();
  supabase.realtime.disconnect = () => Promise.resolve();
  supabase.realtime.channel = () => ({
    subscribe: () => ({ unsubscribe: () => {} }),
    unsubscribe: () => Promise.resolve(),
    on: () => {},
    off: () => {},
  });
}

// Test the client initialization
console.log('Supabase client initialized:', {
  clientExists: !!supabase,
  authExists: !!supabase.auth,
  methodsExist: {
    getSession: typeof supabase.auth.getSession,
    signInWithPassword: typeof supabase.auth.signInWithPassword,
    signUp: typeof supabase.auth.signUp,
  }
});

// Auth helper functions
export const signUp = async (email: string, password: string, fullName?: string) => {
  try {
    console.log('Attempting sign up for:', email);
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    });
    console.log('Sign up result:', { user: data.user?.email, error: error?.message });
    return { data, error };
  } catch (error) {
    console.error('Sign up error:', error);
    return { data: null, error };
  }
};

export const signIn = async (email: string, password: string) => {
  try {
    console.log('Attempting sign in for:', email);
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    console.log('Sign in result:', { user: data.user?.email, error: error?.message });
    return { data, error };
  } catch (error) {
    console.error('Sign in error:', error);
    return { data: null, error };
  }
};

export const signInWithMagicLink = async (email: string) => {
  try {
    console.log('Attempting magic link for:', email);
    const { data, error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        shouldCreateUser: true,
      },
    });
    console.log('Magic link result:', { error: error?.message });
    return { data, error };
  } catch (error) {
    console.error('Magic link error:', error);
    return { data: null, error };
  }
};

export const signOut = async () => {
  try {
    console.log('Attempting sign out');
    const { error } = await supabase.auth.signOut();
    console.log('Sign out result:', { error: error?.message });
    return { error };
  } catch (error) {
    console.error('Sign out error:', error);
    return { error };
  }
};

export const resetPassword = async (email: string) => {
  try {
    console.log('Attempting password reset for:', email);
    const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: 'pulseplan://reset-password',
    });
    console.log('Password reset result:', { error: error?.message });
    return { data, error };
  } catch (error) {
    console.error('Password reset error:', error);
    return { data: null, error };
  }
};

export const updatePassword = async (newPassword: string) => {
  try {
    console.log('Attempting password update');
    const { data, error } = await supabase.auth.updateUser({
      password: newPassword,
    });
    console.log('Password update result:', { error: error?.message });
    return { data, error };
  } catch (error) {
    console.error('Password update error:', error);
    return { data: null, error };
  }
};

export const getCurrentUser = async () => {
  try {
    const { data: { user }, error } = await supabase.auth.getUser();
    console.log('Get current user result:', { user: user?.email, error: error?.message });
    return { user, error };
  } catch (error) {
    console.error('Get current user error:', error);
    return { user: null, error };
  }
};

export const getSession = async () => {
  try {
    const { data: { session }, error } = await supabase.auth.getSession();
    console.log('Get session result:', { 
      hasSession: !!session, 
      user: session?.user?.email, 
      error: error?.message 
    });
    return { session, error };
  } catch (error) {
    console.error('Get session error:', error);
    return { session: null, error };
  }
};

// Auth state listener
const setupAuthListener = () => {
  if (!supabase) {
    console.error('Supabase client not initialized');
    return;
  }
  
  supabase.auth.onAuthStateChange((event, session) => {
    // Handle auth state changes if needed in web context
  });
}; 