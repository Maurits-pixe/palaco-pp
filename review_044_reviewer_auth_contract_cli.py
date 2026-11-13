"""Owner-invoked offline export of unfulfilled reviewer-authentication controls.

No files read without --run. Does not contact an identity provider or
approve receipt, reviews or PALACO ONE access.
"""
import argparse
import json
from pathlib import Path

from review_044_reviewer_auth_contract import (
    ERROR, prepare_reviewer_auth_contract,
)
from review_044_review_protocol import MAX_MANIFEST_BYTES, MAX_PROTOCOL_BYTES
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES


def _limited(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        raw = source.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare unfulfilled reviewer authentication requirements only"
    )
    parser.add_argument("--run", action="store_true")
    for option in ("dossier", "queue", "intake", "plan", "observations",
                   "manifest", "protocol", "export"):
        parser.add_argument("--" + option, type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(getattr(args, k) is None for k in (
        "dossier", "queue", "intake", "plan", "observations",
        "manifest", "protocol", "export"
    )):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_reviewer_auth_contract(
            _limited(args.dossier, MAX_DOSSIER_BYTES),
            _limited(args.queue, MAX_QUEUE_BYTES),
            _limited(args.intake, MAX_INTAKE_BYTES),
            _limited(args.plan, MAX_PLAN_BYTES),
            _limited(args.observations, MAX_REGISTER_BYTES),
            _limited(args.manifest, MAX_MANIFEST_BYTES),
            _limited(args.protocol, MAX_PROTOCOL_BYTES),
        )
        data = (json.dumps(
            report, indent=2, sort_keys=True, ensure_ascii=False
        ) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(data)
        print("REVIEWER_AUTH_REQUIREMENTS_NOT_ESTABLISHED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
