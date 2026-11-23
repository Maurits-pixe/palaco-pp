"""Synthetic negative tests for the unsigned post-matrix CI verdict."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pp_recovery_ci_matrix_verdict import assess_matrix, main
from test_pp_recovery_ci_matrix_gate import RUN, SHA, write_pair


class MatrixVerdictTests(unittest.TestCase):
    def test_synthetic_success_still_denies_all_authority(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_pair(folder)
            result = assess_matrix(folder, expected_sha=SHA, expected_run_id=RUN)
            self.assertEqual(
                "BOTH_RECORDED_SUCCESS_UNTRUSTED",
                result["syntheticMatrixObservation"],
            )
            self.assertEqual("NOT_INDEPENDENTLY_VERIFIED", result["externalCIConclusion"])
            self.assertEqual("HOLD", result["authorization"])
            self.assertEqual("DENY", result["accessDecision"])
            self.assertEqual("NOT_AUTHORIZED", result["issuance"])
            self.assertEqual("BLOCKED", result["deployment"])
            self.assertEqual("1", result["workflowRunAttempt"])
            self.assertEqual({"3.11", "3.12"}, set(result["receiptSha256ByVersion"]))
            self.assertTrue(all(len(value) == 64 for value in result["receiptSha256ByVersion"].values()))

    def test_missing_artifacts_produce_failure_verdict(self):
        with TemporaryDirectory() as tmp:
            result = assess_matrix(
                Path(tmp), expected_sha=SHA, expected_run_id=RUN,
            )
            self.assertEqual("INCOMPLETE_OR_FAILED", result["syntheticMatrixObservation"])
            self.assertEqual("PAIR_REJECTED", result["reason"])
            self.assertEqual({}, result["receiptSha256ByVersion"])

    def test_incomplete_tests_produce_failure_verdict(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_pair(folder, second_outcome="skipped")
            result = assess_matrix(folder, expected_sha=SHA, expected_run_id=RUN)
            self.assertEqual("INCOMPLETE_OR_FAILED", result["syntheticMatrixObservation"])
            self.assertEqual("HOLD", result["authorization"])

    def test_bad_run_context_never_produces_success(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_pair(folder)
            for sha, run in ((SHA, ""), ("z" * 40, RUN), (SHA, "../test")):
                with self.subTest(sha=sha, run=run):
                    result = assess_matrix(
                        folder, expected_sha=sha, expected_run_id=run,
                    )
                    self.assertEqual("INCOMPLETE_OR_FAILED", result["syntheticMatrixObservation"])
                    self.assertEqual("INVALID_WORKFLOW_CONTEXT", result["reason"])

    def test_different_receipt_bytes_change_verdict_fingerprint(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_pair(folder)
            first = assess_matrix(folder, expected_sha=SHA, expected_run_id=RUN)
            target = folder / "pp-recovery-receipt-py3.12" / "pp-recovery-ci-receipt.json"
            # Whitespace is valid JSON but changes the exact bytes observed.
            target.write_bytes(target.read_bytes() + b" ")
            second = assess_matrix(folder, expected_sha=SHA, expected_run_id=RUN)
            self.assertEqual(
                first["receiptSha256ByVersion"]["3.11"],
                second["receiptSha256ByVersion"]["3.11"],
            )
            self.assertNotEqual(
                first["receiptSha256ByVersion"]["3.12"],
                second["receiptSha256ByVersion"]["3.12"],
            )
            self.assertEqual("HOLD", second["authorization"])

    def test_cli_exports_failure_then_exits_nonzero(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "verdict.json"
            with patch.dict(os.environ, {"GITHUB_SHA": SHA, "GITHUB_RUN_ID": RUN}):
                code = main([
                    "--artifacts", str(root / "missing"),
                    "--output", str(output),
                ])
            self.assertEqual(1, code)
            verdict = json.loads(output.read_bytes())
            self.assertEqual("INCOMPLETE_OR_FAILED", verdict["syntheticMatrixObservation"])
            self.assertEqual("DENY", verdict["accessDecision"])

    def test_cli_refuses_overwrite_existing_verdict(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            output = root.parent / (root.name + "-verdict.json")
            try:
                output.write_text("PREEXISTING", encoding="utf-8")
                with patch.dict(os.environ, {"GITHUB_SHA": SHA, "GITHUB_RUN_ID": RUN}):
                    code = main([
                        "--artifacts", str(root), "--output", str(output),
                    ])
                self.assertEqual(1, code)
                self.assertEqual("PREEXISTING", output.read_text(encoding="utf-8"))
            finally:
                output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
