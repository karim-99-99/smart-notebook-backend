-- ============================================================================
-- SUPABASE STORAGE POLICIES - Copy and paste this into Supabase SQL Editor
-- ============================================================================
-- 
-- Make sure you've created the "user-notes" bucket first!
-- Go to Storage → Buckets → Create bucket → Name: "user-notes" → Private
--

-- Policy: Users can upload to their own folder
create policy "Users can upload own images"
  on storage.objects for insert
  with check (
    bucket_id = 'user-notes' and
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Policy: Users can view their own images
create policy "Users can view own images"
  on storage.objects for select
  using (
    bucket_id = 'user-notes' and
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Policy: Users can delete their own images
create policy "Users can delete own images"
  on storage.objects for delete
  using (
    bucket_id = 'user-notes' and
    auth.uid()::text = (storage.foldername(name))[1]
  );

