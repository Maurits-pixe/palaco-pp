"""Synthetic tests for independent re-evaluation of unsigned matrix verdicts."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pp_recovery_ci_matrix_verdict import assess_matrix
from pp_recovery_ci_verdict_audit import audit_verdict
from review_044_release_boundary_snapshot import BoundaryInputError
from test_pp_recovery_ci_matrix_gate import RUN, SHA, write_pair


def encoded(value: dict) -> bytes:
    return (json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ) + "\n").encode("ascii")


class MatrixVerdictAuditTests(unittest.TestCase):
    def test_exact_success_verdict_stays_denied(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            verdict = assess_matrix(root, expected_sha=SHA, expected_run_id=RUN)
            result = audit_verdict(encoded(verdict), root, expected_sha=SHA, expected_run_id=RUN)
            self.assertEqual("MATCHING_UNTRUSTED_EXACT_BYTES", result["audit"])
            self.assertEqual("HOLD", result["authorization"])
            self.assertEqual("DENY", result["accessDecision"])
            self.assertEqual("NOT_AUTHORIZED", result["issuance"])
            self.assertEqual("NOT_INDEPENDENTLY_VERIFIED", result["externalCIConclusion"])

    def test_exact_failure_verdict_consistent_but_not_passed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            verdict = assess_matrix(root, expected_sha=SHA, expected_run_id=RUN)
            result = audit_verdict(encoded(verdict), root, expected_sha=SHA, expected_run_id=RUN)
            self.assertEqual("INCOMPLETE_OR_FAILED", result["syntheticMatrixObservation"])
            self.assertEqual("HOLD", result["authorization"])

    def test_reject_forged_success_on_missing_artifacts(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            verdict = assess_matrix(root, expected_sha=SHA, expected_run_id=RUN)
            verdict["syntheticMatrixObservation"] = "BOTH_RECORDED_SUCCESS_UNTRUSTED"
            with self.assertRaises(BoundaryInputError):
                audit_verdict(encoded(verdict), root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_tampered_fingerprint_and_authority(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            original = assess_matrix(root, expected_sha=SHA, expected_run_id=RUN)
            for field, value in (
                ("authorization", "ALLOW"),
                ("externalCIConclusion", "VERIFIED"),
                ("receiptSha256ByVersion", {"3.11": "0" * 64, "3.12": "0" * 64}),
            ):
                with self.subTest(field=field):
                    altered = dict(original)
                    altered[field] = value
                    with self.assertRaises(BoundaryInputError):
                        audit_verdict(encoded(altered), root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_stale_verdict_after_receipt_bytes_change(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            verdict = assess_matrix(root, expected_sha=SHA, expected_run_id=RUN)
            path = root / "pp-recovery-receipt-attempt1-py3.11" / "pp-recovery-ci-receipt.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaises(BoundaryInputError):
                audit_verdict(encoded(verdict), root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_noncanonical_or_duplicate_key_json(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            verdict = assess_matrix(root, expected_sha=SHA, expected_run_id=RUN)
            for raw in (
                encoded(verdict) + b" ",
                b'{"schema":"x","schema":"y"}',
                b"x" * 8193,
            ):
                with self.subTest(size=len(raw)):
                    with self.assertRaises(BoundaryInputError):
                        audit_verdict(raw, root, expected_sha=SHA, expected_run_id=RUN)


if __name__ == "__main__":
    unittest.main()
