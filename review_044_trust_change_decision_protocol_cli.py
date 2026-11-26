"""Opt-in create-only export of a DENY-only trust change decision protocol.

No input access before --run. No external review, signatures, evidence
acceptance, tests, trust promotion, account change, merge or deployment.
"""
import argparse
import json
from pathlib import Path

from review_044_trust_change_decision_protocol import (
    ERROR, MAX_REVIEW_DOSSIER_BYTES, prepare_trust_change_decision_protocol,
)
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
    MAX_RELEASE_MANIFEST_BYTES,MAX_MATRIX_BYTES,MAX_COCKPIT_BYTES
)
_EXTRAS = ("execution_plan","observation_register","evidence_intake",
           "review_handoff","receipt_protocol","verifier_blueprint",
           "trust_policy","change_control","review_dossier")
_EXTRA_LIMITS = (MAX_PLAN_BYTES,MAX_REGISTER_BYTES,MAX_INTAKE_BYTES,
                 MAX_HANDOFF_BYTES,MAX_RECEIPT_PROTOCOL_BYTES,
                 MAX_BLUEPRINT_BYTES,MAX_POLICY_BYTES,
                 MAX_CHANGE_CONTROL_BYTES,MAX_REVIEW_DOSSIER_BYTES)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as handle:
        result=handle.read(maximum+1)
    if not 0<len(result)<=maximum:
        raise ValueError
    return result


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description="Unsigned PP trust decision protocol; never grants")
    p.add_argument("--run",action="store_true")
    for name in _NAMES+_EXTRAS:
        p.add_argument("--"+name.replace("_","-"),type=Path)
    p.add_argument("--export",type=Path)
    args=p.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args,n) is None
                                  for n in _NAMES+_EXTRAS):
        print(ERROR+" / HOLD / DENY")
        return 2
    try:
        sources=tuple(_read(getattr(args,n),m) for n,m in zip(_NAMES,_LIMITS))
        extra=[_read(getattr(args,n),m) for n,m in zip(_EXTRAS,_EXTRA_LIMITS)]
        report=prepare_trust_change_decision_protocol(sources,*extra)
        raw=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
        with args.export.open("xb") as output:
            output.write(raw)
        print("TRUST_CHANGE_DECISION_DENY_ONLY / NOT_EXECUTED / HOLD / DENY")
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,OverflowError):
        print(ERROR+" / HOLD / DENY")
        return 1


if __name__=="__main__":
    raise SystemExit(main())
