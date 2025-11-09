-- Create table for storing custom intent confidence thresholds
-- This allows runtime configuration of intent-specific confidence thresholds

CREATE TABLE IF NOT EXISTS public.intent_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent VARCHAR(100) NOT NULL UNIQUE,
    high_confidence DECIMAL(4,3) NOT NULL CHECK (high_confidence >= 0 AND high_confidence <= 1),
    low_confidence DECIMAL(4,3) NOT NULL CHECK (low_confidence >= 0 AND low_confidence <= 1),
    requires_context BOOLEAN DEFAULT FALSE,
    context_intents JSONB DEFAULT '[]'::jsonb,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure high_confidence >= low_confidence
    CONSTRAINT valid_threshold_range CHECK (high_confidence >= low_confidence)
);

-- Create index for active thresholds
CREATE INDEX IF NOT EXISTS idx_intent_thresholds_active
ON public.intent_thresholds(intent, is_active)
WHERE is_active = TRUE;

-- Add comments
COMMENT ON TABLE public.intent_thresholds IS 'Custom confidence thresholds for intent classification';
COMMENT ON COLUMN public.intent_thresholds.high_confidence IS 'Confidence threshold for direct execution (no LLM fallback)';
COMMENT ON COLUMN public.intent_thresholds.low_confidence IS 'Minimum confidence threshold (below this triggers LLM fallback)';
COMMENT ON COLUMN public.intent_thresholds.requires_context IS 'Whether this intent requires active conversation context';
COMMENT ON COLUMN public.intent_thresholds.context_intents IS 'JSON array of valid context intent names';

-- Insert default thresholds
INSERT INTO public.intent_thresholds (intent, high_confidence, low_confidence, requires_context, context_intents, description)
VALUES
    -- Calendar & Scheduling (high stakes)
    ('calendar_query', 0.82, 0.65, FALSE, '[]'::jsonb, 'Asking about calendar events'),
    ('calendar_event', 0.82, 0.65, FALSE, '[]'::jsonb, 'Creating/modifying calendar events'),
    ('schedule_event', 0.80, 0.65, FALSE, '[]'::jsonb, 'Scheduling events'),
    ('scheduling', 0.80, 0.65, FALSE, '[]'::jsonb, 'General scheduling operations'),

    -- Temporal slot fill (contextual, low threshold OK)
    ('temporal_slot_fill', 0.60, 0.40, TRUE,
     '["calendar_query","calendar_event","schedule_event","scheduling","task_management","tasks","reminder"]'::jsonb,
     'Providing temporal information in context'),

    -- Task Management (medium stakes)
    ('task_management', 0.78, 0.60, FALSE, '[]'::jsonb, 'Managing tasks'),
    ('tasks', 0.78, 0.60, FALSE, '[]'::jsonb, 'Task operations'),
    ('task_query', 0.78, 0.60, FALSE, '[]'::jsonb, 'Querying tasks'),
    ('reminder', 0.78, 0.60, FALSE, '[]'::jsonb, 'Setting reminders'),

    -- Email (high stakes - don't want wrong emails)
    ('email', 0.85, 0.70, FALSE, '[]'::jsonb, 'Email operations'),
    ('send_email', 0.85, 0.70, FALSE, '[]'::jsonb, 'Sending emails'),
    ('read_emails', 0.75, 0.60, FALSE, '[]'::jsonb, 'Reading emails'),

    -- Search (low stakes)
    ('search', 0.70, 0.55, FALSE, '[]'::jsonb, 'Searching for information'),
    ('user_data_query', 0.70, 0.55, FALSE, '[]'::jsonb, 'Querying user data'),

    -- Conversational (very low stakes)
    ('greeting', 0.60, 0.40, FALSE, '[]'::jsonb, 'Greetings'),
    ('thanks', 0.60, 0.40, FALSE, '[]'::jsonb, 'Thanking'),
    ('chitchat', 0.60, 0.40, FALSE, '[]'::jsonb, 'Casual conversation'),
    ('help', 0.70, 0.50, FALSE, '[]'::jsonb, 'Asking for help')
ON CONFLICT (intent) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_intent_thresholds_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER intent_thresholds_updated_at
    BEFORE UPDATE ON public.intent_thresholds
    FOR EACH ROW
    EXECUTE FUNCTION update_intent_thresholds_updated_at();
