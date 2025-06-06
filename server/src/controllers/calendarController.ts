import { Request, Response } from 'express';
import { google } from 'googleapis';
import { getOAuth2Client, isGoogleOAuthConfigured } from '../config/google';
import supabase from '../config/supabase';

/**
 * Helper function to get a configured OAuth client for a user
 */
async function getUserOAuthClient(userId: string) {
  if (!supabase) { throw new Error("Supabase is not configured on the server."); }
  if (!isGoogleOAuthConfigured()) { throw new Error("Google OAuth is not configured on the server."); }
  
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
    const { 
      maxResults = '50', 
      timeMin = new Date().toISOString(),
      timeMax,
      calendarId = 'primary'
    } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    try {
      // Get OAuth client for this user
      const auth = await getUserOAuthClient(userId);
      
      // Create calendar client
      const calendar = google.calendar({ version: 'v3', auth });
      
      const listParams: any = {
        calendarId: calendarId as string,
        timeMin: timeMin as string,
        maxResults: parseInt(maxResults as string, 10),
        singleEvents: true,
        orderBy: 'startTime'
      };
      
      if (timeMax) {
        listParams.timeMax = timeMax as string;
      }
      
      // List events
      const response = await calendar.events.list(listParams);
      
      // Format events for response
      const events = response.data.items?.map(event => ({
        id: event.id,
        summary: event.summary || 'Untitled Event',
        description: event.description || '',
        start: event.start?.dateTime || event.start?.date,
        end: event.end?.dateTime || event.end?.date,
        location: event.location || '',
        htmlLink: event.htmlLink,
        status: event.status,
        attendees: event.attendees?.map(att => ({
          email: att.email,
          displayName: att.displayName,
          responseStatus: att.responseStatus
        })) || [],
        creator: event.creator,
        organizer: event.organizer,
        colorId: event.colorId,
        visibility: event.visibility,
        transparency: event.transparency,
        calendarId: calendarId,
        source: 'google'
      })) || [];
      
      res.json({ events, totalResults: events.length });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      if (error.message === 'Google OAuth is not configured on the server.') {
        return res.status(503).json({ error: 'Google Calendar integration is not available' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar API error:', error);
    res.status(500).json({ error: 'Failed to fetch calendar events' });
  }
};

/**
 * Create a new calendar event
 */
export const createCalendarEvent = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const { 
      summary, 
      description, 
      start, 
      end, 
      location, 
      attendees, 
      calendarId = 'primary',
      reminders,
      colorId,
      visibility = 'default'
    } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    if (!summary || !start || !end) {
      return res.status(400).json({ error: 'Summary, start, and end are required' });
    }
    
    try {
      // Get OAuth client for this user
      const auth = await getUserOAuthClient(userId);
      
      // Create calendar client
      const calendar = google.calendar({ version: 'v3', auth });
      
      // Prepare event object
      const event: any = {
        summary,
        description: description || '',
        start: {
          dateTime: start,
          timeZone: 'UTC'
        },
        end: {
          dateTime: end,
          timeZone: 'UTC'
        },
        location: location || '',
        visibility,
        status: 'confirmed'
      };
      
      // Add attendees if provided
      if (attendees && Array.isArray(attendees) && attendees.length > 0) {
        event.attendees = attendees.map(attendee => ({
          email: typeof attendee === 'string' ? attendee : attendee.email,
          displayName: typeof attendee === 'object' ? attendee.name : undefined
        }));
      }
      
      // Add reminders if provided
      if (reminders) {
        event.reminders = reminders;
      } else {
        event.reminders = {
          useDefault: true
        };
      }
      
      // Add color if provided
      if (colorId) {
        event.colorId = colorId;
      }
      
      // Create the event
      const response = await calendar.events.insert({
        calendarId: calendarId as string,
        requestBody: event,
        sendUpdates: 'all'
      });
      
      res.status(201).json({ 
        success: true, 
        event: {
          id: response.data.id,
          htmlLink: response.data.htmlLink,
          summary: response.data.summary,
          start: response.data.start,
          end: response.data.end
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

/**
 * Update an existing calendar event
 */
export const updateCalendarEvent = async (req: Request, res: Response) => {
  try {
    const { userId, eventId } = req.params;
    const { 
      summary, 
      description, 
      start, 
      end, 
      location, 
      attendees, 
      calendarId = 'primary',
      status
    } = req.body;
    
    if (!userId || !eventId) {
      return res.status(400).json({ error: 'User ID and Event ID are required' });
    }
    
    try {
      // Get OAuth client for this user
      const auth = await getUserOAuthClient(userId);
      
      // Create calendar client
      const calendar = google.calendar({ version: 'v3', auth });
      
      // Get existing event first
      const existingEvent = await calendar.events.get({
        calendarId: calendarId as string,
        eventId: eventId
      });
      
      // Prepare updated event object
      const updatedEvent: any = {
        ...existingEvent.data,
        summary: summary || existingEvent.data.summary,
        description: description !== undefined ? description : existingEvent.data.description,
        location: location !== undefined ? location : existingEvent.data.location,
        status: status || existingEvent.data.status
      };
      
      if (start) {
        updatedEvent.start = {
          dateTime: start,
          timeZone: 'UTC'
        };
      }
      
      if (end) {
        updatedEvent.end = {
          dateTime: end,
          timeZone: 'UTC'
        };
      }
      
      if (attendees) {
        updatedEvent.attendees = attendees.map(attendee => ({
          email: typeof attendee === 'string' ? attendee : attendee.email,
          displayName: typeof attendee === 'object' ? attendee.name : undefined
        }));
      }
      
      // Update the event
      const response = await calendar.events.update({
        calendarId: calendarId as string,
        eventId: eventId,
        requestBody: updatedEvent,
        sendUpdates: 'all'
      });
      
      res.json({ 
        success: true, 
        event: {
          id: response.data.id,
          htmlLink: response.data.htmlLink,
          summary: response.data.summary,
          start: response.data.start,
          end: response.data.end
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
    res.status(500).json({ error: 'Failed to update calendar event' });
  }
};

/**
 * Delete a calendar event
 */
export const deleteCalendarEvent = async (req: Request, res: Response) => {
  try {
    const { userId, eventId } = req.params;
    const { calendarId = 'primary' } = req.query;
    
    if (!userId || !eventId) {
      return res.status(400).json({ error: 'User ID and Event ID are required' });
    }
    
    try {
      // Get OAuth client for this user
      const auth = await getUserOAuthClient(userId);
      
      // Create calendar client
      const calendar = google.calendar({ version: 'v3', auth });
      
      // Delete the event
      await calendar.events.delete({
        calendarId: calendarId as string,
        eventId: eventId,
        sendUpdates: 'all'
      });
      
      res.json({ success: true, message: 'Event deleted successfully' });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar API error:', error);
    res.status(500).json({ error: 'Failed to delete calendar event' });
  }
};

/**
 * Get user's calendars list
 */
export const getCalendarsList = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    try {
      // Get OAuth client for this user
      const auth = await getUserOAuthClient(userId);
      
      // Create calendar client
      const calendar = google.calendar({ version: 'v3', auth });
      
      // Get calendars list
      const response = await calendar.calendarList.list({});
      
      const calendars = response.data.items?.map(cal => ({
        id: cal.id,
        summary: cal.summary,
        description: cal.description,
        primary: cal.primary,
        accessRole: cal.accessRole,
        backgroundColor: cal.backgroundColor,
        foregroundColor: cal.foregroundColor,
        colorId: cal.colorId,
        timeZone: cal.timeZone,
        selected: cal.selected
      })) || [];
      
      res.json({ calendars });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar API error:', error);
    res.status(500).json({ error: 'Failed to fetch calendars list' });
  }
};

/**
 * Sync all events from Google Calendar to PulsePlan
 */
export const syncCalendarEvents = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const { calendarIds, syncPeriodDays = 30 } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    if (!supabase) {
      return res.status(500).json({ error: 'Supabase is not configured on the server' });
    }
    
    try {
      // Get OAuth client for this user
      const auth = await getUserOAuthClient(userId);
      
      // Create calendar client
      const calendar = google.calendar({ version: 'v3', auth });
      
      const now = new Date();
      const futureDate = new Date(now.getTime() + (syncPeriodDays * 24 * 60 * 60 * 1000));
      
      let allSyncedEvents: any[] = [];
      const calendarsToSync = calendarIds || ['primary'];
      
      for (const calendarId of calendarsToSync) {
        // Get events from Google Calendar
        const response = await calendar.events.list({
          calendarId,
          timeMin: now.toISOString(),
          timeMax: futureDate.toISOString(),
          maxResults: 500,
          singleEvents: true,
          orderBy: 'startTime'
        });
        
        const events = response.data.items || [];
        
        // Store events in database
        for (const event of events) {
          const eventData = {
            user_id: userId,
            provider: 'google',
            external_id: event.id,
            calendar_id: calendarId,
            title: event.summary || 'Untitled Event',
            description: event.description || '',
            start_time: event.start?.dateTime || event.start?.date,
            end_time: event.end?.dateTime || event.end?.date,
            location: event.location || '',
            status: event.status,
            html_link: event.htmlLink,
            attendees: event.attendees ? JSON.stringify(event.attendees) : null,
            creator_email: event.creator?.email,
            organizer_email: event.organizer?.email,
            color_id: event.colorId,
            transparency: event.transparency,
            visibility: event.visibility,
            synced_at: new Date().toISOString()
          };
          
          // Upsert event (update if exists, insert if new)
          const { error: upsertError } = await supabase
            .from('calendar_events')
            .upsert(eventData, {
              onConflict: 'user_id,provider,external_id'
            });
          
          if (upsertError) {
            console.error('Error upserting event:', upsertError);
          } else {
            allSyncedEvents.push(eventData);
          }
        }
      }
      
      res.json({ 
        success: true, 
        syncedEvents: allSyncedEvents.length,
        message: `Successfully synced ${allSyncedEvents.length} events from Google Calendar`
      });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar sync error:', error);
    res.status(500).json({ error: 'Failed to sync calendar events' });
  }
};

/**
 * Get calendar connection status for a user
 */
export const getConnectionStatus = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    
    console.log('🔍 getConnectionStatus called with userId:', userId);
    
    if (!userId) {
      console.log('❌ No userId provided');
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    if (!supabase) {
      console.log('❌ Supabase not configured');
      return res.status(500).json({ error: 'Supabase is not configured on the server' });
    }
    
    console.log('📡 Querying calendar_connections table...');
    
    // Get connection data
    const { data, error } = await supabase
      .from('calendar_connections')
      .select('*')
      .eq('user_id', userId);
    
    console.log('📊 Query result:', { data, error });
    
    if (error) {
      console.error('❌ Database error:', error);
      return res.status(500).json({ error: 'Failed to get connection status', details: error.message });
    }
    
    if (!data || data.length === 0) {
      return res.json({ connected: false, providers: [] });
    }
    
    const providers = data.map(conn => ({
      provider: conn.provider,
      email: conn.email || 'Not available',
      connectedAt: conn.created_at,
      expiresAt: conn.expires_at,
      isActive: !conn.expires_at || new Date(conn.expires_at) > new Date()
    }));
    
    res.json({ 
      connected: true, 
      providers 
    });
    
  } catch (error: any) {
    console.error('💥 Unexpected error in getConnectionStatus:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({ error: 'Failed to check connection status', details: error.message });
  }
};

export const getCalendarEvents = async (req: Request, res: Response) => {
  const { userId } = req.params;
  const { start, end } = req.query;
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }
  const { data: connData, error: connError } = await supabase.from("calendar_connections").select("access_token, refresh_token, expires_at, provider").eq("user_id", userId).single();
  if (connError) { return res.status(500).json({ error: "Failed to fetch calendar connection." }); }
  if (!connData) { return res.status(404).json({ error: "No calendar connection found." }); }
  // (Remaining code unchanged) 
  const { data: evtData, error: evtError } = await supabase.from("calendar_events").select("*").eq("user_id", userId).gte("start", start).lte("end", end);
  if (evtError) { return res.status(500).json({ error: "Failed to fetch calendar events." }); }
  res.status(200).json({ events: evtData });
}; 