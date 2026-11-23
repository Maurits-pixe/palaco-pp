# PALACO-PP | PP-RECOVERY-002 | Release Boundary Snapshot v1

Status: **DRAFT / HOLD / DENY**. No production deployment, recovery authorization, account binding, telecom activation or new number issuance.

## Purpose

`review_044_release_boundary_snapshot.py` checks the structural denial states in an **untrusted** existing `palaco.pp.recovery-002-release-readiness.v0` JSON report. It produces a minimal SHA-256-linked decision-boundary snapshot without copying personal identifiers. It cannot authenticate the source, validate independent reviewer signatures, verify the historical record, or issue permissions. A successful structural match is **never** an approval.

## Manual, synthetic-only test (not yet executed as part of this change)

```powershell
python -m unittest -v test_review_044_release_boundary_snapshot
```

The tests cover malformed JSON, duplicate keys, over-size input, privilege escalation, blocked-gate consistency and privacy. No database or real accounts are needed.

## Integration contract

1. Generate the readiness report using the existing offline `review_044_release_readiness.py` contract.
2. Supply its serialized UTF-8 JSON bytes to `review_boundary_snapshot(report_bytes)`.
3. Any `BoundaryInputError` means **reject**: do not display readiness as passed, do not continue a recovery workflow.
4. If the result is returned, it still explicitly states `HOLD`, `DENY`, `NOT_AUTHORIZED`, `NOT_READY` and `BLOCKED`.
5. **Do not** expose this function as a production recovery endpoint or use it as an authentication, trust-anchor or approval service.

This component is a defensive audit aid. Source authenticity, independent human verification, safe deployment and PALACO One integration remain outside this scope.


## Offline CLI (explicit opt-in)

```powershell
python .\\review_044_release_boundary_snapshot_cli.py --run --report .\\readiness.json
python .\\review_044_release_boundary_snapshot_cli.py --run --report .\\readiness.json --export .\\boundary-snapshot.json
python -m unittest -v test_review_044_release_boundary_snapshot test_review_044_release_boundary_snapshot_cli
```

The CLI refuses to run without `--run`, limits source reads to 64 KiB,
rejects symlink inputs, and creates exports exclusively (no overwrite).
It does not read the P.P. database. The CLI returns a structural inspection,
not trusted verification, identity recovery, an approved account binding,
or authorization to deploy.

**Execution note (22 November 2026):** source and tests were committed to
the draft branch; automated execution in the working environment could not
be completed because GitHub host name resolution failed while cloning.
Test status is **NOT EXECUTED**, not PASS. Owner review remains HOLD.


## Recovery boundary reconciliation (draft v3, 22 November 2026)

`review_044_boundary_reconciliation.py` compares two **untrusted** boundary
snapshots. It enforces the precise v1 snapshot field allowlist, denial states,
valid lowercase SHA-256 digest shape, and a positive integer blocked-gate
count. It compares the reported source digest and gate count, returning
`MATCH_UNTRUSTED` or `MISMATCH`. **Even a match is not evidence of two
independent reviews**, as anyone can copy an unsigned snapshot. No
authenticated PALACO ONE session, P.P. issuance, recovery permission or
release authority results from either outcome.

Manual synthetic-only regression command (execution not yet verified):

```powershell
python -m unittest -v test_review_044_release_boundary_snapshot test_review_044_release_boundary_snapshot_cli test_review_044_boundary_reconciliation
```

Code and tests committed to the existing draft branch; maintain
**HOLD / DENY / NOT_AUTHORIZED** pending independently observed execution
and authorized human review.


## Unsigned evidence inventory / hash-chain v4 (22 November 2026)

The added `review_044_evidence_manifest.py` composes up to 32
bounded, structurally inspected pairs of comparison snapshots into a
deterministic in-memory manifest. Each record includes a SHA-256 digest
of its predecessor. Input duplication is rejected including reversed
pair order. `validate_evidence_manifest` checks the hash chain,
a strict key allowlist, required denial states, SHA-256 digest syntax
and recorded comparisons.

The hash chain does **not** make a local file tamper-proof; anyone who
controls the file can regenerate all its digests. The result explicitly
remains `STRUCTURALLY_CONSISTENT_UNTRUSTED`, `HOLD`, `DENY` and
`NOT_AUTHORIZED`. It grants no issuer/reviewer authority and never
identifies the owner.

New manual synthetic-only regression command:

```powershell
python -m unittest -v test_review_044_evidence_manifest
```

**Execution status:** GitHub writes succeeded; runtime test execution
has not been observed. Direct repository cloning from this execution
environment failed on DNS lookup for github.com. Consequently no
PASS claim is made. Production / merging remains HOLD.


## Detached Ed25519 inspection (draft v5, 22 November 2026)

`review_044_detached_signature_inspection.py` performs *mathematical*
Ed25519 verification over the exact manifest bytes with the fixed
domain-separation prefix `PALACO-PP-RECOVERY-002-MANIFEST-ED25519-V1\\0`.
The public key is caller-supplied and untrusted. This operation neither
enrolls an issuer nor verifies key provenance, revocation, trusted
timestamps, reviewer authority or replay prevention. Even a valid
signature returns `VALID_UNTRUSTED_KEY` plus `HOLD/DENY`.

The optional test dependency is the Python `cryptography` package.
The application runtime does not import it until inspection is invoked;
when unavailable, inspection fails closed. No signing keys are stored
or shipped.

Synthetic-only tests (not yet executed in this environment):

```powershell
python -m pip install cryptography
python -m unittest -v test_review_044_detached_signature_inspection
```

The tests generate ephemeral test-only signing keys; no live accounts,
production identities or P.P. registrations are touched. A genuine
trust decision requires a separately governed trust-anchor registry,
revocation freshness, an atomic replay ledger, independent reviewer
authentication and an authorized human release decision. None of
these controls are provided by the new module.

