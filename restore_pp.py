"""Validate a P.P. snapshot and restore it to a new file; never starts a server."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

from backup_pp import create_backup
from server import PPError, Store


def restore_copy(source, destination):
    def validate(candidate):
        # Deliberately avoid Store.__init__: restoration must not apply startup
        # migrations, create sessions or add historical events to the snapshot.
        checker = Store.__new__(Store)
        checker.path = str(candidate)
        if not checker.verify_integrity()["ok"]:
            raise ValueError("P.P.-integriteitscontrole mislukt; er is geen herstelbestand gepubliceerd.")

    result = create_backup(source, destination, validate_snapshot=validate)
    result["status"] = "RESTORE_COPY_CREATED"
    result["pp_integrity"] = "PASS"
    result["server_started"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path, help="bestaande P.P.-back-up")
    parser.add_argument("destination", type=Path, help="nieuw databasebestand in een bestaande map")
    args = parser.parse_args()
    try:
        result = restore_copy(args.backup, args.destination)
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
