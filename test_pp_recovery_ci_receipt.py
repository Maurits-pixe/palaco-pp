"""Synthetic tests of non-authorizing CI execution receipts."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pp_recovery_ci_receipt import (
    STEPS, build_receipt, encode_receipt, write_receipt,
)


def states(**changes):
    return {name: changes.get(name, "success") for name in STEPS}


class RecoveryCiReceiptTests(unittest.TestCase):
    def test_all_steps_success_is_still_not_authorization(self):
        receipt = build_receipt(
            states(), commit_sha="a" * 40, run_id="123",
            run_attempt="2", python_version="3.12"
        )
        self.assertEqual("ALL_RECORDED_STEPS_SUCCESS", receipt["syntheticExecution"])
        self.assertEqual("NOT_INDEPENDENTLY_VERIFIED", receipt["externalCIConclusion"])
        self.assertEqual("HOLD", receipt["authorization"])
        self.assertEqual("DENY", receipt["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", receipt["issuance"])
        self.assertEqual("BLOCKED", receipt["deployment"])
        self.assertEqual("2", receipt["workflowRunAttempt"])

    def test_failure_skipped_cancelled_or_unknown_never_passes(self):
        for outcome in ("failure", "skipped", "cancelled", "unknown"):
            with self.subTest(outcome=outcome):
                receipt = build_receipt(states(regressions=outcome))
                self.assertEqual("INCOMPLETE_OR_FAILED", receipt["syntheticExecution"])
                self.assertEqual("HOLD", receipt["authorization"])

    def test_reject_missing_extra_or_malformed_steps(self):
        for payload in (
            {}, {"syntax": "success"},
            {**states(), "other": "success"},
            states(boundary="PASS"),
            states(policy=True),
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    build_receipt(payload)

    def test_reject_untrusted_metadata(self):
        for metadata in (
            {"commit_sha": "x" * 40},
            {"commit_sha": "a" * 64},
            {"run_id": "../../etc/passwd"},
            {"python_version": "3.13"},
            {"run_attempt": "0"},
            {"run_attempt": "-1"},
        ):
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    build_receipt(states(), **metadata)

    def test_create_only_export_cannot_overwrite(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "receipt.json"
            payload = encode_receipt(build_receipt(states()))
            write_receipt(path, payload)
            self.assertEqual("HOLD", json.loads(path.read_bytes())["authorization"])
            with self.assertRaises(FileExistsError):
                write_receipt(path, b"altered")
            self.assertEqual(payload, path.read_bytes())

    def test_receipt_contains_no_local_environment_values(self):
        receipt = build_receipt(states(syntax="skipped"))
        serialized = encode_receipt(receipt).decode("ascii")
        self.assertNotIn("HOME", serialized)
        self.assertNotIn("GITHUB_TOKEN", serialized)
        self.assertNotIn("privateKey", serialized)


if __name__ == "__main__":
    unittest.main()
