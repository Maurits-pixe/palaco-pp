# P.P. → bestaande Supabase PALACO — binding v0.1

**Status:** PREPARED / NOT APPLIED / PRODUCTION HOLD  
**Project:** `PALACO`  
**Project ref:** `tflbeiqbykhyyjdmrrvw`  
**Region:** `eu-west-1`  
**Date:** 2026-11-02  
**Authority:** explicit user selection of existing PALACO backend; no live deployment authorization

## Verified inventory (read-only)

The selected project is ACTIVE_HEALTHY and already hosts P.W.G., Bastion, Citadel memory and Levensader tables under `public`, with RLS enabled. The `pp_candidate` schema did **not** exist at inspection time. Never run migrations against or overwrite `pwg_*`, `bastion_*`, `citadel_memory_*`, `levensader_*` or another PALACO namespace.

Supabase security advisor reported:
- Existing INFO: three no-policy tables in other schemas (EARTH and PALACO login lab).
- Existing WARN: leaked-password protection disabled. Enable and verify it before online registration; do not change global Auth settings silently.

## Isolation strategy

Use `design/pp-online-private-schema-v01.sql` as an additive, namespaced **review candidate** only. Before applying:

1. Human review of project ref, SQL and exact target, including no destructive operations.
2. SQL corrected/extended to enforce exact ten options, colors, immutable transitions, ownership of selected option, atomic audit linkage and `PP_ALREADY_SELECTED` responses.
3. Controlled schema installation with RLS and security advisors; schema must not be added to exposed PostgREST schemas until reviewed.
4. Keep production Auth records from existing PALACO services untouched; use synthetic P.P. QA accounts only. A global Auth project shares users and Auth configuration, so the P.P. Site must enforce a **separate P.P. membership/admission gate** beyond authentication.
5. No existing local `data/palaco.sqlite3` data, passwords, sessions, P.P. numbers, notes, or e-mail queue may be uploaded without explicit informed user permission and a reviewed import contract.

## Contract before online Site

The Site must have an authenticated, server-side endpoint that checks both Supabase identity and P.P.-specific admission. Never embed service-role keys, issue grants through static JavaScript, or treat a P.P. number as a key/password. Endpoint writes must be transactional and use least privilege. Offline drafts are not officially registered. A separate owner-only or custom-private Site must not be made public by default.

## Gate state

| Transition | Decision |
| --- | --- |
| Select existing PALACO Supabase project | CONFIRMED |
| Read inventory and advisors | EXECUTED |
| Candidate SQL in GitHub draft | PREPARED |
| Apply candidate SQL to live PALACO database | HOLD — review/authorization |
| New P.P. external accounts or migration | HOLD |
| Private Site publication | HOLD |
| Official P.P. issuance / telecom | DENY |

**TRIAS:** project binding selected, no scope drift.  
**ORACLE:** live project inventory and advisor check performed; no SQL mutation.  
**MENTOR:** close the SQL gate with a reviewed migration and negative RLS tests before building interactive online registration.
