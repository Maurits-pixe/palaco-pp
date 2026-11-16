"""Explicit offline create-only export of unexecuted release verification steps.

Never runs checks automatically. No files read without --run. No review,
verification, approvals, network calls, tests, merge, deployment or login.
"""
import argparse
import json
from pathlib import Path

from review_044_release_execution_plan import (
    ERROR, MAX_COCKPIT_BYTES, prepare_release_verification_execution_plan,
)
from review_044_release_integrity import ARTIFACT_MAXIMA
from review_044_release_evidence_matrix import MAX_RELEASE_MANIFEST_BYTES
from review_044_release_readiness_cockpit import MAX_MATRIX_BYTES

_NAMES = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions",
    "revocation", "assurance", "registry", "impact", "integrity", "matrix",
    "cockpit",
)
_LIMITS = ARTIFACT_MAXIMA + (
    MAX_RELEASE_MANIFEST_BYTES, MAX_MATRIX_BYTES, MAX_COCKPIT_BYTES
)


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        result = source.read(limit + 1)
    if not 0 < len(result) <= limit:
        raise ValueError
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PP release verification: planning only")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None for name in _NAMES):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_release_verification_execution_plan(*[
            _read(getattr(args, name), limit)
            for name, limit in zip(_NAMES, _LIMITS)
        ])
        raw = (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        with args.export.open("xb") as output:
            output.write(raw)
        print("RELEASE_VERIFICATION_PLAN_PREPARED_NOT_EXECUTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
