"""Opt-in, create-only offline export of PP Release Evidence Matrix.

Does not read inputs without --run; performs no tests, signing, verification,
release, deployment, authorization, mutation or external network calls.
"""
import argparse
import json
from pathlib import Path

from review_044_release_evidence_matrix import (
    ERROR, MAX_RELEASE_MANIFEST_BYTES, prepare_release_evidence_matrix,
)
from review_044_release_integrity import ARTIFACT_MAXIMA

_NAMES = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions",
    "revocation", "assurance", "registry", "impact", "integrity",
)
_LIMITS = ARTIFACT_MAXIMA + (MAX_RELEASE_MANIFEST_BYTES,)


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        value = source.read(limit + 1)
    if not 0 < len(value) <= limit:
        raise ValueError
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unverified and blocked release evidence requirements")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path, help="Create a new JSON file only")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None for name in _NAMES):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_release_evidence_matrix(*[
            _read(getattr(args, name), limit)
            for name, limit in zip(_NAMES, _LIMITS)
        ])
        output = (json.dumps(
            report, sort_keys=True, indent=2, ensure_ascii=False
        ) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(output)
        print("RELEASE_EVIDENCE_REQUIREMENTS_UNMET / NOT_READY / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
