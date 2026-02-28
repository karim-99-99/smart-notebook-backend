-- ============================================================================
-- SUPABASE ADMIN + ANALYTICS - Run in Supabase SQL Editor after supabase_schema.sql
-- ============================================================================
-- One admin account only. Analytics tables for errors, accuracy, events, dataset.
-- Only the user in admin_config can read analytics; app users can insert events.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Admin config: single row = one admin user allowed to access dashboard
-- ----------------------------------------------------------------------------
create table if not exists admin_config (
  id integer primary key default 1 check (id = 1),
  admin_user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table admin_config enable row level security;

-- Only the admin can read admin_config (to check if current user is admin)
create policy "Admin can read admin_config"
  on admin_config for select
  using (auth.uid() = admin_user_id);

-- No one can insert/update/delete via anon key (run once in SQL Editor as superuser)
-- Insert your admin user after first sign-up, e.g.:
-- insert into admin_config (admin_user_id) values ('YOUR-ADMIN-USER-UUID');
-- Then: create policy so only service role or same user can update (optional).

-- ----------------------------------------------------------------------------
-- 2. Analytics: errors (app/backend/OCR failures)
-- ----------------------------------------------------------------------------
create table if not exists analytics_errors (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  source text not null, -- 'app' | 'backend' | 'ocr' | 'sync'
  error_code text,
  message text not null,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

create index if not exists analytics_errors_created_at_idx on analytics_errors(created_at desc);
create index if not exists analytics_errors_source_idx on analytics_errors(source);

alter table analytics_errors enable row level security;

-- Any authenticated user (app) can insert errors
create policy "Authenticated can insert analytics_errors"
  on analytics_errors for insert
  with check (auth.uid() is not null);

-- Only admin can select
create policy "Admin can read analytics_errors"
  on analytics_errors for select
  using (
    exists (select 1 from admin_config where admin_user_id = auth.uid())
  );

-- ----------------------------------------------------------------------------
-- 3. Analytics: accuracy (OCR confidence, edit distance, etc.)
-- ----------------------------------------------------------------------------
create table if not exists analytics_accuracy (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  note_id uuid references notes(id) on delete set null,
  metric_name text not null, -- 'ocr_confidence' | 'edit_distance' | 'line_count'
  value numeric not null,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

create index if not exists analytics_accuracy_created_at_idx on analytics_accuracy(created_at desc);
create index if not exists analytics_accuracy_metric_idx on analytics_accuracy(metric_name);

alter table analytics_accuracy enable row level security;

create policy "Authenticated can insert analytics_accuracy"
  on analytics_accuracy for insert
  with check (auth.uid() is not null);

create policy "Admin can read analytics_accuracy"
  on analytics_accuracy for select
  using (
    exists (select 1 from admin_config where admin_user_id = auth.uid())
  );

-- ----------------------------------------------------------------------------
-- 4. Analytics: user behavior events
-- ----------------------------------------------------------------------------
create table if not exists analytics_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  event_name text not null, -- 'login' | 'signup' | 'scan' | 'save_note' | 'create_folder' | 'sync' | etc.
  payload jsonb default '{}',
  created_at timestamptz default now()
);

create index if not exists analytics_events_created_at_idx on analytics_events(created_at desc);
create index if not exists analytics_events_name_idx on analytics_events(event_name);
create index if not exists analytics_events_user_id_idx on analytics_events(user_id);

alter table analytics_events enable row level security;

create policy "Authenticated can insert analytics_events"
  on analytics_events for insert
  with check (auth.uid() is not null);

create policy "Admin can read analytics_events"
  on analytics_events for select
  using (
    exists (select 1 from admin_config where admin_user_id = auth.uid())
  );

-- ----------------------------------------------------------------------------
-- 5. Dataset monitoring snapshots (optional; dashboard can also aggregate live)
-- ----------------------------------------------------------------------------
create table if not exists dataset_snapshots (
  id uuid primary key default gen_random_uuid(),
  snapshot_at timestamptz default now(),
  total_users bigint not null default 0,
  total_notes bigint not null default 0,
  total_folders bigint not null default 0,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

create index if not exists dataset_snapshots_snapshot_at_idx on dataset_snapshots(snapshot_at desc);

alter table dataset_snapshots enable row level security;

-- Only admin can read; allow insert from authenticated (e.g. cron or dashboard)
create policy "Admin can read dataset_snapshots"
  on dataset_snapshots for select
  using (
    exists (select 1 from admin_config where admin_user_id = auth.uid())
  );

create policy "Authenticated can insert dataset_snapshots"
  on dataset_snapshots for insert
  with check (auth.uid() is not null);

-- ----------------------------------------------------------------------------
-- 6. Helper: is current user the admin?
-- ----------------------------------------------------------------------------
create or replace function public.is_admin()
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from admin_config where admin_user_id = auth.uid()
  );
$$;

-- ----------------------------------------------------------------------------
-- 7. Dashboard stats (counts) – only for admin; uses definer to read all
-- ----------------------------------------------------------------------------
create or replace function public.get_dashboard_stats()
returns json
language plpgsql
security definer
set search_path = public
stable
as $$
declare
  result json;
begin
  if not public.is_admin() then
    return json_build_object('allowed', false);
  end if;

  select json_build_object(
    'allowed', true,
    'total_users', (select count(*) from auth.users),
    'total_notes', (select count(*) from notes),
    'total_folders', (select count(*) from folders),
    'errors_count', (select count(*) from analytics_errors),
    'accuracy_count', (select count(*) from analytics_accuracy),
    'events_count', (select count(*) from analytics_events)
  ) into result;

  return result;
end;
$$;

-- ----------------------------------------------------------------------------
-- AFTER RUNNING THIS MIGRATION
-- ----------------------------------------------------------------------------
-- 1. Create your admin account in the app (sign up with the email you want as admin).
-- 2. In Supabase: Authentication → Users → copy the UUID of that user.
-- 3. Run once in SQL Editor:
--    insert into admin_config (admin_user_id) values ('PASTE-ADMIN-UUID-HERE');
-- Only that account will be able to open the Admin Dashboard and see analytics.
-- ============================================================================
