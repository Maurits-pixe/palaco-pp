"""Explicit opt-in offline export of the PP-RECOVERY-002 status report.

Does not read or write without --run; no tests, runtime verification,
account mutation, session creation, network calls or authorization.
"""
import argparse
import json
from pathlib import Path

from review_044_recovery_status import ERROR, build_recovery_status_report
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES


def _bounded(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        result = source.read(limit + 1)
    if not 0 < len(result) <= limit:
        raise ValueError
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare an offline, non-authorizing PP recovery status report."
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--export", type=Path, help="Create a new JSON file; never overwrite")
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
        report = build_recovery_status_report(
            _bounded(args.dossier, MAX_DOSSIER_BYTES),
            _bounded(args.queue, MAX_QUEUE_BYTES),
            _bounded(args.intake, MAX_INTAKE_BYTES),
            _bounded(args.plan, MAX_PLAN_BYTES),
            _bounded(args.observations, MAX_REGISTER_BYTES),
        )
        raw = (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        if args.export is None:
            print(raw.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as output:
                output.write(raw)
            print("RECOVERY_STATUS_REPORT_UNTRUSTED_EXPORTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
