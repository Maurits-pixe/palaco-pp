"""Create-only owner-invoked PP release evidence reference exporter.

Requires explicit --run. Checks the original 18 source artifacts, exact
execution plan, complete observation chain, and the actual evidence bytes.
Writes a NEW unsigned reference snapshot; never uploads evidence or grants.
"""
import argparse
from pathlib import Path

from review_044_release_evidence_intake import (
    ERROR, MAX_INTAKE_BYTES, KINDS, append_release_evidence_intake,
)
from review_044_release_observation_register import (
    MAX_PLAN_BYTES, MAX_REGISTER_BYTES, MAX_EVIDENCE_BYTES,
)
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
    MAX_RELEASE_MANIFEST_BYTES, MAX_MATRIX_BYTES, MAX_COCKPIT_BYTES
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as file:
        data = file.read(maximum + 1)
    if not 0 < len(data) <= maximum:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Untrusted release evidence intake; no approval")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--execution-plan", type=Path)
    parser.add_argument("--observation-register", type=Path)
    parser.add_argument("--previous-intake", type=Path)
    parser.add_argument("--observation-sequence", type=int)
    parser.add_argument("--kind", choices=KINDS)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if (args.export is None or args.execution_plan is None
            or args.observation_register is None
            or args.observation_sequence is None or args.kind is None
            or args.evidence is None
            or any(getattr(args, name) is None for name in _NAMES)):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        sources = tuple(
            _read(getattr(args, name), maximum)
            for name, maximum in zip(_NAMES, _LIMITS)
        )
        data = append_release_evidence_intake(
            sources,
            _read(args.execution_plan, MAX_PLAN_BYTES),
            _read(args.observation_register, MAX_REGISTER_BYTES),
            _read(args.previous_intake, MAX_INTAKE_BYTES)
            if args.previous_intake is not None else None,
            args.observation_sequence,
            args.kind,
            _read(args.evidence, MAX_EVIDENCE_BYTES),
        )
        with args.export.open("xb") as destination:
            destination.write(data)
        print("UNSIGNED_LOCAL_EVIDENCE_REFERENCE / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
