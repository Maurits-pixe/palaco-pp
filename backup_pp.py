"""Explicit local SQLite snapshot; never replaces an existing destination."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent


def create_backup(source, destination, *, validate_snapshot=None):
    source, destination = Path(source).resolve(), Path(destination).absolute()
    if not source.is_file():
        raise ValueError("Bron-database ontbreekt; er is geen nieuwe database gemaakt.")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Bestemming bestaat al. Kies een nieuwe bestandsnaam.")
    if not destination.parent.is_dir():
        raise ValueError("De doelmap ontbreekt. Kies een bestaande map.")
    deadline = time.monotonic() + 15

    def progress(status, remaining, total):
        if time.monotonic() > deadline:
            raise TimeoutError("Back-up duurde te lang; probeer opnieuw als de server gestopt is.")

    with tempfile.TemporaryDirectory(prefix=".pp-backup-", dir=destination.parent) as directory:
        candidate = Path(directory) / "snapshot.sqlite3"
        descriptor = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=1)) as original:
            with closing(sqlite3.connect(candidate, timeout=1)) as snapshot:
                original.backup(snapshot, pages=128, progress=progress, sleep=0.05)
                tables = {row[0] for row in snapshot.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {"consumers", "accounts", "batches", "options", "selections", "memory_entries", "audit"}.issubset(tables):
                    raise ValueError("Dit is geen herkenbare P.P.-database; bron en bestemming zijn niet vervangen.")
                if snapshot.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ValueError("De SQLite-integriteitscontrole van de kopie is mislukt.")
                if snapshot.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise ValueError("De kopie bevat ongeldige databaserelaties.")
        if validate_snapshot is not None:
            validate_snapshot(candidate)
        with candidate.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
            os.fsync(stream.fileno())
        size = candidate.stat().st_size
        # Atomic publication of a completed snapshot; an existing file or symlink wins.
        # If hard links are unsupported, fail explicitly rather than overwrite/copy.
        os.link(candidate, destination)
    return {"status": "BACKUP_CREATED", "bytes": size, "sha256": digest,
            "sqlite_integrity": "PASS", "foreign_keys": "PASS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="nieuw back-upbestand in een bestaande map")
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "palaco.sqlite3")
    args = parser.parse_args()
    try:
        result = create_backup(args.db, args.destination)
    except (OSError, sqlite3.Error, ValueError, TimeoutError) as error:
        print("Back-up niet gemaakt: %s" % error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Back-up afgebroken.", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
