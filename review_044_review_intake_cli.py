"""Opt-in local review intake for PP-RECOVERY-002; NO reviewer authorization.

No file is read without --run. Existing snapshots and source evidence are
never overwritten. The intake contains digest references, not evidence bytes.
"""
import argparse
from pathlib import Path

from review_044_review_intake import (
    ERROR, MAX_EVIDENCE_BYTES, MAX_INTAKE_BYTES, append_review_intake,
)
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES


def _bounded(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Untrusted offline PP recovery review intake")
    parser.add_argument("--run", action="store_true", help="Explicit local intake")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--previous", type=Path, help="Previous intake snapshot, if any")
    parser.add_argument("--request-sequence", type=int)
    parser.add_argument("--evidence", type=Path, help="Original evidence file, maximum 64 KiB")
    parser.add_argument("--kind", choices=("DOCUMENT", "SCREENSHOT", "LOG_EXCERPT", "OTHER_UNTRUSTED"))
    parser.add_argument("--role-claim", choices=("OWNER_CLAIMED", "REVIEWER_CLAIMED", "SOURCE_CLAIMED"))
    parser.add_argument("--export", type=Path, help="New output file; never overwrite")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if (args.dossier is None or args.queue is None or args.evidence is None
            or args.export is None or args.request_sequence is None
            or args.kind is None or args.role_claim is None):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        result = append_review_intake(
            _bounded(args.dossier, MAX_DOSSIER_BYTES),
            _bounded(args.queue, MAX_QUEUE_BYTES),
            _bounded(args.previous, MAX_INTAKE_BYTES) if args.previous else None,
            args.request_sequence,
            _bounded(args.evidence, MAX_EVIDENCE_BYTES),
            args.kind,
            args.role_claim,
        )
        with args.export.open("xb") as output:
            output.write(result)
        print("UNSIGNED_REVIEW_INTAKE_CREATED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
