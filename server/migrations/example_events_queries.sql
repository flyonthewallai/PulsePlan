-- Example Events Database Queries
-- This file contains example queries for common operations with the events schema

-- 1. Insert a new exam event
INSERT INTO events (
    user_id, title, description, type, subject, start_date, end_date, 
    all_day, location, priority, reminder_minutes, status, preparation_time_minutes
) VALUES (
    'user-uuid-here',
    'Calculus Final Exam',
    'Final exam covering chapters 1-12',
    'exam',
    'Mathematics',
    '2024-05-15 09:00:00+00',
    '2024-05-15 11:00:00+00',
    false,
    'Room 101, Science Building',
    'high',
    ARRAY[60, 1440], -- 1 hour and 1 day before
    'scheduled',
    120 -- 2 hours prep time
);

-- 2. Insert a recurring weekly class
INSERT INTO events (
    user_id, title, type, subject, start_date, end_date, 
    all_day, location, priority, is_recurring, recurrence_pattern, 
    recurrence_interval, recurrence_end_date, status
) VALUES (
    'user-uuid-here',
    'Computer Science Lecture',
    'class',
    'Computer Science',
    '2024-03-01 10:00:00+00',
    '2024-03-01 11:30:00+00',
    false,
    'Lecture Hall A',
    'medium',
    true,
    'weekly',
    1,
    '2024-06-01 00:00:00+00',
    'scheduled'
);

-- 3. Insert a virtual meeting
INSERT INTO events (
    user_id, title, description, type, start_date, end_date, 
    location_type, meeting_url, priority, reminder_minutes, attendees
) VALUES (
    'user-uuid-here',
    'Project Team Meeting',
    'Weekly sync for project updates',
    'meeting',
    '2024-03-20 14:00:00+00',
    '2024-03-20 15:00:00+00',
    'virtual',
    'https://zoom.us/j/123456789',
    'medium',
    ARRAY[15, 30],
    ARRAY['teammate1@email.com', 'teammate2@email.com']
);

-- 4. Get all upcoming events for a user (next 7 days)
SELECT 
    id, title, type, subject, start_date, end_date, location, priority, status
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND start_date >= NOW() 
    AND start_date <= NOW() + INTERVAL '7 days'
    AND status NOT IN ('cancelled', 'completed')
ORDER BY start_date ASC;

-- 5. Get today's events for a user
SELECT 
    id, title, type, subject, start_date, end_date, location, priority,
    EXTRACT(HOUR FROM start_date) as start_hour,
    EXTRACT(MINUTE FROM start_date) as start_minute
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND start_date::date = CURRENT_DATE
    AND status NOT IN ('cancelled', 'completed')
ORDER BY start_date ASC;

-- 6. Get all exams in the next month
SELECT 
    id, title, subject, start_date, location, priority, preparation_time_minutes
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND type = 'exam'
    AND start_date >= NOW() 
    AND start_date <= NOW() + INTERVAL '30 days'
    AND status = 'scheduled'
ORDER BY start_date ASC;

-- 7. Get overdue events that haven't been completed
SELECT 
    id, title, type, start_date, priority,
    EXTRACT(EPOCH FROM (NOW() - start_date)) / 3600 as hours_overdue
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND start_date < NOW()
    AND status NOT IN ('completed', 'cancelled')
ORDER BY start_date DESC;

-- 8. Get events by priority
SELECT 
    id, title, type, start_date, priority, status
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND priority IN ('high', 'critical')
    AND start_date >= NOW()
    AND status = 'scheduled'
ORDER BY 
    CASE priority 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        ELSE 3 
    END,
    start_date ASC;

-- 9. Get events by subject (for academic tracking)
SELECT 
    subject,
    COUNT(*) as total_events,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_events,
    COUNT(CASE WHEN type = 'exam' THEN 1 END) as exams,
    COUNT(CASE WHEN type = 'class' THEN 1 END) as classes
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND subject IS NOT NULL
GROUP BY subject
ORDER BY total_events DESC;

-- 10. Get recurring events and their instances
SELECT 
    parent.id as parent_id,
    parent.title as parent_title,
    parent.recurrence_pattern,
    parent.recurrence_interval,
    COUNT(child.id) as instance_count
FROM events parent
LEFT JOIN events child ON child.parent_event_id = parent.id
WHERE 
    parent.user_id = 'user-uuid-here' 
    AND parent.is_recurring = true
GROUP BY parent.id, parent.title, parent.recurrence_pattern, parent.recurrence_interval
ORDER BY parent.created_at DESC;

-- 11. Get events with location information
SELECT 
    id, title, type, start_date, location, location_type, meeting_url
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND start_date >= NOW()
    AND (location IS NOT NULL OR meeting_url IS NOT NULL)
ORDER BY start_date ASC;

-- 12. Get events that need preparation time
SELECT 
    id, title, type, start_date, preparation_time_minutes,
    start_date - INTERVAL '1 minute' * preparation_time_minutes as prep_start_time
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND preparation_time_minutes > 0
    AND start_date >= NOW()
ORDER BY start_date ASC;

-- 13. Get event statistics for analytics
SELECT 
    DATE_TRUNC('week', start_date) as week_start,
    COUNT(*) as total_events,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN type = 'exam' THEN 1 END) as exams,
    COUNT(CASE WHEN type = 'meeting' THEN 1 END) as meetings,
    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_priority
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND start_date >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('week', start_date)
ORDER BY week_start DESC;

-- 14. Search events by title or description
SELECT 
    id, title, description, type, start_date, priority
FROM events 
WHERE 
    user_id = 'user-uuid-here' 
    AND (
        title ILIKE '%search-term%' 
        OR description ILIKE '%search-term%'
    )
    AND status NOT IN ('cancelled')
ORDER BY start_date ASC;

-- 15. Get events with reminders that need to be sent
SELECT 
    e.id, e.title, e.start_date, r.reminder_time, r.type
FROM events e
JOIN event_reminders r ON e.id = r.event_id
WHERE 
    r.user_id = 'user-uuid-here'
    AND r.status = 'pending'
    AND r.reminder_time <= NOW()
ORDER BY r.reminder_time ASC; 