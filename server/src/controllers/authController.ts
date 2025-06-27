import { Request, Response } from 'express';
import supabase from '../config/supabase';
import { userProfileService } from '../services/userProfileService';

export const createUserRecord = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  const { userId, email } = req.body;

  if (!userId || !email) {
    return res.status(400).json({ error: 'User ID and email are required' });
  }

  try {
    // Create user record in our database
    const { data, error } = await supabase
      .from('users')
      .insert([{
        id: userId,
        email,
        subscription_status: 'free',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }])
      .select()
      .single();

    if (error) {
      // If the error is a unique violation, the user might already exist
      if (error.code === '23505') { // PostgreSQL unique violation code
        return res.status(200).json({ message: 'User already exists' });
      }
      console.error('Error creating user record:', error);
      return res.status(500).json({ error: 'Failed to create user record' });
    }

    res.status(201).json(data);
  } catch (error) {
    console.error('Error in createUserRecord:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateUserProfile = async (req: Request, res: Response) => {
  const { userId } = req.params;
  const updates = req.body;

  if (!userId) {
    return res.status(400).json({ error: 'User ID is required' });
  }

  try {
    // Use the userProfileService for comprehensive profile updates with caching
    const updatedProfile = await userProfileService.updateUserProfile(userId, updates);

    if (!updatedProfile) {
      return res.status(404).json({ error: 'User not found or update failed' });
    }

    console.log(`✅ User profile updated for user ${userId}:`, Object.keys(updates));

    res.status(200).json(updatedProfile);
  } catch (error) {
    console.error('Error in updateUserProfile:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getUserProfile = async (req: Request, res: Response) => {
  const { userId } = req.params;

  if (!userId) {
    return res.status(400).json({ error: 'User ID is required' });
  }

  try {
    // Use the userProfileService for cached profile access
    const userProfile = await userProfileService.getUserProfile(userId);

    if (!userProfile) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.status(200).json(userProfile);
  } catch (error) {
    console.error('Error in getUserProfile:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}; 