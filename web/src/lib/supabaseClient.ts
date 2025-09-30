import { createClient } from '@supabase/supabase-js';
import { ENV } from './utils/constants';

// Check if Supabase credentials are available
const hasSupabaseConfig = ENV.SUPABASE_URL && ENV.SUPABASE_ANON_KEY && 
  ENV.SUPABASE_URL !== 'https://placeholder.supabase.co' && 
  ENV.SUPABASE_ANON_KEY !== 'placeholder_key';

if (!hasSupabaseConfig) {
  console.warn(
    '⚠️ Supabase configuration missing or using placeholder values. ' +
    'Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file. ' +
    'Authentication features will not work until configured.'
  );
}

// Initialize the Supabase client for web
export const supabaseClient = createClient(
  ENV.SUPABASE_URL || 'https://placeholder.supabase.co',
  ENV.SUPABASE_ANON_KEY || 'placeholder_key',
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
    // Enable realtime for web
    realtime: {
      params: {
        eventsPerSecond: 10,
      },
    },
  }
);

export default supabaseClient;