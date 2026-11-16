"""Opt-in offline export of PP-RECOVERY-002 decision dossier.

No file reads without --run; no tests, network, database or identity actions.
Optional --export only creates a new file, never overwrites.
"""
import argparse
import json
from pathlib import Path

from review_044_recovery_decision import MARKS, REQUIREMENTS, prepare_decision_dossier
from review_044_recovery_coordination import MAX_COORDINATION_HANDOFF_BYTES
from review_044_inspection_owner_review import MAX_INSPECTION_TECHNICAL_BYTES
from review_044_inspection_owner_binding import MAX_INSPECTION_WORKSHEET_BYTES


def _bounded(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        raw = source.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline PP-RECOVERY-002 blocked decision dossier")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--technical", type=Path)
    parser.add_argument("--worksheet", type=Path)
    parser.add_argument("--marks", type=Path, help="Optional explicit non-authoritative review marks JSON")
    parser.add_argument("--export", type=Path, help="Create-only JSON destination")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if not all((args.handoff, args.technical, args.worksheet)):
        print("PP_RECOVERY_002_DECISION_DOSSIER_INVALID / HOLD / DENY")
        return 2
    try:
        marks = None
        if args.marks is not None:
            mark_bytes = _bounded(args.marks, 4096)
            def unique_pairs(pairs):
                obj = {}
                for key, val in pairs:
                    if key in obj:
                        raise ValueError
                    obj[key] = val
                return obj
            marks = json.loads(mark_bytes.decode("utf-8"), object_pairs_hook=unique_pairs)
            allowed = {name for name, _ in REQUIREMENTS}
            if (type(marks) is not dict or len(marks) > len(allowed)
                    or any(type(name) is not str or name not in allowed
                           or type(value) is not str or value not in MARKS
                           for name, value in marks.items())):
                raise ValueError
        dossier = prepare_decision_dossier(
            _bounded(args.handoff, MAX_COORDINATION_HANDOFF_BYTES),
            _bounded(args.technical, MAX_INSPECTION_TECHNICAL_BYTES),
            _bounded(args.worksheet, MAX_INSPECTION_WORKSHEET_BYTES),
            marks,
        )
        payload = (json.dumps(dossier, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if args.export is None:
            print(payload.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as destination:
                destination.write(payload)
            print("DECISION_DOSSIER_DRAFT_EXPORTED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print("PP_RECOVERY_002_DECISION_DOSSIER_INVALID / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
