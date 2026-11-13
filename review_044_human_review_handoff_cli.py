"""Explicit offline, create-only human review handoff manifest exporter.

Never opens a file without --run. Does not transmit any manifest or evidence,
authenticate a recipient, run checks or alter PALACO ONE permissions.
"""
import argparse
import json
from pathlib import Path

from review_044_human_review_handoff import ERROR, prepare_human_review_handoff
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES


def _bounded(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        raw = source.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unsigned PP-RECOVERY-002 reviewer handoff manifest (no delivery)"
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--export", type=Path, help="Create new JSON only, no overwrite")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(x is None for x in (
        args.dossier, args.queue, args.intake, args.plan, args.observations
    )):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        manifest = prepare_human_review_handoff(
            _bounded(args.dossier, MAX_DOSSIER_BYTES),
            _bounded(args.queue, MAX_QUEUE_BYTES),
            _bounded(args.intake, MAX_INTAKE_BYTES),
            _bounded(args.plan, MAX_PLAN_BYTES),
            _bounded(args.observations, MAX_REGISTER_BYTES),
        )
        encoded = (json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, indent=2
        ) + "\n").encode("utf-8")
        if args.export is None:
            print(encoded.decode("utf-8"), end="")
        else:
            with args.export.open("xb") as destination:
                destination.write(encoded)
            print("UNSIGNED_HANDOFF_MANIFEST_CREATED_NOT_DELIVERED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
