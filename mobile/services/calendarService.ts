import { API_BASE_URL } from '../config/api';
import { Platform } from 'react-native';
import * as Linking from 'expo-linking';

export interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  start: string | { dateTime: string; timeZone?: string };
  end: string | { dateTime: string; timeZone?: string };
  location?: string;
  attendees?: Array<{
    email: string;
    displayName?: string;
    responseStatus?: string;
  }>;
  organizer?: {
    name?: string;
    email: string;
  };
  htmlLink?: string;
  webLink?: string;
  status?: string;
  source: 'google' | 'microsoft';
  calendarId?: string;
  isAllDay?: boolean;
  colorId?: string;
  categories?: string[];
  importance?: string;
  sensitivity?: string;
  recurrence?: any;
}

export interface Calendar {
  id: string;
  summary: string;
  name?: string;
  description?: string;
  primary?: boolean;
  isDefault?: boolean;
  accessRole?: string;
  backgroundColor?: string;
  foregroundColor?: string;
  color?: string;
  canEdit?: boolean;
  canShare?: boolean;
  timeZone?: string;
  selected?: boolean;
}

export interface ConnectionStatus {
  connected: boolean;
  providers: Array<{
    provider: 'google' | 'microsoft';
    email: string;
    connectedAt: string;
    expiresAt?: string;
    isActive: boolean;
  }>;
}

export interface SyncStatus {
  user_id: string;
  last_sync_at: string | null;
  sync_status: 'success' | 'partial_failure' | 'never_synced';
  synced_events_count: number;
  errors: string | null;
  conflicts_count: number;
  google_events: number;
  microsoft_events: number;
}

export interface SyncResult {
  success: boolean;
  syncedEvents: number;
  errors: string[];
  conflicts: CalendarEvent[];
  summary: {
    google: { events: number; calendars: number };
    microsoft: { events: number; calendars: number };
  };
}

export interface CreateEventRequest {
  summary: string;
  description?: string;
  start: string;
  end: string;
  location?: string;
  attendees?: string[] | Array<{ email: string; name?: string }>;
  calendarId?: string;
  isAllDay?: boolean;
  reminders?: any;
  colorId?: string;
  visibility?: string;
  importance?: string;
  categories?: string[];
  sensitivity?: string;
  showAs?: string;
  recurrence?: any;
}

/**
 * Calendar Service
 * Handles all calendar-related operations for both Google and Microsoft calendars
 */
export class CalendarService {
  private static baseUrl = API_BASE_URL;

  /**
   * Authentication Methods
   */

  /**
   * Initiate Google Calendar connection
   */
  static async connectGoogle(userId: string): Promise<void> {
    const url = `${this.baseUrl}/auth/google?userId=${encodeURIComponent(userId)}`;
    
    try {
      // Use Platform.OS to reliably detect environment
      if (Platform.OS === 'web') {
        // Web environment
        console.log('🌐 Using web navigation for Google OAuth');
        if (typeof window !== 'undefined' && window.location) {
          window.location.href = url;
        } else {
          throw new Error('Window location not available');
        }
      } else {
        // React Native environment (iOS/Android) - use Linking API
        console.log('📱 Using React Native Linking for Google OAuth');
        await Linking.openURL(url);
      }
    } catch (error: any) {
      console.error('Error in Google OAuth navigation:', error);
      console.error('Platform.OS:', Platform.OS);
      console.error('Error details:', error?.message || error);
      throw new Error(`Failed to initiate Google Calendar connection: ${error?.message || 'Unknown error'}`);
    }
  }

  /**
   * Initiate Microsoft Calendar connection
   */
  static async connectMicrosoft(userId: string): Promise<void> {
    const url = `${this.baseUrl}/auth/microsoft?userId=${encodeURIComponent(userId)}`;
    
    try {
      // Use Platform.OS to reliably detect environment
      if (Platform.OS === 'web') {
        // Web environment
        console.log('🌐 Using web navigation for Microsoft OAuth');
        if (typeof window !== 'undefined' && window.location) {
          window.location.href = url;
        } else {
          throw new Error('Window location not available');
        }
      } else {
        // React Native environment (iOS/Android) - use Linking API
        console.log('📱 Using React Native Linking for Microsoft OAuth');
        await Linking.openURL(url);
      }
    } catch (error: any) {
      console.error('Error in Microsoft OAuth navigation:', error);
      console.error('Platform.OS:', Platform.OS);
      console.error('Error details:', error?.message || error);
      throw new Error(`Failed to initiate Microsoft Calendar connection: ${error?.message || 'Unknown error'}`);
    }
  }

