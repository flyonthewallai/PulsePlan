import { google } from 'googleapis';
import { Client } from '@microsoft/microsoft-graph-client';
import { getOAuth2Client } from '../config/google';
import { getAccessTokenWithRefreshToken } from '../config/microsoft';
import supabase from '../config/supabase';

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  startTime: string;
  endTime: string;
  location?: string;
  attendees?: Array<{
    email: string;
    name?: string;
    responseStatus?: string;
  }>;
  provider: 'google' | 'microsoft';
  externalId: string;
  calendarId: string;
  userId: string;
  status?: string;
  htmlLink?: string;
  organizer?: {
    name?: string;
    email: string;
  };
  isAllDay?: boolean;
  recurrence?: any;
}

export interface SyncOptions {
  userId: string;
  providers: ('google' | 'microsoft')[];
  syncPeriodDays?: number;
  includeAllCalendars?: boolean;
  calendarIds?: string[];
}

export interface SyncResult {
  success: boolean;
  syncedEvents: number;
  errors: string[];
  conflicts: CalendarEvent[];
  summary: {
    google: {
      events: number;
      calendars: number;
    };
    microsoft: {
      events: number;
      calendars: number;
    };
  };
}

/**
 * Calendar Synchronization Service
 * Handles bidirectional sync between PulsePlan and external calendar providers
 */
export class CalendarSyncService {
  
  /**
   * Main sync function that orchestrates the entire synchronization process
   */
  static async syncAllCalendars(options: SyncOptions): Promise<SyncResult> {
    const result: SyncResult = {
      success: false,
      syncedEvents: 0,
      errors: [],
      conflicts: [],
      summary: {
        google: { events: 0, calendars: 0 },
        microsoft: { events: 0, calendars: 0 }
      }
    };

    try {
      if (!supabase) {
        throw new Error('Supabase is not configured');
      }

      // Sync each provider
      for (const provider of options.providers) {
        try {
          if (provider === 'google') {
            const googleResult = await this.syncGoogleCalendar(options);
            result.syncedEvents += googleResult.syncedEvents;
            result.summary.google = googleResult.summary;
          } else if (provider === 'microsoft') {
            const microsoftResult = await this.syncMicrosoftCalendar(options);
            result.syncedEvents += microsoftResult.syncedEvents;
            result.summary.microsoft = microsoftResult.summary;
          }
        } catch (error: any) {
          result.errors.push(`Error syncing ${provider}: ${error.message}`);
        }
      }

      // Resolve conflicts between providers
      const conflicts = await this.resolveConflicts(options.userId);
      result.conflicts = conflicts;

      result.success = result.errors.length === 0;
      
      // Update sync status in database
      await this.updateSyncStatus(options.userId, result);

      return result;
    } catch (error: any) {
      result.errors.push(`Sync process failed: ${error.message}`);
      return result;
    }
  }

