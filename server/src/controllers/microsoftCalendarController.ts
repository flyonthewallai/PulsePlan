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
    const { 
      maxResults = '50', 
      startDateTime = new Date().toISOString(),
      endDateTime,
      calendarId
    } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    try {
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      // Default to 2 weeks ahead if no end date specified
      const finalEndDateTime = endDateTime || new Date(Date.now() + (14 * 24 * 60 * 60 * 1000)).toISOString();
      
      // Build API endpoint
      let apiEndpoint = '/me/calendar/events';
      if (calendarId && calendarId !== 'primary') {
        apiEndpoint = `/me/calendars/${calendarId}/events`;
      }
      
      // Get events
      const response = await graphClient
        .api(apiEndpoint)
        .query({
          $count: 'true',
          $top: Number(maxResults),
          $orderby: 'start/dateTime',
          $filter: `start/dateTime ge '${startDateTime}' and start/dateTime le '${finalEndDateTime}'`,
          $select: 'id,subject,bodyPreview,start,end,location,webLink,showAs,sensitivity,isAllDay,isCancelled,organizer,attendees,categories,importance,hasAttachments,recurrence'
        })
        .get();
      
      // Format events for response
      const events = response.value.map(event => ({
        id: event.id,
        summary: event.subject || 'Untitled Event',
        description: event.bodyPreview || '',
        start: event.start,
        end: event.end,
        location: event.location?.displayName || '',
        webLink: event.webLink,
        status: event.showAs || '',
        isAllDay: event.isAllDay || false,
        isCancelled: event.isCancelled || false,
        organizer: event.organizer?.emailAddress ? {
          name: event.organizer.emailAddress.name,
          email: event.organizer.emailAddress.address
        } : null,
        attendees: event.attendees?.map(att => ({
          email: att.emailAddress?.address,
          displayName: att.emailAddress?.name,
          responseStatus: att.status?.response,
          type: att.type
        })) || [],
        categories: event.categories || [],
        importance: event.importance,
        hasAttachments: event.hasAttachments || false,
        sensitivity: event.sensitivity,
        recurrence: event.recurrence,
        calendarId: calendarId || 'primary',
        source: 'microsoft'
      }));
      
      res.json({ events, totalResults: events.length });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      if (error.code === 'InvalidAuthenticationToken') {
        return res.status(401).json({ error: 'Invalid authentication token. Please reconnect your Microsoft account.' });
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
    const { 
      subject, 
      body, 
      start, 
      end, 
      attendees, 
      location, 
      isOnlineMeeting,
      calendarId,
      importance = 'normal',
      categories,
      isAllDay = false,
      sensitivity = 'normal',
      showAs = 'busy',
      recurrence
    } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    if (!subject || !start || !end) {
      return res.status(400).json({ error: 'Subject, start, and end are required' });
    }
    
    // Create event object
    const event: any = {
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
      isOnlineMeeting: isOnlineMeeting === true,
      importance,
      sensitivity,
      showAs,
      isAllDay
    };
    
    // Add location if provided
    if (location) {
      event.location = {
        displayName: location
      };
    }
    
    // Add attendees if provided
    if (attendees && Array.isArray(attendees) && attendees.length > 0) {
      event.attendees = attendees.map(attendee => ({
        emailAddress: {
          address: typeof attendee === 'string' ? attendee : attendee.email,
          name: typeof attendee === 'object' ? attendee.name || attendee.email : attendee
        },
        type: 'required'
      }));
    }
    
    // Add categories if provided
    if (categories && Array.isArray(categories)) {
      event.categories = categories;
    }
    
    // Add recurrence if provided
    if (recurrence) {
      event.recurrence = recurrence;
    }
    
    try {
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      // Build API endpoint
      let apiEndpoint = '/me/calendar/events';
      if (calendarId && calendarId !== 'primary') {
        apiEndpoint = `/me/calendars/${calendarId}/events`;
      }
      
      // Create event
      const response = await graphClient
        .api(apiEndpoint)
        .post(event);
      
      res.status(201).json({ 
        success: true, 
        event: {
          id: response.id,
          webLink: response.webLink,
          subject: response.subject,
          start: response.start,
          end: response.end
        }
      });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      if (error.code === 'InvalidAuthenticationToken') {
        return res.status(401).json({ error: 'Invalid authentication token. Please reconnect your Microsoft account.' });
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
      subject, 
      body, 
      start, 
      end, 
      location, 
      attendees, 
      calendarId,
      importance,
      categories,
      isAllDay,
      sensitivity,
      showAs,
      recurrence
    } = req.body;
    
    if (!userId || !eventId) {
      return res.status(400).json({ error: 'User ID and Event ID are required' });
    }
    
    try {
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      // Build API endpoint
      let apiEndpoint = `/me/calendar/events/${eventId}`;
      if (calendarId && calendarId !== 'primary') {
        apiEndpoint = `/me/calendars/${calendarId}/events/${eventId}`;
      }
      
      // Get existing event first
      const existingEvent = await graphClient
        .api(apiEndpoint)
        .get();
      
      // Prepare updated event object
      const updatedEvent: any = {
        subject: subject !== undefined ? subject : existingEvent.subject,
        importance: importance !== undefined ? importance : existingEvent.importance,
        sensitivity: sensitivity !== undefined ? sensitivity : existingEvent.sensitivity,
        showAs: showAs !== undefined ? showAs : existingEvent.showAs,
        isAllDay: isAllDay !== undefined ? isAllDay : existingEvent.isAllDay
      };
      
      if (body !== undefined) {
        updatedEvent.body = {
          contentType: 'HTML',
          content: body
        };
      }
      
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
      
      if (location !== undefined) {
        updatedEvent.location = location ? {
          displayName: location
        } : null;
      }
      
      if (attendees) {
        updatedEvent.attendees = attendees.map(attendee => ({
          emailAddress: {
            address: typeof attendee === 'string' ? attendee : attendee.email,
            name: typeof attendee === 'object' ? attendee.name || attendee.email : attendee
          },
          type: 'required'
        }));
      }
      
      if (categories) {
        updatedEvent.categories = categories;
      }
      
      if (recurrence !== undefined) {
        updatedEvent.recurrence = recurrence;
      }
      
      // Update the event
      const response = await graphClient
        .api(apiEndpoint)
        .patch(updatedEvent);
      
      res.json({ 
        success: true, 
        event: {
          id: response.id,
          webLink: response.webLink,
          subject: response.subject,
          start: response.start,
          end: response.end
        }
      });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      if (error.code === 'InvalidAuthenticationToken') {
        return res.status(401).json({ error: 'Invalid authentication token. Please reconnect your Microsoft account.' });
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
    const { calendarId } = req.query;
    
    if (!userId || !eventId) {
      return res.status(400).json({ error: 'User ID and Event ID are required' });
    }
    
    try {
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      // Build API endpoint
      let apiEndpoint = `/me/calendar/events/${eventId}`;
      if (calendarId && calendarId !== 'primary') {
        apiEndpoint = `/me/calendars/${calendarId}/events/${eventId}`;
      }
      
      // Delete the event
      await graphClient
        .api(apiEndpoint)
        .delete();
      
      res.json({ success: true, message: 'Event deleted successfully' });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      if (error.code === 'InvalidAuthenticationToken') {
        return res.status(401).json({ error: 'Invalid authentication token. Please reconnect your Microsoft account.' });
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
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      // Get calendars list
      const response = await graphClient
        .api('/me/calendars')
        .query({
          $select: 'id,name,color,isDefaultCalendar,canShare,canViewPrivateItems,canEdit,owner'
        })
        .get();
      
      const calendars = response.value.map(cal => ({
        id: cal.id,
        summary: cal.name,
        name: cal.name,
        color: cal.color,
        isDefault: cal.isDefaultCalendar,
        canShare: cal.canShare,
        canViewPrivateItems: cal.canViewPrivateItems,
        canEdit: cal.canEdit,
        owner: cal.owner,
        accessRole: cal.canEdit ? 'writer' : 'reader'
      }));
      
      res.json({ calendars });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      if (error.code === 'InvalidAuthenticationToken') {
        return res.status(401).json({ error: 'Invalid authentication token. Please reconnect your Microsoft account.' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar API error:', error);
    res.status(500).json({ error: 'Failed to fetch calendars list' });
  }
};

/**
 * Sync all events from Microsoft Calendar to PulsePlan
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
      // Get Graph client for this user
      const graphClient = await getGraphClient(userId);
      
      const now = new Date();
      const futureDate = new Date(now.getTime() + (syncPeriodDays * 24 * 60 * 60 * 1000));
      
      let allSyncedEvents: any[] = [];
      const calendarsToSync = calendarIds || ['primary'];
      
      for (const calendarId of calendarsToSync) {
        // Build API endpoint
        let apiEndpoint = '/me/calendar/events';
        if (calendarId !== 'primary') {
          apiEndpoint = `/me/calendars/${calendarId}/events`;
        }
        
        // Get events from Microsoft Calendar
        const response = await graphClient
          .api(apiEndpoint)
          .query({
            $top: 500,
            $orderby: 'start/dateTime',
            $filter: `start/dateTime ge '${now.toISOString()}' and start/dateTime le '${futureDate.toISOString()}'`,
            $select: 'id,subject,bodyPreview,start,end,location,webLink,showAs,sensitivity,isAllDay,isCancelled,organizer,attendees,categories,importance,hasAttachments,recurrence,createdDateTime,lastModifiedDateTime'
          })
          .get();
        
        const events = response.value || [];
        
        // Store events in database
        for (const event of events) {
          const eventData = {
            user_id: userId,
            provider: 'microsoft',
            external_id: event.id,
            calendar_id: calendarId,
            title: event.subject || 'Untitled Event',
            description: event.bodyPreview || '',
            start_time: event.start?.dateTime,
            end_time: event.end?.dateTime,
            location: event.location?.displayName || '',
            status: event.showAs,
            html_link: event.webLink,
            attendees: event.attendees ? JSON.stringify(event.attendees) : null,
            creator_email: event.organizer?.emailAddress?.address,
            organizer_email: event.organizer?.emailAddress?.address,
            categories: event.categories ? JSON.stringify(event.categories) : null,
            importance: event.importance,
            sensitivity: event.sensitivity,
            is_all_day: event.isAllDay || false,
            is_cancelled: event.isCancelled || false,
            has_attachments: event.hasAttachments || false,
            recurrence: event.recurrence ? JSON.stringify(event.recurrence) : null,
            created_at: event.createdDateTime,
            updated_at: event.lastModifiedDateTime,
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
        message: `Successfully synced ${allSyncedEvents.length} events from Microsoft Calendar`
      });
    } catch (error: any) {
      if (error.message === 'Calendar connection not found') {
        return res.status(404).json({ error: 'Calendar connection not found' });
      }
      if (error.code === 'InvalidAuthenticationToken') {
        return res.status(401).json({ error: 'Invalid authentication token. Please reconnect your Microsoft account.' });
      }
      throw error;
    }
  } catch (error) {
    console.error('Calendar sync error:', error);
    res.status(500).json({ error: 'Failed to sync calendar events' });
  }
}; 