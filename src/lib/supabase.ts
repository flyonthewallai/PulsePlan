import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient, SupabaseClient, Session, User } from '@supabase/supabase-js';
import Constants from 'expo-constants';
import { EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY } from '@env';

// Get Supabase credentials from environment variables or app.json
const getSupabaseConfig = () => {
  // Try environment variables first
  let supabaseUrl = EXPO_PUBLIC_SUPABASE_URL;
  let supabaseAnonKey = EXPO_PUBLIC_SUPABASE_ANON_KEY;
  
  // Fallback to app.json if env vars are not available
  if (!supabaseUrl || !supabaseAnonKey || supabaseUrl.includes('your-project-ref')) {
    supabaseUrl = Constants.expoConfig?.extra?.supabaseUrl;
    supabaseAnonKey = Constants.expoConfig?.extra?.supabaseAnonKey;
  }
  
  console.log('Supabase configuration:', {
    hasUrl: !!supabaseUrl,
    hasKey: !!supabaseAnonKey,
    urlValid: supabaseUrl && !supabaseUrl.includes('your-project-ref'),
    keyValid: supabaseAnonKey && !supabaseAnonKey.includes('your-supabase-anon-key'),
    source: EXPO_PUBLIC_SUPABASE_URL ? 'env' : 'app.json'
  });
  
  return { supabaseUrl, supabaseAnonKey };
};

const { supabaseUrl, supabaseAnonKey } = getSupabaseConfig();

// Create a single instance of the Supabase client
let supabaseInstance: SupabaseClient | null = null;

export const getSupabaseClient = (): SupabaseClient => {
  if (!supabaseInstance) {
    if (!supabaseUrl || !supabaseAnonKey || 
        supabaseUrl.includes('your-project-ref') || 
        supabaseAnonKey.includes('your-supabase-anon-key')) {
      console.warn('⚠️ Supabase not configured properly. Using mock client for development.');
      
      // Return a mock client for development
      return {
        auth: {
          signUp: async () => ({ user: null, session: null, error: { message: 'Supabase not configured' } }),
          signIn: async () => ({ user: null, session: null, error: { message: 'Supabase not configured' } }),
          signOut: async () => ({ error: null }),
          session: () => null,
          user: () => null,
          api: {
            resetPasswordForEmail: async () => ({ data: null, error: { message: 'Supabase not configured' } }),
          },
          update: async () => ({ user: null, error: { message: 'Supabase not configured' } }),
          onAuthStateChange: () => ({ data: null, unsubscribe: () => {} }),
        },
        from: () => ({
          select: () => ({ data: [], error: null }),
          insert: () => ({ data: [], error: null }),
          update: () => ({ data: [], error: null }),
          delete: () => ({ data: [], error: null }),
        }),
      } as any;
    }

    try {
      console.log('✅ Creating Supabase client with URL:', supabaseUrl);
      supabaseInstance = createClient(supabaseUrl, supabaseAnonKey, {
        localStorage: AsyncStorage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      });
      
      console.log('✅ Supabase client created successfully');
    } catch (error: unknown) {
      console.error('❌ Error creating Supabase client:', {
        error,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        supabaseUrl: supabaseUrl?.substring(0, 30) + '...',
        hasAnonKey: !!supabaseAnonKey
      });
      throw error;
    }
  }
  return supabaseInstance;
};

export const supabase = getSupabaseClient();

// Supabase v1 Auth helper functions
export const signUp = async (email: string, password: string) => {
  try {
    const { user, session, error } = await supabase.auth.signUp({
      email,
      password,
    });
    return { user, session, error };
  } catch (error) {
    console.error('SignUp error:', error);
    return { user: null, session: null, error };
  }
};

export const signIn = async (email: string, password: string) => {
  try {
    const { user, session, error } = await supabase.auth.signIn({
      email,
      password,
    });
    return { user, session, error };
  } catch (error) {
    console.error('SignIn error:', error);
    return { user: null, session: null, error };
  }
};

export const signOut = async () => {
  try {
    const { error } = await supabase.auth.signOut();
    return { error };
  } catch (error) {
    console.error('SignOut error:', error);
    return { error };
  }
};

export const resetPassword = async (email: string) => {
  try {
    const redirectTo = 'rhythm://reset-password';
    const { data, error } = await supabase.auth.api.resetPasswordForEmail(email, { 
      redirectTo 
    });
    return { data, error };
  } catch (error) {
    console.error('Reset password error:', error);
    return { data: null, error };
  }
};

export const updatePassword = async (newPassword: string) => {
  try {
    const { user, error } = await supabase.auth.update({
      password: newPassword,
    });
    return { user, error };
  } catch (error) {
    console.error('Update password error:', error);
    return { user: null, error };
  }
};

export const getCurrentUser = () => {
  try {
    const user = supabase.auth.user();
    return { user, error: null };
  } catch (error) {
    console.error('Get current user error:', error);
    return { user: null, error };
  }
};

export const getSession = () => {
  try {
    const session = supabase.auth.session();
    return { session, error: null };
  } catch (error) {
    console.error('Get session error:', error);
    return { session: null, error };
  }
}; 