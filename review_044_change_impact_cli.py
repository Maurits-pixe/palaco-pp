"""Explicit offline, create-only export of hypothetical PP contract impact.

No original files are opened without --run. The command does not apply
the proposed change or perform tests, migrations, grants or deployments.
"""
import argparse
import json
from pathlib import Path

from review_044_change_impact import (
    ERROR, MAX_REGISTRY_BYTES, CHANGE_TYPES, prepare_change_impact_register,
)
from review_044_security_assurance import SOURCE_ROLES, SOURCE_MAXIMA
from review_044_contract_compatibility import MAX_ASSURANCE_BYTES

_NAMES = ("dossier", "queue", "intake", "plan", "observations", "manifest",
          "protocol", "contract", "blueprint", "interfaces", "transitions",
          "revocation", "assurance", "registry")
_LIMITS = SOURCE_MAXIMA + (MAX_ASSURANCE_BYTES, MAX_REGISTRY_BYTES)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unsigned, hypothetical change impact")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--changed-role", choices=SOURCE_ROLES)
    parser.add_argument("--change-type", choices=CHANGE_TYPES)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if (args.changed_role is None or args.change_type is None
            or args.export is None
            or any(getattr(args, name) is None for name in _NAMES)):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_change_impact_register(
            *[_read(getattr(args, name), maximum)
              for name, maximum in zip(_NAMES, _LIMITS)],
            args.changed_role, args.change_type,
        )
        raw = (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(raw)
        print("HYPOTHETICAL_CHANGE_IMPACT_ONLY / NOT_APPLIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