**Verification status:** GitHub commits confirmed; runtime tests not
verified. GitHub DNS resolution failed from the local execution
container on 22 November 2026. Merge, issuance and deployment remain
**HOLD / DENY**.


## Parser size-bound correction (draft v6, 22 November 2026)

Previously the manifest validator checked for a maximum of 512 KiB
and then passed data to the shared 64-KiB JSON parser. The shared
parser now accepts a bounded, explicit `max_bytes` parameter,
which the manifest validator sets to `MAX_TOTAL_BYTES` (512 KiB).
Other callers retain the original 64-KiB default. Invalid size-limit
types including bool, limits greater than 512 KiB, duplicate JSON
keys and oversized inputs fail closed.

Two synthetic regression methods were added in
`test_review_044_evidence_manifest.py`. They exercise the parser
boundary directly; they do not imply that a large arbitrary JSON
object passes the manifest's stricter document schema.

Run explicitly:

```powershell
python -m unittest -v test_review_044_evidence_manifest test_review_044_release_boundary_snapshot test_review_044_detached_signature_inspection
```

**Execution status:** code and test changes committed. Automated
runtime test results have not yet been observed for v6. No merge,
production rollout or authorization granted. HOLD / DENY.


## Automated regression workflow v7 (2026-11-22)

Added `.github/workflows/pp-recovery-draft.yml` for branch pushes,
relevant pull-request changes, and manual dispatch. Jobs run on
Python 3.11 and 3.12 with read-only repository permission. They
install the optional cryptography verifier, parse the review module
syntax, run the five synthetic unittest modules for recovery
boundary, CLI, reconciliation, evidence manifest and detached
signature inspection, and assert the release boundary remains
HOLD / DENY / NOT_AUTHORIZED / BLOCKED.

The workflow has **no** merge, artifact upload, privileged secret
access, production deployment, trust-root enrollment or account
mutation step. Synthetic test success does not constitute a
security audit or release authorization.

At the time this change was committed, commit-status and
PR-associated workflow-run queries returned no entries. Therefore
execution remains **NOT VERIFIED**, not PASS. A maintainer must
confirm GitHub Actions is enabled and inspect the actual run
conclusions and logs before recording tests as verified.


## Strict CI execution policy v8 (2026-11-22)

The added `pp_recovery_strict_ci_runner.py` executes the five
synthetic recovery test suites. It fails with a nonzero exit code if
any suite is missing or empty, if no tests execute, or if any test
fails, errors, skips, is expected to fail, or succeeds unexpectedly.
This addresses the risk of marking Ed25519 regression coverage as
passing when the optional cryptographic dependency is absent.

`test_pp_recovery_strict_ci_runner.py` adds policy regression
checks for argument rejection, empty suites, skipped tests and
zero tests executed. The GitHub workflow runs these first, then
the strict synthetic suite, both on Python 3.11 and 3.12.

The CLI test runner does not deploy anything, trust keys,
promote identities or connect PALACO ONE. GitHub commits
do **not** constitute proof of CI execution: inspect the Actions
conclusion and logs. Review / merge / production remain HOLD.


## Trust-anchor proposal preflight v9 (22 November 2026)

`review_044_trust_anchor_preflight.py` checks an **untrusted**
issuer/key-fingerprint proposal with an explicit 16 KiB input cap,
strict schema, fixed purpose, fixed Ed25519 algorithm and
`PENDING_INDEPENDENT_REVIEW` state. The proposal contains only
a public-key SHA-256 fingerprint, not a key or cryptographic proof
of possession. Structural acceptance means **no key enrollment**
and **zero trusted issuers**. This is not issuer identity
verification, revocation verification, reviewer authorization,
or trust-anchor configuration.

`test_review_044_trust_anchor_preflight.py` adds synthetic negative
and privacy tests. The strict CI runner includes the suite.

```powershell
python -m unittest -v test_review_044_trust_anchor_preflight
python pp_recovery_strict_ci_runner.py
```

The branch remains DRAFT. GitHub commits have been confirmed,
but CI success and independent review have not been confirmed.
No release, trust promotion, registration change or merge.
**HOLD / DENY / NOT_AUTHORIZED.**


## Candidate-key binding v10 (22 November 2026)

`review_044_proposed_key_binding.py` joins the existing *untrusted*
trust-anchor preflight to detached Ed25519 mathematical verification:
the SHA-256 fingerprint declared in a candidate proposal must match
the exact 32-byte public key used to verify the domain-separated
manifest signature. A mismatched fingerprint, malformed proposal,
altered signature or altered manifest fails closed.

**No trust decision:** a caller can generate its own key and proposal.
`FINGERPRINT_MATCH_UNTRUSTED` is only a consistency observation and
never authenticates an issuer, reviewer or owner. Key revocation,
independent trust anchors, replay protection, PALACO ONE handoff,
issuance and deployment remain unimplemented or BLOCKED.

Six synthetic test methods in
`test_review_044_proposed_key_binding.py` are included in the
strict CI suite (skips cause CI failure). No actual run result has
been established in this development round; manual test command:

```powershell
python -m unittest -v test_review_044_proposed_key_binding
python pp_recovery_strict_ci_runner.py
```

Release status: **HOLD / DENY / NOT_AUTHORIZED**. No merge.


## Semantic duplicate-evidence hardening (draft v11, 22 November 2026)

Previously the manifest builder deduplicated pairs using SHA-256 of
the **raw serialized** snapshot bytes. Two identical snapshot objects
with different JSON whitespace or object-key ordering could bypass
the duplicate check. The builder now computes an internal pair key
from each strictly parsed, canonicalized JSON object. It recognizes
identical content regardless of formatting and pair order, while
retaining raw snapshot SHA-256 values in output for exact-byte
traceability. Two additional synthetic regression methods cover
these cases.

