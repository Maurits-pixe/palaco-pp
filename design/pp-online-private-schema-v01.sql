-- PALACO Phone / P.P. online-private schema CANDIDATE v0.1
-- REVIEW ONLY. Do not apply to any production or existing P.W.G. project.
-- No issuer functions, outbound mail, telecom interfaces, or elevated app roles.
begin;
create schema if not exists pp_candidate;

create table pp_candidate.consumers (
  user_id uuid primary key references auth.users(id) on delete restrict,
  created_at timestamptz not null default now()
);
create table pp_candidate.batches (
  id uuid primary key default gen_random_uuid(),
  consumer_id uuid not null unique references pp_candidate.consumers(user_id),
  created_at timestamptz not null default now()
);
create table pp_candidate.options (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references pp_candidate.batches(id),
  position smallint not null check (position between 1 and 10),
  pp_number text not null unique check (pp_number ~ '^[1-9][0-9]{9}$'),
  color text not null check (color in ('blue','red','green','yellow')),
  state text not null default 'OFFERED'
    check (state in ('OFFERED','ACTIVE','EXPIRED','REVOKED')),
  offered_at timestamptz not null default now(),
  unique (batch_id, position),
  unique (batch_id, id)
);
create table pp_candidate.selections (
  consumer_id uuid primary key references pp_candidate.consumers(user_id),
  batch_id uuid not null references pp_candidate.batches(id),
  option_id uuid not null unique,
  selected_at timestamptz not null default now(),
  revoked_at timestamptz,
  foreign key (batch_id, option_id)
    references pp_candidate.options(batch_id, id)
);
create table pp_candidate.events (
  sequence bigint generated always as identity primary key,
  consumer_id uuid not null references pp_candidate.consumers(user_id),
  event_type text not null check (
    event_type in ('OPTION_OFFERED','NUMBER_SELECTED','NUMBER_REVOKED')
  ),
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Defensive default: only authenticated reads of self-owned rows.
-- No client INSERT, UPDATE, DELETE or RPC in this candidate.
alter table pp_candidate.consumers enable row level security;
alter table pp_candidate.batches enable row level security;
alter table pp_candidate.options enable row level security;
alter table pp_candidate.selections enable row level security;
alter table pp_candidate.events enable row level security;

create policy consumers_self_read on pp_candidate.consumers
  for select to authenticated using (user_id = (select auth.uid()));
create policy batches_self_read on pp_candidate.batches
  for select to authenticated using (consumer_id = (select auth.uid()));
create policy options_self_read on pp_candidate.options
  for select to authenticated using (
    exists (select 1 from pp_candidate.batches b
      where b.id = batch_id and b.consumer_id = (select auth.uid()))
  );
create policy selections_self_read on pp_candidate.selections
  for select to authenticated using (consumer_id = (select auth.uid()));
create policy events_self_read on pp_candidate.events
  for select to authenticated using (consumer_id = (select auth.uid()));

-- These grants have no write equivalent. Schema API exposure remains off
-- until an independently reviewed deployment phase.
grant usage on schema pp_candidate to authenticated;
grant select on all tables in schema pp_candidate to authenticated;
revoke all on all tables in schema pp_candidate from anon;
commit;
