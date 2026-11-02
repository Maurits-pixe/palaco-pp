-- PALACO Phone hardening candidate v0.2
-- REQUIRES pp-online-private-schema-v01.sql; DO NOT APPLY TO LIVE PALACO.
-- Structural guards only. Does not expose writable APIs or issue identifiers.
begin;

create or replace function pp_candidate.reject_mutation()
returns trigger language plpgsql set search_path = pg_catalog as $$
begin
  raise exception 'PP_IMMUTABLE' using errcode = '23514';
end;
$$;

create trigger pp_batches_no_update
before update or delete on pp_candidate.batches
for each row execute function pp_candidate.reject_mutation();

create trigger pp_events_append_only
before update or delete on pp_candidate.events
for each row execute function pp_candidate.reject_mutation();

create or replace function pp_candidate.guard_option_update()
returns trigger language plpgsql set search_path = pg_catalog as $$
begin
  if new.id is distinct from old.id
     or new.batch_id is distinct from old.batch_id
     or new.position is distinct from old.position
     or new.pp_number is distinct from old.pp_number
     or new.color is distinct from old.color
     or new.offered_at is distinct from old.offered_at then
    raise exception 'PP_OPTION_IDENTITY_IMMUTABLE' using errcode = '23514';
  end if;
  if not (
     (old.state = 'OFFERED' and new.state in ('ACTIVE','EXPIRED'))
     or (old.state = 'ACTIVE' and new.state = 'REVOKED')
  ) then
    raise exception 'PP_OPTION_TRANSITION_INVALID' using errcode = '23514';
  end if;
  return new;
end;
$$;

create trigger pp_options_guard_update
before update on pp_candidate.options
for each row execute function pp_candidate.guard_option_update();

create trigger pp_options_no_delete
before delete on pp_candidate.options
for each row execute function pp_candidate.reject_mutation();

create or replace function pp_candidate.guard_selection_insert()
returns trigger language plpgsql set search_path = pg_catalog as $$
declare owns_option boolean;
begin
  select exists (
    select 1 from pp_candidate.options o
    join pp_candidate.batches b on b.id = o.batch_id
    where o.id = new.option_id
      and b.id = new.batch_id
      and b.consumer_id = new.consumer_id
      and o.state = 'ACTIVE'
  ) into owns_option;
  if not owns_option or new.revoked_at is not null then
    raise exception 'PP_SELECTION_OPTION_MISMATCH' using errcode = '23514';
  end if;
  return new;
end;
$$;

create trigger pp_selections_guard_insert
before insert on pp_candidate.selections
for each row execute function pp_candidate.guard_selection_insert();

create or replace function pp_candidate.guard_selection_update()
returns trigger language plpgsql set search_path = pg_catalog as $$
declare is_revoked boolean;
begin
  if new.consumer_id is distinct from old.consumer_id
     or new.option_id is distinct from old.option_id
     or new.batch_id is distinct from old.batch_id
     or new.selected_at is distinct from old.selected_at
     or old.revoked_at is not null
     or new.revoked_at is null then
    raise exception 'PP_SELECTION_TRANSITION_INVALID' using errcode = '23514';
  end if;
  select exists (
    select 1 from pp_candidate.options o
    where o.id = new.option_id
      and o.batch_id = new.batch_id
      and o.state = 'REVOKED'
  ) into is_revoked;
  if not is_revoked then
    raise exception 'PP_SELECTION_OPTION_NOT_REVOKED' using errcode = '23514';
  end if;
  return new;
end;
$$;

create trigger pp_selections_guard_update
before update on pp_candidate.selections
for each row execute function pp_candidate.guard_selection_update();

create trigger pp_selections_no_delete
before delete on pp_candidate.selections
for each row execute function pp_candidate.reject_mutation();

-- No grants for INSERT/UPDATE/DELETE or service entrypoints are added.
commit;
