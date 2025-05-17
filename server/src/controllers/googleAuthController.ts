import { Request, Response } from 'express';
import { google } from 'googleapis';
import { oauth2Client, SCOPES } from '../config/google';
import supabase from '../config/supabase';

/**
 * Initiates the Google OAuth flow
 */
export const initiateGoogleAuth = (req: Request, res: Response) => {
  try {
    if (!oauth2Client) {
      return res.status(500).json({ error: 'Google OAuth is not configured on the server.' });
    }
    const { userId } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Store userId in state parameter to retrieve it in callback
    const state = Buffer.from(JSON.stringify({ userId })).toString('base64');
    
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES,
      prompt: 'consent', // Force to get refresh token every time
      state: state
    });
    
    res.redirect(authUrl);
  } catch (error) {
    console.error('Error initiating Google auth:', error);
    res.status(500).json({ error: 'Failed to initiate Google authentication' });
  }
};

/**
 * Handles the Google OAuth callback
 */
export const handleGoogleCallback = async (req: Request, res: Response) => {
  const { code, state } = req.query;
  
  if (!code || !state) {
    return res.status(400).json({ error: 'Authorization code or state is missing' });
  }
  
  if (!oauth2Client) {
    return res.status(500).json({ error: 'Google OAuth is not configured on the server.' });
  }
  
  if (!supabase) {
    return res.status(500).json({ error: 'Supabase is not configured on the server.' });
  }
  
  try {
    // Get userId from state
    const { userId } = JSON.parse(Buffer.from(state as string, 'base64').toString());
    
    // Exchange authorization code for tokens
    const { tokens } = await oauth2Client.getToken(code as string);
    
    // Set tokens in client
    oauth2Client.setCredentials(tokens);
    
    // Get user info
    const oauth2 = google.oauth2({ version: 'v2', auth: oauth2Client });
    const userInfo = await oauth2.userinfo.get();
    
    if (!tokens.refresh_token) {
      console.warn('No refresh token received. User may need to revoke access and try again.');
    }
    
    // Store tokens in database
    const { error } = await supabase
      .from('calendar_connections')
      .upsert({
        user_id: userId,
        provider: 'google',
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token || '', // Store empty string if no refresh token
        expires_at: tokens.expiry_date ? new Date(tokens.expiry_date).toISOString() : null,
        scopes: SCOPES,
        email: userInfo.data.email
      }, {
        onConflict: 'user_id,provider'
      });
    
    if (error) {
      console.error('Error storing tokens:', error);
      return res.status(500).json({ error: 'Failed to store connection' });
    }
    
    // Redirect to app with success message
    const clientUrl = process.env.CLIENT_URL || 'http://localhost:8081';
    res.redirect(`${clientUrl}/settings?status=connected&provider=google`);
    
  } catch (error) {
    console.error('OAuth error:', error);
    res.status(500).json({ error: 'Authentication failed' });
  }
};

/**
 * Disconnects Google Calendar
 */
export const disconnectGoogle = async (req: Request, res: Response) => {
  try {
    if (!supabase) {
      return res.status(500).json({ error: 'Supabase is not configured on the server.' });
    }
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Delete the connection from database
    const { error } = await supabase
      .from('calendar_connections')
      .delete()
      .eq('user_id', userId)
      .eq('provider', 'google');
    
    if (error) {
      return res.status(500).json({ error: 'Failed to remove connection' });
    }
    
    res.json({ success: true, message: 'Google Calendar disconnected successfully' });
    
  } catch (error) {
    console.error('Error disconnecting calendar:', error);
    res.status(500).json({ error: 'Failed to disconnect calendar' });
  }
}; 