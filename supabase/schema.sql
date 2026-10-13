-- Optional standalone bootstrap SQL. Apply in a fresh community user's project.
-- Not yet live-tested against Supabase. Do not apply to an unrelated existing app.
create table if not exists public.vso_snapshots (
  owner_id uuid not null references auth.users(id) on delete cascade,
  installation_id uuid not null,
  snapshot jsonb not null default '{}'::jsonb,
  primary key (owner_id, installation_id)
);

alter table public.vso_snapshots enable row level security;
revoke all on public.vso_snapshots from anon;
grant select, insert, update, delete on public.vso_snapshots to authenticated;

create policy "vso_owner_select" on public.vso_snapshots for select to authenticated
using ((select auth.uid()) = owner_id);
create policy "vso_owner_insert" on public.vso_snapshots for insert to authenticated
with check ((select auth.uid()) = owner_id);
create policy "vso_owner_update" on public.vso_snapshots for update to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);
create policy "vso_owner_delete" on public.vso_snapshots for delete to authenticated
using ((select auth.uid()) = owner_id);
