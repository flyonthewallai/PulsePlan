-- Pomodoro settings, phase events, and roll-up summaries

-- 1) user_pomodoro_settings
create table if not exists public.user_pomodoro_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  focus_minutes int not null default 25,
  break_minutes int not null default 5,
  long_break_minutes int not null default 15,
  cycles_per_session int not null default 4,
  auto_start_breaks boolean not null default true,
  auto_start_next_session boolean not null default false,
  play_sound_on_complete boolean not null default true,
  desktop_notifications boolean not null default true,
  updated_at timestamptz not null default now()
);

-- Enable RLS
alter table public.user_pomodoro_settings enable row level security;
drop policy if exists user_pomodoro_settings_is_owner on public.user_pomodoro_settings;
create policy user_pomodoro_settings_is_owner
  on public.user_pomodoro_settings
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- 2) focus_session_phases (event log)
do $$ begin
  if not exists (select 1 from pg_type where typname = 'phase_type') then
    create type phase_type as enum ('focus','break','long_break');
  end if;
end $$;

create table if not exists public.focus_session_phases (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.focus_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  phase_type phase_type not null,
  started_at timestamptz not null default now(),
  ended_at timestamptz null,
  duration_minutes int null,
  interrupted boolean not null default false,
  expected_duration_minutes int null,
  notes jsonb null,
  created_at timestamptz not null default now()
);

create index if not exists idx_focus_session_phases_session_started
  on public.focus_session_phases (session_id, started_at desc);
create index if not exists idx_focus_session_phases_session_type
  on public.focus_session_phases (session_id, phase_type);

alter table public.focus_session_phases enable row level security;
drop policy if exists focus_session_phases_is_owner on public.focus_session_phases;
create policy focus_session_phases_is_owner
  on public.focus_session_phases
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- 3) focus_sessions summary columns
alter table public.focus_sessions
  add column if not exists total_focus_time int not null default 0,
  add column if not exists total_break_time int not null default 0,
  add column if not exists total_cycles int not null default 0,
  add column if not exists long_breaks_completed int not null default 0,
  add column if not exists phase_count int not null default 0,
  add column if not exists avg_focus_length int not null default 0,
  add column if not exists avg_break_length int not null default 0;

-- 4) roll-up function and trigger
create or replace function public.update_focus_session_totals()
returns trigger as $$
declare
  break_count int;
begin
  -- Compute duration if needed
  if NEW.ended_at is not null and NEW.duration_minutes is null then
    NEW.duration_minutes := greatest(0, floor(extract(epoch from (NEW.ended_at - NEW.started_at)) / 60)::int);
  end if;

  update public.focus_sessions fs
  set
    total_focus_time = coalesce((
      select sum(duration_minutes)
      from public.focus_session_phases p
      where p.session_id = NEW.session_id and p.phase_type = 'focus'
    ), 0),
    total_break_time = coalesce((
      select sum(duration_minutes)
      from public.focus_session_phases p
      where p.session_id = NEW.session_id and p.phase_type in ('break','long_break')
    ), 0),
    total_cycles = coalesce((
      select count(*) from public.focus_session_phases p
      where p.session_id = NEW.session_id and p.phase_type = 'focus'
    ), 0),
    long_breaks_completed = coalesce((
      select count(*) from public.focus_session_phases p
      where p.session_id = NEW.session_id and p.phase_type = 'long_break'
    ), 0),
    phase_count = coalesce((
      select count(*) from public.focus_session_phases p
      where p.session_id = NEW.session_id
    ), 0),
    avg_focus_length = coalesce((
      select case when count(*) > 0 then sum(duration_minutes)::int / count(*) else 0 end
      from public.focus_session_phases p
      where p.session_id = NEW.session_id and p.phase_type = 'focus'
    ), 0),
    avg_break_length = coalesce((
      select case when count(*) > 0 then sum(duration_minutes)::int / count(*) else 0 end
      from public.focus_session_phases p
      where p.session_id = NEW.session_id and p.phase_type in ('break','long_break')
    ), 0)
  where fs.id = NEW.session_id;

  return NEW;
end;
$$ language plpgsql;

drop trigger if exists trg_update_focus_session_totals on public.focus_session_phases;
create trigger trg_update_focus_session_totals
after insert or update of ended_at on public.focus_session_phases
for each row execute function public.update_focus_session_totals();


