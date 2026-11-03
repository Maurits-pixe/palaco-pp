-- PP-IDB-001 | review candidate only; do not apply to production without TRIAS approval.
-- This schema does not grant authorization or issue official EDTR records.
begin;
create schema if not exists pp_identity;
revoke all on schema pp_identity from public, anon, authenticated;

create table if not exists pp_identity.lineage_events (
  event_id uuid primary key default gen_random_uuid(),
  event_type text not null check (event_type in (
    'PP_ACCOUNT_CREATED','PERSON_BINDING_PROPOSED',
    'EXTERNAL_BINDING_PROPOSED','CONTACT_VERIFICATION_RECORDED',
    'BINDING_REJECTED','BINDING_REVOKED','HUMAN_REVIEW_RECORDED'
  )),
  local_consumer_ref text not null check (length(local_consumer_ref) between 16 and 256),
  pp_number_ref text check (pp_number_ref is null or length(pp_number_ref) between 16 and 256),
  palaco_person_ref text,
  external_identity_ref text,
  contact_verification_state text not null default 'UNKNOWN'
    check (contact_verification_state in ('UNKNOWN','PENDING','VERIFIED','REJECTED')),
  identity_state text not null default 'CREATED_UNVERIFIED'
    check (identity_state in ('CREATED_UNVERIFIED','BINDING_PENDING','VERIFIED','REJECTED','REVOKED')),
  created_at timestamptz not null default now(),
  created_by text not null check (length(created_by) between 3 and 128),
  policy_version text not null check (length(policy_version) between 3 and 80),
  authorization_ref text,
  provenance_ref text not null check (length(provenance_ref) between 8 and 256),
  revocation_state text not null default 'NOT_REVOKED'
    check (revocation_state in ('NOT_REVOKED','REVOKED')),
  audit_ref text not null check (length(audit_ref) between 8 and 256),
  source_event_ref text not null unique check (length(source_event_ref) between 8 and 256),
  evidence_digest text check (evidence_digest ~ '^[0-9a-f]{64}$'),
  constraint no_implicit_authority check (
    event_type <> 'PP_ACCOUNT_CREATED' or
    (identity_state = 'CREATED_UNVERIFIED'
     and contact_verification_state = 'UNKNOWN'
     and authorization_ref is null)
  ),
  constraint no_automatic_verified_authority check (
    identity_state <> 'VERIFIED' or authorization_ref is null
  )
);
create index if not exists lineage_events_consumer_time_idx
  on pp_identity.lineage_events (local_consumer_ref, created_at, event_id);
create index if not exists lineage_events_person_time_idx
  on pp_identity.lineage_events (palaco_person_ref, created_at)
  where palaco_person_ref is not null;
alter table pp_identity.lineage_events enable row level security;
alter table pp_identity.lineage_events force row level security;
revoke all on pp_identity.lineage_events from public, anon, authenticated;

-- Defense in depth: even a table owner cannot casually rewrite history.
create or replace function pp_identity.reject_lineage_mutation()
returns trigger language plpgsql set search_path = ''
as $$
begin
  raise exception 'PP_LINEAGE_APPEND_ONLY' using errcode = '55000';
end;
$$;
revoke all on function pp_identity.reject_lineage_mutation() from public, anon, authenticated;
drop trigger if exists pp_lineage_no_update on pp_identity.lineage_events;
create trigger pp_lineage_no_update before update on pp_identity.lineage_events
for each row execute function pp_identity.reject_lineage_mutation();
drop trigger if exists pp_lineage_no_delete on pp_identity.lineage_events;
create trigger pp_lineage_no_delete before delete on pp_identity.lineage_events
for each row execute function pp_identity.reject_lineage_mutation();

-- No INSERT/SELECT grants or permissive RLS policies are introduced.
-- A future trusted ingestion service must validate authenticated ownership,
-- signed provenance, idempotency, review authority and server time before inserting.
commit;
