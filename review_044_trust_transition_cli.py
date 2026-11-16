"""Create-only opt-in export of a permanently BLOCKED reviewer trust-transition plan.

No original files are read without --run. This does not run a validator
against real credentials, perform tests or create a session or authorization.
"""
import argparse
import json
from pathlib import Path

from review_044_trust_transition import (
    ERROR, MAX_INTERFACE_BYTES, prepare_trust_transition_protocol,
)
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
)


def _bounded(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        result = stream.read(limit + 1)
    if not 0 < len(result) <= limit:
        raise ValueError
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unimplemented reviewer trust transitions")
    parser.add_argument("--run", action="store_true")
    for name, _ in _INPUTS:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path, help="New JSON file only")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None for name, _ in _INPUTS):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_trust_transition_protocol(
            *[_bounded(getattr(args, name), limit) for name, limit in _INPUTS]
        )
        data = (json.dumps(
            report, ensure_ascii=False, sort_keys=True, indent=2
        ) + "\n").encode("utf-8")
        with args.export.open("xb") as output:
            output.write(data)
        print("TRANSITIONS_PREPARED_ALL_BLOCKED / NOT_EXECUTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
