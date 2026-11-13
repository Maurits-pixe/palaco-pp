"""Opt-in, create-only offline contract compatibility registry exporter.

No files read without --run. No tests, migrations, grants or account updates.
"""
import argparse
import json
from pathlib import Path

from review_044_contract_compatibility import (
    ERROR, MAX_ASSURANCE_BYTES, build_contract_compatibility_register,
)
from review_044_security_assurance import SOURCE_MAXIMA

_NAMES = (
    "dossier", "queue", "intake", "plan", "observations", "manifest",
    "protocol", "contract", "blueprint", "interfaces", "transitions", "revocation",
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file():
        raise ValueError
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise ValueError
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Non-authorizing v0 contract register")
    parser.add_argument("--run", action="store_true")
    for name in _NAMES + ("assurance", "export"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Explicit --run required. HOLD / DENY.")
        return 2
    if any(getattr(args, name) is None for name in _NAMES + ("assurance", "export")):
        print(ERROR + " / HOLD / DENY")
        return 2
    try:
        originals = [
            _read(getattr(args, name), maximum)
            for name, maximum in zip(_NAMES, SOURCE_MAXIMA)
        ]
        report = build_contract_compatibility_register(
            *originals, _read(args.assurance, MAX_ASSURANCE_BYTES)
        )
        raw = (json.dumps(
            report, ensure_ascii=False, sort_keys=True, indent=2
        ) + "\n").encode("utf-8")
        with args.export.open("xb") as target:
            target.write(raw)
        print("V0_INTERNAL_COMPATIBILITY_REGISTER_PREPARED / NOT_VERIFIED / HOLD / DENY")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        print(ERROR + " / HOLD / DENY")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
