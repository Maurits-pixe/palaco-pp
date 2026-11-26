"""Opt-in, offline PP-RECOVERY-002 read-only coordination report.

No input files are opened without --run. No network, database, identity
mutation or PALACO ONE session. Optional JSON export is create-only.
"""
import argparse
import json
from pathlib import Path

from review_044_recovery_coordination import (
    MAX_COORDINATION_HANDOFF_BYTES, compile_recovery_coordination,
)
from review_044_inspection_owner_review import MAX_INSPECTION_TECHNICAL_BYTES
from review_044_inspection_owner_binding import MAX_INSPECTION_WORKSHEET_BYTES


def _bounded(path: Path, cap: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        raw = source.read(cap + 1)
    if not 0 < len(raw) <= cap:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare non-authorizing PP recovery coordination from three local files."
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--technical", type=Path)
    parser.add_argument("--worksheet", type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.handoff is None or args.technical is None or args.worksheet is None:
        print("PP_RECOVERY_002_COORDINATION_INVALID / HOLD / DENY")
        return 2
    try:
        result = compile_recovery_coordination(
            _bounded(args.handoff, MAX_COORDINATION_HANDOFF_BYTES),
            _bounded(args.technical, MAX_INSPECTION_TECHNICAL_BYTES),
            _bounded(args.worksheet, MAX_INSPECTION_WORKSHEET_BYTES),
        )
        encoded = (json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        if args.export is None:
            print(encoded.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as target:
                target.write(encoded)
            print("COORDINATION_DRAFT_EXPORTED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError):
        print("PP_RECOVERY_002_COORDINATION_INVALID / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
