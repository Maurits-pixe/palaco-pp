"""Explicit offline export of blocked PP-RECOVERY-002 release-readiness gaps.

No file read without --run. No tests, source attestation, identity action,
permission grant or overwrite of any existing file.
"""
import argparse
import json
from pathlib import Path

from review_044_release_readiness import ERROR, analyze_release_readiness
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES


def _bounded(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Non-authorizing PP release-readiness gaps")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--export", type=Path, help="Create a new file; overwrite forbidden")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(x is None for x in (
        args.dossier, args.queue, args.intake, args.plan, args.observations
    )):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        result = analyze_release_readiness(
            _bounded(args.dossier, MAX_DOSSIER_BYTES),
            _bounded(args.queue, MAX_QUEUE_BYTES),
            _bounded(args.intake, MAX_INTAKE_BYTES),
            _bounded(args.plan, MAX_PLAN_BYTES),
            _bounded(args.observations, MAX_REGISTER_BYTES),
        )
        payload = (json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if args.export is None:
            print(payload.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as destination:
                destination.write(payload)
            print("READINESS_GAPS_ONLY / NOT_READY / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
