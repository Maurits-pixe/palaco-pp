"""Explicit, offline-only export of the PP-RECOVERY-002 recovery cockpit.

No file I/O without --run. Inputs are bounded; output is create-only.
No server calls, test runner, identity authority or permissions.
"""
import argparse
import json
from pathlib import Path

from review_044_recovery_cockpit import ERROR, prepare_recovery_cockpit
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline, non-authorizing PP recovery cockpit")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--export", type=Path, help="Only create a NEW JSON report")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(value is None for value in (
        args.dossier, args.queue, args.intake, args.plan, args.observations
    )):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_recovery_cockpit(
            _read(args.dossier, MAX_DOSSIER_BYTES),
            _read(args.queue, MAX_QUEUE_BYTES),
            _read(args.intake, MAX_INTAKE_BYTES),
            _read(args.plan, MAX_PLAN_BYTES),
            _read(args.observations, MAX_REGISTER_BYTES),
        )
        output = (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if args.export is None:
            print(output.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as target:
                target.write(output)
            print("RECOVERY_COCKPIT_UNTRUSTED_EXPORTED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
