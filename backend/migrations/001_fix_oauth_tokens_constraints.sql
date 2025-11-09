-- Migration: Fix oauth_tokens table constraints
-- Date: 2025-01-17
-- Description: Add missing unique constraint and allow canvas provider

-- Add unique constraint on (user_id, provider) to prevent duplicate tokens
ALTER TABLE public.oauth_tokens 
ADD CONSTRAINT oauth_tokens_user_provider_unique UNIQUE (user_id, provider);

-- Update CHECK constraint to include 'canvas' provider
ALTER TABLE public.oauth_tokens 
DROP CONSTRAINT IF EXISTS oauth_tokens_provider_check;

ALTER TABLE public.oauth_tokens 
ADD CONSTRAINT oauth_tokens_provider_check 
CHECK (provider = ANY (ARRAY['google'::text, 'outlook'::text, 'apple'::text, 'canvas'::text]));

-- Add comment for documentation
COMMENT ON CONSTRAINT oauth_tokens_user_provider_unique ON public.oauth_tokens IS 
'Ensures each user can only have one token per provider, enabling upsert operations';

COMMENT ON CONSTRAINT oauth_tokens_provider_check ON public.oauth_tokens IS 
'Restricts provider values to supported OAuth providers including Canvas';

