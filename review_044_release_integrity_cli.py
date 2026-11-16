"""Explicit create-only offline export of a NON-RELEASABLE integrity manifest.

Nothing is opened without --run. Does not package software, sign, attest,
test, change accounts, create sessions, merge, deploy or authorize.
"""
import argparse
import json
from pathlib import Path

from review_044_release_integrity import (
    ERROR, ARTIFACT_MAXIMA, prepare_release_integrity_manifest,
)

_OPTIONS = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions",
    "revocation", "assurance", "registry", "impact",
)


def _bounded(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare non-authorizing unsigned PP release-integrity manifest"
    )
    parser.add_argument("--run", action="store_true")
    for name in _OPTIONS:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path, help="Create a NEW local JSON file only")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None for name in _OPTIONS):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        original = [
            _bounded(getattr(args, name), limit)
            for name, limit in zip(_OPTIONS, ARTIFACT_MAXIMA)
        ]
        report = prepare_release_integrity_manifest(*original)
        data = (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(data)
        print("UNSIGNED_RELEASE_INTEGRITY_MANIFEST_CREATED / NOT_READY / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
