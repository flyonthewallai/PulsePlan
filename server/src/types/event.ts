export interface Event {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  
  // Event categorization
  type: 'exam' | 'meeting' | 'appointment' | 'deadline' | 'class' | 'social' | 'personal' | 'work' | 'other';
  subject?: string; // For academic events like exams, classes
  
  // Timing
  start_date: string; // ISO string
  end_date?: string; // ISO string, optional for single-point events
  all_day: boolean;
  
  // Location and details
  location?: string;
  location_type?: 'in_person' | 'virtual' | 'hybrid';
  meeting_url?: string; // For virtual meetings
  
  // Importance and notifications
  priority: 'low' | 'medium' | 'high' | 'critical';
  reminder_minutes?: number[]; // Array of minutes before event to remind (e.g., [15, 60, 1440])
  
  // Status and completion
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled' | 'rescheduled';
  attendance_status?: 'attending' | 'maybe' | 'not_attending' | 'tentative';
  
  // Recurrence (for recurring events)
  is_recurring: boolean;
  recurrence_pattern?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  recurrence_interval?: number; // Every N days/weeks/months/years
  recurrence_end_date?: string; // When to stop recurring
  parent_event_id?: string; // For recurring event instances
  
  // Additional metadata
  color?: string; // Hex color for calendar display
  tags?: string[]; // Array of tags for organization
  attendees?: string[]; // Array of email addresses or names
  preparation_time_minutes?: number; // Time needed to prepare before event
  
  // Integration
  external_calendar_id?: string; // ID from Google Calendar, Outlook, etc.
  external_event_id?: string; // External calendar event ID
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface EventReminder {
  id: string;
  event_id: string;
  user_id: string;
  reminder_time: string; // When to send the reminder
  status: 'pending' | 'sent' | 'cancelled';
  type: 'notification' | 'email' | 'sms';
  created_at: string;
}

export interface EventAttendee {
  id: string;
  event_id: string;
  user_id: string;
  email?: string;
  name?: string;
  status: 'pending' | 'accepted' | 'declined' | 'tentative';
  is_organizer: boolean;
  created_at: string;
  updated_at: string;
} 