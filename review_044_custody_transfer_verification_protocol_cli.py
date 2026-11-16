"""Opt-in create-only export of a non-executing custody transfer protocol.

Without --run no files are opened. No evidence sent, received, authenticated,
signed, accepted, tested, deployed or authorized.
"""
import argparse
import json
from pathlib import Path

from review_044_custody_transfer_verification_protocol import (
    ERROR, MAX_CUSTODY_CONTRACT_BYTES,
    prepare_custody_transfer_verification_protocol,
)
from review_044_audit_evidence_custody_contract import MAX_COLLECTION_PLAN_BYTES
from review_044_audit_evidence_collection_plan import MAX_MATRIX_BYTES
from review_044_audit_evidence_readiness_matrix import MAX_AUDIT_CONTRACT_BYTES
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
from review_044_release_readiness_cockpit import MAX_MATRIX_BYTES as MAX_ORIGINAL_MATRIX_BYTES
from review_044_release_execution_plan import MAX_COCKPIT_BYTES

_NAMES = ("dossier","queue","intake","plan","observations","manifest",
          "protocol","contract","blueprint","interfaces","transitions",
          "revocation","assurance","registry","impact","integrity",
          "matrix","cockpit")
_LIMITS = ARTIFACT_MAXIMA + (
    MAX_RELEASE_MANIFEST_BYTES,MAX_ORIGINAL_MATRIX_BYTES,MAX_COCKPIT_BYTES,
)
_EXTRAS = ("execution_plan","observation_register","evidence_intake",
           "review_handoff","receipt_protocol","verifier_blueprint",
           "trust_policy","change_control","review_dossier",
           "decision_protocol","audit_contract","readiness_matrix",
           "collection_plan","custody_contract")
_EXTRA_LIMITS = (
    MAX_PLAN_BYTES,MAX_REGISTER_BYTES,MAX_INTAKE_BYTES,
    MAX_HANDOFF_BYTES,MAX_RECEIPT_PROTOCOL_BYTES,MAX_BLUEPRINT_BYTES,
    MAX_POLICY_BYTES,MAX_CHANGE_CONTROL_BYTES,MAX_REVIEW_DOSSIER_BYTES,
    MAX_DECISION_PROTOCOL_BYTES,MAX_AUDIT_CONTRACT_BYTES,
    MAX_MATRIX_BYTES,MAX_COLLECTION_PLAN_BYTES,MAX_CUSTODY_CONTRACT_BYTES,
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as handle:
        raw=handle.read(maximum+1)
    if not 0<len(raw)<=maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description="Unsigned custody transfer protocol; no transfer")
    p.add_argument("--run",action="store_true")
    for name in _NAMES+_EXTRAS:
        p.add_argument("--"+name.replace("_","-"),type=Path)
    p.add_argument("--export",type=Path)
    a=p.parse_args(argv)
    if not a.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if a.export is None or any(getattr(a,n) is None for n in _NAMES+_EXTRAS):
        print(ERROR+" / HOLD / DENY")
        return 2
    try:
        original=tuple(_read(getattr(a,n),m) for n,m in zip(_NAMES,_LIMITS))
        extra=[_read(getattr(a,n),m) for n,m in zip(_EXTRAS,_EXTRA_LIMITS)]
        report=prepare_custody_transfer_verification_protocol(original,*extra)
        raw=(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
        with a.export.open("xb") as out:
            out.write(raw)
        print("UNSIGNED_TRANSFER_PROTOCOL / ZERO_TRANSFERS / HOLD / DENY")
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,OverflowError):
        print(ERROR+" / HOLD / DENY")
        return 1


if __name__=="__main__":
    raise SystemExit(main())
