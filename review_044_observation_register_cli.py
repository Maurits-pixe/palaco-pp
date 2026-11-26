"""Explicit opt-in offline observation register snapshot creation.

Never reads sources without --run and never overwrites a previous snapshot.
Records user-supplied observation *category* only, not proof or authorization.
"""
import argparse
from pathlib import Path

from review_044_observation_register import (
    ERROR, MARKS, MAX_PLAN_BYTES, MAX_REGISTER_BYTES, append_observation,
)
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES


def _bounded(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        payload = stream.read(limit + 1)
    if not 0 < len(payload) <= limit:
        raise ValueError
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append unverified self-report to PP recovery check register"
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--previous", type=Path, help="Previous register snapshot")
    parser.add_argument("--intake-sequence", type=int)
    parser.add_argument("--check-order", type=int)
    parser.add_argument("--mark", choices=sorted(MARKS))
    parser.add_argument("--export", type=Path, help="New register snapshot; never overwrite")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if (args.dossier is None or args.queue is None or args.intake is None
            or args.plan is None or args.intake_sequence is None
            or args.check_order is None or args.mark is None or args.export is None):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        result = append_observation(
            _bounded(args.dossier, MAX_DOSSIER_BYTES),
            _bounded(args.queue, MAX_QUEUE_BYTES),
            _bounded(args.intake, MAX_INTAKE_BYTES),
            _bounded(args.plan, MAX_PLAN_BYTES),
            _bounded(args.previous, MAX_REGISTER_BYTES) if args.previous else None,
            args.intake_sequence, args.check_order, args.mark,
        )
        with args.export.open("xb") as output:
            output.write(result)
        print("OBSERVATION_SNAPSHOT_UNVERIFIED / NOT_STARTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
