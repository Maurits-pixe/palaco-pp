"""Explicit opt-in offline PP-RECOVERY-002 human review queue append.

This accepts local untrusted review requests, NOT a reviewer identity,
signature, verification, authorization, or PALACO ONE session.
"""
import argparse
from pathlib import Path

from review_044_human_review_queue import (
    MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES, append_review_request,
    ERROR,
)


def _read(path: Path, cap: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        data = stream.read(cap + 1)
    if not 0 < len(data) <= cap:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline blocked five-gate review queue")
    parser.add_argument("--run", action="store_true", help="Explicitly prepare a request")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--previous", type=Path, help="Previous snapshot; omit for first request")
    parser.add_argument("--requirement", type=str)
    parser.add_argument("--action", type=str)
    parser.add_argument("--export", type=Path, help="New snapshot path, never overwritten")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if not args.dossier or not args.requirement or not args.action or not args.export:
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        dossier = _read(args.dossier, MAX_DOSSIER_BYTES)
        previous = _read(args.previous, MAX_QUEUE_BYTES) if args.previous else None
        snapshot = append_review_request(dossier, previous, args.requirement, args.action)
        # Only the owner's explicit export destination is written.
        with args.export.open("xb") as output:
            output.write(snapshot)
        print("REVIEW_QUEUE_SNAPSHOT_CREATED_UNTRUSTED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
