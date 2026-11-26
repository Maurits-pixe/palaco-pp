"""Explicit opt-in offline reader for PP-RECOVERY-002 boundary snapshots.

No network, database, identity mutation, overwrite or account issuance.
Only outputs the non-authorizing summary; never echoes source JSON.
"""
import argparse
import json
from pathlib import Path

from review_044_release_boundary_snapshot import (
    BoundaryInputError, MAX_INPUT_BYTES, review_boundary_snapshot,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PP recovery boundary: local HOLD/DENY inspection")
    parser.add_argument("--run", action="store_true", help="explicitly inspect report")
    parser.add_argument("--report", type=Path, help="existing offline readiness JSON")
    parser.add_argument("--export", type=Path, help="create new summary (never overwrite)")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / HOLD / DENY / explicit --run required")
        return 2
    if args.report is None:
        print("PP_BOUNDARY_INVALID / HOLD / DENY")
        return 2
    try:
        # Reject symlinks to keep input sources explicit; open no other paths.
        if args.report.is_symlink() or not args.report.is_file():
            raise BoundaryInputError("PP_BOUNDARY_INVALID")
        with args.report.open("rb") as source:
            report = source.read(MAX_INPUT_BYTES + 1)
        snapshot = review_boundary_snapshot(report)
        payload = (json.dumps(snapshot, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if args.export is None:
            print(payload.decode("utf-8"), end="")
        else:
            if args.export.is_symlink():
                raise BoundaryInputError("PP_BOUNDARY_INVALID")
            with args.export.open("xb") as destination:
                destination.write(payload)
            print("BOUNDARY_SNAPSHOT_CREATED / NOT_READY / HOLD / DENY")
        return 0
    except (OSError, BoundaryInputError, ValueError, TypeError, OverflowError):
        print("PP_BOUNDARY_INVALID / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
