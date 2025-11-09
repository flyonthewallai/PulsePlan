-- Migration: Add User Roles
-- Purpose: Add role-based access control for admin features
-- Date: 2025-10-25

-- Add role column to public.users
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin'));

-- Create index for role lookups
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

-- Add comment
COMMENT ON COLUMN public.users.role IS 'User role: user (default) or admin';

-- Set your user as admin (replace with your actual email)
-- UPDATE public.users SET role = 'admin' WHERE email = 'your-email@pulseplan.com';
