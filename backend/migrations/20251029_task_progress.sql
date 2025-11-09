-- Task progress accumulation from focus phases

-- 1) Add completed_cycles to tasks (if not exists)
alter table public.tasks
  add column if not exists completed_cycles int not null default 0;

-- 2) task_progress event table
create table if not exists public.task_progress (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.tasks(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid not null references public.focus_sessions(id) on delete cascade,
  duration_minutes int not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_task_progress_task on public.task_progress(task_id, created_at desc);

alter table public.task_progress enable row level security;
drop policy if exists task_progress_is_owner on public.task_progress;
create policy task_progress_is_owner on public.task_progress
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- 3) Extend roll-up trigger to also update tasks and insert task_progress rows when a focus phase ends
create or replace function public.update_focus_session_totals()
returns trigger as $$
declare
  target_task uuid;
  dur int;
begin
  -- Compute duration if needed
  if NEW.ended_at is not null and NEW.duration_minutes is null then
    NEW.duration_minutes := greatest(0, floor(extract(epoch from (NEW.ended_at - NEW.started_at)) / 60)::int);
  end if;

  -- Existing rollups
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

  -- If a focus phase just ended, increment task.completed_cycles and add task_progress row
  if TG_OP in ('INSERT','UPDATE') and NEW.ended_at is not null and NEW.phase_type = 'focus' then
    select task_id into target_task from public.focus_sessions where id = NEW.session_id;
    if target_task is not null then
      update public.tasks set completed_cycles = coalesce(completed_cycles,0) + 1 where id = target_task;
      dur := coalesce(NEW.duration_minutes, 0);
      insert into public.task_progress(task_id, user_id, session_id, duration_minutes)
      values (target_task, NEW.user_id, NEW.session_id, dur);
    end if;
  end if;

  return NEW;
end;
$$ language plpgsql;








