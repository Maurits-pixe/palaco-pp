"""Opt-in create-only offline export of deny-all verifier trust policy.

No files opened without --run. No issuer trusted, key imported, crypto
verified, account changed, tests executed, merge, release or deployment.
"""
import argparse
import json
from pathlib import Path

from review_044_verifier_trust_policy import (
    ERROR, MAX_BLUEPRINT_BYTES, prepare_verifier_trust_policy_register,
)
from review_044_independent_receipt_verifier_blueprint import MAX_RECEIPT_PROTOCOL_BYTES
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
_EXTRA = ("execution_plan", "observation_register", "evidence_intake",
          "review_handoff", "receipt_protocol", "verifier_blueprint")
_EXTRA_LIMITS = (MAX_PLAN_BYTES, MAX_REGISTER_BYTES, MAX_INTAKE_BYTES,
                 MAX_HANDOFF_BYTES, MAX_RECEIPT_PROTOCOL_BYTES,
                 MAX_BLUEPRINT_BYTES)


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Untrusted offline trust policy, deny-all")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES + _EXTRA:
        parser.add_argument("--" + name.replace("_", "-"), type=Path)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None
                                  for name in _NAMES + _EXTRA):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        original = tuple(_read(getattr(args, name), limit)
                         for name, limit in zip(_NAMES, _LIMITS))
        extra = [_read(getattr(args, name), limit)
                 for name, limit in zip(_EXTRA, _EXTRA_LIMITS)]
        report = prepare_verifier_trust_policy_register(original, *extra)
        raw = (json.dumps(report, indent=2, sort_keys=True,
                          ensure_ascii=False) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(raw)
        print("DENY_ALL_TRUST_POLICY_SNAPSHOT / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
