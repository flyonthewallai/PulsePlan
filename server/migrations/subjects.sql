create table public.subjects (
  id uuid not null default gen_random_uuid (),
  user_id uuid null,
  name text not null,
  color text not null,
  icon text null,
  created_at timestamp with time zone null default now(),
  constraint subjects_pkey primary key (id),
  constraint subjects_user_id_fkey foreign KEY (user_id) references users (id) on delete CASCADE
) TABLESPACE pg_default;