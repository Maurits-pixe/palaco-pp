"""Synthetic regression cases for the fail-closed PP recovery boundary.

Run manually: python -m unittest -v test_review_044_release_boundary_snapshot
These tests do not read or change production accounts or the P.P. database.
"""
import json
import unittest

from review_044_release_boundary_snapshot import (
    BoundaryInputError, EXPECTED_GLOBAL_BLOCKERS, EXPECTED_GATES,\n    EXPECTED_CHECK_IDS, review_boundary_snapshot,
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
        "blockedGateCount": len(EXPECTED_GATES),
        "gateReadiness": [
            {
                "requirementId": name,
                "description": description,
                "missingChecks": [
                    {
                        "checkOrder": order,
                        "checkId": EXPECTED_CHECK_IDS[order - 1],
                        "status": "NOT_STARTED",
                        "verification": "NOT_VERIFIED",
                    }
                    for order in orders
                ],
                "missingCount": len(orders),
                "nextManualAction": next_action,
                "gate": "BLOCKED",
                "readiness": "NOT_READY",
            }
            for name, description, orders, next_action in EXPECTED_GATES
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
        self.assertEqual(len(EXPECTED_GATES), result["blockedGateCount"])

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

    def test_reject_missing_reordered_or_duplicated_gate(self):
        for mutation in ("missing", "reordered", "duplicate", "count"):
            with self.subTest(mutation=mutation):
                report = valid_report()
                gates = report["gateReadiness"]
                if mutation == "missing":
                    report["gateReadiness"] = gates[:-1]
                    report["blockedGateCount"] -= 1
                elif mutation == "reordered":
                    gates[0], gates[1] = gates[1], gates[0]
                elif mutation == "duplicate":
                    gates[1] = dict(gates[0])
                else:
                    report["blockedGateCount"] = 2
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(encode(report))

    def test_reject_forged_gate_check_or_status(self):
        for field, value in (
            ("checkOrder", 2),
            ("checkId", "FAKE_CHECK"),
            ("status", "COMPLETED"),
            ("verification", "VERIFIED"),
        ):
            with self.subTest(field=field):
                report = valid_report()
                report["gateReadiness"][0]["missingChecks"][0][field] = value
                with self.assertRaises(BoundaryInputError):
                    review_boundary_snapshot(encode(report))

    def test_reject_missing_gate_metadata_and_wrong_counts(self):
        for mode in ("missingCount", "description", "action", "unknownField"):
            with self.subTest(mode=mode):
                report = valid_report()
                gate = report["gateReadiness"][0]
                if mode == "missingCount":
                    gate["missingCount"] = True
                elif mode == "description":
                    gate["description"] = "synthetic-fake"
                elif mode == "action":
                    gate["nextManualAction"] = "AUTO_APPROVE"
                else:
                    gate["extra"] = "APPROVED"
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
