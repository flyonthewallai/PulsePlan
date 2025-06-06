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

// OAuth Sign-In Functions
export const signInWithGoogle = async () => {
  try {
    console.log('🔑 Attempting Google OAuth sign in...');
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: 'rhythm://auth/callback',
        queryParams: {
          access_type: 'offline',
          prompt: 'consent',
        },
      },
    });
    
    console.log('Google OAuth result:', { 
      success: !!data, 
      error: error?.message,
      url: data?.url ? 'OAuth URL generated' : 'No URL'
    });
    
    return { data, error };
  } catch (error: any) {
    console.error('❌ Google OAuth error:', error);
    return { data: null, error };
  }
};

export const signInWithMicrosoft = async () => {
  try {
    console.log('🔑 Attempting Microsoft OAuth sign in...');
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'azure',
      options: {
        redirectTo: 'rhythm://auth/callback',
        scopes: 'email profile openid',
      },
    });
    
    console.log('Microsoft OAuth result:', { 
      success: !!data, 
      error: error?.message,
      url: data?.url ? 'OAuth URL generated' : 'No URL'
    });
    
    return { data, error };
  } catch (error: any) {
    console.error('❌ Microsoft OAuth error:', error);
    return { data: null, error };
  }
};

export const signInWithApple = async () => {
  try {
    console.log('🔑 Attempting Apple OAuth sign in...');
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'apple',
      options: {
        redirectTo: 'rhythm://auth/callback',
        scopes: 'email name',
      },
    });
    
    console.log('Apple OAuth result:', { 
      success: !!data, 
      error: error?.message,
      url: data?.url ? 'OAuth URL generated' : 'No URL'
    });
    
    return { data, error };
  } catch (error: any) {
    console.error('❌ Apple OAuth error:', error);
    return { data: null, error };
  }
};

// Helper function to determine if user is new (for onboarding)
export const isNewUser = (user: any): boolean => {
  if (!user) return false;
  
  // Check if user was created recently (within last 5 minutes)
  const createdAt = new Date(user.created_at);
  const now = new Date();
  const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
  
  const isNew = createdAt > fiveMinutesAgo;
  console.log('🔍 User creation check:', {
    email: user.email,
    createdAt: createdAt.toISOString(),
    fiveMinutesAgo: fiveMinutesAgo.toISOString(),
    isNew
  });
  
  return isNew;
};

export const signOut = async () => {
  try {
    console.log('🚪 Starting comprehensive sign out process...');
    console.log('🔍 Current session before logout:');
    
    // Check current session first
    const { session: currentSession } = await getSession();
    console.log('📊 Session details:', {
      hasSession: !!currentSession,
      userEmail: currentSession?.user?.email,
      accessToken: currentSession?.access_token ? 'Present' : 'None',
      refreshToken: currentSession?.refresh_token ? 'Present' : 'None'
    });
    
    // First, try to sign out from Supabase
    console.log('🔄 Calling Supabase signOut...');
    const { error: signOutError } = await supabase.auth.signOut();
    
    if (signOutError) {
      console.warn('⚠️ Supabase sign out error (continuing with cleanup):', signOutError.message);
    } else {
      console.log('✅ Supabase sign out successful');
    }
    
    // Always clear all local auth data regardless of Supabase response
    console.log('🧹 Clearing local auth data...');
    const clearResult = await clearAllAuthData();
    console.log('🗑️ Clear data result:', clearResult);
    
    // Verify session is cleared
    console.log('🔍 Verifying session cleared...');
    const { session: verifySession } = await getSession();
    console.log('📊 Session after logout:', {
      hasSession: !!verifySession,
      userEmail: verifySession?.user?.email || 'None'
    });
    
    console.log('✅ Sign out process completed successfully');
    return { error: null, success: true };
  } catch (error: any) {
    console.error('❌ Unexpected sign out error:', error);
    console.log('🛠️ Attempting emergency cleanup...');
    
    // Even if there's an error, try to clear local data
    try {
      await clearAllAuthData();
      console.log('🛠️ Emergency cleanup successful');
    } catch (cleanupError) {
      console.error('💥 Emergency cleanup failed:', cleanupError);
    }
    
    // Return success since we attempted cleanup
    return { error, success: false };
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