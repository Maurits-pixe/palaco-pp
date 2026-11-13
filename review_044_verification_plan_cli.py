"""Opt-in offline export of PP-RECOVERY-002 verification plan.

Never opens files without --run. Does not perform verification checks,
authenticate reviewers, change identity state, or overwrite old exports.
"""
import argparse
import json
from pathlib import Path

from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_verification_plan import prepare_verification_plan, ERROR


def _bounded(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare, but do not execute, blocked PP recovery verification checks."
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--export", type=Path, help="Create new plan JSON, without overwriting")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.dossier is None or args.queue is None or args.intake is None:
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        plan = prepare_verification_plan(
            _bounded(args.dossier, MAX_DOSSIER_BYTES),
            _bounded(args.queue, MAX_QUEUE_BYTES),
            _bounded(args.intake, MAX_INTAKE_BYTES),
        )
        payload = (json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if args.export is None:
            print(payload.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as destination:
                destination.write(payload)
            print("VERIFICATION_PLAN_PREPARED_NOT_EXECUTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
