"""Offline CLI regression tests: use synthetic temporary files only."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from review_044_release_boundary_snapshot_cli import main
from test_review_044_release_boundary_snapshot import valid_report


class RecoveryBoundaryCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.report = self.root / "synthetic-report.json"
        self.report.write_text(json.dumps(valid_report()), encoding="utf-8")

    def invoke(self, *args):
        output = StringIO()
        with redirect_stdout(output):
            status = main(list(args))
        return status, output.getvalue()

    def test_no_implicit_execution(self):
        code, output = self.invoke("--report", str(self.report))
        self.assertEqual(2, code)
        self.assertIn("NOT EXECUTED", output)

    def test_valid_local_snapshot_remains_denied(self):
        code, output = self.invoke("--run", "--report", str(self.report))
        self.assertEqual(0, code)
        result = json.loads(output)
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("BLOCKED", result["deployment"])

    def test_export_create_only(self):
        target = self.root / "boundary.json"
        code, _ = self.invoke("--run", "--report", str(self.report), "--export", str(target))
        self.assertEqual(0, code)
        original = target.read_bytes()
        code, output = self.invoke("--run", "--report", str(self.report), "--export", str(target))
        self.assertEqual(1, code)
        self.assertIn("HOLD / DENY", output)
        self.assertEqual(original, target.read_bytes())

    def test_reject_oversize(self):
        self.report.write_bytes(b"x" * 65537)
        code, output = self.invoke("--run", "--report", str(self.report))
        self.assertEqual(1, code)
        self.assertIn("PP_BOUNDARY_INVALID", output)

    def test_reject_untrusted_escalation(self):
        report = valid_report()
        report["accessDecision"] = "ALLOW"
        self.report.write_text(json.dumps(report), encoding="utf-8")
        code, output = self.invoke("--run", "--report", str(self.report))
        self.assertEqual(1, code)
        self.assertNotIn("ALLOW", output)

    def test_reject_missing_input(self):
        code, _ = self.invoke("--run", "--report", str(self.root / "missing.json"))
        self.assertEqual(1, code)


if __name__ == "__main__":
    unittest.main()
