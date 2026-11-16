"""Future owner-only opt-in local snapshot writer; does not run tests.

Explicit --run reads the 18 original sources and exact plan, verifies the
prior append-only register and creates a NEW snapshot. No overwrite, network,
authority, reviewer signature or PALACO ONE session is performed.
"""
import argparse
from pathlib import Path

from review_044_release_observation_register import (
    ERROR, MAX_PLAN_BYTES, MAX_REGISTER_BYTES, MAX_EVIDENCE_BYTES,
    MARKS, _ROLES, append_release_observation,
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
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unsigned release observation; not verification")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--execution-plan", type=Path)
    parser.add_argument("--previous-register", type=Path)
    parser.add_argument("--check-id")
    parser.add_argument("--mark", choices=MARKS)
    parser.add_argument("--role-claim", choices=_ROLES)
    parser.add_argument("--note", default="")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / --run is required. HOLD / DENY.")
        return 2
    if (args.export is None or args.execution_plan is None
            or args.check_id is None or args.mark is None
            or args.role_claim is None
            or any(getattr(args, name) is None for name in _NAMES)):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        sources = tuple(
            _read(getattr(args, name), maximum)
            for name, maximum in zip(_NAMES, _LIMITS)
        )
        plan = _read(args.execution_plan, MAX_PLAN_BYTES)
        previous = (_read(args.previous_register, MAX_REGISTER_BYTES)
                    if args.previous_register is not None else None)
        evidence = (_read(args.evidence, MAX_EVIDENCE_BYTES)
                    if args.evidence is not None else None)
        result = append_release_observation(
            sources, plan, previous, args.check_id, args.mark,
            args.role_claim, args.note, evidence
        )
        with args.export.open("xb") as target:
            target.write(result)
        print("UNSIGNED_LOCAL_OBSERVATION_RECORDED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
