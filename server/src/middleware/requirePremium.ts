import { Request, Response, NextFunction } from 'express';
import supabase from '../config/supabase';

/**
 * Middleware to protect premium-only routes
 * Verifies that the user has a premium subscription
 */
export const requirePremium = async (req: Request, res: Response, next: NextFunction) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }
  try {
    // Extract user ID from request
    // This assumes the user ID is passed in the request body, query, or params
    const userId = req.body.userId || req.query.userId || req.params.userId;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    // Check if user has premium subscription
    const { data, error } = await supabase
      .from('users')
      .select('subscription_status')
      .eq('id', userId)
      .single();
    
    if (error) {
      console.error('Error checking subscription status:', error);
      return res.status(500).json({ error: 'Failed to verify subscription status' });
    }
    
    // If user doesn't have premium subscription, deny access
    if (!data || data.subscription_status !== 'premium') {
      return res.status(403).json({ 
        error: 'Premium subscription required',
        message: 'This feature requires a premium subscription'
      });
    }
    
    // User has premium subscription, proceed to the route handler
    next();
  } catch (error) {
    console.error('Error in premium middleware:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}; 