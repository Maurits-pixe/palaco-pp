import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from backup_pp import create_backup
from server import Store


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pp backup ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.sqlite3"
        self.destination = self.root / "kopie privé.sqlite3"
        self.store = Store(self.source)

    def test_wal_snapshot_preserves_number_account_memory_and_integrity(self):
        consumer, token = self.store.create_consumer()
        self.store.register_account(consumer, "backup.owner", "Synthetic backup password 2026!", token)
        self.store.select(consumer, self.store.options(consumer)["options"][2]["id"])
        number = self.store.me(consumer)
        note = self.store.save_memory(consumer, None, "Private title", "PRIVATE_CONTENT", ["test"])
        with self.store.connection() as live:
            live.execute("PRAGMA journal_mode=WAL")
            marker, _ = self.store.create_consumer()
            self.assertTrue(Path(str(self.source) + "-wal").exists())
            result = create_backup(self.source, self.destination)
            self.assertEqual("BACKUP_CREATED", result["status"])
            self.assertEqual(hashlib.sha256(self.destination.read_bytes()).hexdigest(), result["sha256"])
            restored = Store(self.destination)
            self.assertEqual(number, restored.me(consumer))
            self.assertEqual(note, restored.list_memory(consumer)["entries"][0])
            self.assertTrue(restored.verify_integrity()["ok"])
            with restored.connection() as copied:
                self.assertEqual(1, copied.execute("SELECT count(*) FROM consumers WHERE id=?", (marker,)).fetchone()[0])
                self.assertEqual("backup.owner", copied.execute("SELECT username FROM accounts WHERE consumer_id=?", (consumer,)).fetchone()[0])
        self.assertEqual(number, self.store.me(consumer))
        self.assertEqual([self.destination.name, self.source.name], sorted(p.name for p in self.root.iterdir()))

    def test_existing_target_and_source_target_are_never_replaced(self):
        self.destination.write_bytes(b"KEEP_EXISTING_FILE")
        original = self.source.read_bytes()
        for target in (self.destination, self.source):
            with self.assertRaises(ValueError):
                create_backup(self.source, target)
        self.assertEqual(b"KEEP_EXISTING_FILE", self.destination.read_bytes())
        self.assertEqual(original, self.source.read_bytes())

    def test_missing_corrupt_and_unrelated_sources_publish_nothing(self):
        missing = self.root / "missing.sqlite3"
        corrupt = self.root / "corrupt.sqlite3"
        corrupt.write_bytes(b"NOT_A_DATABASE_PRIVATE_SENTINEL")
        unrelated = self.root / "other.sqlite3"
        with sqlite3.connect(unrelated) as db:
            db.execute("CREATE TABLE other(value)")
        for source in (missing, corrupt, unrelated):
            with self.subTest(source=source), self.assertRaises((ValueError, sqlite3.Error)):
                create_backup(source, self.destination)
            self.assertFalse(self.destination.exists())
            self.assertFalse(list(self.root.glob(".pp-backup-*")))
        self.assertFalse(missing.exists())

    def test_competing_destination_wins_without_overwrite(self):
        import os
        original_link = os.link
        def competing_link(source, destination):
            Path(destination).write_bytes(b"OTHER_WRITER")
            return original_link(source, destination)
        with patch("backup_pp.os.link", side_effect=competing_link), self.assertRaises(FileExistsError):
            create_backup(self.source, self.destination)
        self.assertEqual(b"OTHER_WRITER", self.destination.read_bytes())
        self.assertFalse(list(self.root.glob(".pp-backup-*")))

    def test_unsupported_publication_fails_without_partial_backup(self):
        with patch("backup_pp.os.link", side_effect=OSError("not supported")), self.assertRaises(OSError):
            create_backup(self.source, self.destination)
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.root.glob(".pp-backup-*")))

    def test_cli_reports_checksum_without_private_contents(self):
        consumer, _ = self.store.create_consumer()
        self.store.save_memory(consumer, None, "PRIVATE_TITLE", "PRIVATE_CONTENT", [])
        script = Path(__file__).with_name("backup_pp.py").resolve()
        result = subprocess.run([sys.executable, str(script), str(self.destination), "--db", str(self.source)],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("BACKUP_CREATED", json.loads(result.stdout)["status"])
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
