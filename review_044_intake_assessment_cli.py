"""Explicit offline-only intake assessment report; no execution by default.

Owner-operated after --run. Does not run fixtures, verify actor identity,
authenticate source evidence or alter any PALACO account.
"""
import argparse
import json
from pathlib import Path

from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_intake_assessment import assess_review_intake, ERROR


def _read_limited(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        payload = source.read(maximum + 1)
    if not 0 < len(payload) <= maximum:
        raise ValueError
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Strict, non-authorizing PP recovery intake assessment"
    )
    parser.add_argument("--run", action="store_true",
                        help="Explicitly read and assess three original JSON files")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--export", type=Path,
                        help="Explicit path to a NEW report; will not overwrite")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.dossier is None or args.queue is None or args.intake is None:
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = assess_review_intake(
            _read_limited(args.dossier, MAX_DOSSIER_BYTES),
            _read_limited(args.queue, MAX_QUEUE_BYTES),
            _read_limited(args.intake, MAX_INTAKE_BYTES),
        )
        encoded = (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        if args.export is None:
            print(encoded.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as destination:
                destination.write(encoded)
            print("UNSIGNED_INTAKE_ASSESSMENT_EXPORTED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
