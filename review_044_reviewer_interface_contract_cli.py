"""Create-only local export of disabled reviewer interface contracts.

No file access without --run; no API routes, provider calls, tests, authorization,
audit execution, issuance or overwrite of any prior artifact.
"""
import argparse
import json
from pathlib import Path

from review_044_reviewer_interface_contract import (
    ERROR, MAX_BLUEPRINT_BYTES, prepare_reviewer_interface_contract,
)
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
    ("blueprint", MAX_BLUEPRINT_BYTES),
)


def _read_bounded(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Disabled reviewer API interface contract export")
    parser.add_argument("--run", action="store_true")
    for name, _ in _INPUTS:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path, help="Create new JSON only")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if args.export is None or any(getattr(args, name) is None for name, _ in _INPUTS):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        sources = [
            _read_bounded(getattr(args, name), maximum)
            for name, maximum in _INPUTS
        ]
        report = prepare_reviewer_interface_contract(*sources)
        raw = (json.dumps(
            report, sort_keys=True, indent=2, ensure_ascii=False
        ) + "\n").encode("utf-8")
        with args.export.open("xb") as destination:
            destination.write(raw)
        print("INTERFACE_CONTRACT_PREPARED / ENDPOINTS_DISABLED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