  /**
   * Sync Google Calendar events
   */
  private static async syncGoogleCalendar(options: SyncOptions) {
    const { userId, syncPeriodDays = 30, calendarIds } = options;
    
    // Get user's Google tokens
    const { data: connection, error } = await supabase!
      .from('calendar_connections')
      .select('*')
      .eq('user_id', userId)
      .eq('provider', 'google')
      .single();

    if (error || !connection) {
      throw new Error('Google Calendar connection not found');
    }

    // Setup OAuth client
    const auth = getOAuth2Client();
    auth.setCredentials({
      access_token: connection.access_token,
      refresh_token: connection.refresh_token,
      expiry_date: connection.expires_at ? new Date(connection.expires_at).getTime() : undefined
    });

    const calendar = google.calendar({ version: 'v3', auth });

    const now = new Date();
    const futureDate = new Date(now.getTime() + (syncPeriodDays * 24 * 60 * 60 * 1000));

    let syncedEvents = 0;
    const calendarsToSync = calendarIds || ['primary'];

    // Get user's calendars if includeAllCalendars is true
    if (options.includeAllCalendars) {
      const calendarList = await calendar.calendarList.list();
      calendarsToSync.push(...(calendarList.data.items?.map(cal => cal.id).filter((id): id is string => id !== undefined && id !== 'primary') || []));
    }

    for (const calendarId of calendarsToSync) {
      try {
        const response = await calendar.events.list({
          calendarId,
          timeMin: now.toISOString(),
          timeMax: futureDate.toISOString(),
          maxResults: 500,
          singleEvents: true,
          orderBy: 'startTime'
        });

        const events = response.data.items || [];

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
            is_all_day: !event.start?.dateTime,
            recurrence: event.recurrence ? JSON.stringify(event.recurrence) : null,
            synced_at: new Date().toISOString()
          };

          const { error: upsertError } = await supabase!
            .from('calendar_events')
            .upsert(eventData, {
              onConflict: 'user_id,provider,external_id'
            });

          if (!upsertError) {
            syncedEvents++;
          }
        }
      } catch (error) {
        console.error(`Error syncing Google calendar ${calendarId}:`, error);
      }
    }

    return {
      syncedEvents,
      summary: { events: syncedEvents, calendars: calendarsToSync.length }
    };
  }

  /**
   * Sync Microsoft Calendar events
   */
  private static async syncMicrosoftCalendar(options: SyncOptions) {
    const { userId, syncPeriodDays = 30, calendarIds } = options;
    
    // Get user's Microsoft tokens
    const { data: connection, error } = await supabase!
      .from('calendar_connections')
      .select('*')
      .eq('user_id', userId)
      .eq('provider', 'microsoft')
      .single();

    if (error || !connection) {
      throw new Error('Microsoft Calendar connection not found');
    }

    // Setup Graph client
    let accessToken = connection.access_token;
    
    // Refresh token if expired
    if (connection.expires_at && new Date(connection.expires_at) <= new Date()) {
      const tokenResponse = await getAccessTokenWithRefreshToken(connection.refresh_token);
      if (tokenResponse) {
        accessToken = tokenResponse.accessToken;
        
        // Update tokens in database
        await supabase!
          .from('calendar_connections')
          .update({
            access_token: tokenResponse.accessToken,
            expires_at: tokenResponse.expiresOn ? new Date(tokenResponse.expiresOn).toISOString() : null
          })
          .eq('id', connection.id);
      }
    }

    const graphClient = Client.init({
      authProvider: (done) => {
        done(null, accessToken);
      }
    });

    const now = new Date();
    const futureDate = new Date(now.getTime() + (syncPeriodDays * 24 * 60 * 60 * 1000));

    let syncedEvents = 0;
    const calendarsToSync = calendarIds || ['primary'];

    // Get user's calendars if includeAllCalendars is true
    if (options.includeAllCalendars) {
      const calendarList = await graphClient.api('/me/calendars').get();
      calendarsToSync.push(...(calendarList.value?.map((cal: any) => cal.id).filter((id: string) => id !== 'primary') || []));
    }

    for (const calendarId of calendarsToSync) {
      try {
        let apiEndpoint = '/me/calendar/events';
        if (calendarId !== 'primary') {
          apiEndpoint = `/me/calendars/${calendarId}/events`;
        }

        const response = await graphClient
          .api(apiEndpoint)
          .query({
            $top: 500,
            $orderby: 'start/dateTime',
            $filter: `start/dateTime ge '${now.toISOString()}' and start/dateTime le '${futureDate.toISOString()}'`
          })
          .get();

        const events = response.value || [];

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
            recurrence: event.recurrence ? JSON.stringify(event.recurrence) : null,
            synced_at: new Date().toISOString()
          };

          const { error: upsertError } = await supabase!
            .from('calendar_events')
            .upsert(eventData, {
              onConflict: 'user_id,provider,external_id'
            });

          if (!upsertError) {
            syncedEvents++;
          }
        }
      } catch (error) {
        console.error(`Error syncing Microsoft calendar ${calendarId}:`, error);
      }
    }

    return {
      syncedEvents,
      summary: { events: syncedEvents, calendars: calendarsToSync.length }
    };
  }

  /**
   * Resolve conflicts between different calendar providers
   */
  private static async resolveConflicts(userId: string): Promise<CalendarEvent[]> {
    if (!supabase) return [];

    // Find events that might be duplicates across providers
    const { data: events, error } = await supabase
      .from('calendar_events')
      .select('*')
      .eq('user_id', userId)
      .gte('start_time', new Date().toISOString());

    if (error || !events) return [];

    const conflicts: CalendarEvent[] = [];
    const eventGroups = new Map<string, any[]>();

    // Group events by title and approximate time
    events.forEach(event => {
      const key = `${event.title}_${new Date(event.start_time).toDateString()}`;
      if (!eventGroups.has(key)) {
        eventGroups.set(key, []);
      }
      eventGroups.get(key)?.push(event);
    });

    // Find groups with multiple providers (potential conflicts)
    eventGroups.forEach((group) => {
      if (group.length > 1) {
        const providers = new Set(group.map(event => event.provider));
        if (providers.size > 1) {
          // This is a potential conflict
          conflicts.push(...group.map(event => ({
            id: event.id,
            title: event.title,
            description: event.description,
            startTime: event.start_time,
            endTime: event.end_time,
            location: event.location,
            provider: event.provider,
            externalId: event.external_id,
            calendarId: event.calendar_id,
            userId: event.user_id,
            status: event.status,
            htmlLink: event.html_link,
            isAllDay: event.is_all_day
          })));
        }
      }
    });

    return conflicts;
  }

  /**
   * Update sync status in the database
   */
  private static async updateSyncStatus(userId: string, result: SyncResult) {
    if (!supabase) return;

    const syncStatus = {
      user_id: userId,
      last_sync_at: new Date().toISOString(),
      sync_status: result.success ? 'success' : 'partial_failure',
      synced_events_count: result.syncedEvents,
      errors: result.errors.length > 0 ? JSON.stringify(result.errors) : null,
      conflicts_count: result.conflicts.length,
      google_events: result.summary.google.events,
      microsoft_events: result.summary.microsoft.events
    };

    await supabase
      .from('calendar_sync_status')
      .upsert(syncStatus, {
        onConflict: 'user_id'
      });
  }

  /**
   * Get sync status for a user
   */
  static async getSyncStatus(userId: string) {
    if (!supabase) {
      throw new Error('Supabase is not configured');
    }

    const { data, error } = await supabase
      .from('calendar_sync_status')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error || !data) {
      return {
        user_id: userId,
        last_sync_at: null,
        sync_status: 'never_synced',
        synced_events_count: 0,
        errors: null,
        conflicts_count: 0,
        google_events: 0,
        microsoft_events: 0
      };
    }

    return data;
  }

  /**
   * Create a PulsePlan event in external calendars
   */
  static async createEventInExternalCalendars(
    userId: string, 
    event: {
      title: string;
      description?: string;
      startTime: string;
      endTime: string;
      location?: string;
      attendees?: string[];
    },
    providers: ('google' | 'microsoft')[] = ['google', 'microsoft']
  ) {
    const results: any[] = [];

    for (const provider of providers) {
      try {
        if (provider === 'google') {
          const result = await this.createGoogleCalendarEvent(userId, event);
          results.push({ provider: 'google', success: true, eventId: result.id });
        } else if (provider === 'microsoft') {
          const result = await this.createMicrosoftCalendarEvent(userId, event);
          results.push({ provider: 'microsoft', success: true, eventId: result.id });
        }
      } catch (error: any) {
        results.push({ provider, success: false, error: error.message });
      }
    }

    return { success: true, results };
  }

  /**
   * Create event in Google Calendar
   */
  private static async createGoogleCalendarEvent(userId: string, event: any) {
    if (!supabase) {
      throw new Error('Supabase is not configured');
    }

    // Get user's Google tokens
    const { data: connection, error } = await supabase
      .from('calendar_connections')
      .select('*')
      .eq('user_id', userId)
      .eq('provider', 'google')
      .single();

    if (error || !connection) {
      throw new Error('Google Calendar connection not found');
    }

    // Setup OAuth client
    const auth = getOAuth2Client();
    auth.setCredentials({
      access_token: connection.access_token,
      refresh_token: connection.refresh_token,
      expiry_date: connection.expires_at ? new Date(connection.expires_at).getTime() : undefined
    });

    const calendar = google.calendar({ version: 'v3', auth });

    const googleEvent = {
      summary: event.title,
      description: event.description,
      start: {
        dateTime: event.startTime,
        timeZone: 'UTC'
      },
      end: {
        dateTime: event.endTime,
        timeZone: 'UTC'
      },
      location: event.location,
      attendees: event.attendees?.map((email: string) => ({ email }))
    };

    const response = await calendar.events.insert({
      calendarId: 'primary',
      requestBody: googleEvent
    });

    return response.data;
  }

  /**
   * Create event in Microsoft Calendar
   */
  private static async createMicrosoftCalendarEvent(userId: string, event: any) {
    if (!supabase) {
      throw new Error('Supabase is not configured');
    }

    // Get user's Microsoft tokens
    const { data: connection, error } = await supabase
      .from('calendar_connections')
      .select('*')
      .eq('user_id', userId)
      .eq('provider', 'microsoft')
      .single();

    if (error || !connection) {
      throw new Error('Microsoft Calendar connection not found');
    }

    // Setup Graph client
    let accessToken = connection.access_token;
    
    // Refresh token if expired
    if (connection.expires_at && new Date(connection.expires_at) <= new Date()) {
      const tokenResponse = await getAccessTokenWithRefreshToken(connection.refresh_token);
      if (tokenResponse) {
        accessToken = tokenResponse.accessToken;
      }
    }

    const graphClient = Client.init({
      authProvider: (done) => {
        done(null, accessToken);
      }
    });

    const microsoftEvent = {
      subject: event.title,
      bodyPreview: event.description,
      start: {
        dateTime: event.startTime,
        timeZone: 'UTC'
      },
      end: {
        dateTime: event.endTime,
        timeZone: 'UTC'
      },
      location: {
        displayName: event.location
      },
      attendees: event.attendees?.map((email: string) => ({
        emailAddress: { address: email }
      }))
    };

    const response = await graphClient
      .api('/me/calendar/events')
      .post(microsoftEvent);

    return response;
  }
} 