`validate_evidence_manifest` cannot independently reconstruct
semantic deduplication from only raw snapshot hashes. Therefore
**validation of a standalone unsigned manifest does not establish
that its underlying source documents are unique**. External evidence
availability and trusted auditing are still required.

Manual regression command:
```powershell
python -m unittest -v test_review_044_evidence_manifest
python pp_recovery_strict_ci_runner.py
```

**Status:** code and regression tests committed; GitHub CI PASS
not yet independently established. HOLD / DENY / NOT_AUTHORIZED.


## Logical self-consistency of evidence (draft v12, 22 November 2026)

The evidence-manifest verifier now rejects impossible comparison claims
for entries with **identical raw snapshot digests**. In that case, a
reported mismatch in source digest, blocked-gate count or comparison
is contradictory, regardless of whether the unsigned hash chain has
been recalculated. Two regression methods explicitly recompute the
record hash after modifying the flags and require rejection.

This is a narrow consistency safeguard, not proof of identity, origin,
independent signatures, freshness or chain-of-custody. Nonidentical
snapshot digests still cannot establish trusted equality or inequality
of underlying subject identity without source documents.

Manual command:
```powershell
python -m unittest -v test_review_044_evidence_manifest
python pp_recovery_strict_ci_runner.py
```

Testing remains **NOT VERIFIED**: the local container still cannot
resolve github.com for a clone, and no successful CI status was
observed for this round. No release, merge, key promotion or P.P.
registration changes. HOLD / DENY / NOT_AUTHORIZED.


## Unsigned key-revocation claim inspection (draft v13, 22 November 2026)

`review_044_unsigned_revocation_notice.py` checks an unsigned
revocation **claim** against the existing pending trust-anchor
proposal. The notice must use the exact expected schema and declare
the same issuer ID, candidate key ID, and SHA-256 public-key
fingerprint. JSON with duplicate keys, unknown fields, malformed or
oversized data, mismatched subjects, or a misleading `ACTIVE` or
`NOT_REVOKED` claim is rejected.

The output is only an untrusted, privacy-minimized observation:
`REVOKED_UNTRUSTED`, `NOT_VERIFIED`, `HOLD`, `DENY` and
`NOT_AUTHORIZED`. The module never asserts that the key is
safe, imports a trust anchor, applies revocation, re-enables a key,
or changes a real account. Absence of a notice is **not** proof
of non-revocation. Trusted issuer signatures, trusted time and
revocation-feed freshness require independent infrastructure.

Six synthetic unittest methods are included in the strict CI runner.

```powershell
python -m unittest -v test_review_044_unsigned_revocation_notice
python pp_recovery_strict_ci_runner.py
```

**Build state:** committed to the draft branch only. Runtime PASS
has not been verified; release remains **HOLD / DENY**.


## Mathematical revocation signature inspection (draft v14, 22 November 2026)

`review_044_revocation_signature_inspection.py` extends the untrusted
revocation-claim reader with exact-byte, domain-separated Ed25519
mathematical verification. The public key must match the pending
candidate's SHA-256 fingerprint; a wrong key, invalid signature or
signature copied from another domain is rejected. Seven synthetic
test methods were added in
`test_review_044_revocation_signature_inspection.py` and included
in the strict CI runner (skipped cryptographic tests cause CI failure).

The signing key is supplied by the caller and remains **untrusted**.
A caller can self-sign a notice. No authentic issuer has been
established, no authoritative revocation feed has been checked and
no timestamp, replay ledger, independent review or trust root is
configured. Therefore even mathematical success returns
`VALID_UNTRUSTED_KEY`, `NOT_VERIFIED`, `HOLD`,
`DENY`, `NOT_AUTHORIZED` and `BLOCKED`.

Manual synthetic-only checks:

```powershell
python -m unittest -v test_review_044_revocation_signature_inspection
python pp_recovery_strict_ci_runner.py
```

GitHub changes are committed to the **draft** branch. Test
execution has not been independently verified. No merge,
number issuance, trusted key enrollment, identity recovery or
production deployment.


## Explicit trust-prerequisite denial (draft v15, 22 November 2026)

The release boundary previously checked top-level HOLD/DENY and
blocked gate states, but did not validate the *canonical* readiness
producer's additional trust fields. A conflicting report could
therefore claim `sourceAuthenticity: VERIFIED` or
`reviewerAuthority: ESTABLISHED` while retaining HOLD/DENY.

The boundary now requires:
- `manualDecision: REQUIRED_OUTSIDE_THIS_MODULE`
- `sourceAuthenticity: NOT_ESTABLISHED`
- `subjectBinding: NOT_ESTABLISHED`
- `reviewerAuthority: NOT_ESTABLISHED`
- a nonempty bounded list of unique string `globalBlockers`

These fields are already emitted by the existing
`review_044_release_readiness.py` producer. The synthetic fixture
has been updated and three regression methods added for trust
promotion, missing requirements and malformed blockers.

No source identity is authenticated by this check. No authority,
P.P. issuance, account binding, merge or deployment occurs.
Tests have not been independently executed in this round.
**HOLD / DENY / NOT_AUTHORIZED**.


## Canonical global-blocker enforcement (draft v16, 22 November 2026)

The release boundary now requires **all six global blocker codes
in their canonical order**, matching the existing
`review_044_release_readiness.py` producer. Nonempty arbitrary lists
are no longer accepted. This includes rejection of omitted, fake,
extra, repeated and reordered blocker claims.

