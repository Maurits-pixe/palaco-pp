"""Synthetic offline tests for evidence manifest v1 (no account/database access)."""
import json
import unittest

from review_044_evidence_manifest import (
    build_evidence_manifest, validate_evidence_manifest,
)
from review_044_release_boundary_snapshot import BoundaryInputError
from test_review_044_boundary_reconciliation import snapshot
from test_review_044_release_boundary_snapshot import valid_report, encode


class EvidenceManifestTests(unittest.TestCase):
    def test_manifest_chain_valid_but_untrusted(self):
        first = snapshot()
        report = valid_report()
        report["synthetic"] = "CHANGED"
        second = snapshot(report)
        manifest = build_evidence_manifest(((first, second), (first, first)))
        result = validate_evidence_manifest(encode(manifest))
        self.assertEqual(2, result["entryCount"])
        self.assertEqual("STRUCTURALLY_CONSISTENT_UNTRUSTED", result["hashChain"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("BLOCKED", result["deployment"])

    def test_reject_duplicate_reordered_pair(self):
        a = snapshot()
        report = valid_report()
        report["synthetic"] = "NEW"
        b = snapshot(report)
        with self.assertRaises(BoundaryInputError):
            build_evidence_manifest(((a, b), (b, a)))

    def test_reject_privilege_escalation(self):
        manifest = build_evidence_manifest(((snapshot(), snapshot()),))
        manifest["authorization"] = "ALLOW"
        with self.assertRaises(BoundaryInputError):
            validate_evidence_manifest(encode(manifest))

    def test_reject_tampered_record(self):
        manifest = build_evidence_manifest(((snapshot(), snapshot()),))
        manifest["entries"][0]["blockedGateCountMatch"] = False
        with self.assertRaises(BoundaryInputError):
            validate_evidence_manifest(encode(manifest))

    def test_reject_malformed_and_limits(self):
        s = snapshot()
        for data in ((), ((s,),), (("not bytes", s),), ((s, s),) * 33):
            with self.subTest(length=len(data)):
                with self.assertRaises(BoundaryInputError):
                    build_evidence_manifest(data)
        with self.assertRaises(BoundaryInputError):
            validate_evidence_manifest(b'{"x":1,"x":2}')

    def test_no_private_identifiers_leak(self):
        report = valid_report()
        report["consumerId"] = "SYNTHETIC_SECRET_OWNER"
        report["ppNumber"] = "1234567890"
        evidence = build_evidence_manifest(((snapshot(report), snapshot(report)),))
        payload = json.dumps(evidence)
        self.assertNotIn("SYNTHETIC_SECRET_OWNER", payload)
        self.assertNotIn("1234567890", payload)


if __name__ == "__main__":
    unittest.main()
