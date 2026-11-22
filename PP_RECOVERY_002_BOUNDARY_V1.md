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
