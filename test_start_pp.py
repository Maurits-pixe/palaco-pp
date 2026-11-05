"""Real-process checks of the local starter using only temporary databases."""
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

STARTER = Path(__file__).resolve().with_name("start_pp.py")


class StarterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pp starter ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.environment = {k: v for k, v in os.environ.items() if not k.startswith("PP_")}

    def run_starter(self, *args):
        return subprocess.run([sys.executable, str(STARTER), *args], cwd=self.root,
                              env=self.environment, capture_output=True, text=True, timeout=10)

    def test_help_from_another_directory_does_not_create_data(self):
        result = self.run_starter("--help")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--db", result.stdout)
        self.assertEqual([], list(self.root.iterdir()))

    def test_diagnosis_leaves_missing_database_and_parent_uncreated(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        database = self.root / "new folder" / "test.sqlite3"
        result = self.run_starter("--diagnose", "--port", str(port), "--db", str(database))
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ready"])
        self.assertEqual("NEW_DATABASE", report["checks"]["database_header"])
        self.assertFalse(database.parent.exists())

    def test_diagnosis_reports_busy_port_and_does_not_read_private_content(self):
        database = self.root / "invalid.sqlite3"
        database.write_text("PRIVATE_SENTINEL_NOT_A_DATABASE")
        before = database.read_bytes()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            result = self.run_starter("--diagnose", "--port", str(listener.getsockname()[1]),
                                      "--db", str(database))
        self.assertEqual(1, result.returncode)
        report = json.loads(result.stdout)
        self.assertFalse(report["ready"])
        self.assertEqual("BLOCKED", report["checks"]["port"])
        self.assertEqual("FAIL", report["checks"]["database_header"])
        self.assertNotIn("PRIVATE_SENTINEL", result.stdout + result.stderr)
        self.assertEqual(before, database.read_bytes())

    def test_diagnosis_rejects_invalid_port_without_creating_database(self):
        result = self.run_starter("--diagnose", "--port", "0", "--db", str(self.root / "missing.db"))
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([], list(self.root.iterdir()))

    def test_busy_port_is_reported_and_existing_listener_survives(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            result = self.run_starter("--port", str(occupied.getsockname()[1]),
                                      "--db", str(self.root / "test.sqlite3"))
            self.assertEqual(1, result.returncode)
            self.assertIn("P.P. kon niet starten", result.stderr)
            self.assertIn("geen ander proces gestopt", result.stderr)
            with socket.create_connection(occupied.getsockname(), timeout=2):
                connection, _ = occupied.accept()
                connection.close()

    def test_custom_port_and_database_start_without_mail_or_browser(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        database = self.root / "eigen data" / "test.sqlite3"
        process = subprocess.Popen([sys.executable, str(STARTER), "--port", str(port),
                                    "--db", str(database)], cwd=self.root,
                                   env=self.environment, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 8
            while True:
                self.assertIsNone(process.poll(), "starter stopped unexpectedly")
                try:
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                    connection.request("GET", "/")
                    response = connection.getresponse()
                    body = response.read()
                    self.assertEqual(200, response.status)
                    self.assertIn(b"PALACO", body)
                    self.assertIsNone(response.getheader("Set-Cookie"))
                    connection.close()
                    break
                except (OSError, http.client.HTTPException):
                    if time.monotonic() >= deadline:
                        self.fail("server did not become ready")
                    time.sleep(0.05)
            self.assertTrue(database.is_file())
        finally:
            process.terminate()
            process.wait(timeout=5)
        checked = self.run_starter("--db", str(database), "--check")
        self.assertEqual(0, checked.returncode, checked.stderr)


if __name__ == "__main__":
    unittest.main()
