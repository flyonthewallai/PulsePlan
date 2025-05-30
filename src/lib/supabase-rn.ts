import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY } from '@env';

// Import only auth-related types and functions to avoid realtime issues
import type { Session, User, AuthError, AuthResponse } from '@supabase/supabase-js';

// Custom minimal Supabase client for React Native
class SupabaseAuthClient {
  private url: string;
  private key: string;
  private headers: Record<string, string>;

  constructor(url: string, key: string) {
    this.url = url;
    this.key = key;
    this.headers = {
      'apikey': key,
      'Authorization': `Bearer ${key}`,
      'Content-Type': 'application/json',
      'X-Client-Info': 'supabase-js-react-native',
    };
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.url}/auth/v1${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.headers,
        ...options.headers,
      },
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || `HTTP ${response.status}`);
    }

    return data;
  }

  async signUp(email: string, password: string, metadata?: any) {
    try {
      console.log('Attempting sign up for:', email);
      const data = await this.request('/signup', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          data: metadata,
        }),
      });
      console.log('Sign up result:', { user: data.user?.email, error: data.error });
      return { data, error: null };
    } catch (error: any) {
      console.error('Sign up error:', error);
      return { data: null, error: { message: error.message } };
    }
  }

  async signInWithPassword(email: string, password: string) {
    try {
      console.log('Attempting sign in for:', email);
      const data = await this.request('/token?grant_type=password', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
        }),
      });
      
      // Structure the response to match Supabase format
      const sessionData = {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        expires_in: data.expires_in,
        expires_at: data.expires_at,
        token_type: data.token_type,
        user: data.user,
      };
      
      // Store session in AsyncStorage
      if (data.access_token && data.user) {
        await AsyncStorage.setItem('supabase.auth.token', JSON.stringify(sessionData));
      }
      
      console.log('Sign in result:', { user: data.user?.email, hasToken: !!data.access_token });
      return { 
        data: { 
          user: data.user, 
          session: sessionData 
        }, 
        error: null 
      };
    } catch (error: any) {
      console.error('Sign in error:', error);
      return { data: null, error: { message: error.message } };
    }
  }

  async signOut() {
    try {
      console.log('Attempting sign out');
      
      // Try to call the logout endpoint, but don't fail if it errors
      try {
        await this.request('/logout', {
          method: 'POST',
        });
        console.log('Server logout successful');
      } catch (serverError) {
        console.warn('Server logout failed (this is okay):', serverError);
        // Continue with local logout even if server logout fails
      }
      
      // Always clear the local session regardless of server response
      await AsyncStorage.removeItem('supabase.auth.token');
      console.log('Local session cleared');
      
      console.log('Sign out completed successfully');
      return { error: null };
    } catch (error: any) {
      console.error('Sign out error:', error);
      
      // Even if there's an error, try to clear local session
      try {
        await AsyncStorage.removeItem('supabase.auth.token');
        console.log('Local session cleared despite error');
      } catch (clearError) {
        console.error('Failed to clear local session:', clearError);
      }
      
      // Return success anyway since we cleared local session
      return { error: null };
    }
  }

  async getSession() {
    try {
      const storedSession = await AsyncStorage.getItem('supabase.auth.token');
      if (!storedSession) {
        console.log('No stored session found');
        return { session: null, error: null };
      }

      const session = JSON.parse(storedSession);
      console.log('Get session result:', { 
        hasSession: !!session, 
        user: session?.user?.email,
        hasAccessToken: !!session?.access_token,
        sessionKeys: Object.keys(session || {})
      });
      return { session, error: null };
    } catch (error: any) {
      console.error('Get session error:', error);
      return { session: null, error: { message: error.message } };
    }
  }

  async getUser() {
    try {
      const { session } = await this.getSession();
      const user = session?.user || null;
      console.log('Get user result:', { user: user?.email });
      return { user, error: null };
    } catch (error: any) {
      console.error('Get user error:', error);
      return { user: null, error: { message: error.message } };
    }
  }
}

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

// Create the custom Supabase client
export const supabaseAuth = new SupabaseAuthClient(supabaseUrl, supabaseAnonKey);

// Export individual auth functions for compatibility
export const signUp = (email: string, password: string, fullName?: string) => 
  supabaseAuth.signUp(email, password, fullName ? { full_name: fullName } : undefined);

export const signIn = (email: string, password: string) => 
  supabaseAuth.signInWithPassword(email, password);

export const signOut = () => supabaseAuth.signOut();

export const getSession = () => supabaseAuth.getSession();

export const getCurrentUser = () => supabaseAuth.getUser();

// Mock functions for features not needed
export const signInWithMagicLink = async (email: string) => {
  console.log('Magic link not implemented in RN client');
  return { data: null, error: { message: 'Magic link not supported in this client' } };
};

export const resetPassword = async (email: string) => {
  console.log('Password reset not implemented in RN client');
  return { data: null, error: { message: 'Password reset not supported in this client' } };
};

export const updatePassword = async (newPassword: string) => {
  console.log('Password update not implemented in RN client');
  return { data: null, error: { message: 'Password update not supported in this client' } };
};

export const onAuthStateChange = (callback: (event: string, session: Session | null) => void) => {
  console.log('Auth state listener not implemented in RN client');
  return { data: { subscription: { unsubscribe: () => {} } } };
}; 