  /**
   * Disconnect Google Calendar
   */
  static async disconnectGoogle(userId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/auth/google/${userId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to disconnect Google Calendar');
    }

    return response.json();
  }

  /**
   * Disconnect Microsoft Calendar
   */
  static async disconnectMicrosoft(userId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/auth/microsoft/${userId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to disconnect Microsoft Calendar');
    }

    return response.json();
  }

  /**
   * Get connection status
   */
  static async getConnectionStatus(userId: string): Promise<ConnectionStatus> {
    try {
      console.log(`Fetching connection status from: ${this.baseUrl}/calendar/status/${userId}`);
      
      const response = await fetch(`${this.baseUrl}/calendar/status/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      console.log(`Connection status response: ${response.status}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Failed to get connection status: ${response.status} - ${errorText}`);
        throw new Error(`Failed to get connection status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Connection status data:', data);
      return data;
    } catch (error) {
      console.error('Error in getConnectionStatus:', error);
      throw error;
    }
  }

  /**
   * Event Management Methods
   */

  /**
   * Get events from Google Calendar
   */
  static async getGoogleEvents(
    userId: string,
    options: {
      maxResults?: number;
      timeMin?: string;
      timeMax?: string;
      calendarId?: string;
    } = {}
  ): Promise<{ events: CalendarEvent[]; totalResults: number }> {
    const params = new URLSearchParams();
    if (options.maxResults) params.append('maxResults', options.maxResults.toString());
    if (options.timeMin) params.append('timeMin', options.timeMin);
    if (options.timeMax) params.append('timeMax', options.timeMax);
    if (options.calendarId) params.append('calendarId', options.calendarId);

    const response = await fetch(`${this.baseUrl}/calendar/google/events/${userId}?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch Google Calendar events');
    }

    return response.json();
  }

  /**
   * Get events from Microsoft Calendar
   */
  static async getMicrosoftEvents(
    userId: string,
    options: {
      maxResults?: number;
      startDateTime?: string;
      endDateTime?: string;
      calendarId?: string;
    } = {}
  ): Promise<{ events: CalendarEvent[]; totalResults: number }> {
    const params = new URLSearchParams();
    if (options.maxResults) params.append('maxResults', options.maxResults.toString());
    if (options.startDateTime) params.append('startDateTime', options.startDateTime);
    if (options.endDateTime) params.append('endDateTime', options.endDateTime);
    if (options.calendarId) params.append('calendarId', options.calendarId);

    const response = await fetch(`${this.baseUrl}/calendar/microsoft/events/${userId}?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch Microsoft Calendar events');
    }

    return response.json();
  }

  /**
   * Get all events from connected calendars
   */
  static async getAllEvents(
    userId: string,
    options: {
      maxResults?: number;
      timeMin?: string;
      timeMax?: string;
      providers?: ('google' | 'microsoft')[];
    } = {}
  ): Promise<CalendarEvent[]> {
    const { providers = ['google', 'microsoft'] } = options;
    const allEvents: CalendarEvent[] = [];

    const promises = providers.map(async (provider) => {
      try {
        if (provider === 'google') {
          const result = await this.getGoogleEvents(userId, {
            maxResults: options.maxResults,
            timeMin: options.timeMin,
            timeMax: options.timeMax,
          });
          return result.events;
        } else if (provider === 'microsoft') {
          const result = await this.getMicrosoftEvents(userId, {
            maxResults: options.maxResults,
            startDateTime: options.timeMin,
            endDateTime: options.timeMax,
          });
          return result.events;
        }
        return [];
      } catch (error) {
        console.error(`Error fetching ${provider} events:`, error);
        return [];
      }
    });

    const results = await Promise.all(promises);
    results.forEach(events => allEvents.push(...events));

    // Sort events by start time
    return allEvents.sort((a, b) => {
      const startA = typeof a.start === 'string' ? a.start : a.start.dateTime;
      const startB = typeof b.start === 'string' ? b.start : b.start.dateTime;
      return new Date(startA).getTime() - new Date(startB).getTime();
    });
  }

  /**
   * Create event in Google Calendar
   */
  static async createGoogleEvent(
    userId: string,
    event: CreateEventRequest
  ): Promise<{ success: boolean; event: any }> {
    const response = await fetch(`${this.baseUrl}/calendar/google/events/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(event),
    });

    if (!response.ok) {
      throw new Error('Failed to create Google Calendar event');
    }

    return response.json();
  }

  /**
   * Create event in Microsoft Calendar
   */
  static async createMicrosoftEvent(
    userId: string,
    event: CreateEventRequest
  ): Promise<{ success: boolean; event: any }> {
    const response = await fetch(`${this.baseUrl}/calendar/microsoft/events/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subject: event.summary,
        body: event.description,
        start: event.start,
        end: event.end,
        location: event.location,
        attendees: event.attendees,
        calendarId: event.calendarId,
        importance: event.importance,
        categories: event.categories,
        isAllDay: event.isAllDay,
        sensitivity: event.sensitivity,
        showAs: event.showAs,
        recurrence: event.recurrence,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to create Microsoft Calendar event');
    }

    return response.json();
  }

  /**
   * Update event in Google Calendar
   */
  static async updateGoogleEvent(
    userId: string,
    eventId: string,
    event: Partial<CreateEventRequest>
  ): Promise<{ success: boolean; event: any }> {
    const response = await fetch(`${this.baseUrl}/calendar/google/events/${userId}/${eventId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(event),
    });

    if (!response.ok) {
      throw new Error('Failed to update Google Calendar event');
    }

    return response.json();
  }

  /**
   * Update event in Microsoft Calendar
   */
  static async updateMicrosoftEvent(
    userId: string,
    eventId: string,
    event: Partial<CreateEventRequest>
  ): Promise<{ success: boolean; event: any }> {
    const response = await fetch(`${this.baseUrl}/calendar/microsoft/events/${userId}/${eventId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subject: event.summary,
        body: event.description,
        start: event.start,
        end: event.end,
        location: event.location,
        attendees: event.attendees,
        calendarId: event.calendarId,
        importance: event.importance,
        categories: event.categories,
        isAllDay: event.isAllDay,
        sensitivity: event.sensitivity,
        showAs: event.showAs,
        recurrence: event.recurrence,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to update Microsoft Calendar event');
    }

    return response.json();
  }

  /**
   * Delete event from Google Calendar
   */
  static async deleteGoogleEvent(
    userId: string,
    eventId: string,
    calendarId: string = 'primary'
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(
      `${this.baseUrl}/calendar/google/events/${userId}/${eventId}?calendarId=${calendarId}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok) {
      throw new Error('Failed to delete Google Calendar event');
    }

    return response.json();
  }

  /**
   * Delete event from Microsoft Calendar
   */
  static async deleteMicrosoftEvent(
    userId: string,
    eventId: string,
    calendarId?: string
  ): Promise<{ success: boolean; message: string }> {
    const params = calendarId ? `?calendarId=${calendarId}` : '';
    const response = await fetch(
      `${this.baseUrl}/calendar/microsoft/events/${userId}/${eventId}${params}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok) {
      throw new Error('Failed to delete Microsoft Calendar event');
    }

    return response.json();
  }

  /**
   * Calendar Management Methods
   */

  /**
   * Get Google Calendars list
   */
  static async getGoogleCalendars(userId: string): Promise<{ calendars: Calendar[] }> {
    const response = await fetch(`${this.baseUrl}/calendar/google/calendars/${userId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch Google Calendars');
    }

    return response.json();
  }

  /**
   * Get Microsoft Calendars list
   */
  static async getMicrosoftCalendars(userId: string): Promise<{ calendars: Calendar[] }> {
    const response = await fetch(`${this.baseUrl}/calendar/microsoft/calendars/${userId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch Microsoft Calendars');
    }

    return response.json();
  }

  /**
   * Get all calendars from connected providers
   */
  static async getAllCalendars(userId: string): Promise<{
    google: Calendar[];
    microsoft: Calendar[];
  }> {
    const [googleResult, microsoftResult] = await Promise.allSettled([
      this.getGoogleCalendars(userId),
      this.getMicrosoftCalendars(userId),
    ]);

    return {
      google: googleResult.status === 'fulfilled' ? googleResult.value.calendars : [],
      microsoft: microsoftResult.status === 'fulfilled' ? microsoftResult.value.calendars : [],
    };
  }

  /**
   * Synchronization Methods
   */

  /**
   * Sync all calendars
   */
  static async syncAllCalendars(
    userId: string,
    options: {
      providers?: ('google' | 'microsoft')[];
      syncPeriodDays?: number;
      includeAllCalendars?: boolean;
      calendarIds?: string[];
    } = {}
  ): Promise<SyncResult> {
    const response = await fetch(`${this.baseUrl}/calendar/sync-all/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(options),
    });

    if (!response.ok) {
      throw new Error('Failed to sync calendars');
    }

    return response.json();
  }

  /**
   * Get sync status
   */
  static async getSyncStatus(userId: string): Promise<SyncStatus> {
    const response = await fetch(`${this.baseUrl}/calendar/sync-status/${userId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get sync status');
    }

    return response.json();
  }

  /**
   * Create event in external calendars
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
  ): Promise<{ success: boolean; results: any[] }> {
    const response = await fetch(`${this.baseUrl}/calendar/create-external/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...event, providers }),
    });

    if (!response.ok) {
      throw new Error('Failed to create event in external calendars');
    }

    return response.json();
  }

  /**
   * Utility Methods
   */

  /**
   * Format event for display
   */
  static formatEventForDisplay(event: CalendarEvent): {
    title: string;
    startTime: Date;
    endTime: Date;
    duration: string;
    provider: string;
    location?: string;
    description?: string;
  } {
    const startTime = new Date(typeof event.start === 'string' ? event.start : event.start.dateTime);
    const endTime = new Date(typeof event.end === 'string' ? event.end : event.end.dateTime);
    
    const durationMs = endTime.getTime() - startTime.getTime();
    const durationHours = Math.floor(durationMs / (1000 * 60 * 60));
    const durationMinutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    
    let duration = '';
    if (durationHours > 0) {
      duration += `${durationHours}h `;
    }
    if (durationMinutes > 0) {
      duration += `${durationMinutes}m`;
    }
    duration = duration.trim() || '0m';

    return {
      title: event.summary,
      startTime,
      endTime,
      duration,
      provider: event.source === 'google' ? 'Google Calendar' : 'Outlook Calendar',
      location: event.location,
      description: event.description,
    };
  }

  /**
   * Check if events conflict
   */
  static eventsConflict(event1: CalendarEvent, event2: CalendarEvent): boolean {
    const start1 = new Date(typeof event1.start === 'string' ? event1.start : event1.start.dateTime);
    const end1 = new Date(typeof event1.end === 'string' ? event1.end : event1.end.dateTime);
    const start2 = new Date(typeof event2.start === 'string' ? event2.start : event2.start.dateTime);
    const end2 = new Date(typeof event2.end === 'string' ? event2.end : event2.end.dateTime);

    return start1 < end2 && start2 < end1;
  }

  /**
   * Get events for a specific date range
   */
  static async getEventsForDateRange(
    userId: string,
    startDate: Date,
    endDate: Date,
    providers: ('google' | 'microsoft')[] = ['google', 'microsoft']
  ): Promise<CalendarEvent[]> {
    return this.getAllEvents(userId, {
      timeMin: startDate.toISOString(),
      timeMax: endDate.toISOString(),
      providers,
      maxResults: 500,
    });
  }

  /**
   * Get today's events
   */
  static async getTodaysEvents(
    userId: string,
    providers: ('google' | 'microsoft')[] = ['google', 'microsoft']
  ): Promise<CalendarEvent[]> {
    const today = new Date();
    const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const endOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);

    return this.getEventsForDateRange(userId, startOfDay, endOfDay, providers);
  }

  /**
   * Get this week's events
   */
  static async getWeekEvents(
    userId: string,
    providers: ('google' | 'microsoft')[] = ['google', 'microsoft']
  ): Promise<CalendarEvent[]> {
    const today = new Date();
    const startOfWeek = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay());
    const endOfWeek = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay() + 7);

    return this.getEventsForDateRange(userId, startOfWeek, endOfWeek, providers);
  }
} 