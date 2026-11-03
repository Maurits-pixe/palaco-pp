# PP-IDB-001 — PALACO Phone identity lineage contract (DRAFT)

Status: **CONDITIONAL GO for internal development; HOLD for merge, deployment, production, issuance and authorization.**

## Grounded current behavior

The local prototype uses SQLite and already creates an `ACCOUNT_CREATED` audit record inside the same transaction as registration. This is a **local account creation**, not identity proof. The local `consumer_id`, a future PALACO Person ID, GitHub ID and selected P.P. number are distinct identifiers.

## Candidate Supabase schema

`supabase/candidates/pp_idb_001.sql` is **not** a deployed migration. It creates a private `pp_identity` schema with an append-only event ledger, no exposed Data API access, no authenticated or anonymous grants, and no permissive RLS policies.

The ledger stores **opaque references**, never the full P.P. number or plaintext contact details. Do not place a raw consumer ID, contact address, GitHub access token, password, session token, or personal profile data in provenance or audit fields. References must be generated or pseudonymized by a future trusted adapter. A raw SHA-256 of a low-entropy phone number is insufficient pseudonymization; use a protected server-side keyed reference.

## Identity-event matrix

| Event | Required independent evidence | Effect |
| --- | --- | --- |
| `PP_ACCOUNT_CREATED` | Local registration audit event and deduplication reference | `CREATED_UNVERIFIED`, no authority |
| `PERSON_BINDING_PROPOSED` | Trusted person ID and proof reference | `BINDING_PENDING` only |
| `EXTERNAL_BINDING_PROPOSED` | Fresh provider assertion bound to the same user | No authority |
| `CONTACT_VERIFICATION_RECORDED` | Time-bound proof of challenge completion | Evidence only |
| `HUMAN_REVIEW_RECORDED` | Authenticated administrator with separate review policy | Advisory record; no automatic grant |
| `BINDING_REJECTED` / `BINDING_REVOKED` | Reason and operator evidence | Deny/HOLD; never erase history |

Do **not** infer an individual's identity from the username `maurits` or from the GitHub repository owner. The designation “De Architect” is lineage context, not a grant.

## Offline-first ingestion protocol (not yet implemented)

1. Record local occurrence in the existing SQLite append-only audit.
2. Queue a minimal opaque event envelope with a random idempotency key, schema/policy version and local sequence; encrypt sensitive queue contents at rest.
3. On connectivity, authenticate to the trusted ingestion service; send over TLS and await a server-issued receipt.
4. Server validates account ownership, replay/idempotency, allowed event transitions, payload digest and trusted time. A client clock is never trusted for authorization.
5. Preserve local event and receipt independently. Discrepancies stay in `SYNC_REVIEW_REQUIRED`; never auto-grant rights or silently overwrite.

## Before connection to PALACO MONO

- Inspect current project and its existing schema/RLS; check for naming conflicts.
- Verify exact Supabase project ownership; do not hardcode or guess project IDs.
- Design ingestion with least-privilege server identity and explicit per-actor proof, never browser-side service-role keys.
- Execute in a disposable test environment first, then run security advisors, negative RLS tests, duplicate replay tests, immutability tests, offline retry tests, cross-account isolation tests and reconciliation tests.
- Require independent review and a separate human GO before any production migration or official EDTR issuance.

This branch intentionally does **not** change `server.py`, credentials, live data, account authorization, or existing sessions.


## PP-IDB-002 — atomic local integration candidate

The existing `Store.register_account()` now calls `enqueue_identity_event()` inside its existing SQLite `BEGIN IMMEDIATE` transaction, **after** the existing `ACCOUNT_CREATED` audit entry. A failed outbox insert rolls back the account, audit entry, and session rotation together. The lineage payload contains an independently random local reference; its provenance points to the local audit sequence. The local audit remains the authoritative account-to-event join **within this prototype**, not a verified PALACO Person ID.

The integration intentionally does not send events, mark contact details verified, connect to Supabase, or grant authority. It does not backfill pre-existing accounts. Existing users need a separately reviewed migration strategy, not silent event forgery.

Offline events currently carry only random references and event metadata; **encrypted storage at rest, trusted receipt verification, cross-device identity binding, and authenticated synchronization are not implemented**. SQLite append-only triggers prevent ordinary UPDATE/DELETE queries but do not protect against a privileged local filesystem attacker.

Tests added in `test_identity_integration.py`: atomic registration, injected outbox failure rollback, duplicate registration, offline persistence across reopen, and SQL trigger rejection rollback. The separate CI workflow is `.github/workflows/pp-idb-001.yml`. A committed test file is not evidence of PASS: record the exact GitHub Actions run result before marking verification complete.

**Release gate:** remain DRAFT / HOLD until tests execute successfully, the real app is smoke-tested, local database recovery is examined, and a human reviewer accepts changes.
