"""Owner-invoked, create-only export of unsigned verifier architecture.

No inputs read without --run. No cryptographic processing, external service
calls, tests, key operations, sessions, signing, deployment or authorization.
"""
import argparse
import json
from pathlib import Path

from review_044_independent_receipt_verifier_blueprint import (
    ERROR, MAX_RECEIPT_PROTOCOL_BYTES,
    prepare_independent_receipt_verifier_blueprint,
)
from review_044_independent_receipt_protocol import MAX_HANDOFF_BYTES
from review_044_release_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES
from review_044_release_evidence_intake import MAX_INTAKE_BYTES
from review_044_release_integrity import ARTIFACT_MAXIMA
from review_044_release_evidence_matrix import MAX_RELEASE_MANIFEST_BYTES
from review_044_release_readiness_cockpit import MAX_MATRIX_BYTES
from review_044_release_execution_plan import MAX_COCKPIT_BYTES

_NAMES = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions",
    "revocation", "assurance", "registry", "impact", "integrity",
    "matrix", "cockpit",
)
_LIMITS = ARTIFACT_MAXIMA + (
    MAX_RELEASE_MANIFEST_BYTES, MAX_MATRIX_BYTES, MAX_COCKPIT_BYTES,
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        result = source.read(maximum + 1)
    if not 0 < len(result) <= maximum:
        raise ValueError
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unsigned PP independent receipt verifier architecture"
    )
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    for name in (
        "execution_plan", "observation_register", "evidence_intake",
        "review_handoff", "receipt_protocol", "export"
    ):
        parser.add_argument("--" + name.replace("_", "-"), type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(getattr(args, name) is None for name in _NAMES + (
        "execution_plan", "observation_register", "evidence_intake",
        "review_handoff", "receipt_protocol", "export"
    )):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        sources = tuple(
            _read(getattr(args, name), maximum)
            for name, maximum in zip(_NAMES, _LIMITS)
        )
        report = prepare_independent_receipt_verifier_blueprint(
            sources,
            _read(args.execution_plan, MAX_PLAN_BYTES),
            _read(args.observation_register, MAX_REGISTER_BYTES),
            _read(args.evidence_intake, MAX_INTAKE_BYTES),
            _read(args.review_handoff, MAX_HANDOFF_BYTES),
            _read(args.receipt_protocol, MAX_RECEIPT_PROTOCOL_BYTES),
        )
        raw = (json.dumps(report, indent=2, sort_keys=True,
                          ensure_ascii=False) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(raw)
        print("RECEIPT_VERIFIER_BLUEPRINT_ONLY / NOT_CONFIGURED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
