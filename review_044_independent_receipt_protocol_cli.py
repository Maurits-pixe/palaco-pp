"""Opt-in create-only export of UNSIGNED independent receipt specification.

No input files accessed without --run. No external reviewer contacted.
No signature verification, receipt issuance, tests, merge, deployment or grant.
"""
import argparse
import json
from pathlib import Path

from review_044_independent_receipt_protocol import (
    ERROR, MAX_HANDOFF_BYTES, prepare_independent_review_receipt_protocol,
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


def _read_bounded(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        value = source.read(maximum + 1)
    if not 0 < len(value) <= maximum:
        raise ValueError
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="PP unsigned independent receipt protocol, not a receipt"
    )
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--execution-plan", type=Path)
    parser.add_argument("--observation-register", type=Path)
    parser.add_argument("--evidence-intake", type=Path)
    parser.add_argument("--review-handoff", type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if (any(getattr(args, name) is None for name in _NAMES)
            or any(getattr(args, name) is None for name in (
                "execution_plan", "observation_register", "evidence_intake",
                "review_handoff", "export"
            ))):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        sources = tuple(
            _read_bounded(getattr(args, name), limit)
            for name, limit in zip(_NAMES, _LIMITS)
        )
        report = prepare_independent_review_receipt_protocol(
            sources,
            _read_bounded(args.execution_plan, MAX_PLAN_BYTES),
            _read_bounded(args.observation_register, MAX_REGISTER_BYTES),
            _read_bounded(args.evidence_intake, MAX_INTAKE_BYTES),
            _read_bounded(args.review_handoff, MAX_HANDOFF_BYTES),
        )
        raw = (json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        with args.export.open("xb") as destination:
            destination.write(raw)
        print("UNSIGNED_RECEIPT_PROTOCOL_ONLY / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
