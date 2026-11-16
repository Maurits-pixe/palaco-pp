"""Explicit opt-in offline export of strict Review 044 owner-worksheet evidence.

No file opens without --run. Source bytes are read once and bounded; results
are printed or exclusively created at --export (never overwrite an artifact).
No network, database, account, identity, or permission operations.
"""
import argparse
import json
from pathlib import Path

from review_044_inspection_owner_review import MAX_INSPECTION_TECHNICAL_BYTES
from review_044_inspection_owner_binding import MAX_INSPECTION_WORKSHEET_BYTES
from review_044_inspection_evidence import compile_inspection_owner_evidence


def _read_bounded(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review 044: strictly assess original synthetic inspection owner files."
    )
    parser.add_argument("--run", action="store_true", help="Explicitly start local validation")
    parser.add_argument("--technical", type=Path, help="Original technical report JSON")
    parser.add_argument("--worksheet", type=Path, help="Original owner worksheet JSON")
    parser.add_argument("--export", type=Path, help="Explicit new JSON export path; no overwrite")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.technical is None or args.worksheet is None:
        print("PP_REVIEW_044_INSPECTION_EVIDENCE_INVALID / HOLD / DENY")
        return 2
    try:
        technical = _read_bounded(args.technical, MAX_INSPECTION_TECHNICAL_BYTES)
        worksheet = _read_bounded(args.worksheet, MAX_INSPECTION_WORKSHEET_BYTES)
        evidence = compile_inspection_owner_evidence(technical, worksheet)
        output = (json.dumps(evidence, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if args.export is None:
            print(output.decode("utf-8"), end="")
        else:
            # The user explicitly selects the path; exclusive create prevents
            # accidental destruction of existing evidence.
            with args.export.open("xb") as stream:
                stream.write(output)
            print("REVIEW_044_EVIDENCE_EXPORTED_UNTRUSTED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError):
        # Do not leak paths, raw payloads or exception details to output.
        print("PP_REVIEW_044_INSPECTION_EVIDENCE_INVALID / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
