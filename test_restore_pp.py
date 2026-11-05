import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from backup_pp import create_backup
from restore_pp import ChecksumError, restore_copy
from server import Store


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pp herstel ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "original.sqlite3"
        self.backup = self.root / "backup.sqlite3"
        self.restored = self.root / "hersteld privé.sqlite3"
        self.store = Store(self.database)

    def test_roundtrip_preserves_id_number_notes_history_and_sessions(self):
        consumer, token = self.store.create_consumer()
        self.store.register_account(consumer, "restore.owner", "Synthetic restore password 2026!", token)
        self.store.select(consumer, self.store.options(consumer)["options"][0]["id"])
        self.store.save_memory(consumer, None, "Private title", "PRIVATE_BODY", [])
        create_backup(self.database, self.backup)
        source_bytes = self.backup.read_bytes()
        with self.store.connection() as db:
            original_dump = list(db.iterdump())
        result = restore_copy(self.backup, self.restored)
        self.assertEqual("RESTORE_COPY_CREATED", result["status"])
        self.assertFalse(result["server_started"])
        self.assertEqual(hashlib.sha256(self.restored.read_bytes()).hexdigest(), result["sha256"])
        checker = Store.__new__(Store)
        checker.path = str(self.restored)
        with checker.connection() as db:
            self.assertEqual(original_dump, list(db.iterdump()))
        self.assertEqual(self.store.me(consumer), checker.me(consumer))
        self.assertEqual(self.store.list_memory(consumer), checker.list_memory(consumer))
        self.assertEqual(source_bytes, self.backup.read_bytes())

    def test_existing_target_or_backup_itself_is_never_replaced(self):
        create_backup(self.database, self.backup)
        self.restored.write_bytes(b"KEEP_THIS_FILE")
        source_bytes = self.backup.read_bytes()
        for destination in (self.restored, self.backup):
            with self.assertRaises(ValueError):
                restore_copy(self.backup, destination)
        self.assertEqual(b"KEEP_THIS_FILE", self.restored.read_bytes())
        self.assertEqual(source_bytes, self.backup.read_bytes())

    def test_expected_checksum_restores_the_captured_file(self):
        create_backup(self.database, self.backup)
        digest = hashlib.sha256(self.backup.read_bytes()).hexdigest()
        real_backup = create_backup
        def change_original_after_capture(source, destination, **options):
            self.assertNotEqual(self.backup, Path(source))
            self.assertEqual(digest, hashlib.sha256(Path(source).read_bytes()).hexdigest())
            self.backup.write_bytes(b"CHANGED_AFTER_CAPTURE")
            return real_backup(source, destination, **options)
        with patch("restore_pp.create_backup", side_effect=change_original_after_capture):
            report = restore_copy(self.backup, self.restored, expected_sha256=digest.upper())
        self.assertEqual("MATCH", report["source_checksum"])
        self.assertEqual(digest, report["source_sha256"])
        self.assertTrue(self.restored.is_file())
        self.assertFalse(list(self.root.glob(".pp-restore-*")))

    def test_checksum_mismatch_and_invalid_values_publish_nothing(self):
        create_backup(self.database, self.backup)
        before = self.backup.read_bytes()
        for digest in ("0" * 64, "abc", "g" * 64, " " * 64):
            with self.subTest(digest=digest), self.assertRaises(ChecksumError):
                restore_copy(self.backup, self.restored, expected_sha256=digest)
            self.assertFalse(self.restored.exists())
            self.assertFalse(list(self.root.glob(".pp-restore-*")))
        self.assertEqual(before, self.backup.read_bytes())

    def test_checksum_mode_rejects_sidecar_data(self):
        create_backup(self.database, self.backup)
        digest = hashlib.sha256(self.backup.read_bytes()).hexdigest()
        wal = Path(str(self.backup) + "-wal")
        wal.write_bytes(b"PENDING_WAL")
        with self.assertRaises(ChecksumError):
            restore_copy(self.backup, self.restored, expected_sha256=digest)
        self.assertFalse(self.restored.exists())
        self.assertEqual(b"PENDING_WAL", wal.read_bytes())

    def test_cli_checksum_mismatch_has_clear_message_and_nonzero_exit(self):
        create_backup(self.database, self.backup)
        script = Path(__file__).with_name("restore_pp.py").resolve()
        result = subprocess.run([sys.executable, str(script), str(self.backup), str(self.restored),
                                 "--expected-sha256", "0" * 64], capture_output=True, text=True, timeout=10)
        self.assertEqual(1, result.returncode)
        self.assertIn("Controlewaarde komt niet overeen", result.stderr)
        self.assertFalse(self.restored.exists())

    def test_invalid_pp_history_blocks_publication_without_repairing_source(self):
        consumer, _ = self.store.create_consumer()
        with self.store.transaction() as db:
            self.store.audit(db, consumer, "NUMBER_SELECTED", {})
        create_backup(self.database, self.backup)
        source_bytes = self.backup.read_bytes()
        with self.assertRaises(ValueError):
            restore_copy(self.backup, self.restored)
        self.assertFalse(self.restored.exists())
        self.assertFalse(list(self.root.glob(".pp-backup-*")))
        self.assertEqual(source_bytes, self.backup.read_bytes())

    def test_missing_or_corrupt_backup_creates_no_destination(self):
        with self.assertRaises(ValueError):
            restore_copy(self.backup, self.restored)
        self.backup.write_bytes(b"BROKEN_PRIVATE_SENTINEL")
        script = Path(__file__).with_name("restore_pp.py").resolve()
        result = subprocess.run([sys.executable, str(script), str(self.backup), str(self.restored)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(1, result.returncode)
        self.assertFalse(self.restored.exists())
        self.assertNotIn("PRIVATE_SENTINEL", result.stdout + result.stderr)

    def test_cli_success_is_explicit_and_does_not_start_server(self):
        create_backup(self.database, self.backup)
        script = Path(__file__).with_name("restore_pp.py").resolve()
        result = subprocess.run([sys.executable, str(script), str(self.backup), str(self.restored)],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("PASS", report["pp_integrity"])
        self.assertFalse(report["server_started"])
        self.assertIn("geen tweede worker", result.stderr)


if __name__ == "__main__":
    unittest.main()
