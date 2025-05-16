import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';
import Constants from 'expo-constants';

// Initialize Supabase client
const supabaseUrl = Constants.expoConfig?.extra?.supabaseUrl || process.env.EXPO_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = Constants.expoConfig?.extra?.supabaseAnonKey || process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase URL or Anon Key. Please check your environment variables.');
}

// Create a single instance of the Supabase client
let supabaseInstance: ReturnType<typeof createClient> | null = null;

export const getSupabaseClient = () => {
  if (!supabaseInstance) {
    console.log('Creating new Supabase client instance...');
    supabaseInstance = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        storage: AsyncStorage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      },
      // Add React Native specific headers
      headers: {
        'X-Client-Info': 'supabase-js-react-native',
      },
    });
    
    // Debug: Log available auth methods
    console.log('Supabase auth methods:', Object.keys(supabaseInstance.auth));
  }
  return supabaseInstance;
};

export const supabase = getSupabaseClient();

// Debug: Log the actual client instance
console.log('Supabase client instance:', {
  hasAuth: !!supabase.auth,
  authMethods: supabase.auth ? Object.keys(supabase.auth) : [],
  version: supabase.supabaseUrl ? 'v1.x' : 'unknown'
});

// Auth helper functions
export const signUp = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });
  return { data, error };
};

export const signIn = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signIn({
    email,
    password,
  });
  return { data, error };
};

export const signOut = async () => {
  const { error } = await supabase.auth.signOut();
  return { error };
};

export const resetPassword = async (email: string) => {
  console.log('Attempting password reset with email:', email);
  // Use a deep link URL that will open your app
  const redirectTo = 'rhythm://reset-password';
  const { data, error } = await supabase.auth.api.resetPasswordForEmail(email, { redirectTo });
  return { data, error };
};

export const updatePassword = async (newPassword: string) => {
  const { data, error } = await supabase.auth.update({
    password: newPassword,
  });
  return { data, error };
};

export const getCurrentUser = () => {
  const user = supabase.auth.user();
  return { user, error: null };
};

export const getSession = () => {
  const session = supabase.auth.session();
  return { session, error: null };
}; 