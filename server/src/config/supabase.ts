import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';

dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL || '';
const supabaseKey = process.env.SUPABASE_SERVICE_KEY || '';

// Only warn in development, don't exit
if (!supabaseUrl || !supabaseKey) {
  console.warn('Supabase URL or key not found in environment variables. Database features will be disabled.');
}

// Create Supabase client only if credentials are available
const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null;

export default supabase; 