The expected tuple is a deliberate fail-closed mirror in the minimal
release boundary, avoiding a dependency on the producer's deeper
module imports. A producer contract change will require deliberate
review and update rather than silently weakening the check.
The synthetic boundary fixture now includes the producer's six
codes; a new regression method tests incomplete and forged lists.

```powershell
python -m unittest -v test_review_044_release_boundary_snapshot
python pp_recovery_strict_ci_runner.py
```

Changes were committed on the draft branch only. No independent
runtime test PASS is claimed; no merge or release occurred.
**HOLD / DENY / NOT_AUTHORIZED**.


## Canonical review-gate identity validation (draft v17, 22 November 2026)

The release-boundary validator now rejects synthetic placeholder gates
and validates the exact five gate identities in their original order:
SOURCE_ATTESTATION, CROSS_SOURCE_SUBJECT, OWNER_AUTHORITY,
RUNTIME_EXECUTION and HUMAN_REVIEW. It checks each gate's canonical
description, manual action, required check order and six-check ID
mapping, as well as `NOT_STARTED`, `NOT_VERIFIED`,
`BLOCKED`, `NOT_READY` and exact integer counts.

This mirrors the existing producer's `REQUIREMENTS`,
`GATE_PREREQUISITES`, `CHECKS` and `_NEXT_ACTIONS`
without importing production identity processing into the minimal
boundary component. The shared synthetic fixture now represents
five real contract-shaped gates instead of two placeholders.
Three regression methods cover reordered/duplicated gates,
fake completed evidence, wrong metadata and counts.

The inspection remains **structural and untrusted**: it does not
authenticate the source files, reviewer or owner.

```powershell
python -m unittest -v test_review_044_release_boundary_snapshot
python pp_recovery_strict_ci_runner.py
```

No successful CI execution was verified in this turn.
Release, merge and authorization remain **HOLD / DENY**.


## Static producer/boundary contract parity (draft v18, 22 November 2026)

The fail-closed boundary deliberately mirrors four independent producer
declarations. New `test_review_044_contract_parity.py` now extracts
the static declarations using the Python AST **without executing**
the original recovery stack or importing real account/database
integrations. It compares the exact sequence of:
- original `REQUIREMENTS` names and descriptions;
- `GATE_PREREQUISITES` and corresponding `_NEXT_ACTIONS`;
- the six `CHECKS` identifiers;
- the six `GLOBAL_BLOCKERS` codes.

Seven synthetic unit methods exercise current source parity, renamed
gates/checks/blockers/actions, dynamic expression refusal and ambiguous
declaration rejection. The test is part of the strict CI suite:
changes to either producer or boundary declarations cannot silently
drift through a successful test run.

Run manually in the repository:
```powershell
python -m unittest -v test_review_044_contract_parity
python pp_recovery_strict_ci_runner.py
```

**Evidence limitation:** A code commit is not evidence that CI ran.
No successful CI outcome has been established by this update.
Production and authorization remain **HOLD / DENY / NOT_AUTHORIZED**.


## Synthetic end-to-end recovery-chain regression (draft v19, 22 November 2026)

`test_review_044_recovery_chain_e2e.py` now links the release
boundary, reconciled snapshots, evidence manifest, candidate-key
Ed25519 binding, and domain-separated revocation observation in one
**synthetic-only** unittest suite. Six test methods cover the
all-gates-blocked path, false reviewer authority, manifest tampering,
cross-protocol signature replay, unrelated signing keys, and the
inability of self-signed evidence to establish issuer authority.

All keys are ephemeral and generated only inside the tests. The
suite is registered with `pp_recovery_strict_ci_runner.py`, which
fails on skipped tests and exceptions. Neither the suite nor
the recovery code enrolls identities, changes P.P. numbers, connects
to a telecom provider or writes to a production database.

Run in a Python environment with `cryptography` available:

```powershell
python -m unittest -v test_review_044_recovery_chain_e2e
python pp_recovery_strict_ci_runner.py
```

**Important:** an end-to-end synthetic test is not live end-to-end
identity verification. Independent source authenticity, trust anchors,
human authority, freshness and replay storage remain unresolved.
Committing tests is not proof of their execution; inspect GitHub
Actions before claiming PASS. **HOLD / DENY / NOT_AUTHORIZED.**


## Scoped CI inventory fail-closed guard (draft v20, 22 November 2026)

The newly added `pp_recovery_ci_inventory.py` checks the exact
**explicitly scoped** PALACO-PP recovery security surface before
the strict test runner starts. It requires nine critical source
modules, their nine matching regression suites, and the two
integration suites (contract parity and synthetic end-to-end).
Missing/duplicate/extra suite registrations, missing files or a
test file without test methods block the run, while preserving
HOLD/DENY. It parses test files without importing or executing them.

`test_pp_recovery_ci_inventory.py` adds six synthetic policy checks.
The GitHub Actions workflow checks syntax and executes these
tests on Python 3.11 and 3.12 before the strict regression
suite. The new source/test files are included in workflow path
filters to ensure future changes trigger CI.

**Scope limitation:** This inventory enforces the named security
modules, not every historical repository test or an automatic
glob over arbitrary new modules. New critical modules must be
registered explicitly and reviewed; these checks do not prove
independent source or reviewer authenticity.

Manual commands:
```powershell
python -m unittest -v test_pp_recovery_ci_inventory test_pp_recovery_strict_ci_runner
python pp_recovery_strict_ci_runner.py
```

Code committed on a non-production draft branch. An external CI
PASS has not been verified and no authorization, registration,
merge or deployment occurs. **HOLD / DENY / NOT_AUTHORIZED.**


## Machine-readable, non-authorizing CI receipt (draft v21, 22 November 2026)

