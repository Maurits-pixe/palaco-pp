from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import http.client
import hashlib
import json
from pathlib import Path
import sqlite3
import smtplib
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from server import (PPError, Server, Store, main, smtp_configuration,
                    process_confirmation, deliver_confirmation, confirmation_worker)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / "test.sqlite3")
        self.consumer, self.token = self.store.create_consumer()

    def assert_code(self, expected, function, *args):
        with self.assertRaises(PPError) as caught:
            function(*args)
        self.assertEqual(expected, caught.exception.code)

    def test_confirmation_is_atomic_unique_and_persistent(self):
        batch = self.store.options(self.consumer)
        option = batch["options"][0]["id"]
        original = self.store.audit

        def fail_queue_audit(db, consumer, event, detail=None):
            if event == "CONFIRMATION_MAIL_QUEUED":
                raise sqlite3.OperationalError("audit unavailable")
            original(db, consumer, event, detail)

        with patch.object(self.store, "audit", side_effect=fail_queue_audit):
            with self.assertRaises(sqlite3.OperationalError):
                self.store.select(self.consumer, option, email="synthetic@example.test")
        self.assertEqual("OFFERED", self.store.me(self.consumer)["status"])
        self.assertEqual("NOT_REQUESTED", self.store.mail_status(self.consumer)["status"])
        self.store.select(self.consumer, option, email="synthetic@example.test")
        restarted = Store(Path(self.store.path))
        self.assertEqual("QUEUED", restarted.mail_status(self.consumer)["status"])
        with self.assertRaises(PPError):
            restarted.select(self.consumer, option, email="other@example.test")
        with self.store.connection() as db:
            self.assertEqual(1, db.execute("SELECT count(*) FROM confirmation_mail").fetchone()[0])
            self.assertNotIn("synthetic@example.test", str([
                dict(row) for row in db.execute("SELECT * FROM audit")
            ]))

    def test_confirmation_validates_email_without_making_selection(self):
        option = self.store.options(self.consumer)["options"][0]["id"]
        for email in (None, 7, "bad", "a@b", "a\n@example.test", "a..b@example.test",
                      ".a@example.test", "a.@example.test", "é@example.test",
                      "a@" + "x" * 64 + ".test", "a" * 65 + "@example.test"):
            with self.subTest(email=email), self.assertRaises(PPError) as caught:
                self.store.select(self.consumer, option, email=email)
            self.assertEqual("PP_EMAIL_INVALID", caught.exception.code)
        self.store.select(self.consumer, option)
        self.assertEqual("NOT_REQUESTED", self.store.mail_status(self.consumer)["status"])

    def test_confirmation_worker_sends_once_and_preserves_selection_on_failure(self):
        self.store.select(self.consumer, self.store.options(self.consumer)["options"][0]["id"],
                          email="synthetic@example.test")
        with patch("server.deliver_confirmation") as send:
            self.assertTrue(process_confirmation(self.store, {}))
            self.assertFalse(process_confirmation(self.store, {}))
            send.assert_called_once()
        self.assertEqual("SENT", self.store.mail_status(self.consumer)["status"])
        self.assertEqual("ACTIVE", self.store.me(self.consumer)["status"])

    def test_confirmation_failure_retry_limit_and_unknown_block(self):
        option = self.store.options(self.consumer)["options"][0]["id"]
        self.store.select(self.consumer, option, email="synthetic@example.test")
        for attempt in range(3):
            with self.store.transaction() as db:
                db.execute("UPDATE confirmation_mail SET next_attempt_at='2000-01-01'")
            with patch("server.deliver_confirmation", side_effect=smtplib.SMTPAuthenticationError(
                535, b"synthetic failure"
            )):
                process_confirmation(self.store, {})
            self.assertEqual("FAILED" if attempt == 2 else "QUEUED",
                             self.store.mail_status(self.consumer)["status"])
        self.assertEqual(3, self.store.mail_status(self.consumer)["attempts"])
        self.assertEqual("ACTIVE", self.store.me(self.consumer)["status"])
        with self.store.transaction() as db:
            db.execute("UPDATE confirmation_mail SET status='QUEUED',next_attempt_at='2000-01-01'")
        with patch("server.deliver_confirmation", side_effect=smtplib.SMTPServerDisconnected()):
            process_confirmation(self.store, {})
        self.assertEqual("UNKNOWN", self.store.mail_status(self.consumer)["status"])
        with patch("server.deliver_confirmation") as send:
            self.assertFalse(process_confirmation(self.store, {}))
            send.assert_not_called()

    def test_confirmation_recovers_interrupted_send_without_duplicate(self):
        self.store.select(self.consumer, self.store.options(self.consumer)["options"][0]["id"],
                          email="synthetic@example.test")
        with self.store.transaction() as db:
            db.execute("UPDATE confirmation_mail SET status='SENDING'")
        stop = threading.Event()
        stop.set()
        with patch("server.deliver_confirmation") as send:
            confirmation_worker(self.store, {}, stop)
            send.assert_not_called()
        self.assertEqual("UNKNOWN", self.store.mail_status(self.consumer)["status"])

    def test_concurrent_confirmation_workers_claim_only_once(self):
        self.store.select(self.consumer, self.store.options(self.consumer)["options"][0]["id"],
                          email="synthetic@example.test")
        with patch("server.deliver_confirmation") as send:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: process_confirmation(self.store, {}), range(2)))
            self.assertEqual([False, True], sorted(results))
            send.assert_called_once()

    def test_smtp_configuration_tls_and_confirmation_message(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(smtp_configuration())
        env = {"PP_SMTP_HOST": "smtp.example.test", "PP_SMTP_FROM": "palaco@example.test",
               "PP_SMTP_USER": "synthetic", "PP_SMTP_PASSWORD": "synthetic-test-only"}
        with patch.dict(os.environ, env, clear=True):
            config = smtp_configuration()
            self.assertEqual(587, config["port"])
            with patch("server.smtplib.SMTP") as smtp, patch("server.ssl.create_default_context"):
                client = smtp.return_value.__enter__.return_value
                client.send_message.return_value = {}
                deliver_confirmation(config, {
                    "consumer_id": self.consumer, "recipient": "synthetic@example.test",
                    "number": "1234567890", "created_at": "2026-10-26",
                })
                client.starttls.assert_called_once()
                client.login.assert_called_once_with("synthetic", "synthetic-test-only")
                message = client.send_message.call_args.args[0]
                self.assertEqual("synthetic@example.test", message["To"])
                self.assertIn("1234567890", message.get_content())
                self.assertIn("geen telefoonlijn", message.get_content())
                client.send_message.return_value = {"synthetic@example.test": (550, b"rejected")}
                with self.assertRaises(smtplib.SMTPRecipientsRefused):
                    deliver_confirmation(config, {
                        "consumer_id": self.consumer, "recipient": "synthetic@example.test",
                        "number": "1234567890", "created_at": "2026-10-26",
                    })
        for values in ({"PP_SMTP_HOST": "smtp.example.test"},
                       {**env, "PP_SMTP_TLS": "none"},
                       {**env, "PP_SMTP_PORT": "not-a-port"},
                       {**env, "PP_SMTP_PASSWORD": ""}):
            with patch.dict(os.environ, values, clear=True):
                with self.assertRaises((ValueError, PPError)):
                    smtp_configuration()

    def test_ten_unique_ten_digit_options_and_repeat_is_stable(self):
        batch = self.store.options(self.consumer)
        self.assertEqual(10, len(batch["options"]))
        self.assertEqual(10, len({o["number"] for o in batch["options"]}))
        self.assertEqual({"blue", "red", "green", "yellow"}, {o["color"] for o in batch["options"]})
        for option in batch["options"]:
            self.assertRegex(option["number"], r"^[1-9][0-9]{9}$")
            self.assertEqual("OFFERED", option["status"])
        self.assertEqual(batch, self.store.options(self.consumer))
        self.assertEqual("OFFERED", self.store.me(self.consumer)["status"])

    def test_admin_identity_is_separate_rotated_expiring_and_hashed(self):
        password = "Admin unique password 2026!"
        self.assertEqual("local.admin", self.store.create_admin("Local.Admin", password))
        self.assert_code("PP_USERNAME_TAKEN", self.store.create_admin, "local.admin", password)
        _, username, token = self.store.login_account("local.admin", password, None, admin=True)
        self.assertEqual(username, self.store.admin_me(token)["username"])
        self.assertIsNone(self.store.identify(token))
        with self.assertRaises(PPError):
            self.store.admin_me(self.token)
        _, _, rotated = self.store.login_account("local.admin", password, token, admin=True)
        self.assert_code("PP_ADMIN_REQUIRED", self.store.admin_me, token)
        restarted = Store(Path(self.store.path))
        self.assertEqual(username, restarted.admin_me(rotated)["username"])
        with self.store.transaction() as db:
            row = db.execute("SELECT * FROM administrators").fetchone()
            self.assertNotEqual(password.encode(), row["password_hash"])
            self.assertNotEqual(password.encode(), row["password_salt"])
            self.assertNotIn(rotated, str([dict(r) for r in db.execute("SELECT * FROM admin_sessions")]))
            db.execute("UPDATE admin_sessions SET expires_at='2000-01-01'")
        self.assert_code("PP_ADMIN_REQUIRED", restarted.admin_me, rotated)

    def test_admin_cli_requires_matching_hidden_password_and_never_overwrites(self):
        password = "CLI admin unique password 2026!"
        args = ["server.py", "--db", self.store.path, "--create-admin"]
        with patch("sys.argv", args), patch("builtins.input", return_value="cli.admin"), \
                patch("server.getpass.getpass", side_effect=[password, "different"]), \
                patch("builtins.print"):
            self.assertEqual(1, main())
        with self.store.connection() as db:
            self.assertEqual(0, db.execute("SELECT count(*) FROM administrators").fetchone()[0])
        with patch("sys.argv", args), patch("builtins.input", return_value="cli.admin"), \
                patch("server.getpass.getpass", side_effect=[password, password]), \
                patch("builtins.print"):
            self.assertEqual(0, main())
        with patch("sys.argv", args), patch("builtins.input", return_value="cli.admin"), \
                patch("server.getpass.getpass", side_effect=[password, password]):
            self.assertEqual(1, main())
        _, _, token = self.store.login_account("cli.admin", password, None, admin=True)
        self.assertEqual("cli.admin", self.store.admin_me(token)["username"])

    def test_admin_rate_limit_and_password_namespaces_are_separate(self):
        password = "Admin unique password 2026!"
        self.store.create_admin("same.name", password)
        self.store.register_account(self.consumer, "same.name", password, self.token)
        for index in range(5):
            with self.assertRaises(PPError) as caught:
                self.store.login_account("same.name", "Wrong password 2026!", None, admin=True)
            self.assertEqual("PP_LOGIN_RATE_LIMITED" if index == 4 else "PP_CREDENTIALS_INVALID",
                             caught.exception.code)
        with self.assertRaises(PPError) as caught:
            Store(Path(self.store.path)).login_account("same.name", password, None, admin=True)
        self.assertEqual(429, caught.exception.status)
        self.assertEqual(self.consumer, self.store.login_account("same.name", password, None)[0])

    def test_admin_search_filters_literal_text_status_and_pagination(self):
        password = "Synthetic search password 2026!"
        self.store.create_admin("search.admin", password)
        _, _, token = self.store.login_account("search.admin", password, None, admin=True)
        self.store.register_account(self.consumer, "search.owner", password, self.token)
        batch = self.store.options(self.consumer)
        number = batch["options"][0]["number"]
        self.store.select(self.consumer, batch["options"][0]["id"])
        self.store.save_memory(self.consumer, None, "invisible needle", "private needle", [])
        for _ in range(51):
            self.store.create_consumer()
        offered, _ = self.store.create_consumer()
        self.store.options(offered)
        all_rows = self.store.admin_overview(token, 0)
        self.assertEqual(53, all_rows["total"])
        self.assertEqual(50, len(all_rows["entries"]))
        page_two = self.store.admin_overview(token, 50)
        self.assertEqual(3, len(page_two["entries"]))
        self.assertTrue(
            {r["consumerId"] for r in all_rows["entries"]}.isdisjoint(
                r["consumerId"] for r in page_two["entries"]
            )
        )
        for needle in (" SEARCH.OWNER ", self.consumer.upper(), number, number[2:7]):
            result = self.store.admin_overview(token, 0, search=needle, status="ACTIVE")
            self.assertEqual(1, result["total"])
            self.assertEqual(self.consumer, result["entries"][0]["consumerId"])
            self.assertEqual(53, result["counts"]["consumers"])
        for needle in ("%", "_", "' OR 1=1 --", "private needle", "invisible needle"):
            self.assertEqual(0, self.store.admin_overview(token, 0, search=needle)["total"])
        for state, expected in (("NEW", 51), ("OFFERED", 1), ("ACTIVE", 1),
                                ("REVOKED", 0), ("UNKNOWN", 0)):
            self.assertEqual(expected, self.store.admin_overview(token, 0, status=state)["total"])
        self.assertEqual(0, self.store.admin_overview(
            token, 0, search="search.owner", status="REVOKED"
        )["total"])
        self.store.revoke(self.consumer)
        self.assertEqual(1, self.store.admin_overview(
            token, 0, search=number, status="REVOKED"
        )["total"])
        with self.assertRaises(PPError) as caught:
            self.store.admin_overview(token, 0, search="x" * 121)
        self.assertEqual("PP_REQUEST_INVALID", caught.exception.code)

    def test_admin_audit_projection_search_status_and_pagination(self):
        password = "Synthetic audit password 2026!"
        self.store.create_admin("audit.actor", password)
        admin_id, _, token = self.store.login_account("audit.actor", password, None, admin=True)
        self.store.register_account(self.consumer, "audit.target", password, self.token)
        batch = self.store.options(self.consumer)
        self.store.select(self.consumer, batch["options"][0]["id"])
        self.store.revoke(self.consumer, admin_token=token, reason="Unieke auditreden 100%")
        with self.store.transaction() as db:
            for index in range(52):
                self.store.audit(db, None, "ERROR", {"code": "SYNTHETIC",
                                                   "password": "NEVER-EXPOSE-THIS"})
            self.store.audit(db, self.consumer, "MEMORY_CREATED",
                             {"memoryId": "private-note", "content": "PRIVATE-CONTENT"})
            self.store.audit(db, None, "ADMIN_LOGIN",
                             {"adminId": "missing-admin", "password": "NEVER-EXPOSE-THIS"})
        page = self.store.admin_audit(token, 0)
        self.assertEqual(50, len(page["entries"]))
        second = self.store.admin_audit(token, 50)
        self.assertEqual(page["total"] - 50, len(second["entries"]))
        self.assertTrue(
            {r["sequence"] for r in page["entries"]}.isdisjoint(
                r["sequence"] for r in second["entries"]
            )
        )
        self.assertEqual(sorted((r["sequence"] for r in page["entries"]), reverse=True),
                         [r["sequence"] for r in page["entries"]])
        self.assertEqual(11, self.store.admin_audit(token, 0, status="OFFERED")["total"])
        active = self.store.admin_audit(token, 0, status="ACTIVE")
        self.assertEqual(["NUMBER_SELECTED"], [r["event"] for r in active["entries"]])
        self.assertEqual(2, self.store.admin_audit(token, 0, status="REVOKED")["total"])
        for needle in (" AUDIT.ACTOR ", admin_id, "unieke auditreden", "100%",
                       self.consumer.upper(), "AUDIT.TARGET"):
            result = self.store.admin_audit(
                token, 0, search=needle, event="ADMIN_NUMBER_REVOKED", status="REVOKED",
            )
            self.assertEqual(1, result["total"], needle)
            self.assertEqual("Unieke auditreden 100%", result["entries"][0]["reason"])
        unknown = self.store.admin_audit(token, 0, search="missing-admin")
        self.assertEqual(1, unknown["total"])
        self.assertIsNone(unknown["entries"][0]["adminUsername"])
        self.assertEqual("missing-admin", unknown["entries"][0]["adminId"])
        for needle in ("NEVER-EXPOSE-THIS", "PRIVATE-CONTENT", "private-note", "' OR 1=1 --"):
            self.assertEqual(0, self.store.admin_audit(token, 0, search=needle)["total"])
        serialized = json.dumps(page["entries"] + second["entries"])
        self.assertNotIn("NEVER-EXPOSE-THIS", serialized)
        self.assertNotIn("PRIVATE-CONTENT", serialized)
        self.assertNotIn("MEMORY_CREATED", serialized)
        self.assert_code("PP_ADMIN_REQUIRED", self.store.admin_audit, self.token, 0)

    def test_admin_audit_fails_closed_on_invalid_actor_or_reason(self):
        password = "Synthetic audit password 2026!"
        self.store.create_admin("audit.check", password)
        admin_id, _, token = self.store.login_account("audit.check", password, None, admin=True)
        for detail in ("{bad-json", "[]", "null", "{}", '{"adminId": 7}',
                       json.dumps({"adminId": admin_id, "reason": 5}),
                       json.dumps({"adminId": admin_id, "reason": "x"}),
                       json.dumps({"adminId": admin_id, "reason": "x" * 241})):
            with self.subTest(detail=detail), tempfile.TemporaryDirectory() as directory:
                isolated = Store(Path(directory) / "invalid.sqlite3")
                isolated.create_admin("audit.check", password)
                _, _, isolated_token = isolated.login_account(
                    "audit.check", password, None, admin=True,
                )
                with isolated.transaction() as db:
                    db.execute(
                        "INSERT INTO audit(consumer_id,event,detail,created_at) VALUES(?,?,?,?)",
                        (None, "ADMIN_NUMBER_REVOKED", detail, "2026-01-01"),
                    )
                with self.assertRaises(PPError) as caught:
                    isolated.admin_audit(isolated_token, 0, search="no match")
                self.assertEqual("PP_AUDIT_UNKNOWN", caught.exception.code)
                self.assertEqual(503, caught.exception.status)

    def test_admin_revocation_is_atomic_and_preserves_lifecycle(self):
        self.store.create_admin("revoke.admin", "Admin unique password 2026!")
        admin_id, _, token = self.store.login_account(
            "revoke.admin", "Admin unique password 2026!", None, admin=True,
        )
        batch = self.store.options(self.consumer)
        self.store.select(self.consumer, batch["options"][0]["id"])
        with self.assertRaises(PPError):
            self.store.revoke(self.consumer, admin_token=token, reason="x")
        original_audit = self.store.audit

        def fail_admin_audit(db, consumer, event, detail=None):
            if event == "ADMIN_NUMBER_REVOKED":
                raise sqlite3.OperationalError("simulated audit failure")
            original_audit(db, consumer, event, detail)

        with patch.object(self.store, "audit", side_effect=fail_admin_audit):
            with self.assertRaises(sqlite3.OperationalError):
                self.store.revoke(self.consumer, admin_token=token, reason="Test intrekking")
        self.assertEqual("ACTIVE", self.store.me(self.consumer)["status"])
        self.store.revoke(self.consumer, admin_token=token, reason="Test intrekking")
        self.assertTrue(self.store.verify_integrity()["ok"])
        self.assert_code("PP_ALREADY_SELECTED", self.store.options, self.consumer)
        with self.store.connection() as db:
            detail = json.loads(db.execute(
                "SELECT detail FROM audit WHERE event='ADMIN_NUMBER_REVOKED'"
            ).fetchone()[0])
        self.assertEqual({"adminId": admin_id, "reason": "Test intrekking"}, detail)
        self.store.admin_logout(token)
        self.assert_code("PP_ADMIN_REQUIRED", self.store.admin_me, token)

    def test_collision_is_retried_without_duplicate_number(self):
        with patch("server.secrets.randbelow", side_effect=[0, 0] + list(range(1, 10))):
            batch = self.store.options(self.consumer)
        self.assertEqual(10, len({o["number"] for o in batch["options"]}))
        with self.store.connection() as db:
            self.assertEqual(1, db.execute(
                "SELECT count(*) FROM audit WHERE event='NUMBER_CONFLICT'"
            ).fetchone()[0])

    def test_exhausted_generation_rolls_back_entire_batch(self):
        with patch("server.secrets.randbelow", return_value=0):
            self.assert_code("PP_NUMBER_CONFLICT", self.store.options, self.consumer)
        with self.store.connection() as db:
            self.assertEqual(0, db.execute("SELECT count(*) FROM options").fetchone()[0])
            self.assertEqual(0, db.execute("SELECT count(*) FROM batches").fetchone()[0])

    def test_selection_expires_nine_and_blocks_reselection(self):
        options = self.store.options(self.consumer)["options"]
        result = self.store.select(self.consumer, options[2]["id"])
        self.assertEqual(options[2]["number"], result["ppNumber"])
        self.assertEqual("ACTIVE", self.store.me(self.consumer)["status"])
        self.assert_code("PP_ALREADY_SELECTED", self.store.select, self.consumer, options[3]["id"])
        self.assert_code("PP_ALREADY_SELECTED", self.store.options, self.consumer)
        with self.store.connection() as db:
            states = dict(db.execute("SELECT status,count(*) FROM options GROUP BY status"))
            self.assertEqual({"ACTIVE": 1, "EXPIRED": 9}, states)
            self.assertEqual(1, db.execute(
                "SELECT count(*) FROM audit WHERE event='NUMBER_SELECTED'"
            ).fetchone()[0])

    def test_history_records_each_offer_and_only_the_consumers_lifecycle(self):
        batch = self.store.options(self.consumer)
        options = batch["options"]
        events = self.store.history(self.consumer)
        self.assertEqual(10, len(events))
        self.assertTrue(all(event["event"] == "OPTION_OFFERED" for event in events))
        self.assertEqual(
            {option["number"] for option in options},
            {event["detail"]["ppNumber"] for event in events},
        )
        self.assertEqual(
            {option["color"] for option in options},
            {event["detail"]["color"] for event in events},
        )
        self.assertEqual(
            sorted(event["sequence"] for event in events),
            [event["sequence"] for event in events],
        )
        second, _ = self.store.create_consumer()
        self.store.options(second)
        self.assertEqual(events, self.store.history(self.consumer))
        selected = options[2]
        self.store.select(self.consumer, selected["id"])
        self.store.revoke(self.consumer)
        history = self.store.history(self.consumer)
        self.assertEqual(
            ["OPTION_OFFERED"] * 10 + ["NUMBER_SELECTED", "NUMBER_REVOKED"],
            [event["event"] for event in history],
        )
        for event in history[-2:]:
            self.assertEqual(selected["number"], event["detail"]["ppNumber"])
            self.assertEqual(selected["color"], event["detail"]["color"])
            self.assertEqual(selected["id"], event["detail"]["optionId"])
        second_history = self.store.history(second)
        self.assertEqual(10, len(second_history))
        self.assertNotEqual(
            {event["detail"]["ppNumber"] for event in history},
            {event["detail"]["ppNumber"] for event in second_history},
        )

    def test_history_enriches_legacy_selection_event_from_owned_option(self):
        batch = self.store.options(self.consumer)
        option = batch["options"][0]
        with self.store.transaction() as db:
            self.store.audit(
                db,
                self.consumer,
                "NUMBER_SELECTED",
                {"optionId": option["id"]},
            )
        event = self.store.history(self.consumer)[-1]
        self.assertEqual(option["number"], event["detail"]["ppNumber"])
        self.assertEqual(option["color"], event["detail"]["color"])
        self.assertEqual(batch["batchId"], event["detail"]["batchId"])

    def test_memory_crud_is_private_and_audit_never_stores_note_content(self):
        secret_note = "private note content must not enter audit"
        entry = self.store.save_memory(
            self.consumer,
            None,
            "  My note  ",
            f"  {secret_note}  ",
            [" idee ", "later", "IDEE"],
        )
        self.assertEqual("My note", entry["title"])
        self.assertEqual(secret_note, entry["content"])
        self.assertEqual(["idee", "later"], entry["tags"])
        self.assertEqual(entry["createdAt"], entry["updatedAt"])

        second, _ = self.store.create_consumer()
        self.store.save_memory(second, None, "Andere privé-notitie", "Niet van de eerste gebruiker.", [])
        own_list = self.store.list_memory(self.consumer)
        other_list = self.store.list_memory(second)
        self.assertEqual([entry["id"]], [item["id"] for item in own_list["entries"]])
        self.assertEqual("Andere privé-notitie", other_list["entries"][0]["title"])
        self.assertNotIn(secret_note, json.dumps(other_list))
        self.assertEqual(100, own_list["limit"])

        updated = self.store.save_memory(
            self.consumer, entry["id"], "Bijgewerkt", "Vervangende privétekst", ["werk"]
        )
        self.assertEqual(entry["id"], updated["id"])
        self.assertEqual(entry["createdAt"], updated["createdAt"])
        self.assertGreaterEqual(updated["updatedAt"], entry["updatedAt"])
        self.assertEqual("Vervangende privétekst", self.store.list_memory(self.consumer)["entries"][0]["content"])

        self.assert_code("PP_MEMORY_UNKNOWN", self.store.save_memory, second, entry["id"],
                         "Probe", "Cross-account update", [])
        self.assert_code("PP_MEMORY_UNKNOWN", self.store.delete_memory, second, entry["id"])
        self.assertEqual("Bijgewerkt", self.store.list_memory(self.consumer)["entries"][0]["title"])
        self.assertEqual({"deleted": True, "id": entry["id"]},
                         self.store.delete_memory(self.consumer, entry["id"]))
        self.assertEqual([], self.store.list_memory(self.consumer)["entries"])

        with self.store.connection() as db:
            audit_rows = db.execute(
                """SELECT event,detail FROM audit
                   WHERE event IN ('MEMORY_CREATED','MEMORY_UPDATED','MEMORY_DELETED')"""
            ).fetchall()
        self.assertEqual(["MEMORY_CREATED", "MEMORY_CREATED", "MEMORY_UPDATED", "MEMORY_DELETED"],
                         [row["event"] for row in audit_rows])
        self.assertNotIn(secret_note, json.dumps([dict(row) for row in audit_rows]))
        self.assertNotIn("Vervangende privétekst", json.dumps([dict(row) for row in audit_rows]))
        self.assertTrue(all(set(json.loads(row["detail"])) == {"memoryId"} for row in audit_rows))

    def test_memory_validates_fields_and_enforces_per_account_limit(self):
        for title, content, tags in (
            ("", "content", []),
            ("title", "", []),
            ("t" * 121, "content", []),
            ("title", "x" * 5001, []),
            ("title", "content", ["tag"] * 9),
            ("title", "content", ["t" * 25]),
            ("title", "content", ["valid", 7]),
            ("title", "bad\x00content", []),
        ):
            self.assert_code(
                "PP_MEMORY_INVALID",
                self.store.save_memory,
                self.consumer,
                None,
                title,
                content,
                tags,
            )
        for index in range(100):
            self.store.save_memory(self.consumer, None, f"Note {index}", "Body", [])
        with self.store.connection() as db:
            self.assertEqual(100, db.execute(
                "SELECT count(*) FROM audit WHERE event='MEMORY_CREATED'"
            ).fetchone()[0])
            with self.assertRaisesRegex(sqlite3.IntegrityError, "MEMORY_ENTRY_LIMIT"):
                db.execute(
                    """INSERT INTO memory_entries
                       (id,consumer_id,title,content,tags_json,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    ("over-limit", self.consumer, "Extra", "Body", "[]", "now", "now"),
                )
        self.assertEqual(100, len(self.store.list_memory(self.consumer)["entries"]))
        self.assert_code(
            "PP_MEMORY_LIMIT",
            self.store.save_memory,
            self.consumer,
            None,
            "Over limit",
            "Body",
            [],
        )
        editable = self.store.list_memory(self.consumer)["entries"][0]
        self.store.save_memory(self.consumer, editable["id"], "Edited at capacity", "Still allowed", [])
        self.assertEqual(100, len(self.store.list_memory(self.consumer)["entries"]))
        self.assert_code("PP_MEMORY_INVALID", self.store.delete_memory, self.consumer, "")

    def test_startup_backfills_legacy_offer_events_once_in_original_order(self):
        batch_id = "legacy-batch"
        offered = "2026-10-20T10:00:00+00:00"
        with self.store.transaction() as db:
            db.execute("INSERT INTO batches VALUES(?,?)", (batch_id, self.consumer))
            for index, color in enumerate(
                ("blue", "red", "green", "yellow", "blue",
                 "red", "green", "yellow", "blue", "red")
            ):
                db.execute(
                    "INSERT INTO options VALUES(?,?,?,?,?,?)",
                    (
                        f"legacy-option-{index}",
                        batch_id,
                        str(1_234_567_890 + index),
                        "OFFERED",
                        color,
                        offered,
                    ),
                )
        migrated = Store(self.store.path)
        events = migrated.history(self.consumer)
        self.assertEqual(10, len(events))
        self.assertTrue(all(event["event"] == "OPTION_OFFERED" for event in events))
        self.assertTrue(all(event["createdAt"] == offered for event in events))
        self.assertEqual(10, len({event["detail"]["ppNumber"] for event in events}))
        restarted = Store(self.store.path)
        self.assertEqual(events, restarted.history(self.consumer))

    def test_foreign_or_missing_option_cannot_be_selected(self):
        second, _ = self.store.create_consumer()
        foreign = self.store.options(second)["options"][0]["id"]
        self.assert_code("PP_OPTION_INVALID", self.store.select, self.consumer, foreign)
        self.assert_code("PP_OPTION_INVALID", self.store.select, self.consumer, "missing")
        self.assertEqual("NEW", self.store.me(self.consumer)["status"])

    def test_concurrent_options_share_one_batch(self):
        barrier = threading.Barrier(8)

        def get_options(_):
            barrier.wait()
            return self.store.options(self.consumer)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(get_options, range(8)))
        self.assertTrue(all(result == results[0] for result in results))
        with self.store.connection() as db:
            self.assertEqual(10, db.execute("SELECT count(*) FROM options").fetchone()[0])

    def test_concurrent_selections_have_exactly_one_winner(self):
        options = self.store.options(self.consumer)["options"]
        barrier = threading.Barrier(10)

        def choose(option):
            barrier.wait()
            try:
                return self.store.select(self.consumer, option["id"])["status"]
            except PPError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(choose, options))
        self.assertEqual(1, results.count("ACTIVE"))
        self.assertEqual(9, results.count("PP_ALREADY_SELECTED"))

    def test_concurrent_consumers_have_globally_unique_numbers(self):
        consumers = [self.store.create_consumer()[0] for _ in range(8)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            batches = list(pool.map(self.store.options, consumers))
        self.assertEqual(80, len({o["number"] for b in batches for o in b["options"]}))

    def test_revocation_keeps_history_and_permanently_blocks_new_selection(self):
        option = self.store.options(self.consumer)["options"][0]
        self.store.select(self.consumer, option["id"])
        self.store.revoke(self.consumer)
        state = self.store.me(self.consumer)
        self.assertEqual("REVOKED", state["status"])
        self.assertIsNotNone(state["revokedAt"])
        self.assertEqual(option["number"], state["ppNumber"])
        self.assert_code("PP_ALREADY_SELECTED", self.store.options, self.consumer)
        self.assert_code("PP_ALREADY_SELECTED", self.store.select, self.consumer, option["id"])
        self.assert_code("PP_SELECTION_REVOKED", self.store.revoke, self.consumer)

    def test_restart_preserves_session_options_and_selection(self):
        option = self.store.options(self.consumer)["options"][0]
        self.store.select(self.consumer, option["id"])
        restarted = Store(self.store.path)
        self.assertEqual(self.consumer, restarted.identify(self.token))
        self.assertEqual(option["number"], restarted.me(self.consumer)["ppNumber"])
        self.assert_code("PP_ALREADY_SELECTED", restarted.options, self.consumer)

    def test_storage_constraints_and_append_only_audit(self):
        batch = self.store.options(self.consumer)
        with self.store.connection() as db:
            for number in ("123", "0123456789", "123456789x", "12345678901"):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(
                        "INSERT INTO options VALUES(?,?,?,?,?,?)",
                        (number, batch["batchId"], number, "OFFERED", "blue", "test"),
                    )
            for sql in ("DELETE FROM audit", "UPDATE audit SET event = 'changed'"):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(sql)

    def test_database_enforces_append_only_number_identity_and_valid_lifecycle(self):
        batch = self.store.options(self.consumer)
        option = batch["options"][0]
        with self.store.connection() as db:
            invalid_statements = (
                ("UPDATE options SET number = '0000000000' WHERE id = ?", (option["id"],)),
                (
                    "UPDATE options SET color = CASE color WHEN 'blue' THEN 'red' ELSE 'blue' END WHERE id = ?",
                    (option["id"],),
                ),
                ("UPDATE options SET status = 'REVOKED' WHERE id = ?", (option["id"],)),
                ("UPDATE options SET status = 'OFFERED' WHERE id = ?", (option["id"],)),
                ("DELETE FROM options WHERE id = ?", (option["id"],)),
                ("UPDATE batches SET consumer_id = ? WHERE id = ?", (self.consumer, batch["batchId"])),
                ("DELETE FROM batches WHERE id = ?", (batch["batchId"],)),
            )
            for sql, params in invalid_statements:
                with self.subTest(sql=sql):
                    with self.assertRaises(sqlite3.IntegrityError):
                        db.execute(sql, params)
        self.store.select(self.consumer, option["id"])
        with self.store.connection() as db:
            for sql, params in (
                (
                    "UPDATE selections SET option_id = ? WHERE consumer_id = ?",
                    (batch["options"][1]["id"], self.consumer),
                ),
                (
                    "UPDATE selections SET revoked_at = ? WHERE consumer_id = ?",
                    ("2026-10-21T12:00:00+00:00", self.consumer),
                ),
                ("DELETE FROM selections WHERE consumer_id = ?", (self.consumer,)),
            ):
                with self.subTest(sql=sql):
                    with self.assertRaises(sqlite3.IntegrityError):
                        db.execute(sql, params)

    def test_database_rejects_selection_for_another_consumers_active_option(self):
        batch = self.store.options(self.consumer)
        option = batch["options"][0]
        other, _ = self.store.create_consumer()
        with self.store.connection() as db:
            db.execute("UPDATE options SET status = 'ACTIVE' WHERE id = ?", (option["id"],))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO selections VALUES(?,?,?,NULL)",
                    (other, option["id"], "2026-10-21T12:00:00+00:00"),
                )
        self.assertEqual("OFFERED", self.store.me(self.consumer)["status"])

    def test_integrity_verifier_accepts_valid_offer_selection_and_revocation(self):
        batch = self.store.options(self.consumer)
        report = self.store.verify_integrity()
        self.assertTrue(report["ok"], report)
        self.assertEqual(10, report["counts"]["options"])
        option = batch["options"][0]
        self.store.select(self.consumer, option["id"])
        self.assertTrue(self.store.verify_integrity()["ok"])
        self.store.revoke(self.consumer)
        self.assertTrue(self.store.verify_integrity()["ok"])

    def test_integrity_verifier_fails_closed_on_incomplete_batch(self):
        self.store.options(self.consumer)
        with self.store.connection() as db:
            db.execute("DROP TRIGGER options_immutable_identity")
            db.execute("UPDATE options SET color = 'blue'")
        report = self.store.verify_integrity()
        self.assertFalse(report["ok"])
        self.assertIn("BATCH_SHAPE_INVALID", report["issues"])

    def test_integrity_verifier_detects_missing_lifecycle_audit(self):
        batch = self.store.options(self.consumer)
        option_id = batch["options"][0]["id"]
        with self.store.connection() as db:
            db.execute("DROP TRIGGER audit_no_delete")
            db.execute(
                """DELETE FROM audit WHERE rowid = (
                     SELECT rowid FROM audit WHERE event = 'OPTION_OFFERED'
                       AND json_extract(detail, '$.optionId') = ?
                   )""",
                (option_id,),
            )
        report = self.store.verify_integrity()
        self.assertFalse(report["ok"])
        self.assertIn("OFFER_AUDIT_INCOMPLETE", report["issues"])

    def test_integrity_and_history_fail_closed_on_malformed_audit_json(self):
        self.store.options(self.consumer)
        with self.store.connection() as db:
            db.execute("DROP TRIGGER audit_no_update")
            db.execute(
                """UPDATE audit SET detail = '{broken json'
                   WHERE event = 'OPTION_OFFERED'"""
            )
        report = self.store.verify_integrity()
        self.assertFalse(report["ok"])
        self.assertIn("AUDIT_DETAIL_INVALID", report["issues"])
        self.assert_code("PP_SELECTION_UNKNOWN", self.store.history, self.consumer)

    def test_integrity_verifier_detects_duplicate_offer_audits(self):
        self.store.options(self.consumer)
        with self.store.connection() as db:
            db.execute("DROP TRIGGER audit_no_delete")
            db.execute(
                """INSERT INTO audit(consumer_id,event,detail,created_at)
                   SELECT consumer_id,event,detail,created_at FROM audit
                   WHERE event = 'OPTION_OFFERED' LIMIT 1"""
            )
        report = self.store.verify_integrity()
        self.assertFalse(report["ok"])
        self.assertIn("OFFER_AUDIT_INCOMPLETE", report["issues"])

    def test_failed_audit_rolls_back_selection(self):
        option = self.store.options(self.consumer)["options"][0]
        with self.store.connection() as db:
            db.execute("""CREATE TRIGGER fail_selection_audit BEFORE INSERT ON audit
                          WHEN NEW.event = 'NUMBER_SELECTED'
                          BEGIN SELECT RAISE(ABORT, 'TEST_FAILURE'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.select(self.consumer, option["id"])
        self.assertEqual("OFFERED", self.store.me(self.consumer)["status"])
        self.assertEqual(10, len(self.store.options(self.consumer)["options"]))
        self.assertEqual(
            10,
            len(self.store.history(self.consumer)),
            "failed selection must not append a lifecycle history event",
        )

    def test_inconsistent_state_fails_closed(self):
        option = self.store.options(self.consumer)["options"][0]
        self.store.select(self.consumer, option["id"])
        with self.store.connection() as db:
            # Simulate an out-of-band administrator bypassing lifecycle guards.
            db.execute("DROP TRIGGER options_valid_status_transition")
            db.execute("UPDATE options SET status='OFFERED' WHERE id=?", (option["id"],))
        self.assert_code("PP_SELECTION_UNKNOWN", self.store.me, self.consumer)

    def test_registration_links_existing_consumer_and_batch(self):
        batch = self.store.options(self.consumer)
        username, new_token = self.store.register_account(
            self.consumer, "  PALACO.User  ", "Correct horse battery 2026!", self.token
        )
        self.assertEqual("palaco.user", username)
        self.assertEqual(self.consumer, self.store.identify(new_token))
        self.assertIsNone(self.store.identify(self.token))
        self.assertEqual({"authenticated": True, "username": "palaco.user"},
                         self.store.auth_state(self.consumer))
        self.assertEqual(batch, self.store.options(self.consumer))

    def test_login_normalizes_username_and_rejects_wrong_credentials(self):
        self.store.register_account(
            self.consumer, "Palaco.User", "Correct horse battery 2026!", self.token
        )
        guest, guest_token = self.store.create_consumer()
        owner, username, new_token = self.store.login_account(
            "PALACO.USER", "Correct horse battery 2026!", guest_token
        )
        self.assertEqual(self.consumer, owner)
        self.assertEqual("palaco.user", username)
        self.assertEqual(owner, self.store.identify(new_token))
        self.assertIsNone(self.store.identify(guest_token))
        self.assertFalse(self.store.auth_state(guest)["authenticated"])
        self.assert_code(
            "PP_CREDENTIALS_INVALID",
            self.store.login_account,
            "palaco.user",
            "Wrong password 2026!",
            None,
        )

    def test_repeated_failed_logins_are_limited_and_success_resets_attempts(self):
        self.store.register_account(
            self.consumer, "limited.user", "Correct horse battery 2026!", self.token
        )
        for _ in range(4):
            self.assert_code(
                "PP_CREDENTIALS_INVALID",
                self.store.login_account,
                "limited.user",
                "Wrong password 2026!",
                None,
            )
        self.assert_code(
            "PP_LOGIN_RATE_LIMITED",
            self.store.login_account,
            "limited.user",
            "Wrong password 2026!",
            None,
        )
        self.assert_code(
            "PP_LOGIN_RATE_LIMITED",
            self.store.login_account,
            "limited.user",
            "Correct horse battery 2026!",
            None,
        )
        username_hash = hashlib.sha256(b"limited.user").hexdigest()
        with self.store.transaction() as db:
            db.execute(
                "UPDATE auth_login_attempts SET blocked_until = ? WHERE username_hash = ?",
                ("2000-01-01T00:00:00+00:00", username_hash),
            )
        consumer, _, new_token = self.store.login_account(
            "limited.user", "Correct horse battery 2026!", None
        )
        self.assertEqual(self.consumer, consumer)
        self.assertEqual(self.consumer, self.store.identify(new_token))
        with self.store.connection() as db:
            self.assertEqual(
                0,
                db.execute(
                    "SELECT count(*) FROM auth_login_attempts WHERE username_hash = ?",
                    (username_hash,),
                ).fetchone()[0],
            )

    def test_unknown_username_has_same_failure_and_rate_limit_behavior(self):
        for _ in range(4):
            self.assert_code(
                "PP_CREDENTIALS_INVALID",
                self.store.login_account,
                "missing.user",
                "Wrong password 2026!",
                None,
            )
        self.assert_code(
            "PP_LOGIN_RATE_LIMITED",
            self.store.login_account,
            "missing.user",
            "Wrong password 2026!",
            None,
        )

    def test_duplicate_accounts_and_invalid_credentials_are_rejected(self):
        self.store.register_account(
            self.consumer, "palaco.user", "Correct horse battery 2026!", self.token
        )
        second, _ = self.store.create_consumer()
        self.assert_code(
            "PP_USERNAME_TAKEN",
            self.store.register_account,
            second,
            "PALACO.USER",
            "Another secure password 2026!",
            None,
        )
        self.assert_code(
            "PP_USERNAME_INVALID",
            self.store.register_account,
            second,
            "ab",
            "Another secure password 2026!",
            None,
        )
        self.assert_code(
            "PP_PASSWORD_INVALID",
            self.store.register_account,
            second,
            "another.user",
            "short",
            None,
        )

    def test_logout_does_not_resurrect_old_session_after_restart(self):
        _, rotated = self.store.register_account(
            self.consumer, "palaco.user", "Correct horse battery 2026!", self.token
        )
        self.store.logout(self.consumer, rotated)
        restarted = Store(self.store.path)
        self.assertIsNone(restarted.identify(rotated))

    def test_existing_pre_account_session_is_migrated_without_losing_consumer(self):
        legacy_path = Path(self.temp.name) / "legacy.sqlite3"
        legacy_token = "pre-account-session-token"
        legacy_consumer = "legacy-consumer"
        with closing(sqlite3.connect(legacy_path)) as db:
            with db:
                db.execute(
                    "CREATE TABLE consumers(id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL)"
                )
                db.execute(
                    "INSERT INTO consumers VALUES(?,?,?)",
                    (
                        legacy_consumer,
                        hashlib.sha256(legacy_token.encode()).hexdigest(),
                        "2026-10-20T12:00:00+00:00",
                    ),
                )
        migrated = Store(legacy_path)
        self.assertEqual(legacy_consumer, migrated.identify(legacy_token))
        self.assertFalse(migrated.auth_state(legacy_consumer)["authenticated"])

    def test_password_storage_contains_only_salted_hash(self):
        password = "Correct horse battery 2026!"
        self.store.register_account(self.consumer, "hashed.user", password, self.token)
        with self.store.connection() as db:
            account = db.execute(
                "SELECT password_salt,password_hash FROM accounts WHERE username = ?",
                ("hashed.user",),
            ).fetchone()
        self.assertNotEqual(password.encode(), account["password_hash"])
        self.assertEqual(16, len(account["password_salt"]))
        self.assertEqual(32, len(account["password_hash"]))


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / "api.sqlite3")
        self.server = Server(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.cookie = None
        self.host = f"127.0.0.1:{self.server.server_port}"

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, data=None, origin=True):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = f"http://{self.host}"
        if self.cookie:
            headers["Cookie"] = self.cookie
        connection.request(method, path, json.dumps(data) if data is not None else None, headers)
        response = connection.getresponse()
        body = response.read()
        cookie = response.getheader("Set-Cookie")
        if cookie:
            self.cookie = cookie.split(";")[0]
        status = response.status
        content_type = response.getheader("Content-Type")
        connection.close()
        return status, json.loads(body) if content_type == "application/json" else body

    def test_tile_assets_are_public_and_do_not_create_identity(self):
        status, page = self.request("GET", "/")
        self.assertEqual(200, status)
        self.assertIn(b'href="/manifest.webmanifest"', page)
        status, body = self.request("GET", "/manifest.webmanifest")
        self.assertEqual(200, status)
        manifest = json.loads(body)
        self.assertEqual("standalone", manifest["display"])
        self.assertEqual("/", manifest["start_url"])
        self.assertEqual("P.P.", manifest["short_name"])
        for icon in manifest["icons"]:
            connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
            connection.request("GET", icon["src"])
            response = connection.getresponse()
            image = response.read()
            self.assertEqual(200, response.status)
            self.assertEqual("image/png", response.getheader("Content-Type"))
            self.assertIsNone(response.getheader("Set-Cookie"))
            self.assertEqual(b'\x89PNG\r\n\x1a\n', image[:8])
            expected = int(icon["sizes"].split("x")[0])
            self.assertEqual(expected, int.from_bytes(image[16:20], "big"))
            self.assertEqual(expected, int.from_bytes(image[20:24], "big"))
            connection.close()
        self.assertIsNone(self.cookie)
        with self.store.connection() as db:
            self.assertEqual(0, db.execute("SELECT count(*) FROM consumers").fetchone()[0])
        self.assertEqual(401, self.request("GET", "/api/pp/me")[0])

    def test_selection_email_api_is_optional_authenticated_and_never_sends_twice(self):
        self.assertEqual(401, self.request("GET", "/api/pp/mail")[0])
        self.request("POST", "/api/session", {})
        self.request("POST", "/api/auth/register", {
            "username": "mail.owner", "password": "Synthetic mail password 2026!",
        })
        cookie = self.cookie
        option = self.request("POST", "/api/pp/options", {})[1]["options"][0]["id"]
        body = {"optionId": option, "email": "synthetic@example.test"}
        self.assertEqual(503, self.request("POST", "/api/pp/select", body)[0])
        self.assertEqual("OFFERED", self.request("GET", "/api/pp/me")[1]["status"])
        self.assertFalse(self.request("GET", "/api/pp/mail")[1]["available"])
        self.server.mail_config = {"synthetic": True}
        self.assertEqual(400, self.request(
            "POST", "/api/pp/select", {"optionId": option, "email": "bad\r\nmail"}
        )[0])
        self.assertEqual(200, self.request("POST", "/api/pp/select", body)[0])
        status = self.request("GET", "/api/pp/mail")[1]
        self.assertTrue(status["available"])
        self.assertEqual("QUEUED", status["status"])
        self.assertNotIn("synthetic@example.test", json.dumps(status))
        self.assertEqual(409, self.request("POST", "/api/pp/select", body)[0])
        self.cookie = None
        self.request("POST", "/api/session", {})
        self.request("POST", "/api/auth/register", {
            "username": "mail.other", "password": "Synthetic mail password 2026!",
        })
        self.assertEqual("NOT_REQUESTED", self.request("GET", "/api/pp/mail")[1]["status"])
        other_option = self.request("POST", "/api/pp/options", {})[1]["options"][0]["id"]
        self.server.mail_config = None
        self.assertEqual(200, self.request(
            "POST", "/api/pp/select", {"optionId": other_option}
        )[0])
        self.cookie = cookie
        self.assertEqual("QUEUED", self.request("GET", "/api/pp/mail")[1]["status"])

    def test_admin_api_login_overview_audit_revoke_and_isolation(self):
        password = "Admin unique password 2026!"
        self.store.create_admin("office.admin", password)
        for path in ("/admin", "/admin.js", "/admin.css"):
            self.assertEqual(200, self.request("GET", path)[0])
        self.request("POST", "/api/session", {})
        self.request("POST", "/api/auth/register",
                     {"username": "office.consumer", "password": password})
        consumer_cookie = self.cookie
        consumer = self.store.identify(consumer_cookie.split("=", 1)[1])
        self.store.save_memory(consumer, None, "PRIVATE TITLE", "PRIVATE BODY", ["private"])
        batch = self.store.options(consumer)
        self.store.select(consumer, batch["options"][0]["id"])
        self.assertEqual(401, self.request("GET", "/api/admin/overview")[0])
        self.assertEqual(401, self.request(
            "POST", "/api/admin/login", {"username": "office.consumer", "password": password}
        )[0])
        self.assertEqual(403, self.request(
            "POST", "/api/admin/login", {"username": "office.admin", "password": password},
            origin=False,
        )[0])
        status, logged_in = self.request(
            "POST", "/api/admin/login", {"username": "office.admin", "password": password}
        )
        self.assertEqual(200, status)
        self.assertTrue(logged_in["authenticated"])
        admin_cookie = self.cookie
        self.assertEqual(401, self.request("GET", "/api/memory")[0])
        self.assertEqual(401, self.request("GET", "/api/pp/me")[0])
        overview = self.request("GET", "/api/admin/overview?offset=0")[1]
        self.assertEqual(1, overview["counts"]["active"])
        self.assertEqual("office.consumer", overview["entries"][0]["username"])
        self.assertEqual([], self.request("GET", "/api/admin/overview?offset=50")[1]["entries"])
        self.assertEqual(400, self.request("GET", "/api/admin/overview?offset=-1")[0])
        audit = self.request("GET", "/api/admin/audit")[1]
        self.assertFalse(any(row["event"].startswith("MEMORY_") for row in audit["entries"]))
        for secret in ("PRIVATE TITLE", "PRIVATE BODY", "password_hash", "password_salt"):
            self.assertNotIn(secret, json.dumps([overview, audit]))
        body = {"consumerId": consumer, "reason": "Beheer test", "confirm": False}
        self.assertEqual(400, self.request("POST", "/api/admin/revoke", body)[0])
        self.assertEqual("ACTIVE", self.store.me(consumer)["status"])
        body["confirm"] = True
        self.assertEqual(200, self.request("POST", "/api/admin/revoke", body)[0])
        self.assertEqual(409, self.request("POST", "/api/admin/revoke", body)[0])
        self.assertEqual(200, self.request("GET", "/api/admin/me")[0])
        self.assertEqual(200, self.request("POST", "/api/admin/logout", {})[0])
        self.cookie = admin_cookie
        self.assertEqual(401, self.request("GET", "/api/admin/overview")[0])
        self.cookie = consumer_cookie
        self.assertEqual("REVOKED", self.request("GET", "/api/pp/me")[1]["status"])
        self.assertEqual("PRIVATE BODY", self.request("GET", "/api/memory")[1]["entries"][0]["content"])

    def test_admin_search_api_validates_query_and_retains_auth_boundary(self):
        password = "Synthetic search password 2026!"
        self.assertEqual(401, self.request(
            "GET", "/api/admin/overview?q=test&status=NEW"
        )[0])
        self.store.create_admin("query.admin", password)
        self.request("POST", "/api/admin/login",
                     {"username": "query.admin", "password": password})
        consumer, token = self.store.create_consumer()
        self.store.register_account(consumer, "query.owner", password, token)
        result = self.request("GET", "/api/admin/overview?status=NEW&q=QUERY.OWNER&offset=0")
        self.assertEqual(200, result[0])
        self.assertEqual(1, result[1]["total"])
        self.assertEqual(consumer, result[1]["entries"][0]["consumerId"])
        self.assertEqual(0, self.request("GET", "/api/admin/overview?q=%25")[1]["total"])
        self.assertEqual(0, self.request("GET", "/api/admin/overview?q=%27%20OR%201%3D1")[1]["total"])
        for query in ("q=x&q=y", "status=INVALID", "q=" + "x" * 121,
                      "offset=-1", "offset=abc", "offset=1000000000",
                      "unknown=1", "q", "q=%FF", "offset=0&q=x&status=NEW&extra=x"):
            status, body = self.request("GET", "/api/admin/overview?" + query)
            self.assertEqual(400, status, query)
            self.assertEqual("PP_REQUEST_INVALID", body["error"])
        self.assertEqual(200, self.request("GET", "/api/admin/audit?q=x")[0])
        self.assertEqual(200, self.request("GET", "/api/admin/audit?offset=0")[0])

    def test_admin_audit_api_details_filters_validation_and_no_private_data(self):
        password = "Synthetic audit password 2026!"
        self.assertEqual(401, self.request("GET", "/api/admin/audit?q=test")[0])
        self.store.create_admin("audit.admin", password)
        self.request("POST", "/api/admin/login",
                     {"username": "audit.admin", "password": password})
        consumer, token = self.store.create_consumer()
        self.store.register_account(consumer, "audit.owner", password, token)
        batch = self.store.options(consumer)
        self.store.select(consumer, batch["options"][0]["id"])
        self.store.save_memory(consumer, None, "SECRET-NOTE-TITLE", "SECRET-NOTE-BODY", [])
        reason = "Synthetische intrekking <b>geen HTML</b>"
        admin_token = self.cookie.split("=", 1)[1]
        self.store.revoke(consumer, admin_token=admin_token, reason=reason)
        status, result = self.request(
            "GET", "/api/admin/audit?offset=0&q=AUDIT.ADMIN&event=ADMIN_NUMBER_REVOKED&status=REVOKED"
        )
        self.assertEqual(200, status)
        self.assertEqual(1, result["total"])
        entry = result["entries"][0]
        self.assertEqual(reason, entry["reason"])
        self.assertEqual("audit.admin", entry["adminUsername"])
        self.assertEqual("audit.owner", entry["username"])
        self.assertEqual(consumer, entry["consumerId"])
        self.assertEqual("REVOKED", entry["status"])
        self.assertNotIn("detail", entry)
        self.assertEqual(0, self.request(
            "GET", "/api/admin/audit?event=ADMIN_NUMBER_REVOKED&status=ACTIVE"
        )[1]["total"])
        all_entries = self.request("GET", "/api/admin/audit")[1]["entries"]
        serialized = json.dumps(all_entries)
        for secret in ("SECRET-NOTE-TITLE", "SECRET-NOTE-BODY", "password_hash",
                       "password_salt", admin_token):
            self.assertNotIn(secret, serialized)
        for query in ("event=MEMORY_CREATED", "event=NO_EVENT", "status=NEW",
                      "status=UNKNOWN", "q=" + "a" * 121, "q=x&q=y", "event=%FF",
                      "offset=-1", "extra=x", "q=x&event=&status=&offset=0&extra=x"):
            self.assertEqual(400, self.request("GET", "/api/admin/audit?" + query)[0], query)
        with self.store.transaction() as db:
            db.execute(
                """INSERT INTO audit(consumer_id,event,detail,created_at)
                   VALUES(NULL,'ADMIN_NUMBER_REVOKED','[]','2026-01-01')"""
            )
        status, result = self.request("GET", "/api/admin/audit")
        self.assertEqual(503, status)
        self.assertEqual({"error": "PP_AUDIT_UNKNOWN"}, result)

    def test_full_http_flow_and_reload(self):
        self.assertEqual(200, self.request("GET", "/")[0])
        for path in ("/app.js", "/style.css"):
            self.assertEqual(200, self.request("GET", path)[0])
        self.assertEqual(401, self.request("GET", "/api/pp/me")[0])
        self.assertEqual(401, self.request("GET", "/api/pp/history")[0])
        status, session = self.request("POST", "/api/session", {})
        self.assertEqual(200, status)
        self.assertFalse(session["authenticated"])
        self.assertEqual(session, self.request("POST", "/api/session", {})[1])
        status, account = self.request(
            "POST",
            "/api/auth/register",
            {"username": "demo.account", "password": "Correct horse battery 2026!"},
        )
        self.assertEqual(201, status)
        self.assertTrue(account["authenticated"])
        self.assertEqual(session["consumerId"], account["consumerId"])
        batch = self.request("POST", "/api/pp/options", {})[1]
        self.assertEqual(10, len(batch["options"]))
        offered_history = self.request("GET", "/api/pp/history")[1]["events"]
        self.assertEqual(10, len(offered_history))
        self.assertTrue(all(event["event"] == "OPTION_OFFERED" for event in offered_history))
        self.assertEqual(batch, self.request("POST", "/api/pp/options", {})[1])
        status, chosen = self.request("POST", "/api/pp/select", {"optionId": batch["options"][0]["id"]})
        self.assertEqual(200, status)
        selected_history = self.request("GET", "/api/pp/history")[1]["events"]
        self.assertEqual(11, len(selected_history))
        self.assertEqual("NUMBER_SELECTED", selected_history[-1]["event"])
        self.assertEqual(chosen["ppNumber"], selected_history[-1]["detail"]["ppNumber"])
        self.assertEqual(chosen["ppNumber"], self.request("GET", "/api/pp/me")[1]["ppNumber"])
        self.assertEqual(409, self.request("POST", "/api/pp/select", {"optionId": batch["options"][1]["id"]})[0])
        self.assertEqual(200, self.request("POST", "/api/pp/revoke", {})[0])
        self.assertEqual("REVOKED", self.request("GET", "/api/pp/me")[1]["status"])
        revoked_history = self.request("GET", "/api/pp/history")[1]["events"]
        self.assertEqual(12, len(revoked_history))
        self.assertEqual("NUMBER_REVOKED", revoked_history[-1]["event"])
        self.assertEqual(chosen["ppNumber"], revoked_history[-1]["detail"]["ppNumber"])
        self.assertEqual(409, self.request("POST", "/api/pp/options", {})[0])
        self.assertEqual(200, self.request("POST", "/api/auth/logout", {})[0])
        self.assertEqual(401, self.request("GET", "/api/pp/me")[0])
        status, logged_in = self.request(
            "POST",
            "/api/auth/login",
            {"username": "DEMO.ACCOUNT", "password": "Correct horse battery 2026!"},
        )
        self.assertEqual(200, status)
        self.assertEqual(account["consumerId"], logged_in["consumerId"])
        self.assertEqual("REVOKED", self.request("GET", "/api/pp/me")[1]["status"])

    def test_origin_and_invalid_payload_fail_with_audit(self):
        self.assertEqual(403, self.request("POST", "/api/session", {}, origin=False)[0])
        self.request("POST", "/api/session", {})
        self.request(
            "POST",
            "/api/auth/register",
            {"username": "audit.user", "password": "Correct horse battery 2026!"},
        )
        self.assertEqual(400, self.request("POST", "/api/pp/select", {"optionId": 7})[0])
        self.assertEqual(400, self.request("POST", "/api/pp/select", [1, 2])[0])
        with self.store.connection() as db:
            self.assertEqual(3, db.execute(
                "SELECT count(*) FROM audit WHERE event='ERROR'"
            ).fetchone()[0])

    def test_consumer_id_in_body_cannot_impersonate_another_consumer(self):
        self.request("POST", "/api/session", {})
        self.request(
            "POST",
            "/api/auth/register",
            {"username": "owner.user", "password": "Correct horse battery 2026!"},
        )
        other, _ = self.store.create_consumer()
        option = self.store.options(other)["options"][0]
        status, error = self.request(
            "POST", "/api/pp/select", {"consumerId": other, "optionId": option["id"]}
        )
        self.assertEqual(404, status)
        self.assertEqual("PP_OPTION_INVALID", error["error"])
        self.assertEqual("OFFERED", self.store.me(other)["status"])

    def test_unknown_cookie_is_cleared_without_replacing_an_identity(self):
        self.cookie = "pp_session=unknown"
        status, result = self.request("POST", "/api/session", {})
        self.assertEqual(200, status)
        self.assertIsNone(result["consumerId"])
        self.assertFalse(result["authenticated"])
        with self.store.connection() as db:
            self.assertEqual(0, db.execute("SELECT count(*) FROM consumers").fetchone()[0])

    def test_account_authentication_gates_selection_and_preserves_guest_options(self):
        _, session = self.request("POST", "/api/session", {})
        consumer = session["consumerId"]
        batch = self.store.options(consumer)
        self.assertEqual(401, self.request("POST", "/api/pp/options", {})[0])
        status, account = self.request(
            "POST",
            "/api/auth/register",
            {"username": "linked.account", "password": "Correct horse battery 2026!"},
        )
        self.assertEqual(201, status)
        self.assertEqual(consumer, account["consumerId"])
        self.assertEqual(batch, self.request("POST", "/api/pp/options", {})[1])
        self.assertEqual(200, self.request("POST", "/api/auth/logout", {})[0])
        status, login_error = self.request(
            "POST",
            "/api/auth/login",
            {"username": "linked.account", "password": "Wrong password 2026!"},
        )
        self.assertEqual(401, status)
        self.assertEqual("PP_CREDENTIALS_INVALID", login_error["error"])
        status, login = self.request(
            "POST",
            "/api/auth/login",
            {"username": "linked.account", "password": "Correct horse battery 2026!"},
        )
        self.assertEqual(200, status)
        self.assertEqual(consumer, login["consumerId"])
        self.assertEqual(batch, self.request("POST", "/api/pp/options", {})[1])

    def test_engine_history_is_scoped_to_authenticated_account(self):
        self.request("POST", "/api/session", {})
        owner, _ = self.store.create_consumer()
        owner_batch = self.store.options(owner)
        self.store.register_account(
            owner, "history.owner", "Owner password secure 2026!", None
        )
        self.assertEqual(
            200,
            self.request(
                "POST",
                "/api/auth/login",
                {"username": "history.owner", "password": "Owner password secure 2026!"},
            )[0],
        )
        owner_history = self.request("GET", "/api/pp/history")[1]["events"]
        self.assertEqual(10, len(owner_history))
        self.assertEqual(
            {option["number"] for option in owner_batch["options"]},
            {event["detail"]["ppNumber"] for event in owner_history},
        )

        other, _ = self.store.create_consumer()
        other_batch = self.store.options(other)
        self.store.register_account(
            other, "history.other", "Other password secure 2026!", None
        )
        status, logged_in = self.request(
            "POST",
            "/api/auth/login",
            {"username": "history.other", "password": "Other password secure 2026!"},
        )
        self.assertEqual(200, status)
        self.assertEqual(other, logged_in["consumerId"])
        other_history = self.request("GET", "/api/pp/history")[1]["events"]
        self.assertEqual(
            {option["number"] for option in other_batch["options"]},
            {event["detail"]["ppNumber"] for event in other_history},
        )
        self.assertTrue(
            {event["detail"]["ppNumber"] for event in owner_history}.isdisjoint(
                event["detail"]["ppNumber"] for event in other_history
            )
        )

    def test_memory_api_requires_auth_and_supports_private_crud(self):
        status, guest = self.request("POST", "/api/session", {})
        self.assertEqual(200, status)
        self.assertFalse(guest["authenticated"])
        self.assertEqual(401, self.request("GET", "/api/memory")[0])
        self.assertEqual(401, self.request(
            "POST", "/api/memory/save",
            {"title": "Private", "content": "Do not expose", "tags": []},
        )[0])
        status, account = self.request(
            "POST", "/api/auth/register",
            {"username": "memory.owner", "password": "Memory owner secure 2026!"},
        )
        self.assertEqual(201, status)
        self.assertEqual(0, len(self.request("GET", "/api/memory")[1]["entries"]))
        status, created = self.request(
            "POST", "/api/memory/save",
            {"title": "Private memo", "content": "Only my account can read this.", "tags": ["idea"]},
        )
        self.assertEqual(200, status)
        self.assertEqual(["idea"], created["tags"])
        self.assertEqual([created], self.request("GET", "/api/memory")[1]["entries"])
        status, updated = self.request(
            "POST", "/api/memory/save",
            {"id": created["id"], "title": "Updated memo", "content": "Updated body", "tags": []},
        )
        self.assertEqual(200, status)
        self.assertEqual(created["createdAt"], updated["createdAt"])
        self.assertEqual("Updated body", self.request("GET", "/api/memory")[1]["entries"][0]["content"])
        status, invalid = self.request(
            "POST", "/api/memory/save",
            {"title": "Invalid", "content": "Content", "tags": [], "consumerId": account["consumerId"]},
        )
        self.assertEqual(400, status)
        self.assertEqual("PP_MEMORY_INVALID", invalid["error"])
        status, deleted = self.request("POST", "/api/memory/delete", {"id": created["id"]})
        self.assertEqual(200, status)
        self.assertTrue(deleted["deleted"])
        self.assertEqual([], self.request("GET", "/api/memory")[1]["entries"])
        self.assertEqual(200, self.request("POST", "/api/auth/logout", {})[0])
        self.assertEqual(401, self.request("GET", "/api/memory")[0])
        with self.store.connection() as db:
            rows = db.execute(
                """SELECT event,detail FROM audit WHERE event LIKE 'MEMORY_%'
                   ORDER BY sequence"""
            ).fetchall()
        self.assertEqual(["MEMORY_CREATED", "MEMORY_UPDATED", "MEMORY_DELETED"],
                         [row["event"] for row in rows])
        audit_json = json.dumps([dict(row) for row in rows])
        self.assertNotIn("Only my account can read this.", audit_json)
        self.assertNotIn("Updated body", audit_json)
        self.assertTrue(all(set(json.loads(row["detail"])) == {"memoryId"} for row in rows))

    def test_login_rate_limit_is_returned_as_http_429(self):
        self.request("POST", "/api/session", {})
        self.request(
            "POST",
            "/api/auth/register",
            {"username": "throttle.api", "password": "Correct horse battery 2026!"},
        )
        self.assertEqual(200, self.request("POST", "/api/auth/logout", {})[0])
        for _ in range(4):
            status, error = self.request(
                "POST",
                "/api/auth/login",
                {"username": "throttle.api", "password": "Wrong password 2026!"},
            )
            self.assertEqual(401, status)
            self.assertEqual("PP_CREDENTIALS_INVALID", error["error"])
        status, error = self.request(
            "POST",
            "/api/auth/login",
            {"username": "throttle.api", "password": "Wrong password 2026!"},
        )
        self.assertEqual(429, status)
        self.assertEqual("PP_LOGIN_RATE_LIMITED", error["error"])


if __name__ == "__main__":
    unittest.main()

