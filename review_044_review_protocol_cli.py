"""Explicit offline export of unsigned PP review protocol claims.

Without --run: no reads or writes. Each run creates a NEW file and
never authenticates a reviewer, proves delivery, or executes reviews.
"""
import argparse
from pathlib import Path

from review_044_review_protocol import (
    ERROR, MARKS, ROLES, REQUIREMENTS, MAX_MANIFEST_BYTES,
    MAX_PROTOCOL_BYTES, append_review_protocol_claim,
)
from review_044_human_review_queue import MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES
from review_044_review_intake import MAX_INTAKE_BYTES
from review_044_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as source:
        data = source.read(maximum + 1)
    if not 0 < len(data) <= maximum:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unsigned receipt and review claims, no authentication")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--dossier", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--mark", choices=sorted(MARKS))
    parser.add_argument("--role-claim", choices=sorted(ROLES))
    parser.add_argument("--requirement", choices=REQUIREMENTS)
    parser.add_argument("--export", type=Path, help="New JSON only, never overwrite")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(x is None for x in (
        args.dossier, args.queue, args.intake, args.plan, args.observations,
        args.manifest, args.mark, args.role_claim, args.requirement, args.export
    )):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        result = append_review_protocol_claim(
            _read(args.dossier, MAX_DOSSIER_BYTES),
            _read(args.queue, MAX_QUEUE_BYTES),
            _read(args.intake, MAX_INTAKE_BYTES),
            _read(args.plan, MAX_PLAN_BYTES),
            _read(args.observations, MAX_REGISTER_BYTES),
            _read(args.manifest, MAX_MANIFEST_BYTES),
            _read(args.previous, MAX_PROTOCOL_BYTES) if args.previous else None,
            args.mark, args.role_claim, args.requirement,
        )
        with args.export.open("xb") as output:
            output.write(result)
        print("UNSIGNED_REVIEW_CLAIM_RECORDED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
