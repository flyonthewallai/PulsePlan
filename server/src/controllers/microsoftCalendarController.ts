import { Request, Response } from 'express';
import { Client } from '@microsoft/microsoft-graph-client';
import { getAccessTokenWithRefreshToken } from '../config/microsoft';
import supabase from '../config/supabase';

/**
 * Helper function to get a Microsoft Graph client for a user
 */
async function getGraphClient(userId: string) {
  if (!supabase) { throw new Error("Supabase is not configured on the server."); }
  try {
    // Get user's tokens
    const { data, error } = await supabase
      .from('calendar_connections')
      .select('*')
      .eq('user_id', userId)
      .eq('provider', 'microsoft')
      .single();
    
    if (error || !data) {
      throw new Error('Calendar connection not found');
    }
    
    // Check if token is expired and refresh if needed
    const isExpired = data.expires_at ? new Date(data.expires_at) <= new Date() : true;
    
    let accessToken = data.access_token;
    
    if (isExpired && data.refresh_token) {
      try {
        // Refresh the access token
        const tokenResponse = await getAccessTokenWithRefreshToken(data.refresh_token);
        
        if (!tokenResponse) {
          throw new Error('Failed to refresh token');
        }
        
        accessToken = tokenResponse.accessToken;
        
        // Update tokens in database
        const { error: updateError } = await supabase
          .from('calendar_connections')
          .update({
            access_token: tokenResponse.accessToken,
            refresh_token: (tokenResponse as any).refreshToken || data.refresh_token,
            expires_at: tokenResponse.expiresOn ? new Date(tokenResponse.expiresOn).toISOString() : null
          })
          .eq('id', data.id);
        
        if (updateError) {
          throw new Error('Failed to update tokens');
        }
      } catch (error) {
        console.error('Error refreshing token:', error);
        throw new Error('Failed to refresh token');
      }
    }
    
    // Create and return Graph client with access token
    return Client.init({
      authProvider: (done) => {
        done(null, accessToken);
      }
    });
  } catch (error) {
    console.error('Error getting graph client:', error);
    throw error;
  }
}

/**
 * Get upcoming calendar events for a user
 */
export const getUpcomingEvents = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const { maxResults = '10', startDateTime = new Date().toISOString() } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    try {
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      // ISO format for startDateTime and endDateTime
      const endDateTime = new Date();
      endDateTime.setDate(endDateTime.getDate() + 14); // Default to 2 weeks ahead
      
      // Get events
      const response = await graphClient
        .api('/me/calendar/events')
        .query({
          $count: 'true',
          $top: Number(maxResults),
          $orderby: 'start/dateTime',
          $filter: `start/dateTime ge '${startDateTime}' and start/dateTime le '${endDateTime.toISOString()}'`
        })
        .get();
      
      // Format events for response
      const events = response.value.map(event => ({
        id: event.id,
        summary: event.subject,
        description: event.bodyPreview,
        start: event.start,
        end: event.end,
        location: event.location?.displayName || '',
        webLink: event.webLink,
        status: event.status?.response || '',
        organizer: event.organizer?.emailAddress?.name || ''
      }));
      
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
 * Create a calendar event for a user
 */
export const createCalendarEvent = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const { subject, body, start, end, attendees, location, isOnlineMeeting } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    if (!subject || !start || !end) {
      return res.status(400).json({ error: 'Subject, start, and end are required' });
    }
    
    // Create event object
    const event = {
      subject,
      body: {
        contentType: 'HTML',
        content: body || ''
      },
      start: {
        dateTime: start,
        timeZone: 'UTC'
      },
      end: {
        dateTime: end,
        timeZone: 'UTC'
      },
      isOnlineMeeting: isOnlineMeeting === true
    };
    
    // Add location if provided
    if (location) {
      event['location'] = {
        displayName: location
      };
    }
    
    // Add attendees if provided
    if (attendees && Array.isArray(attendees) && attendees.length > 0) {
      event['attendees'] = attendees.map(attendee => ({
        emailAddress: {
          address: attendee.email,
          name: attendee.name || ''
        },
        type: 'required'
      }));
    }
    
    try {
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      // Create event
      const response = await graphClient
        .api('/me/calendar/events')
        .post(event);
      
      res.status(201).json({ 
        success: true, 
        event: {
          id: response.id,
          webLink: response.webLink
        }
      });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar API error:', error);
    res.status(500).json({ error: 'Failed to create calendar event' });
  }
}; 