import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
import n8nAgentConfig from './n8nAgent';

dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL || '';
const supabaseKey = process.env.SUPABASE_SERVICE_KEY || '';

// Only warn in development, don't exit
if (!supabaseUrl || !supabaseKey) {
  console.warn('Supabase URL or key not found in environment variables. Database features will be disabled.');
}

// Create Supabase client with timeout configurations
const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey, {
      db: {
        schema: 'public',
      },
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
      global: {
        headers: {
          'X-Client-Info': 'pulseplan-server',
        },
      },
      // Configure timeout for database operations
      realtime: {
        timeout: n8nAgentConfig.databaseTimeout,
      },
    })
  : null;

export default supabase; 