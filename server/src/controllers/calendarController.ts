import { Request, Response } from 'express';
import { google } from 'googleapis';
import { getOAuth2Client } from '../config/google';
import supabase from '../config/supabase';

/**
 * Helper function to get a configured OAuth client for a user
 */
async function getUserOAuthClient(userId: string) {
  // Get user's tokens
  const { data, error } = await supabase
    .from('calendar_connections')
    .select('*')
    .eq('user_id', userId)
    .eq('provider', 'google')
    .single();
  
  if (error || !data) {
    throw new Error('Calendar connection not found');
  }
  
  // Check if token is expired and refresh if needed
  const isExpired = data.expires_at ? new Date(data.expires_at) <= new Date() : true;
  const userOAuth2Client = getOAuth2Client();
  
  if (isExpired && data.refresh_token) {
    // Set refresh token
    userOAuth2Client.setCredentials({
      refresh_token: data.refresh_token
    });
    
    try {
      // Refresh the access token
      const refreshResponse = await userOAuth2Client.refreshAccessToken();
      const tokens = refreshResponse.credentials;
      
      // Update tokens in database
      const { error: updateError } = await supabase
        .from('calendar_connections')
        .update({
          access_token: tokens.access_token,
          expires_at: tokens.expiry_date ? new Date(tokens.expiry_date).toISOString() : null
        })
        .eq('id', data.id);
      
      if (updateError) {
        throw new Error('Failed to update tokens');
      }
      
      return userOAuth2Client;
    } catch (error) {
      console.error('Error refreshing token:', error);
      throw new Error('Failed to refresh token');
    }
  }
  
  // Create and return OAuth client with existing tokens
  userOAuth2Client.setCredentials({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expiry_date: data.expires_at ? new Date(data.expires_at).getTime() : undefined
  });
  
  return userOAuth2Client;
}

/**
 * Get upcoming calendar events for a user
 */
export const getUpcomingEvents = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const { maxResults = '10', timeMin = new Date().toISOString() } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    try {
      // Get OAuth client for this user
      const auth = await getUserOAuthClient(userId);
      
      // Create calendar client
      const calendar = google.calendar({ version: 'v3', auth });
      
      // List events
      const response = await calendar.events.list({
        calendarId: 'primary',
        timeMin: timeMin as string,
        maxResults: parseInt(maxResults as string, 10),
        singleEvents: true,
        orderBy: 'startTime'
      });
      
      // Format events for response
      const events = response.data.items?.map(event => ({
        id: event.id,
        summary: event.summary,
        description: event.description,
        start: event.start?.dateTime || event.start?.date,
        end: event.end?.dateTime || event.end?.date,
        location: event.location,
        htmlLink: event.htmlLink,
        status: event.status
      })) || [];
      
      res.json({ events });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar API error:', error);
    res.status(500).json({ error: 'Failed to fetch calendar events' });
  }
};

/**
 * Get calendar connection status for a user
 */
export const getConnectionStatus = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Get connection data
    const { data, error } = await supabase
      .from('calendar_connections')
      .select('provider, email, created_at, expires_at')
      .eq('user_id', userId);
    
    if (error) {
      return res.status(500).json({ error: 'Failed to get connection status' });
    }
    
    if (!data || data.length === 0) {
      return res.json({ connected: false, providers: [] });
    }
    
    const providers = data.map(conn => ({
      provider: conn.provider,
      email: conn.email,
      connectedAt: conn.created_at,
      expiresAt: conn.expires_at
    }));
    
    res.json({ 
      connected: true, 
      providers 
    });
    
  } catch (error) {
    console.error('Error checking connection status:', error);
    res.status(500).json({ error: 'Failed to check connection status' });
  }
}; 