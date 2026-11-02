# PALACO Phone — Backend negative acceptance matrix v0.2

**State: SPECIFICATION / NOT EXECUTED.** Target: existing PALACO Supabase project, isolated `pp_candidate` namespace after separate authorized review. Do not run tests against live users. Do not apply the candidate SQL during this stage.

## Test fixtures

- Two distinct synthetic Auth users A and B, each admitted explicitly to the P.P. candidate app; an unauthenticated user N.
- Deterministic test numbers are *never* genuine P.P. registrations. Use an isolated staging transaction and rollback or a disposable review environment.
- Each case records the exact schema revision/commit, principal claims, request and HTTP/SQL result, timestamp and log reference. Redact tokens and session cookies.

## Negative security and integrity checks

| ID | Setup/action | Expected |
| --- | --- | --- |
| RLS-01 | N reads consumers, batches, options, selections, events | DENY / no records |
| RLS-02 | A queries B's rows using direct REST or SQL under A claims | Zero visible B rows |
| RLS-03 | A issues direct INSERT/UPDATE/DELETE against any candidate table | DENY |
| RLS-04 | A guesses B's option UUID | No disclosure, same error as unknown option |
| IMM-01 | Privileged transaction attempts changing batch ID/consumer | `PP_IMMUTABLE` |
| IMM-02 | Change option number, color, position or batch | `PP_OPTION_IDENTITY_IMMUTABLE` |
| IMM-03 | Revert `ACTIVE` to `OFFERED` or `REVOKED` to `ACTIVE` | `PP_OPTION_TRANSITION_INVALID` |
| IMM-04 | Delete an option or selection | `PP_IMMUTABLE` |
| IMM-05 | Update or delete event | `PP_IMMUTABLE` |
| SEL-01 | Insert selection for another consumer's active option | `PP_SELECTION_OPTION_MISMATCH` |
| SEL-02 | Insert selection while option is `OFFERED` | `PP_SELECTION_OPTION_MISMATCH` |
| SEL-03 | Change selection's identity/selected time | `PP_SELECTION_TRANSITION_INVALID` |
| SEL-04 | Update revocation without option in `REVOKED` | `PP_SELECTION_OPTION_NOT_REVOKED` |
| SEL-05 | Set revoked selection back to active | `PP_SELECTION_TRANSITION_INVALID` |
| SEL-06 | Two concurrent selection requests for same consumer | Exactly one success; second 409 `PP_ALREADY_SELECTED` |
| SEL-07 | Re-select after revocation | 409 `PP_ALREADY_SELECTED`, no state change |
| BATCH-01 | Create/reload batch for one user twice/concurrently | Same ten numbers/order/colors, four colors represented |
| AUD-01 | Select, expire nine, append event, then forced error before commit | All rolled back |
| AUD-02 | Successful select then revoke | Exactly one matching event of each type; append-only |
| AUTH-01 | Existing PALACO Auth user lacks P.P. admission | DENY P.P. access |
| OFF-01 | Offline/local draft attempts official activation | DENY; no cloud mutation |

## Additional review blockers

`v0.2` only adds *structural triggers*. It does not provide authenticated server-side `offer/select/revoke` functions, atomic append-only event correlation, the exactly-ten-and-four-colors batch invariant, an admission gate, rate limiting, retention, private online Site or browser acceptance. Even if the SQL validates, the system is not a functional online P.P. registration.

Before any apply: independent SQL/security review, advisor scan, staging rollback proof, transaction/RPC implementation and end-to-end negative tests. Keep production and official issuance HOLD.

**TRIAS:** fail-closed boundary preserved. **ORACLE:** no runtime evidence claimed. **MENTOR:** implement the three transactional functions and test them in a disposable staging environment next.
