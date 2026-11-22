"""Synthetic regression cases for the fail-closed PP recovery boundary.

Run manually: python -m unittest -v test_review_044_release_boundary_snapshot
These tests do not read or change production accounts or the P.P. database.
"""
import json
import unittest

from review_044_release_boundary_snapshot import (
    BoundaryInputError, EXPECTED_GLOBAL_BLOCKERS, review_boundary_snapshot,
)


def valid_report():
    return {
        "schema": "palaco.pp.recovery-002-release-readiness.v0",
        "reference": "PP-RECOVERY-002",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "overallReadiness": "NOT_READY",
        "manualDecision": "REQUIRED_OUTSIDE_THIS_MODULE",
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "subjectBinding": "NOT_ESTABLISHED",
        "reviewerAuthority": "NOT_ESTABLISHED",
        "globalBlockers": list(EXPECTED_GLOBAL_BLOCKERS),
        "palacoOneHandoff": "BLOCKED",
        "palacoOneSession": "NOT_CREATED",
        "independentVerification": "NOT_VERIFIED",
        "humanReview": "NOT_COMPLETED",
        "blockedGateCount": 2,
        "gateReadiness": [
            {"gate": "BLOCKED", "readiness": "NOT_READY"},
            {"gate": "BLOCKED", "readiness": "NOT_READY"},
        ],
    }


def encode(data):
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


class RecoveryBoundaryTests(unittest.TestCase):
    def test_valid_report_still_denies(self):
        result = review_boundary_snapshot(encode(valid_report()))
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", result["issuance"])
        self.assertEqual("BLOCKED", result["deployment"])
        self.assertEqual("BLOCKED", result["palacoOneHandoff"])
        self.assertEqual(2, result["blockedGateCount"])

    def test_privacy_no_identifiers_copied(self):
        report = valid_report()
        report["consumerId"] = "SYNTHETIC_SECRET_CONSUMER"
        report["ppNumber"] = "1234567890"
        result = review_boundary_snapshot(encode(report))
        serialized = json.dumps(result)
        self.assertNotIn("SYNTHETIC_SECRET_CONSUMER", serialized)
        self.assertNotIn("1234567890", serialized)

    def test_reject_privilege_escalation(self):
        for key, value in [
            ("authorization", "ALLOW"),
            ("accessDecision", "ALLOW"),
            ("issuance", "AUTHORIZED"),
            ("overallReadiness", "READY"),
            ("palacoOneHandoff", "APPROVED"),
            ("palacoOneSession", "CREATED"),
            ("independentVerification", "VERIFIED"),
            ("humanReview", "COMPLETED"),
            ("blockedGateCount", True),
            ("blockedGateCount", 0),
        ]:
            with self.subTest(key=key, value=value):
                report = valid_report()
                report[key] = value
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(encode(report))

    def test_reject_false_authenticity_and_reviewer_claims(self):
        for key, value in (
            ("sourceAuthenticity", "VERIFIED"),
            ("subjectBinding", "ESTABLISHED"),
            ("reviewerAuthority", "ESTABLISHED"),
            ("manualDecision", "APPROVED"),
        ):
            with self.subTest(key=key):
                report = valid_report()
                report[key] = value
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(encode(report))

    def test_reject_missing_trust_prerequisites(self):
        for key in (
            "sourceAuthenticity", "subjectBinding", "reviewerAuthority",
            "manualDecision", "globalBlockers",
        ):
            with self.subTest(key=key):
                report = valid_report()
                del report[key]
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(encode(report))

    def test_reject_empty_duplicate_or_fake_global_blockers(self):
        for blockers in (
            [], ["DUPLICATE", "DUPLICATE"], [True], "NOT_A_LIST",
        ):
            with self.subTest(blockers=blockers):
                report = valid_report()
                report["globalBlockers"] = blockers
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(encode(report))

    def test_reject_incomplete_or_forged_blocker_list(self):
        for blockers in (
            list(EXPECTED_GLOBAL_BLOCKERS[:-1]),
            list(EXPECTED_GLOBAL_BLOCKERS[1:]),
            list(EXPECTED_GLOBAL_BLOCKERS) + ["EXTRA_FAKE_BLOCKER"],
            list(reversed(EXPECTED_GLOBAL_BLOCKERS)),
            ["FAKE_BLOCKER"] * len(EXPECTED_GLOBAL_BLOCKERS),
        ):
            with self.subTest(blockers=blockers):
                report = valid_report()
                report["globalBlockers"] = blockers
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(encode(report))

    def test_reject_unblocked_gate(self):
        report = valid_report()
        report["gateReadiness"][0]["gate"] = "PASSED"
        with self.assertRaises(BoundaryInputError):
            review_boundary_snapshot(encode(report))

    def test_reject_duplicate_json_keys(self):
        data = b'{"schema":"x","schema":"y"}'
        with self.assertRaises(BoundaryInputError):
            review_boundary_snapshot(data)

    def test_reject_malformed_oversized_and_invalid_types(self):
        for data in [b"", b"not json", b"[]", b"\xff", b"x" * 65537, "text", None]:
            with self.subTest(data_type=type(data).__name__):
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(data)


if __name__ == "__main__":
    unittest.main()