`pp_recovery_ci_receipt.py` accepts explicit GitHub Actions outcomes
for four synthetic steps: source syntax, runner/inventory policy,
security regressions and blocked authorization boundary. It exports
a bounded, create-only JSON receipt with the commit SHA, run ID,
Python version, and step outcomes (success/failure/cancelled/skipped/
unknown). A receipt says `ALL_RECORDED_STEPS_SUCCESS` **only** if
all four are explicitly `success`; every other combination says
`INCOMPLETE_OR_FAILED`. Neither state implies verified provenance,
human authorization, identity recovery, or deployment.

Six regression methods in `test_pp_recovery_ci_receipt.py` cover
failure/skip/cancelled/unknown states, malformed metadata, missing
steps, write-once export and denial invariants.

The GitHub Actions matrix now writes one unsigned JSON artifact per
Python version using `if: always()`, with 7-day retention.
Artifacts are **not** signed attestations. A failed checkout or a
failed receipt writer can leave no artifact; the workflow result
and logs still need external inspection. The workflow currently
does not independently assert a successful run or establish a
trusted CI identity.

Manual checks:
```powershell
python -m unittest -v test_pp_recovery_ci_receipt
python pp_recovery_strict_ci_runner.py
```

No successful GitHub Actions run has been independently observed by
this documentation change. Production and authorization remain
**HOLD / DENY / NOT_AUTHORIZED**.


## Python matrix receipt-pair inspection (draft v22, 22 November 2026)

`pp_recovery_ci_receipt_pair.py` provides an **offline and
non-authorizing** comparison of two unsigned per-version JSON
execution receipts. It strictly parses their fixed schema and
reconstructs the exact allowed receipt claims. It requires one
Python 3.11 receipt and one Python 3.12 receipt with the same
nonempty, format-valid Git commit SHA and workflow run ID. It
rejects inconsistent metadata, forged success/authorization
claims, duplicate JSON keys and malformed or oversized inputs.

Only two explicitly successful sets of recorded steps produce
`BOTH_RECORDED_SUCCESS_UNTRUSTED`. Any recorded failure,
skipped, cancelled or unknown step produces
`INCOMPLETE_OR_FAILED`. Both outputs retain
`externalCIConclusion: NOT_INDEPENDENTLY_VERIFIED`,
`HOLD`, `DENY` and `NOT_AUTHORIZED`. This is consistency
inspection, **not** proof that either receipt came from GitHub.

Eight synthetic regression methods in
`test_pp_recovery_ci_receipt_pair.py` cover accepted
denial-preserving pairs and manipulated inputs. GitHub Actions
includes these regression tests in its policy stage on both
Python versions. Pair inspection is not an automatic release
gate and does not fetch artifacts itself: a separate evidence
reviewer must obtain the two artifacts and independently
verify the actual GitHub run.

```powershell
python -m unittest -v test_pp_recovery_ci_receipt_pair
```

No production execution, trust promotion, merge or P.P.
issuance. No GitHub Actions PASS is claimed.
**HOLD / DENY / NOT_AUTHORIZED**.


## Post-matrix CI receipt verification (draft v23, 22 November 2026)

`pp_recovery_ci_matrix_gate.py` now reads only the two expected
artifact paths for Python 3.11 and Python 3.12. It verifies the pair
using the existing strict receipt schema, requires identical
workflow run ID and commit SHA, and additionally matches both
against the current GitHub Actions environment. Missing, symlinked,
oversized, stale, cross-run or incomplete receipts fail closed.
The module is read-only and never creates trust or authorizes
identity recovery.

Six synthetic regression test methods in
`test_pp_recovery_ci_matrix_gate.py` cover valid-but-untrusted
pairs, missing artifacts, failed/skipped/cancelled/unknown checks,
cross-run or cross-commit evidence, mismatching current-run context
and oversized/symlinked files.

A new independent `recovery-matrix-verification` GitHub Actions
job runs with `if: always()` after the two-version matrix,
downloads this run's unsigned artifacts, and executes the fail-closed
post-matrix gate. It requires read-only repository and Actions
permissions; it never enables release, signs a receipt or deploys.
If the first matrix job fails or artifacts are missing, this
verification job is still scheduled and should fail rather than
creating a false PASS.

Manual synthetic verification:
```powershell
python -m unittest -v test_pp_recovery_ci_matrix_gate
```

The receipt artifacts and the comparison result remain **unsigned**
and are not independent provenance attestations. A successful
GitHub Actions job also does not establish owner/reviewer authority,
trusted identity binding or telecom permissions. No CI PASS has
been verified in this turn. **HOLD / DENY / NOT_AUTHORIZED**.


## Strict matrix artifact directory inventory (draft v24, 23 November 2026)

The post-matrix verifier previously read two expected JSON paths while
ignoring unexpected files and possible symlinked parent directories.
It now requires **exactly two named artifact subdirectories**, each
containing **exactly one expected JSON receipt**. An unexpected
directory/file or symlinked artifact directory fails closed, as does
the existing rejection of oversized, missing, tampered, stale or
cross-run receipts.

Three new synthetic test methods cover an extra version directory,
extra file inside a known directory, and a parent directory symlink
that points outside the artifact root. No trusted issuer, owner or
reviewer authority is established by these filename checks.

Manual verification:
```powershell
python -m unittest -v test_pp_recovery_ci_matrix_gate
```

Changes are committed only on the draft branch. No independent
GitHub Actions PASS has been observed. Production remains
**HOLD / DENY / NOT_AUTHORIZED**.


## Machine-readable post-matrix verdict (draft v25, 23 November 2026)

