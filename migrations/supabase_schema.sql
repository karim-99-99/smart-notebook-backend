-- ============================================================================
-- SUPABASE DATABASE SCHEMA - Copy and paste this into Supabase SQL Editor
-- ============================================================================

-- Folders Table
create table folders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  name text not null,
  color text,
  icon text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  unique(user_id, name)
);

-- Enable Row Level Security for folders
alter table folders enable row level security;

-- Policy: Users can only see their own folders
create policy "Users can view own folders"
  on folders for select
  using (auth.uid() = user_id);

-- Policy: Users can insert their own folders
create policy "Users can insert own folders"
  on folders for insert
  with check (auth.uid() = user_id);

-- Policy: Users can update their own folders
create policy "Users can update own folders"
  on folders for update
  using (auth.uid() = user_id);

-- Policy: Users can delete their own folders
create policy "Users can delete own folders"
  on folders for delete
  using (auth.uid() = user_id);

-- Notes Table
create table notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  folder_id uuid references folders(id) on delete set null,
  title text,
  image_url text,
  raw_text text not null,
  corrected_text text not null,
  line_count integer default 0,
  average_confidence text,
  lines jsonb, -- JSONB for queryable line-level data
  timestamp bigint,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  synced_at timestamp with time zone
);

-- Enable Row Level Security for notes
alter table notes enable row level security;

-- Policy: Users can only see their own notes
create policy "Users can view own notes"
  on notes for select
  using (auth.uid() = user_id);

-- Policy: Users can insert their own notes
create policy "Users can insert own notes"
  on notes for insert
  with check (auth.uid() = user_id);

-- Policy: Users can update their own notes
create policy "Users can update own notes"
  on notes for update
  using (auth.uid() = user_id);

-- Policy: Users can delete their own notes
create policy "Users can delete own notes"
  on notes for delete
  using (auth.uid() = user_id);

-- Indexes for faster queries
create index notes_user_id_idx on notes(user_id);
create index notes_folder_id_idx on notes(folder_id);
create index notes_created_at_idx on notes(created_at desc);

