-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Event categorization
    type VARCHAR(20) NOT NULL CHECK (type IN ('exam', 'meeting', 'appointment', 'deadline', 'class', 'social', 'personal', 'work', 'other')),
    subject VARCHAR(100),
    
    -- Timing
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    all_day BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Location and details
    location VARCHAR(500),
    location_type VARCHAR(20) CHECK (location_type IN ('in_person', 'virtual', 'hybrid')),
    meeting_url TEXT,
    
    -- Importance and notifications
    priority VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    reminder_minutes INTEGER[],
    
    -- Status and completion
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'rescheduled')),
    attendance_status VARCHAR(20) CHECK (attendance_status IN ('attending', 'maybe', 'not_attending', 'tentative')),
    
    -- Recurrence
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_pattern VARCHAR(10) CHECK (recurrence_pattern IN ('daily', 'weekly', 'monthly', 'yearly')),
    recurrence_interval INTEGER DEFAULT 1,
    recurrence_end_date TIMESTAMPTZ,
    parent_event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    
    -- Additional metadata
    color VARCHAR(7), -- Hex color code
    tags TEXT[], -- Array of tags
    attendees TEXT[], -- Array of email addresses or names
    preparation_time_minutes INTEGER DEFAULT 0,
    
    -- Integration
    external_calendar_id VARCHAR(255),
    external_event_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT valid_recurrence CHECK (
        (is_recurring = FALSE) OR 
        (is_recurring = TRUE AND recurrence_pattern IS NOT NULL)
    ),
    CONSTRAINT valid_preparation_time CHECK (preparation_time_minutes >= 0)
);

-- Create event_reminders table
CREATE TABLE IF NOT EXISTS event_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled')),
    type VARCHAR(20) NOT NULL DEFAULT 'notification' CHECK (type IN ('notification', 'email', 'sms')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create event_attendees table (for multi-user events)
CREATE TABLE IF NOT EXISTS event_attendees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255),
    name VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'tentative')),
    is_organizer BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure unique attendee per event
    UNIQUE(event_id, user_id),
    UNIQUE(event_id, email)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_end_date ON events(end_date);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_priority ON events(priority);
CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject);
CREATE INDEX IF NOT EXISTS idx_events_parent_event_id ON events(parent_event_id);
CREATE INDEX IF NOT EXISTS idx_events_external_calendar_id ON events(external_calendar_id);
CREATE INDEX IF NOT EXISTS idx_events_date_range ON events(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_event_reminders_event_id ON event_reminders(event_id);
CREATE INDEX IF NOT EXISTS idx_event_reminders_user_id ON event_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_event_reminders_reminder_time ON event_reminders(reminder_time);
CREATE INDEX IF NOT EXISTS idx_event_reminders_status ON event_reminders(status);

CREATE INDEX IF NOT EXISTS idx_event_attendees_event_id ON event_attendees(event_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_user_id ON event_attendees(user_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_email ON event_attendees(email);

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_events_updated_at 
    BEFORE UPDATE ON events 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_attendees_updated_at 
    BEFORE UPDATE ON event_attendees 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_attendees ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own events" ON events
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own events" ON events
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own events" ON events
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own events" ON events
    FOR DELETE USING (user_id = auth.uid());

CREATE POLICY "Users can view their own event reminders" ON event_reminders
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own event reminders" ON event_reminders
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own event reminders" ON event_reminders
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own event reminders" ON event_reminders
    FOR DELETE USING (user_id = auth.uid());

CREATE POLICY "Users can view events they're invited to" ON event_attendees
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Event organizers can manage attendees" ON event_attendees
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM events 
            WHERE events.id = event_attendees.event_id 
            AND events.user_id = auth.uid()
        )
    );

-- Create a view for upcoming events (next 30 days)
CREATE OR REPLACE VIEW upcoming_events AS
SELECT 
    e.*,
    CASE 
        WHEN e.start_date::date = CURRENT_DATE THEN 'today'
        WHEN e.start_date::date = CURRENT_DATE + INTERVAL '1 day' THEN 'tomorrow'
        WHEN e.start_date::date <= CURRENT_DATE + INTERVAL '7 days' THEN 'this_week'
        ELSE 'later'
    END as time_category,
    EXTRACT(EPOCH FROM (e.start_date - NOW())) / 60 as minutes_until_start
FROM events e
WHERE 
    e.start_date >= NOW() 
    AND e.start_date <= NOW() + INTERVAL '30 days'
    AND e.status NOT IN ('cancelled', 'completed')
ORDER BY e.start_date ASC;

-- Create a view for overdue events
CREATE OR REPLACE VIEW overdue_events AS
SELECT 
    e.*,
    EXTRACT(EPOCH FROM (NOW() - e.start_date)) / 60 as minutes_overdue
FROM events e
WHERE 
    e.start_date < NOW() 
    AND e.status NOT IN ('cancelled', 'completed')
ORDER BY e.start_date DESC; 