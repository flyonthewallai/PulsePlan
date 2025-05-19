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

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase credentials:', { supabaseUrl, supabaseAnonKey });
  throw new Error('Missing Supabase URL or Anon Key. Please check your environment variables.');
}

// Create a single instance of the Supabase client
let supabaseInstance: SupabaseClient | null = null;

export const getSupabaseClient = (): SupabaseClient => {
  if (!supabaseInstance) {
    try {
      console.log('Attempting to create Supabase client with URL:', supabaseUrl);
      supabaseInstance = createClient(supabaseUrl, supabaseAnonKey, {
        // @ts-expect-error: 'auth' is valid in v1 but not in v2 types
        auth: {
          storage: AsyncStorage,
          autoRefreshToken: true,
          persistSession: true,
          detectSessionInUrl: false,
        },
      });
      
      // Test the connection
      void (async () => {
        try {
          await supabaseInstance?.from('_test_connection').select('*').limit(1);
          console.log('Successfully connected to Supabase');
        } catch (error: unknown) {
          console.error('Supabase connection test failed:', {
            error,
            errorMessage: error instanceof Error ? error.message : 'Unknown error',
            errorDetails: (error as any)?.details,
            errorHint: (error as any)?.hint,
            statusCode: (error as any)?.code
          });
        }
      })();
    } catch (error: unknown) {
      console.error('Error creating Supabase client:', {
        error,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        supabaseUrl,
        hasAnonKey: !!supabaseAnonKey
      });
      throw error;
    }
  }
  return supabaseInstance;
};

export const supabase = getSupabaseClient();

// Auth helper functions
export const signUp = async (email: string, password: string): Promise<{ user: User | null; session: Session | null; error: any }> => {
  const { user, session, error } = await supabase.auth.signUp({
    email,
    password,
  });
  return { user, session, error };
};

export const signIn = async (email: string, password: string): Promise<{ user: User | null; session: Session | null; error: any }> => {
  const { user, session, error } = await supabase.auth.signIn({
    email,
    password,
  });
  return { user, session, error };
};

export const signOut = async (): Promise<{ error: any }> => {
  const { error } = await supabase.auth.signOut();
  return { error };
};

export const resetPassword = async (email: string): Promise<{ data: any; error: any }> => {
  // Use a deep link URL that will open your app
  const redirectTo = 'rhythm://reset-password';
  const { data, error } = await supabase.auth.api.resetPasswordForEmail(email, { redirectTo });
  return { data, error };
};

export const updatePassword = async (newPassword: string): Promise<{ user: User | null; error: any }> => {
  const { user, error } = await supabase.auth.update({
    password: newPassword,
  });
  return { user, error };
};

export const getCurrentUser = (): { user: User | null; error: null } => {
  const user = supabase.auth.user();
  return { user, error: null };
};

export const getSession = (): { session: Session | null; error: null } => {
  const session = supabase.auth.session();
  return { session, error: null };
}; 