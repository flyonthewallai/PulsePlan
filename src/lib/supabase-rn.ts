import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { createClient } from '@supabase/supabase-js';
import { EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY } from '@env';

// Get Supabase configuration - try environment variables first, then fall back to app.json
const getSupabaseConfig = () => {
  // Try environment variables first
  let supabaseUrl = EXPO_PUBLIC_SUPABASE_URL;
  let supabaseAnonKey = EXPO_PUBLIC_SUPABASE_ANON_KEY;

  // If environment variables are undefined, fall back to app.json
  if (!supabaseUrl || !supabaseAnonKey) {
    console.log('Environment variables not found, falling back to app.json');
    supabaseUrl = Constants.expoConfig?.extra?.supabaseUrl;
    supabaseAnonKey = Constants.expoConfig?.extra?.supabaseAnonKey;
  }

  return { supabaseUrl, supabaseAnonKey };
};

// Debug: Log environment variables
console.log('Environment variables:', {
  fromEnv: {
    supabaseUrl: EXPO_PUBLIC_SUPABASE_URL,
    supabaseAnonKey: EXPO_PUBLIC_SUPABASE_ANON_KEY,
  },
  fromAppJson: {
    supabaseUrl: Constants.expoConfig?.extra?.supabaseUrl,
    supabaseAnonKey: Constants.expoConfig?.extra?.supabaseAnonKey,
  }
});

// Initialize Supabase client
const { supabaseUrl, supabaseAnonKey } = getSupabaseConfig();

console.log('Supabase configuration:', {
  supabaseUrl,
  hasAnonKey: !!supabaseAnonKey,
  anonKeyLength: supabaseAnonKey?.length,
});

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase credentials:', { supabaseUrl, supabaseAnonKey });
  throw new Error('Missing Supabase URL or Anon Key. Please check your environment variables or app.json configuration.');
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

// Create the official Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
    flowType: 'pkce',
  },
  // Disable realtime for React Native compatibility
  realtime: {
    params: {
      eventsPerSecond: 0,
    },
  },
  global: {
    headers: {
      'X-Client-Info': 'supabase-js-react-native',
      'X-Supabase-Client': 'react-native',
    },
  },
});

// Clear all auth data function
export const clearAllAuthData = async () => {
  try {
    console.log('🧹 Clearing all auth data...');
    
    // Clear Supabase session
    await supabase.auth.signOut();
    
    // Clear all possible auth-related keys from AsyncStorage
    const authKeys = [
      'supabase.auth.token',
      'sb-auth-token',
      '@supabase/auth-token',
      'supabaseAuthToken',
      'user_session',
      'auth_session',
    ];
    
    await Promise.all(authKeys.map(key => AsyncStorage.removeItem(key)));
    
    // Clear any cached task data since it's user-specific
    await AsyncStorage.removeItem('cached_tasks');
    await AsyncStorage.removeItem('last_sync_timestamp');
    
    console.log('✅ All auth data cleared successfully');
    return { success: true };
  } catch (error) {
    console.error('❌ Error clearing auth data:', error);
    return { success: false, error };
  }
};

// Debug function - expose globally for browser console access
if (typeof window !== 'undefined') {
  (window as any).clearAuthData = clearAllAuthData;
  (window as any).debugAuth = async () => {
    console.log('🔍 Current auth state:');
    const session = await getSession();
    console.log('Session:', session);
    
    // Check AsyncStorage for auth data
    const authKeys = [
      'supabase.auth.token',
      'sb-auth-token', 
      '@supabase/auth-token',
      'supabaseAuthToken',
      'user_session',
      'auth_session',
    ];
    
    for (const key of authKeys) {
      const value = await AsyncStorage.getItem(key);
      if (value) {
        console.log(`Found cached data for ${key}:`, value.substring(0, 50) + '...');
      }
    }
  };
  console.log('🛠️ Debug functions available:');
  console.log('- window.clearAuthData() - Clear all auth data');
  console.log('- window.debugAuth() - Show current auth state');
}

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
  } catch (error: any) {
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
  } catch (error: any) {
    console.error('Sign in error:', error);
    return { data: null, error };
  }
};

export const signInWithMagicLink = async (email: string) => {
  try {
    console.log('Attempting magic link sign in for:', email);
    const { data, error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        shouldCreateUser: false,
      },
    });
    console.log('Magic link result:', { success: !!data, error: error?.message });
    return { data, error };
  } catch (error: any) {
    console.error('Magic link error:', error);
    return { data: null, error };
  }
};

export const resetPassword = async (email: string) => {
  try {
    console.log('Attempting password reset for:', email);
    const { data, error } = await supabase.auth.resetPasswordForEmail(email);
    console.log('Password reset result:', { success: !!data, error: error?.message });
    return { data, error };
  } catch (error: any) {
    console.error('Password reset error:', error);
    return { data: null, error };
  }
};

export const signOut = async () => {
  try {
    console.log('🚪 Attempting sign out...');
    
    // First, try to sign out from Supabase
    const { error } = await supabase.auth.signOut();
    
    if (error) {
      console.warn('Supabase sign out error (continuing with cleanup):', error.message);
    } else {
      console.log('✅ Supabase sign out successful');
    }
    
    // Always clear all local auth data regardless of Supabase response
    await clearAllAuthData();
    
    console.log('✅ Sign out completed successfully');
    return { error: null };
  } catch (error: any) {
    console.error('❌ Sign out error:', error);
    
    // Even if there's an error, try to clear local data
    await clearAllAuthData();
    
    // Return success since we cleared local data
    return { error: null };
  }
};

export const getCurrentUser = async () => {
  try {
    const { data: { user }, error } = await supabase.auth.getUser();
    console.log('Get current user result:', { user: user?.email, error: error?.message });
    return { user, error };
  } catch (error: any) {
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
  } catch (error: any) {
    console.error('Get session error:', error);
    return { session: null, error };
  }
};

export const onAuthStateChange = (callback: (event: string, session: any) => void) => {
  return supabase.auth.onAuthStateChange(callback);
};

// Export the client for direct usage if needed
export { supabase as supabaseAuth }; 