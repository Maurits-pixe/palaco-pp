"""Owner-invoked create-only export of a reviewer service architecture blueprint.

No files opened without --run. No provider, auth decision, audit record,
runtime tests, network operations or PALACO ONE mutation.
"""
import argparse
import json
from pathlib import Path

from review_044_reviewer_service_blueprint import (
    ERROR, MAX_CONTRACT_BYTES, prepare_reviewer_service_blueprint,
)
from review_044_review_protocol import MAX_MANIFEST_BYTES, MAX_PROTOCOL_BYTES
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    if not 0 < len(value) <= limit:
        raise ValueError
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Non-authorizing reviewer service blueprint")
    parser.add_argument("--run", action="store_true")
    for name in ("dossier", "queue", "intake", "plan", "observations",
                 "manifest", "protocol", "contract", "export"):
        parser.add_argument("--" + name, type=Path)
    options = parser.parse_args(argv)
    if not options.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(getattr(options, field) is None for field in (
        "dossier", "queue", "intake", "plan", "observations",
        "manifest", "protocol", "contract", "export"
    )):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        result = prepare_reviewer_service_blueprint(
            _read(options.dossier, MAX_DOSSIER_BYTES),
            _read(options.queue, MAX_QUEUE_BYTES),
            _read(options.intake, MAX_INTAKE_BYTES),
            _read(options.plan, MAX_PLAN_BYTES),
            _read(options.observations, MAX_REGISTER_BYTES),
            _read(options.manifest, MAX_MANIFEST_BYTES),
            _read(options.protocol, MAX_PROTOCOL_BYTES),
            _read(options.contract, MAX_CONTRACT_BYTES),
        )
        serialized = (json.dumps(
            result, sort_keys=True, indent=2, ensure_ascii=False
        ) + "\n").encode("utf-8")
        with options.export.open("xb") as target:
            target.write(serialized)
        print("BLUEPRINT_PREPARED_NOT_IMPLEMENTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
