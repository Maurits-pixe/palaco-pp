"""Validate a P.P. snapshot and restore it to a new file; never starts a server."""
import argparse
import json
import hashlib
import hmac
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

from backup_pp import create_backup
from server import PPError, Store


class ChecksumError(ValueError):
    pass


def restore_copy(source, destination, *, expected_sha256=None):
    def validate(candidate):
        # Deliberately avoid Store.__init__: restoration must not apply startup
        # migrations, create sessions or add historical events to the snapshot.
        checker = Store.__new__(Store)
        checker.path = str(candidate)
        if not checker.verify_integrity()["ok"]:
            raise ValueError("P.P.-integriteitscontrole mislukt; er is geen herstelbestand gepubliceerd.")

    if expected_sha256 is None:
        result = create_backup(source, destination, validate_snapshot=validate)
        result["source_checksum"] = "NOT_REQUESTED"
    else:
        if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
            raise ChecksumError("Gebruik de volledige SHA-256-controlewaarde van 64 hexadecimale tekens.")
        source = Path(source).resolve()
        destination = Path(destination).absolute()
        def check_sidecars():
            wal = Path(str(source) + "-wal")
            if (wal.exists() and wal.stat().st_size) or Path(str(source) + "-journal").exists():
                raise ChecksumError("Gebruik een afgesloten back-upbestand zonder actieve WAL/journal-bestanden.")
        check_sidecars()
        # Hash exactly the private byte copy later supplied to SQLite, rather than
        # checking a path and reopening a potentially changed source for restore.
        with tempfile.TemporaryDirectory(prefix=".pp-restore-", dir=destination.parent) as directory:
            captured = Path(directory) / "source.sqlite3"
            digest = hashlib.sha256()
            descriptor = os.open(captured, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as target, source.open("rb") as original:
                while True:
                    block = original.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
                    target.write(block)
            check_sidecars()
            if not hmac.compare_digest(digest.hexdigest(), expected_sha256.lower()):
                raise ChecksumError("Controlewaarde komt niet overeen: herstel gestopt, er is geen herstelbestand gemaakt.")
            result = create_backup(captured, destination, validate_snapshot=validate)
            result["source_checksum"] = "MATCH"
            result["source_sha256"] = digest.hexdigest()
    result["status"] = "RESTORE_COPY_CREATED"
    result["pp_integrity"] = "PASS"
    result["server_started"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path, help="bestaande P.P.-back-up")
    parser.add_argument("destination", type=Path, help="nieuw databasebestand in een bestaande map")
    parser.add_argument("--expected-sha256", help="eerder apart bewaarde SHA-256 van het back-upbestand")
    args = parser.parse_args()
    try:
        result = restore_copy(args.backup, args.destination, expected_sha256=args.expected_sha256)
    except ChecksumError as error:
        print("Herstelkopie niet gemaakt. %s" % error, file=sys.stderr)
        return 1
    except (OSError, sqlite3.Error, ValueError, TimeoutError, PPError):
        print("Herstelkopie niet gemaakt. Controleer bron, doelmap en P.P.-integriteit. "
              "Bestaande bestanden zijn niet vervangen.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Herstel afgebroken.", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    print("Stop de oorspronkelijke server voordat je deze kopie gebruikt. "
          "De mailwachtrij en sessies zijn meegekopieerd; draai geen tweede worker.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
