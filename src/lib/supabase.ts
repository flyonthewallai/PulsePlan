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
          signUp: async () => ({ data: { user: null, session: null }, error: { message: 'Supabase not configured' } }),
          signInWithPassword: async () => ({ data: { user: null, session: null }, error: { message: 'Supabase not configured' } }),
          signOut: async () => ({ error: null }),
          getSession: async () => ({ data: { session: null }, error: null }),
          getUser: async () => ({ data: { user: null }, error: null }),
          resetPasswordForEmail: async () => ({ data: null, error: { message: 'Supabase not configured' } }),
          updateUser: async () => ({ data: { user: null }, error: { message: 'Supabase not configured' } }),
          onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } }, error: null }),
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
        auth: {
          storage: AsyncStorage,
          autoRefreshToken: true,
          persistSession: true,
          detectSessionInUrl: false,
        },
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

// Supabase v2 Auth helper functions
export const signUp = async (email: string, password: string) => {
  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });
    return { user: data.user, session: data.session, error };
  } catch (error) {
    console.error('SignUp error:', error);
    return { user: null, session: null, error };
  }
};

export const signIn = async (email: string, password: string) => {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { user: data.user, session: data.session, error };
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
    const { data, error } = await supabase.auth.resetPasswordForEmail(email, { 
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
    const { data, error } = await supabase.auth.updateUser({
      password: newPassword,
    });
    return { user: data.user, error };
  } catch (error) {
    console.error('Update password error:', error);
    return { user: null, error };
  }
};

export const getCurrentUser = async () => {
  try {
    const { data, error } = await supabase.auth.getUser();
    return { user: data.user, error };
  } catch (error) {
    console.error('Get current user error:', error);
    return { user: null, error };
  }
};

export const getSession = async () => {
  try {
    const { data, error } = await supabase.auth.getSession();
    return { session: data.session, error };
  } catch (error) {
    console.error('Get session error:', error);
    return { session: null, error };
  }
}; 