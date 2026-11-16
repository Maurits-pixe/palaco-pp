"""Owner-invoked, create-only offline Release Readiness Cockpit snapshot.

No inputs read without --run. No tests, deployment, approval, signing,
user sessions, identity mutations, network operations or package release.
"""
import argparse
import json
from pathlib import Path

from review_044_release_readiness_cockpit import (
    ERROR, MAX_MATRIX_BYTES, prepare_release_readiness_cockpit,
)
from review_044_release_integrity import ARTIFACT_MAXIMA
from review_044_release_evidence_matrix import MAX_RELEASE_MANIFEST_BYTES

_OPTIONS = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions",
    "revocation", "assurance", "registry", "impact", "integrity", "matrix",
)
_LIMITS = ARTIFACT_MAXIMA + (MAX_RELEASE_MANIFEST_BYTES, MAX_MATRIX_BYTES)


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unsigned PP release-readiness snapshot; not a release approval"
    )
    parser.add_argument("--run", action="store_true")
    for name in _OPTIONS:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None for name in _OPTIONS):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_release_readiness_cockpit(*[
            _read(getattr(args, name), limit)
            for name, limit in zip(_OPTIONS, _LIMITS)
        ])
        raw = (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        with args.export.open("xb") as output:
            output.write(raw)
        print("RELEASE_READINESS_NOT_READY / SIX_GATES_BLOCKED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
