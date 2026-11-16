"""Offline, opt-in create-only export of unsigned audit evidence readiness.

No source read without --run, no tests, external verification, signing,
reviewer authorization, activation, deployment, or PALACO ONE session.
"""
import argparse
import json
from pathlib import Path

from review_044_audit_evidence_readiness_matrix import (
    ERROR, MAX_AUDIT_CONTRACT_BYTES, prepare_audit_evidence_readiness_matrix,
)
from review_044_trust_decision_audit_contract import MAX_DECISION_PROTOCOL_BYTES
from review_044_trust_change_decision_protocol import MAX_REVIEW_DOSSIER_BYTES
from review_044_trust_change_review_dossier import MAX_CHANGE_CONTROL_BYTES
from review_044_trust_policy_change_control import MAX_POLICY_BYTES
from review_044_verifier_trust_policy import MAX_BLUEPRINT_BYTES
from review_044_independent_receipt_verifier_blueprint import MAX_RECEIPT_PROTOCOL_BYTES
from review_044_independent_receipt_protocol import MAX_HANDOFF_BYTES
from review_044_release_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES
from review_044_release_evidence_intake import MAX_INTAKE_BYTES
from review_044_release_integrity import ARTIFACT_MAXIMA
from review_044_release_evidence_matrix import MAX_RELEASE_MANIFEST_BYTES
from review_044_release_readiness_cockpit import MAX_MATRIX_BYTES
from review_044_release_execution_plan import MAX_COCKPIT_BYTES

_NAMES = ("dossier","queue","intake","plan","observations","manifest",
          "protocol","contract","blueprint","interfaces","transitions",
          "revocation","assurance","registry","impact","integrity",
          "matrix","cockpit")
_LIMITS = ARTIFACT_MAXIMA + (
    MAX_RELEASE_MANIFEST_BYTES, MAX_MATRIX_BYTES, MAX_COCKPIT_BYTES,
)
_EXTRAS = ("execution_plan","observation_register","evidence_intake",
           "review_handoff","receipt_protocol","verifier_blueprint",
           "trust_policy","change_control","review_dossier",
           "decision_protocol","audit_contract")
_EXTRA_LIMITS = (MAX_PLAN_BYTES,MAX_REGISTER_BYTES,MAX_INTAKE_BYTES,
                 MAX_HANDOFF_BYTES,MAX_RECEIPT_PROTOCOL_BYTES,
                 MAX_BLUEPRINT_BYTES,MAX_POLICY_BYTES,
                 MAX_CHANGE_CONTROL_BYTES,MAX_REVIEW_DOSSIER_BYTES,
                 MAX_DECISION_PROTOCOL_BYTES,MAX_AUDIT_CONTRACT_BYTES)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as handle:
        data = handle.read(maximum + 1)
    if not 0 < len(data) <= maximum:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unsigned audit readiness requirements; no verification")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES + _EXTRAS:
        parser.add_argument("--" + name.replace("_","-"), type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None
                                  for name in _NAMES + _EXTRAS):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        originals = tuple(_read(getattr(args, name), maximum)
                          for name, maximum in zip(_NAMES, _LIMITS))
        extras = [_read(getattr(args, name), maximum)
                  for name, maximum in zip(_EXTRAS, _EXTRA_LIMITS)]
        report = prepare_audit_evidence_readiness_matrix(originals, *extras)
        data = (json.dumps(report, sort_keys=True, indent=2,
                           ensure_ascii=False) + "\n").encode("utf-8")
        with args.export.open("xb") as output:
            output.write(data)
        print("AUDIT_READINESS_REQUIREMENTS_ONLY / 0_OF_8_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
