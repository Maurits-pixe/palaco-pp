"""PP-IDB-001 atomic account-registration integration tests (offline only)."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from server import Store, PPError
from identity_outbox import pending


class AtomicIdentityRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "palaco.sqlite3"
        self.store = Store(self.path)
        self.consumer, self.token = self.store.create_consumer()

    def tearDown(self):
        self.tmp.cleanup()

    def _register(self):
        return self.store.register_account(
            self.consumer, "testarchitect", "correct horse battery staple", self.token
        )

    def _snapshot(self):
        with self.store.connection() as db:
            return {
                "accounts": db.execute("SELECT count(*) FROM accounts").fetchone()[0],
                "events": db.execute(
                    "SELECT count(*) FROM audit WHERE event='ACCOUNT_CREATED'"
                ).fetchone()[0],
                "outbox": db.execute(
                    "SELECT count(*) FROM pp_lineage_outbox"
                ).fetchone()[0],
                "sessions": db.execute(
                    "SELECT count(*) FROM auth_sessions WHERE consumer_id=?",
                    (self.consumer,),
                ).fetchone()[0],
            }

    def test_creation_is_atomic_and_unauthorized(self):
        self._register()
        state = self._snapshot()
        self.assertEqual((state["accounts"], state["events"], state["outbox"]), (1, 1, 1))
        with self.store.connection() as db:
            envelope = pending(db)[0]
            self.assertEqual(envelope["event_type"], "PP_ACCOUNT_CREATED")
            self.assertEqual(envelope["identity_state"], "CREATED_UNVERIFIED")
            self.assertIsNone(envelope["authorization_ref"])
            self.assertNotEqual(envelope["local_consumer_ref"], self.consumer)
            self.assertNotIn(self.consumer, json.dumps(envelope))
            self.assertNotIn("testarchitect", json.dumps(envelope))

    def test_outbox_failure_rolls_back_account_and_audit_and_session_rotation(self):
        original = self._snapshot()
        with patch("server.enqueue_identity_event", side_effect=sqlite3.OperationalError("outbox unavailable")):
            with self.assertRaises(sqlite3.OperationalError):
                self._register()
        self.assertEqual(self._snapshot(), original)

    def test_duplicate_registration_never_creates_second_event(self):
        self._register()
        with self.assertRaises(PPError) as error:
            self._register()
        self.assertEqual(error.exception.code, "PP_ACCOUNT_EXISTS")
        self.assertEqual(self._snapshot()["outbox"], 1)

    def test_event_survives_reopen_without_network(self):
        self._register()
        reopened = Store(self.path)
        with reopened.connection() as db:
            self.assertEqual(len(pending(db)), 1)
            self.assertEqual(
                db.execute(
                    "SELECT count(*) FROM audit WHERE event='ACCOUNT_CREATED'"
                ).fetchone()[0], 1
            )

    def test_failure_on_event_insertion_rolls_back(self):
        original = self._snapshot()
        with self.store.connection() as db:
            db.execute(
                """CREATE TRIGGER reject_new_lineage BEFORE INSERT ON pp_lineage_outbox
                BEGIN SELECT RAISE(ABORT, 'INJECTED_STORAGE_FAILURE'); END;"""
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self._register()
        self.assertEqual(self._snapshot(), original)


if __name__ == "__main__":
    unittest.main()
