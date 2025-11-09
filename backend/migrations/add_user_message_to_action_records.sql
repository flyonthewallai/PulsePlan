-- Add user_message column to action_records table for semantic similarity in continuations
-- This stores the original user message that triggered the action

ALTER TABLE public.action_records
ADD COLUMN IF NOT EXISTS user_message TEXT;

-- Add index for better query performance when retrieving last action
CREATE INDEX IF NOT EXISTS idx_action_records_user_id_created_at
ON public.action_records(user_id, created_at DESC);

-- Add comment
COMMENT ON COLUMN public.action_records.user_message IS 'Original user message that triggered this action (used for semantic similarity in continuations)';
