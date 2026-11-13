"""Explicit create-only offline export of PP Security Assurance Dossier.

No file reads without --run. No tests, network calls, signature validation,
account changes, grants, session issuance or deployment.
"""
import argparse
import json
from pathlib import Path

from review_044_security_assurance import (
    ERROR, SOURCE_ROLES, SOURCE_MAXIMA, prepare_security_assurance_dossier,
)

OPTIONS = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions", "revocation",
)


def _read_bounded(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if not 0 < len(data) <= maximum:
        raise ValueError
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline, non-authorizing PP assurance report")
    parser.add_argument("--run", action="store_true")
    for name in OPTIONS:
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--export", type=Path, help="Create a new JSON report only")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if (args.export is None or len(OPTIONS) != len(SOURCE_ROLES)
            or any(getattr(args, name) is None for name in OPTIONS)):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        report = prepare_security_assurance_dossier(*[
            _read_bounded(getattr(args, name), maximum)
            for name, maximum in zip(OPTIONS, SOURCE_MAXIMA)
        ])
        raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        with args.export.open("xb") as destination:
            destination.write(raw)
        print("SECURITY_ASSURANCE_DOSSIER_CREATED_UNATTESTED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
