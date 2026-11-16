"""Owner-opt-in, create-only offline export of revocation requirements.

No file reading without --run. No actual revocation, permission update,
auth-provider connection, test execution, deployment or merge.
"""
import argparse
import json
from pathlib import Path

from review_044_revocation_recovery import (
    ERROR, MAX_TRANSITION_BYTES, prepare_revocation_recovery_contract,
)
from review_044_trust_transition import MAX_INTERFACE_BYTES
from review_044_reviewer_interface_contract import MAX_BLUEPRINT_BYTES
from review_044_reviewer_service_blueprint import MAX_CONTRACT_BYTES
from review_044_review_protocol import MAX_MANIFEST_BYTES, MAX_PROTOCOL_BYTES
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES

_INPUTS = (
    ("dossier", MAX_DOSSIER_BYTES), ("queue", MAX_QUEUE_BYTES),
    ("intake", MAX_INTAKE_BYTES), ("plan", MAX_PLAN_BYTES),
    ("observations", MAX_REGISTER_BYTES), ("manifest", MAX_MANIFEST_BYTES),
    ("protocol", MAX_PROTOCOL_BYTES), ("contract", MAX_CONTRACT_BYTES),
    ("blueprint", MAX_BLUEPRINT_BYTES), ("interfaces", MAX_INTERFACE_BYTES),
    ("transitions", MAX_TRANSITION_BYTES),
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        content = stream.read(maximum + 1)
    if not 0 < len(content) <= maximum:
        raise ValueError
    return content


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Revocation/recovery contract, not execution")
    parser.add_argument("--run", action="store_true")
    for name, _ in _INPUTS:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path, help="Create only a new local JSON file")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None for name, _ in _INPUTS):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_revocation_recovery_contract(
            *[_read(getattr(args, name), maximum) for name, maximum in _INPUTS]
        )
        payload = (json.dumps(
            report, indent=2, sort_keys=True, ensure_ascii=False
        ) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(payload)
        print("REVOCATION_REQUIREMENTS_PREPARED_NOT_EXECUTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
