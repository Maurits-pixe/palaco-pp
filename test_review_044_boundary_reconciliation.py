"""Synthetic tests for offline PP boundary reconciliation."""
import json
import unittest

from review_044_boundary_reconciliation import reconcile_boundary_snapshots
from review_044_release_boundary_snapshot import (
    BoundaryInputError, review_boundary_snapshot,
)
from test_review_044_release_boundary_snapshot import encode, valid_report


def snapshot(report=None):
    report = valid_report() if report is None else report
    return encode(review_boundary_snapshot(encode(report)))


class ReconciliationTests(unittest.TestCase):
    def test_identical_untrusted_snapshots_remain_denied(self):
        data = snapshot()
        result = reconcile_boundary_snapshots(data, data)
        self.assertEqual("MATCH_UNTRUSTED", result["comparison"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", result["issuance"])
        self.assertEqual("NOT_VERIFIED", result["independentVerification"])

    def test_distinct_input_digests_report_mismatch(self):
        report = valid_report()
        report["syntheticExtra"] = "DIFFERENT"
        result = reconcile_boundary_snapshots(snapshot(), snapshot(report))
        self.assertEqual("MISMATCH", result["comparison"])
        self.assertFalse(result["sourceDigestMatch"])
        self.assertEqual("BLOCKED", result["deployment"])

    def test_different_gate_counts_report_mismatch(self):
        one = snapshot()
        two = json.loads(one)
        two["blockedGateCount"] = 3
        result = reconcile_boundary_snapshots(one, encode(two))
        self.assertEqual("MISMATCH", result["comparison"])
        self.assertFalse(result["blockedGateCountMatch"])

    def test_reject_privilege_escalation_or_added_claims(self):
        for key, value in [
            ("authorization", "ALLOW"),
            ("deployment", "READY"),
            ("inputValidation", "SOURCE_AUTHENTICATED"),
            ("newAuthority", "OWNER"),
            ("blockedGateCount", True),
            ("inputSha256", "z" * 64),
        ]:
            with self.subTest(key=key):
                bad = json.loads(snapshot())
                bad[key] = value
                with self.assertRaises(BoundaryInputError):
                    reconcile_boundary_snapshots(snapshot(), encode(bad))

    def test_reject_duplicate_keys_and_oversized_input(self):
        for bad in (b'{"schema":"x","schema":"y"}', b"x" * 65537, b"[]", b""):
            with self.subTest(size=len(bad)):
                with self.assertRaises(BoundaryInputError):
                    reconcile_boundary_snapshots(snapshot(), bad)

    def test_no_user_identifiers_in_comparison(self):
        report = valid_report()
        report["consumerId"] = "SYNTHETIC_SECRET"
        report["ppNumber"] = "1234567890"
        result = reconcile_boundary_snapshots(snapshot(report), snapshot(report))
        data = json.dumps(result)
        self.assertNotIn("SYNTHETIC_SECRET", data)
        self.assertNotIn("1234567890", data)


if __name__ == "__main__":
    unittest.main()