`pp_recovery_ci_matrix_verdict.py` adds a create-only, unsigned JSON
verdict to the final post-matrix workflow. It calls the strict artifact
verification logic and records a failure as
`INCOMPLETE_OR_FAILED` with `PAIR_REJECTED` or
`INVALID_WORKFLOW_CONTEXT`, returning a **nonzero process status**.
Only an explicitly complete synthetic matrix produces
`BOTH_RECORDED_SUCCESS_UNTRUSTED` and a zero exit status; even
that still reports `externalCIConclusion: NOT_INDEPENDENTLY_VERIFIED`,
`HOLD`, `DENY`, `NOT_AUTHORIZED` and `BLOCKED`.

The separate GitHub Actions verification job now attempts to upload
`pp-recovery-matrix-verdict.json` whether the check passes or fails.
Six synthetic tests cover successful-but-untrusted execution,
missing artifacts, skipped tests, malformed current-run context,
export of a failing verdict, and overwrite rejection.

A checkout, artifact-download, or interpreter failure *before* the
verdict tool runs can still prevent artifact creation; absence of
a verdict remains a failure to verify, never proof of success.
No production/recovery authorization or merge has occurred.
The GitHub Actions result was not independently verified in this
turn. **HOLD / DENY / NOT_AUTHORIZED**.


## Exact-byte receipt fingerprints in final matrix verdict (draft v26, 23 November 2026)

The unsigned post-matrix verdict now includes
`receiptSha256ByVersion` for a successfully matched Python 3.11
and Python 3.12 pair. These are SHA-256 hashes of the **exact
receipt bytes** used to determine the synthetic observation; the
verdict does not duplicate the receipt contents or personally
identifiable data. Incomplete/failed verdicts carry an empty
fingerprint map, never invented evidence.

An additional regression verifies that modifying the bytes
of one receipt changes only that receipt's recorded SHA-256
digest while preserving `HOLD`. The existing test suite now
also validates the two populated digests on success and the
empty map on failure.

SHA-256 gives content linkage, **not provenance authentication**.
These fingerprints do not verify that GitHub produced the
artifacts or that the workflow conclusion was independently
confirmed. No live CI PASS was confirmed in this turn.
Authorization remains **HOLD / DENY / NOT_AUTHORIZED**.


## Exact-byte, independent re-evaluation of CI verdict (draft v27, 23 November 2026)

`pp_recovery_ci_verdict_audit.py` independently recomputes the expected
post-matrix observation from the two unsigned CI receipts and the
current commit SHA/workflow run ID. It parses the create-only verdict
using strict JSON with duplicate-key rejection, requires its entire
object to equal the recomputed result, and additionally requires
byte-for-byte canonical JSON serialization (bounded to 8192 bytes).

Six synthetic regressions in `test_pp_recovery_ci_verdict_audit.py`
cover: matching-but-untrusted success; consistent failure without
release; forged success on missing artifacts; tampered digest or
authority; stale verdict after receipt-byte modification; duplicate-key,
noncanonical and oversized JSON refusal.

GitHub Actions now runs the verdict audit after creating the verdict
and before uploading its artifact. The audit step is `always()`,
so a failed verdict write cannot be silently treated as an audit PASS.
Neither an audit match nor a successful synthetic test represents
independent GitHub provenance or a production release decision.

Manual command:
```powershell
python -m unittest -v test_pp_recovery_ci_verdict_audit
```

No merge, deployment, P.P. issuance or trust promotion occurs.
No successful CI execution has been independently confirmed here.
**HOLD / DENY / NOT_AUTHORIZED**.


## Run-attempt separation for GitHub Actions reruns (draft v28, 23 November 2026)

GitHub Actions may rerun a workflow with the same `GITHUB_RUN_ID`
but a higher `GITHUB_RUN_ATTEMPT`. The unsigned per-version
receipts now record `workflowRunAttempt` as an explicit
positive decimal string, and the receipt-pair validator requires
that both Python versions use the same attempt. The matrix gate
requires that this attempt matches the **current** environment;
the final matrix verdict and independent verdict audit propagate
the attempt as well.

Artifact names now include `attemptN`, for both individual
Python receipts and the combined matrix verdict. The matrix
verification job downloads only the current attempt's two
receipt artifacts and rejects all unexpected extra directories.
This avoids accidental mixture with older attempts and avoids
overwriting the previous attempt's immutable GitHub artifacts.
Older pre-v28 receipts lack the required attempt field and
correctly fail the new contract.

The synthetic tests now cover cross-attempt mismatch, a
valid second attempt, rejection of a previous attempt under a
new current attempt, and non-authorizing attempt metadata.

This is **attempt-consistency** checking of unsigned observations,
not cryptographic proof of GitHub provenance or human authority.
No independent CI PASS is claimed and nothing is merged, deployed
or issued. **HOLD / DENY / NOT_AUTHORIZED**.


## Contract parity protection against top-level mutation (draft v29, 23 November 2026)

The source-only recovery contract parity audit now rejects additional
top-level writes to contract constants even when they use Python
annotated assignments, augmented assignments, nested control-flow
assignments, deletion, direct subscript mutation or common in-place
dictionary/list mutator calls. Previously it extracted the first
literal assignment and could miss a later top-level mutation.
The check still uses the Python AST and `ast.literal_eval`; it does
not execute producer modules.

Three new synthetic test methods exercise rebinding/mutation bypasses
and ensure unrelated declarations do not trigger false positives.
This is deliberately conservative **top-level static analysis**, not a
complete whole-program noninterference proof. Mutations that happen
indirectly inside invoked functions or through reflective aliases
require separate code review and tests.

The existing strict CI suite includes
`test_review_044_contract_parity`; no merge, production operation
or identity authorization follows from parity alone. GitHub Actions
PASS has not been independently confirmed.
**HOLD / DENY / NOT_AUTHORIZED**.


## Nested contract mutation and direct alias rejection (draft v30, 23 November 2026)

