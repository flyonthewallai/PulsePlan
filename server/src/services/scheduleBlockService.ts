import supabase from '../config/supabase';

// Helper function to ensure Supabase client is available
const getSupabaseClient = () => {
  if (!supabase) {
    throw new Error('Supabase client is not initialized');
  }
  return supabase;
};

export const getScheduleBlocksForUser = async (userId: string) => {
  const client = getSupabaseClient();
  const { data, error } = await client
    .from('schedule_blocks')
    .select('*')
    .eq('user_id', userId);

  if (error) throw error;
  return data;
};

export const createScheduleBlock = async (userId: string, block: any) => {
  const client = getSupabaseClient();
  const { data, error } = await client
    .from('schedule_blocks')
    .insert([{ ...block, user_id: userId }])
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const updateScheduleBlock = async (userId: string, blockId: string, updates: any) => {
  const client = getSupabaseClient();
  const { data, error } = await client
    .from('schedule_blocks')
    .update(updates)
    .eq('id', blockId)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const deleteScheduleBlock = async (userId: string, blockId: string) => {
  const client = getSupabaseClient();
  const { error } = await client
    .from('schedule_blocks')
    .delete()
    .eq('id', blockId)
    .eq('user_id', userId);

  if (error) throw error;
}; 