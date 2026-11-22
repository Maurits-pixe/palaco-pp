"""Synthetic negative cases for unsigned Python-matrix receipt comparison."""
import copy
import unittest

from pp_recovery_ci_receipt import STEPS, build_receipt, encode_receipt
from pp_recovery_ci_receipt_pair import inspect_receipt_pair
from review_044_release_boundary_snapshot import BoundaryInputError


def receipt(version, *, run="1922", commit="a" * 40, outcome="success"):
    return encode_receipt(build_receipt(
        {name: outcome for name in STEPS},
        commit_sha=commit, run_id=run, python_version=version,
    ))


class RecoveryCiReceiptPairTests(unittest.TestCase):
    def test_matching_matrix_never_authorizes(self):
        result = inspect_receipt_pair(receipt("3.11"), receipt("3.12"))
        self.assertEqual("BOTH_RECORDED_SUCCESS_UNTRUSTED", result["syntheticExecution"])
        self.assertEqual("NOT_INDEPENDENTLY_VERIFIED", result["externalCIConclusion"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", result["issuance"])
        self.assertEqual("BLOCKED", result["deployment"])

    def test_failure_and_skipped_remain_incomplete(self):
        for outcome in ("failure", "skipped", "cancelled", "unknown"):
            with self.subTest(outcome=outcome):
                result = inspect_receipt_pair(
                    receipt("3.11"), receipt("3.12", outcome=outcome)
                )
                self.assertEqual("INCOMPLETE_OR_FAILED", result["syntheticExecution"])

    def test_reject_duplicate_python_version(self):
        with self.assertRaises(BoundaryInputError):
            inspect_receipt_pair(receipt("3.11"), receipt("3.11"))

    def test_reject_mismatched_run_or_commit(self):
        for altered in (
            receipt("3.12", run="1923"),
            receipt("3.12", commit="b" * 40),
        ):
            with self.subTest(altered=altered[:30]):
                with self.assertRaises(BoundaryInputError):
                    inspect_receipt_pair(receipt("3.11"), altered)

    def test_reject_missing_immutable_metadata(self):
        with self.assertRaises(BoundaryInputError):
            inspect_receipt_pair(
                encode_receipt(build_receipt(
                    {name: "success" for name in STEPS},
                    python_version="3.11",
                )), receipt("3.12"),
            )

    def test_reject_forged_authorization_even_with_success(self):
        import json
        altered = json.loads(receipt("3.12"))
        for field, value in (
            ("authorization", "ALLOW"),
            ("syntheticExecution", "ALL_RECORDED_STEPS_SUCCESS_TRUSTED"),
            ("externalCIConclusion", "VERIFIED"),
        ):
            with self.subTest(field=field):
                forged = dict(altered)
                forged[field] = value
                with self.assertRaises(BoundaryInputError):
                    inspect_receipt_pair(
                        receipt("3.11"), encode_receipt(forged)
                    )

    def test_reject_duplicate_json_keys_and_oversized_receipt(self):
        for altered in (b'{"schema":"a","schema":"b"}', b"x" * 8193, b"[]"):
            with self.subTest(length=len(altered)):
                with self.assertRaises(BoundaryInputError):
                    inspect_receipt_pair(receipt("3.11"), altered)

    def test_order_independent_results(self):
        a = inspect_receipt_pair(receipt("3.11"), receipt("3.12"))
        b = inspect_receipt_pair(receipt("3.12"), receipt("3.11"))
        self.assertEqual(a["syntheticExecution"], b["syntheticExecution"])
        self.assertEqual(a["receiptSha256ByVersion"], b["receiptSha256ByVersion"])


if __name__ == "__main__":
    unittest.main()
