-- Migration: Add user_hobbies table for persisting user hobbies with scheduling preferences
-- Created: 2025-01-28

-- Create user_hobbies table
CREATE TABLE IF NOT EXISTS public.user_hobbies (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  name text NOT NULL,
  icon text NOT NULL DEFAULT 'Target'::text,
  preferred_time text NOT NULL CHECK (preferred_time IN ('morning', 'afternoon', 'evening', 'night', 'any')),
  specific_time jsonb DEFAULT NULL, -- {"start": "HH:MM", "end": "HH:MM"}
  days text[] NOT NULL DEFAULT ARRAY['Mon','Tue','Wed','Thu','Fri','Sat','Sun']::text[],
  duration_min integer NOT NULL CHECK (duration_min >= 5 AND duration_min <= 480),
  duration_max integer NOT NULL CHECK (duration_max >= 5 AND duration_max <= 480 AND duration_max >= duration_min),
  flexibility text NOT NULL DEFAULT 'medium'::text CHECK (flexibility IN ('low', 'medium', 'high')),
  notes text DEFAULT ''::text,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT user_hobbies_pkey PRIMARY KEY (id),
  CONSTRAINT user_hobbies_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_hobbies_user_id ON public.user_hobbies(user_id);

-- Create index on is_active for filtering active hobbies
CREATE INDEX IF NOT EXISTS idx_user_hobbies_is_active ON public.user_hobbies(is_active);

-- Enable Row Level Security
ALTER TABLE public.user_hobbies ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can view their own hobbies
CREATE POLICY "Users can view their own hobbies"
  ON public.user_hobbies
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own hobbies
CREATE POLICY "Users can insert their own hobbies"
  ON public.user_hobbies
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own hobbies
CREATE POLICY "Users can update their own hobbies"
  ON public.user_hobbies
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can delete their own hobbies
CREATE POLICY "Users can delete their own hobbies"
  ON public.user_hobbies
  FOR DELETE
  USING (auth.uid() = user_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_hobbies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_hobbies_updated_at
  BEFORE UPDATE ON public.user_hobbies
  FOR EACH ROW
  EXECUTE FUNCTION update_user_hobbies_updated_at();
