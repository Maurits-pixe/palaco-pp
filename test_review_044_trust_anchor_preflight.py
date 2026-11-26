"""Synthetic regression tests for non-authorizing trust-anchor preflight."""
import json
import unittest

from review_044_release_boundary_snapshot import BoundaryInputError
from review_044_trust_anchor_preflight import (
    inspect_trust_anchor_proposal, PURPOSE, SCHEMA,
)


def proposal():
    return {
        "schema": SCHEMA,
        "reference": "PP-RECOVERY-002",
        "issuerId": "synthetic.example",
        "keyId": "synthetic-key-001",
        "publicKeySha256": "a" * 64,
        "algorithm": "Ed25519",
        "purpose": PURPOSE,
        "proposedState": "PENDING_INDEPENDENT_REVIEW",
    }


def encode(obj):
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")


class TrustAnchorPreflightTests(unittest.TestCase):
    def test_valid_proposal_remains_untrusted_and_blocked(self):
        result = inspect_trust_anchor_proposal(encode(proposal()))
        self.assertEqual("VALID_UNTRUSTED_PROPOSAL", result["structuralInspection"])
        self.assertEqual(0, result["trustedIssuerCount"])
        self.assertEqual(0, result["allowedSigningKeys"])
        self.assertFalse(result["trustAnchorImported"])
        self.assertFalse(result["registryModified"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])

    def test_reject_trust_promotion(self):
        for field, value in (
            ("proposedState", "APPROVED"),
            ("algorithm", "none"),
            ("purpose", "LOGIN"),
            ("reference", "OTHER"),
            ("publicKeySha256", "z" * 64),
            ("issuerId", "bad issuer"),
            ("keyId", "x"),
        ):
            with self.subTest(field=field):
                bad = proposal()
                bad[field] = value
                with self.assertRaises(BoundaryInputError):
                    inspect_trust_anchor_proposal(encode(bad))

    def test_reject_added_public_key_material(self):
        bad = proposal()
        bad["privateKey"] = "secret-do-not-use"
        with self.assertRaises(BoundaryInputError):
            inspect_trust_anchor_proposal(encode(bad))

    def test_reject_duplicate_json_and_oversized(self):
        for raw in (b'{"a":1,"a":2}', b"x" * 16385, b"", b"[]", b"not json"):
            with self.subTest(size=len(raw)):
                with self.assertRaises(BoundaryInputError):
                    inspect_trust_anchor_proposal(raw)

    def test_no_proposal_identifiers_in_output(self):
        result = inspect_trust_anchor_proposal(encode(proposal()))
        serialized = json.dumps(result)
        self.assertNotIn("synthetic.example", serialized)
        self.assertNotIn("synthetic-key-001", serialized)
        self.assertNotIn("a" * 64, serialized)


if __name__ == "__main__":
    unittest.main()