The source-only recovery parity guard now inspects **all AST scopes**
rather than stopping at top-level statements. It rejects reassignment,
deletion, direct dictionary/list mutations and common named in-place
mutator calls referring to any of the five guarded contract constants,
including inside function or class bodies. It also conservatively
rejects direct aliases such as `alias = GATE_PREREQUISITES`, including
nested aliases, because an alias could mutate a shared dictionary
without referring to the original constant name again.

Two additional synthetic test methods exercise nested function/class
writes and direct alias escapes. Existing expected producer declarations
remain unchanged. The audit never imports or executes the source text
under inspection.

The AST guard is **not a complete alias analysis**: reflective
lookup via `globals()`, indirect effects through dynamically called
helpers, or other adversarial control/data flows require separate
review. Such gaps must not be described as verified. The strict
test suite includes the parity tests on the draft branch, but no
independent GitHub Actions PASS is confirmed here.
**HOLD / DENY / NOT_AUTHORIZED**.


## Reflective symbol access fails closed (draft v31, 23 November 2026)

The static parity guard for five security contract constants now
rejects dynamic builtins that could access or mutate contract names
indirectly: `globals()`, `locals()`, `vars()`, `eval()`,
`exec()`, `compile()`, `setattr()`, `delattr()` and
`__import__()`. Both top-level and nested occurrences are rejected
when examining a producer module, rather than being executed. An
unrelated conventional call such as `tuple(REQUIREMENTS)` remains
permitted. The declaration-node set is precomputed once for a
clearer bounded AST scan.

Three additional tests exercise reflective lookups, nested
reflection and non-reflective reads. This is a **conservative source
audit**: dynamically aliased builtins, indirect imported helpers,
monkeypatching from another module and other unexamined runtime
paths remain outside its proof boundary. No unsupported guarantee
of comprehensive security is made.

The changes exist only on the draft recovery branch. GitHub
Actions execution and PASS have not been independently verified.
No production access, identity binding, merge or issuance:
**HOLD / DENY / NOT_AUTHORIZED / BLOCKED**.


## CI parseability repair and source syntax audit (draft v32, 23 November 2026)

A concrete Python syntax defect was identified in
`test_review_044_release_boundary_snapshot.py`: the import contained
literal escaped newline characters (`\\n`) outside a quoted Python
string. That prevented Python from importing the boundary test
module. The malformed import was corrected to a real newline.

The fail-closed inventory audit in `pp_recovery_ci_inventory.py` now
parses every explicitly scoped critical security source module using
`ast.parse` before accepting the inventory. Previously it checked
whether the source file existed, but did not verify parseability.
No runtime import, database operation or source execution occurs.

Two inventory regression methods were added: malformed critical
security source must yield `PP_CI_SOURCE_SYNTAX_INVALID`, and a
malformed registered security test must also fail the inventory.
A malformed test fixture is deliberately syntactically invalid,
rather than merely containing escaped line separators.

This repair addresses a discovered pre-test blocker, **not** proof
that the entire workflow has executed or passed. CI execution
remains to be independently confirmed. The branch remains a
non-authorizing draft: **HOLD / DENY / NOT_AUTHORIZED / BLOCKED**.


## Distinct security suite inventory failure codes (draft v33, 23 November 2026)

Review identified a CI regression-test mismatch: the inventory used
`PP_CI_UNREGISTERED_OR_MISSING_SUITE` for both missing and
unexpected suite names, while its own regression test expected
`MISSING_SUITE` for omissions. This could report a test failure
even though the underlying inventory correctly refused a missing
security test.

`pp_recovery_ci_inventory.py` now reports
`PP_CI_MISSING_SUITE` when any required suite is absent, and
`PP_CI_UNREGISTERED_SUITE` when an additional unknown suite is
present. A missing required suite takes precedence if both apply,
so inserting a non-security test can never compensate for
the missing scoped security suite.

An additional synthetic regression tests the replacement and
extra-suite cases. Existing regressions for missing, duplicated
and unknown suites retain meaningful matching error identifiers.

These commits do not prove that the full test runner or GitHub
Actions passed. No release, deployment, merge or recovery authorization
has occurred. **HOLD / DENY / NOT_AUTHORIZED / BLOCKED**.


## Unittest discovery coverage gate (draft v34, 23 November 2026)

A review of all 11 explicitly scoped recovery security suites confirmed
that the current test classes directly inherit `unittest.TestCase`.
The earlier AST inventory accepted any class with a method named
`test_*`, even a plain class that `unittest` will not discover.
That allowed a falsely reassuring source-level inventory result.

`pp_recovery_ci_inventory.py` now requires at least one
`test_*` method inside a statically recognizable direct
`unittest.TestCase` subclass. If absent, it rejects the suite with
`PP_CI_SUITE_WITHOUT_DISCOVERABLE_TESTS`. One new negative
regression covers an ordinary class containing an undiscoverable
`test_*` method. The existing empty-suite test expects the more
accurate failure identifier.

This is a **static preflight**, not test execution. It deliberately
does not infer inheritance through aliases or intermediate base classes.
The strict runner must still actually load the suites, reject skip
and unexpected success states, and require all tests to pass.
Neither runtime CI results nor independent human review is established
by this commit. **HOLD / DENY / NOT_AUTHORIZED / BLOCKED**.


## Async unittest false-positive prevention (draft v35, 23 November 2026)

The scoped static test inventory previously accepted
`ast.AsyncFunctionDef` methods named `test_*` in a class directly
inheriting `unittest.TestCase`. A regular `unittest.TestCase` method
is not automatically awaited, so this could produce false confidence:
assertions inside an unawaited coroutine may never execute.

