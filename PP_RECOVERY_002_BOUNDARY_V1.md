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
