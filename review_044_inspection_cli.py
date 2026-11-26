"""Opt-in, offline Review 044 inspection import (no network or database writes).

Usage (owner test session only):
  python review_044_inspection_cli.py --run --registry PATH --inspection PATH
  python review_044_inspection_cli.py --run --registry PATH --inspection PATH --json

No --run means no files are opened and no validation is executed.
"""
import argparse
import json
from pathlib import Path

from review_044_owner_inspection import (
    MAX_INSPECTION_BYTES,
    validate_owner_inspection,
)
from review_044_owner_registry import MAX_REGISTRY_BYTES


def _read_limited(path: Path, maximum: int) -> bytes:
    # Only explicit local paths. Refuse directories, empty and oversized files.
    if not path.is_file():
        raise ValueError("PP_REVIEW_044_OWNER_INSPECTION_INVALID")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError("PP_REVIEW_044_OWNER_INSPECTION_INVALID")
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Strict, offline, non-authorizing Review 044 row inspection."
    )
    parser.add_argument("--run", action="store_true", help="Explicitly execute the review")
    parser.add_argument("--registry", type=Path, help="Original owner registry JSON")
    parser.add_argument("--inspection", type=Path, help="Downloaded row inspection JSON")
    parser.add_argument("--json", action="store_true", help="Print limited JSON result")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.registry is None or args.inspection is None:
        parser.error("--registry and --inspection are required with --run")
    try:
        registry_bytes = _read_limited(args.registry, MAX_REGISTRY_BYTES)
        inspection_bytes = _read_limited(args.inspection, MAX_INSPECTION_BYTES)
        result = validate_owner_inspection(registry_bytes, inspection_bytes)
    except (OSError, ValueError, TypeError) :
        # No file paths, filenames, secret material, or exception details echoed.
        print("PP_REVIEW_044_OWNER_INSPECTION_INVALID / HOLD / DENY")
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"{result['result']} / regel {result['sequence']} / "
            "NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
