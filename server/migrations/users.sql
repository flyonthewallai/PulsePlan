create table public.users (
  id uuid not null default gen_random_uuid (),
  email text not null,
  created_at timestamp with time zone not null default now(),
  onboarding_complete boolean null default false,
  subscription_status text not null default 'free'::text,
  apple_transaction_id text null,
  subscription_expires_at timestamp with time zone null,
  subscription_updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  name text null,
  avatar_url text null,
  timezone text null default 'UTC'::text,
  last_login_at timestamp with time zone null,
  preferences jsonb null default '{}'::jsonb,
  working_hours jsonb null default '{"endHour": 17, "startHour": 9}'::jsonb,
  onboarding_step integer null default 0,
  school text null,
  text smallint null,
  memories jsonb null default '{}'::jsonb,
  academic_year text null,
  user_type character varying(20) null,
  study_preferences jsonb null,
  work_preferences jsonb null,
  integration_preferences jsonb null,
  notification_preferences jsonb null,
  onboarding_completed_at timestamp with time zone null,
  constraint users_pkey primary key (id),
  constraint users_email_key unique (email),
  constraint users_academic_year_check check ((text > 2025)),
  constraint users_user_type_check check (
    (
      (user_type)::text = any (
        (
          array[
            'student'::character varying,
            'professional'::character varying,
            'educator'::character varying
          ]
        )::text[]
      )
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_users_user_type on public.users using btree (user_type) TABLESPACE pg_default;

create index IF not exists idx_users_onboarding_completed on public.users using btree (onboarding_completed_at) TABLESPACE pg_default;

create index IF not exists idx_users_subscription_status on public.users using btree (subscription_status) TABLESPACE pg_default;

create trigger update_users_subscription_updated_at BEFORE
update OF subscription_status,
apple_transaction_id,
subscription_expires_at on users for EACH row
execute FUNCTION update_subscription_updated_at ();