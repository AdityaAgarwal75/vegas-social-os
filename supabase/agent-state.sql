-- Apply through the setup agent to a DEDICATED installation project.
-- Server-only encrypted state. No browser access and no permissive user policies.
create table if not exists public.vso_installations (
  installation_id uuid primary key,
  revision bigint not null check (revision > 0),
  ciphertext text not null,
  updated_at timestamptz not null default now()
);
alter table public.vso_installations enable row level security;
revoke all on public.vso_installations from anon, authenticated;
grant select, insert, update on public.vso_installations to service_role;

create or replace function public.vso_commit_state(
  p_installation_id uuid, p_expected_revision bigint, p_ciphertext text
) returns bigint
language plpgsql security invoker set search_path = '' as $$
declare result_revision bigint;
begin
  if p_expected_revision = 0 then
    insert into public.vso_installations(installation_id, revision, ciphertext)
    values (p_installation_id, 1, p_ciphertext)
    on conflict (installation_id) do nothing
    returning revision into result_revision;
  else
    update public.vso_installations
    set revision = revision + 1, ciphertext = p_ciphertext, updated_at = now()
    where installation_id = p_installation_id and revision = p_expected_revision
    returning revision into result_revision;
  end if;
  if result_revision is null then
    raise exception 'state_revision_conflict';
  end if;
  return result_revision;
end;
$$;
revoke all on function public.vso_commit_state(uuid, bigint, text) from public, anon, authenticated;
grant execute on function public.vso_commit_state(uuid, bigint, text) to service_role;
