"""Offline-only PP-IDB-001 tests; no external services or credentials."""
import sqlite3
import unittest
from identity_outbox import initialize, enqueue, pending, record_receipt

REF = "opaque-reference-001"
PROVENANCE = "provenance-ref-001"
SOURCE = "source-event-ref-001"

class IdentityOutboxTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def test_replay_is_idempotent_and_no_authorization(self):
        args = dict(source_event_ref=SOURCE, event_type="PP_ACCOUNT_CREATED",
                    local_consumer_ref=REF, provenance_ref=PROVENANCE)
        one = enqueue(self.db, **args)
        self.assertEqual(one, enqueue(self.db, **args))
        self.assertEqual(1, len(pending(self.db)))
        self.assertEqual("CREATED_UNVERIFIED", pending(self.db)[0]["identity_state"])
        self.assertIsNone(pending(self.db)[0]["authorization_ref"])

    def test_conflicting_replay_fails(self):
        enqueue(self.db, source_event_ref=SOURCE, event_type="PP_ACCOUNT_CREATED",
                local_consumer_ref=REF, provenance_ref=PROVENANCE)
        with self.assertRaises(ValueError):
            enqueue(self.db, source_event_ref=SOURCE,
                    event_type="BINDING_REVOKED",
                    local_consumer_ref=REF, provenance_ref=PROVENANCE)

    def test_receipt_is_monotone(self):
        event_id = enqueue(self.db, source_event_ref=SOURCE,
                           event_type="PP_ACCOUNT_CREATED",
                           local_consumer_ref=REF, provenance_ref=PROVENANCE)
        record_receipt(self.db, event_id, "trusted-receipt-0001")
        record_receipt(self.db, event_id, "trusted-receipt-0001")
        self.assertFalse(pending(self.db))
        with self.assertRaises(ValueError):
            record_receipt(self.db, event_id, "trusted-receipt-0002")

    def test_payload_immutable_and_no_delete(self):
        enqueue(self.db, source_event_ref=SOURCE, event_type="PP_ACCOUNT_CREATED",
                local_consumer_ref=REF, provenance_ref=PROVENANCE)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM pp_lineage_outbox")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE pp_lineage_outbox SET event_type='BINDING_REVOKED'")

    def test_invalid_ref_and_event_rejected(self):
        with self.assertRaises(ValueError):
            enqueue(self.db, source_event_ref="raw", event_type="PP_ACCOUNT_CREATED",
                    local_consumer_ref=REF, provenance_ref=PROVENANCE)
        with self.assertRaises(ValueError):
            enqueue(self.db, source_event_ref=SOURCE, event_type="AUTHORIZED",
                    local_consumer_ref=REF, provenance_ref=PROVENANCE)

if __name__ == "__main__":
    unittest.main()
