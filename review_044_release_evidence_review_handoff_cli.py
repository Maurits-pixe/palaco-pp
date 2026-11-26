"""Optional local export of an unsigned, NOT SENT review handoff.

Requires explicit --run. Does not contact a reviewer, upload evidence, run
tests, authenticate, sign, release, deploy or create a PALACO ONE session.
"""
import argparse
import json
from pathlib import Path

from review_044_release_evidence_review_handoff import (
    ERROR, prepare_release_evidence_review_handoff,
)
from review_044_release_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES
from review_044_release_evidence_intake import MAX_INTAKE_BYTES
from review_044_release_integrity import ARTIFACT_MAXIMA
from review_044_release_evidence_matrix import MAX_RELEASE_MANIFEST_BYTES
from review_044_release_readiness_cockpit import MAX_MATRIX_BYTES
from review_044_release_execution_plan import MAX_COCKPIT_BYTES

_NAMES = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions",
    "revocation", "assurance", "registry", "impact", "integrity", "matrix",
    "cockpit",
)
_LIMITS = ARTIFACT_MAXIMA + (
    MAX_RELEASE_MANIFEST_BYTES, MAX_MATRIX_BYTES, MAX_COCKPIT_BYTES,
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as handle:
        data = handle.read(maximum + 1)
    if not 0 < len(data) <= maximum:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare unsigned, unsent independent review request")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--execution-plan", type=Path)
    parser.add_argument("--observation-register", type=Path)
    parser.add_argument("--evidence-intake", type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if (any(getattr(args, name) is None for name in _NAMES)
            or args.execution_plan is None or args.observation_register is None
            or args.evidence_intake is None or args.export is None):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        originals = tuple(
            _read(getattr(args, name), maximum)
            for name, maximum in zip(_NAMES, _LIMITS)
        )
        report = prepare_release_evidence_review_handoff(
            originals,
            _read(args.execution_plan, MAX_PLAN_BYTES),
            _read(args.observation_register, MAX_REGISTER_BYTES),
            _read(args.evidence_intake, MAX_INTAKE_BYTES),
        )
        data = (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(data)
        print("UNSIGNED_HANDOFF_PREPARED_NOT_SENT / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
