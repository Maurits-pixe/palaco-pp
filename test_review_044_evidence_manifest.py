"""Synthetic offline tests for evidence manifest v1 (no account/database access)."""
import json
import unittest

from review_044_evidence_manifest import (
    build_evidence_manifest, validate_evidence_manifest,
)
from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json
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

    def test_reject_semantic_duplicate_with_different_json_encoding(self):
        # Same snapshot object, but different whitespace and property order.
        original = snapshot()
        changed_encoding = json.dumps(
            json.loads(original), sort_keys=True, indent=2
        ).encode("utf-8")
        self.assertNotEqual(original, changed_encoding)
        with self.assertRaisesRegex(BoundaryInputError, "PP_MANIFEST_DUPLICATE"):
            build_evidence_manifest((
                (original, original),
                (changed_encoding, changed_encoding),
            ))

    def test_reject_semantic_duplicate_reversed_with_reformatting(self):
        first = snapshot()
        report = valid_report()
        report["synthetic"] = "different-source"
        second = snapshot(report)
        reformatted_first = json.dumps(
            json.loads(first), sort_keys=True, indent=2
        ).encode("utf-8")
        reformatted_second = json.dumps(
            json.loads(second), sort_keys=True, indent=2
        ).encode("utf-8")
        with self.assertRaisesRegex(BoundaryInputError, "PP_MANIFEST_DUPLICATE"):
            build_evidence_manifest((
                (first, second),
                (reformatted_second, reformatted_first),
            ))

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

    def test_manifest_parser_accepts_bounded_large_json(self):
        # Exercise the parser boundary separately: the strict manifest
        # schema may still reject this oversized JSON object later.
        large = json.dumps({"padding": "x" * (70 * 1024)}).encode("utf-8")
        self.assertGreater(len(large), 64 * 1024)
        self.assertEqual(70 * 1024, len(_parse_json(
            large, max_bytes=512 * 1024
        )["padding"]))
        with self.assertRaises(BoundaryInputError):
            _parse_json(large)

    def test_manifest_parser_rejects_oversize_and_duplicates(self):
        with self.assertRaises(BoundaryInputError):
            _parse_json(b"x" * (512 * 1024 + 1), max_bytes=512 * 1024)
        with self.assertRaises(BoundaryInputError):
            _parse_json(b'{"a":1,"a":2}', max_bytes=512 * 1024)
        with self.assertRaises(BoundaryInputError):
            _parse_json(b"{}", max_bytes=True)
        with self.assertRaises(BoundaryInputError):
            _parse_json(b"{}", max_bytes=512 * 1024 + 1)

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