The inventory now rejects **any** async `test_*` method inside
the recognized `unittest.TestCase` classes with
`PP_CI_ASYNC_TEST_UNSUPPORTED`, including a mixed suite containing
both synchronous and asynchronous tests. It counts only synchronous
`ast.FunctionDef` methods when deciding whether the suite has
recognizable tests. Two additional synthetic regression methods
cover pure-async and mixed-async cases.

This is intentionally restrictive. A future genuine asynchronous
test suite would require separately reviewed `IsolatedAsyncioTestCase`
support and verified interpreter behavior before being admitted;
it is not automatically trusted by this static inventory.

No complete runtime test execution or GitHub Actions PASS has
been confirmed by this change. No merge, deployment, owner
authorization or number issuance: **HOLD / DENY / NOT_AUTHORIZED**.


## First independently checked GitHub Actions success (23 November 2026)

The previous repeated statement "no confirmed CI PASS" was limited by
a commit-status/PR-run endpoint that did not surface the relevant runs.
Direct inspection of the branch's GitHub Actions run collection now
confirms actual workflow run
[45126879152](https://github.com/Maurits-pixe/palaco-pp/actions/runs/45126879152),
triggered by `pull_request`, with `conclusion: success`, on
commit `6ca299a0eee61a7a93f880e0bcbb3419d08e85d8`
(draft v35), completed 23 November 2026 at 06:51 UTC.

The workflow job API reports three successfully completed jobs:

- `Synthetic recovery security (Python 3.11)`: **success**,
  including Python compilation, strict CI policy/unittest,
  offline synthetic regressions, denial-boundary confirmation
  and unsigned receipt artifact upload.
- `Synthetic recovery security (Python 3.12)`: **success**,
  with the equivalent checks and receipt upload.
- `Verify both unsigned Python receipts (never authorize)`:
  **success**, including artifact download, fail-closed
  matrix verdict export and exact-byte verdict audit.

The workflow's artifact API also confirms these three stored ZIP
artifacts for this run (archive digests are provided by GitHub,
distinct from the embedded receipt-byte digests):

| Artifact | GitHub artifact id | GitHub SHA-256 archive digest |
| --- | ---: | --- |
| `pp-recovery-receipt-attempt1-py3.11` | 14795354686 | `30aebb1944975ea71a4d4954cd3f957c619288d93d9cab193e27d1b4a404f5d7` |
| `pp-recovery-receipt-attempt1-py3.12` | 14796092091 | `ef6ae03ba5f9135c160b1c6a5b3ef703885f9646b02909c89881b5b6eed28089` |
| `pp-recovery-matrix-verdict-attempt1` | 14795792772 | `ae310738eb55f37710f854b9c2a35147cc319c42705f7a2250a2f80025251cb3` |

Artifact retention was configured for seven days; artifacts may expire
30 November 2026. This records a real GitHub Actions run result for
the **specified commit**, not a new runtime test executed by this
documentation commit or a blanket PASS for later branch changes.
Workflow success does not authenticate P.P. ownership, third-party
source provenance, signing authority or independent human review.
**HOLD / DENY / NOT_AUTHORIZED / BLOCKED** remains unchanged.


## Loaded-versus-executed regression count reconciliation (draft v37, 23 November 2026)

The strict synthetic recovery CI runner now enforces **three distinct
counts for each of the eleven scoped security suites**:

1. `pp_recovery_ci_inventory.py` statically records the number of
   declared synchronous `test_*` methods for every recognized
   `unittest.TestCase` subclass. It exposes an explicit
   `declaredTestMethodsBySuite` map, which remains unsigned and
   non-authorizing.
2. The strict runner requires the `unittest` loader to return
   **exactly that many tests per named module**, rejecting mismatches
   with `PP_CI_LOADED_TEST_COUNT_MISMATCH`. A missing, malformed,
   or non-positive count map fails closed.
3. The test runner also requires the number of actually executed
   tests to equal the sum of those declared counts. Missing
   executions, failures, errors, skips and unexpected successes
   remain rejection conditions.

New negative runner regressions cover a wrong loaded count,
missing count map and a truncated executed count. Existing skip
and zero-run tests were updated so they still reach the relevant
result handling rather than being stopped prematurely by count
mismatch. The inventory test checks the complete positive map.

**Scope warning:** this reconciles counts, not the identities of
individual test methods or their assertion strength. The last
separately verified GitHub Actions PASS before these commits was
run 45127611844 at commit `1093ae956781b2872c6b2af4496c65bc398cb3cc`.
This new change must obtain its own passing workflow result
before claiming CI PASS. No deployment, identity recovery or P.P.
number authorization: **HOLD / DENY / NOT_AUTHORIZED / BLOCKED**.


## Verified v37 synthetic CI run (23 November 2026)

After adding source/loader/execution count reconciliation, GitHub Actions
[run 45130235987](https://github.com/Maurits-pixe/palaco-pp/actions/runs/45130235987)
completed with `conclusion: success` for commit
`744144e24009354226cfb324835d4083b16812df`. The three jobs all
reported success: Python 3.11 security regressions, Python 3.12
security regressions and independent synthetic receipt-matrix verdict
verification. Actual job logs confirm **56 CI-policy tests plus 87
strict recovery tests per Python version**; combined across two
versions this represents 286 test executions. Both versions logged
`PP_CI_SYNTHETIC_PASS / 87 tests / AUTHORIZATION_HOLD`.
The final job logged `BOTH_RECORDED_SUCCESS_UNTRUSTED`
followed by `PP_CI_VERDICT_AUDIT_MATCH_UNTRUSTED`.

The previous cancelled jobs were transient concurrency cancellations,
not a replacement for this completed successful run. This result
applies specifically to commit `744144e...`, before subsequent
documentation-only edits. Test success concerns synthetic regression
behavior; production and identity gates remain **HOLD / DENY /
NOT_AUTHORIZED / BLOCKED**.
