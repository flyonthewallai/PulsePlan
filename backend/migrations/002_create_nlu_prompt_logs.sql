-- Migration: Create NLU Prompt Logs Table
-- Purpose: Capture user prompts for continuous model refinement
-- Date: 2025-10-25

-- Create nlu_prompt_logs table
CREATE TABLE IF NOT EXISTS public.nlu_prompt_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Prompt and prediction
    prompt TEXT NOT NULL,
    predicted_intent TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- Multi-intent support
    secondary_intents JSONB DEFAULT '[]'::jsonb,

    -- Human-in-the-loop corrections
    corrected_intent TEXT,
    correction_notes TEXT,

    -- Workflow feedback
    was_successful BOOLEAN,
    workflow_type TEXT,
    execution_error TEXT,

    -- Context tracking
    conversation_id UUID,
    message_index INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_nlu_prompt_logs_user_id ON public.nlu_prompt_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_nlu_prompt_logs_created_at ON public.nlu_prompt_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nlu_prompt_logs_predicted_intent ON public.nlu_prompt_logs(predicted_intent);
CREATE INDEX IF NOT EXISTS idx_nlu_prompt_logs_confidence ON public.nlu_prompt_logs(confidence);
CREATE INDEX IF NOT EXISTS idx_nlu_prompt_logs_corrected ON public.nlu_prompt_logs(corrected_intent) WHERE corrected_intent IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_nlu_prompt_logs_failed ON public.nlu_prompt_logs(was_successful) WHERE was_successful = FALSE;

-- Enable Row Level Security
ALTER TABLE public.nlu_prompt_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can only see their own logs
CREATE POLICY "Users can view their own NLU logs"
    ON public.nlu_prompt_logs
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own logs
CREATE POLICY "Users can insert their own NLU logs"
    ON public.nlu_prompt_logs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own logs (for corrections)
CREATE POLICY "Users can update their own NLU logs"
    ON public.nlu_prompt_logs
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Service role can do everything (for admin corrections and analysis)
CREATE POLICY "Service role has full access to NLU logs"
    ON public.nlu_prompt_logs
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Add comment to table
COMMENT ON TABLE public.nlu_prompt_logs IS 'Logs of user prompts and intent predictions for continuous model improvement';
COMMENT ON COLUMN public.nlu_prompt_logs.prompt IS 'Raw user input text';
COMMENT ON COLUMN public.nlu_prompt_logs.predicted_intent IS 'Intent predicted by NLU model';
COMMENT ON COLUMN public.nlu_prompt_logs.confidence IS 'Prediction confidence score (0-1)';
COMMENT ON COLUMN public.nlu_prompt_logs.secondary_intents IS 'Array of secondary intents with scores: [{"intent": "...", "score": 0.8}]';
COMMENT ON COLUMN public.nlu_prompt_logs.corrected_intent IS 'Manual correction if prediction was wrong';
COMMENT ON COLUMN public.nlu_prompt_logs.was_successful IS 'Whether the workflow execution succeeded';
