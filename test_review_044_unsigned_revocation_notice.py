"""Synthetic regression tests for untrusted revocation-notice inspection."""
import json
import unittest

from review_044_release_boundary_snapshot import BoundaryInputError
from review_044_unsigned_revocation_notice import (
    SCHEMA, inspect_unsigned_revocation_notice,
)
from test_review_044_trust_anchor_preflight import encode, proposal


def notice():
    candidate = proposal()
    return {
        "schema": SCHEMA,
        "reference": "PP-RECOVERY-002",
        "issuerId": candidate["issuerId"],
        "keyId": candidate["keyId"],
        "publicKeySha256": candidate["publicKeySha256"],
        "claim": "REVOKED",
        "evidenceState": "UNSIGNED_UNVERIFIED",
    }


class UnsignedRevocationNoticeTests(unittest.TestCase):
    def test_matching_notice_still_denies(self):
        result = inspect_unsigned_revocation_notice(encode(proposal()), encode(notice()))
        self.assertEqual("REVOKED_UNTRUSTED", result["claim"])
        self.assertEqual("NOT_VERIFIED", result["trustedRevocation"])
        self.assertEqual("NOT_ESTABLISHED", result["nonRevocation"])
        self.assertFalse(result["registryModified"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", result["issuance"])

    def test_reject_wrong_issuer_key_or_digest(self):
        for key, value in (
            ("issuerId", "another.example"),
            ("keyId", "other-key-0001"),
            ("publicKeySha256", "b" * 64),
        ):
            with self.subTest(key=key):
                altered = notice()
                altered[key] = value
                with self.assertRaises(BoundaryInputError):
                    inspect_unsigned_revocation_notice(
                        encode(proposal()), encode(altered)
                    )

    def test_reject_claim_of_safe_key_or_signed_status(self):
        for key, value in (
            ("claim", "ACTIVE"),
            ("claim", "NOT_REVOKED"),
            ("evidenceState", "SIGNED_TRUSTED"),
        ):
            with self.subTest(key=key, value=value):
                altered = notice()
                altered[key] = value
                with self.assertRaises(BoundaryInputError):
                    inspect_unsigned_revocation_notice(encode(proposal()), encode(altered))

    def test_reject_extra_fields_and_duplicate_keys(self):
        altered = notice()
        altered["privateKey"] = "synthetic-secret"
        with self.assertRaises(BoundaryInputError):
            inspect_unsigned_revocation_notice(encode(proposal()), encode(altered))
        with self.assertRaises(BoundaryInputError):
            inspect_unsigned_revocation_notice(
                encode(proposal()), b'{"schema":"a","schema":"b"}'
            )

    def test_reject_oversize_and_bad_types(self):
        for raw in (None, "text", b"", b"x" * 8193, b"[]"):
            with self.subTest(raw_type=type(raw).__name__):
                with self.assertRaises(BoundaryInputError):
                    inspect_unsigned_revocation_notice(encode(proposal()), raw)

    def test_no_identifier_or_secret_echo(self):
        result = inspect_unsigned_revocation_notice(encode(proposal()), encode(notice()))
        serialized = json.dumps(result)
        self.assertNotIn("synthetic.example", serialized)
        self.assertNotIn("synthetic-key-001", serialized)
        self.assertNotIn("a" * 64, serialized)


if __name__ == "__main__":
    unittest.main()
