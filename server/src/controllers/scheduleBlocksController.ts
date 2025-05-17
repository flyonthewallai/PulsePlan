import { Response } from 'express';
import supabase from '../config/supabase';
import { AuthenticatedRequest } from '../middleware/authenticate';

// GET /schedule_blocks
export const getScheduleBlocks = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }
  const userId = req.user?.id;
  const { data, error } = await supabase
    .from('schedule_blocks')
    .select('*')
    .eq('user_id', userId)
    .order('start_time', { ascending: true });
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
};

// POST /schedule_blocks
export const createScheduleBlock = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }
  const userId = req.user?.id;
  const { task_id, start_time, end_time, status, notes } = (req as any).body;
  if (!task_id || !start_time || !end_time) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  const { data, error } = await supabase
    .from('schedule_blocks')
    .insert([{ user_id: userId, task_id, start_time, end_time, status, notes }])
    .select()
    .single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json(data);
};

// PUT /schedule_blocks/:id
export const updateScheduleBlock = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }
  const userId = req.user?.id;
  const { id } = (req as any).params;
  const { start_time, end_time, status, notes } = (req as any).body;
  // Only update if the block belongs to the user
  const { data, error } = await supabase
    .from('schedule_blocks')
    .update({ start_time, end_time, status, notes })
    .eq('id', id)
    .eq('user_id', userId)
    .select()
    .single();
  if (error) return res.status(500).json({ error: error.message });
  if (!data) return res.status(404).json({ error: 'Schedule block not found' });
  res.json(data);
};

// DELETE /schedule_blocks/:id
export const deleteScheduleBlock = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }
  const userId = req.user?.id;
  const { id } = (req as any).params;
  // Only delete if the block belongs to the user
  const { error } = await supabase
    .from('schedule_blocks')
    .delete()
    .eq('id', id)
    .eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.status(204).send();
}; 