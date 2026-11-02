# PALACO Phone — Online Private Backend Candidate v0.1

**Classification:** IMPLEMENTATION CANDIDATE / NOT DEPLOYED / NOT AUTHORIZED  
**Owner:** Maurits Benjamin / PALACO INDUSTRIE  
**Scope:** `Maurits-pixe/palaco-pp`; candidate SQL in `design/pp-online-private-schema-v01.sql`  
**Decision:** PRIVATE BUILD PREPARATION: GO; EXTERNAL ACCOUNTS, PRODUCTION, OFFICIAL PP ISSUANCE: HOLD

## Baseline from the local app

`server.py` is a Python standard-library HTTP server bound to `127.0.0.1`. It stores accounts, hashed local sessions, batches, options, selections, confirmation email queue, memory notes and audit in local SQLite. The local /check command was reported as 10/10 PASS; the same-context browser acceptance is still not independently demonstrated. The copied `data/palaco.sqlite3` may contain private data; it must not be committed, uploaded or used as an import source without a separate authorized, consent-based migration.

The existing UI may inform the online interface but MUST NOT directly call an offline-only API in production. `browser_acceptance.js` is a useful contract; it is not a cloud test result.

## Target architecture

1. **Private ChatGPT Site:** authenticated owner-only/private audience; `chatgpt.site` is the front door, not the authority to issue identities. Label online prototype clearly.
2. **Backend:** separate *new, explicitly approved* Supabase project or isolated staging environment, Postgres transactional domain functions. Do not reuse P.W.G. `tflbeiqbykhyyjdmrrvw` without a separate explicit choice.
3. **Identity:** Supabase Auth `auth.users.id` maps one-to-one to a P.P. consumer. P.P. number is a non-secret identifier, never a password, recovery factor, or encryption key. No automatic mapping from a local username to a real person.
4. **Storage:** `pp_candidate` schema as a read-only structural proposal. No hosted account, P.P. option, selection or mail transfer yet.
5. **Authorization:** RLS limits user reads to their own rows; public/anonymous access denied. No client writes. All future mutations require a separately reviewed authenticated transaction function with least privilege, event insertion, rate limits and consistent errors. No service-role key in browser or Site static assets.
6. **Offline-first:** client-side drafts/cache may function offline, but live identity, selected-number uniqueness, revocation and authorization require online server verification. An offline number is a *draft*, never a registered global P.P. number.

## Invariants to port before any interactive online preview

- Ten globally unique 10-digit candidate numbers per authenticated consumer; exactly one persistent batch and exactly four represented colors; stable position, color and number through reload.
- One final selection per consumer even under racing requests; `BEGIN`-equivalent transactional locking and unique constraints. Selection marks nine alternatives EXPIRED and emits one event atomically.
- Revocation is monotonic and cannot reopen selection or create a fresh batch. `PP_ALREADY_SELECTED` with HTTP 409 is required on any reselection, including after revocation.
- Storage-level immutable identity/status transitions; append-only event trace for offered, selected, revoked. Never allow a client to directly modify options, selections, events or user roles.
- API requires an authenticated identity, validates Origin/CSRF where cookies are used, rate-limits auth and selection requests, denies cross-account access and avoids user enumeration.
- No telecom assignment, SMS, WhatsApp, official issuance, verified identity claims or signed certificate. UI, API and events say `LOCAL/PRIVATE DEMO · UNVERIFIED`.

## Migration boundary

**Phase A — this PR:** schema draft, architecture and gate, no Supabase application, no credentials, no public site and no SQLite export.  
**Phase B — staging only, separate authorization:** create an isolated staging Supabase project; verify SQL with RLS/advisors, negative unauthenticated and cross-consumer tests; add reviewed server-side functions in a subsequent PR.  
**Phase C — private test site:** build a separate online adapter and private Site; do not include `data/` or user secrets. Register entirely synthetic test users.  
**Phase D — candidate validation:** test 10 options, four colors, reload, concurrency, revoke/reload, 409 on reselect, unauthorized data access, offline uncertainty, crash/replay, mobile and keyboard. Collect build SHA, deployment ID, test date, browser/device and evidence reference.  
**Phase E — explicit human gate:** privacy/security review, key and recovery management, backup/retention policy, user consent for any real-data migration, cost acceptance, and independent reviewer. Until then production remains HOLD.

## Known gaps in this schema candidate

- No user provisioning flow or authenticated mutation functions are implemented.
- Full cross-table invariants (exactly 10 options and all four colors, option ownership on selection, transactional event correspondence, immutable state and audit) are not yet enforced by this SQL. **Do not deploy or expose it as a functional registration backend.**
- Encrypted private memory notes, offline sync conflict handling, mail queue, admin dashboard and account recovery need separate contracts.
- Supabase schema API exposure, application claims and platform-specific private Site authentication are not configured.

## Acceptance record

| Control | State |
| --- | --- |
| Source-model read | INSPECTED (`server.py`) |
| Local SQLite self-check | PASS_CLAIMED by user, not reproduced here |
| Schema candidate authored | PREPARED, not applied |
| SQL execution / Supabase advisors | NOT EXECUTED |
| Same-context browser acceptance | NOT EXECUTED here |
| External account/user migration | DENY |
| Official P.P. issuance / production | HOLD |

**TRIAS:** separates prototype capability from authority.  
**ORACLE:** source-backed design; no database or browser execution evidence.  
**MENTOR:** first review the schema, then add transaction functions and negative tests on staging, followed by private UI deployment.
