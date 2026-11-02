from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from microsoft_mail import MicrosoftMailer, MicrosoftMailError, SCOPES, build_application
from server import Store, deliver_confirmation, process_confirmation, smtp_configuration


CLIENT_ID = "12345678-1234-1234-1234-123456789abc"
SENDER = "synthetic@hotmail.com"


class MicrosoftMailTests(unittest.TestCase):
    def make_mailer(self, app):
        with patch("microsoft_mail.build_application", return_value=app):
            return MicrosoftMailer(CLIENT_ID, SENDER, Path("unused.bin"))

    def test_invalid_client_id_is_rejected_before_accessing_cache_or_network(self):
        with patch("microsoft_mail.build_application") as build:
            for client_id in ("", "weet ik niet", "../secret", "not-a-client-id"):
                with self.assertRaises(MicrosoftMailError):
                    MicrosoftMailer(client_id, SENDER, Path("unused.bin"))
            build.assert_not_called()

    def test_token_is_silently_renewed_for_exact_sender_and_not_printed(self):
        app = MagicMock()
        account = {"username": SENDER}
        app.get_accounts.return_value = [account]
        app.acquire_token_silent.return_value = {"access_token": "synthetic-token"}
        mailer = self.make_mailer(app)
        self.assertEqual("synthetic-token", mailer.access_token())
        app.get_accounts.assert_called_once_with(username=SENDER)
        app.acquire_token_silent.assert_called_once_with(SCOPES, account=account)
        for accounts, result in (([], None), ([account, account], None),
                                 ([account], None), ([account], {"error": "synthetic-secret"})):
            app.get_accounts.return_value = accounts
            app.acquire_token_silent.return_value = result
            with self.assertRaises(MicrosoftMailError) as caught:
                mailer.access_token()
            self.assertNotIn("synthetic-secret", str(caught.exception))

    def test_device_login_uses_microsoft_scopes_and_checks_sender(self):
        app = MagicMock()
        app.initiate_device_flow.return_value = {"user_code": "TEST-CODE"}
        app.acquire_token_by_device_flow.return_value = {
            "access_token": "do-not-print",
            "id_token_claims": {"preferred_username": SENDER.upper()},
        }
        app.get_accounts.return_value = [{"username": SENDER}]
        app.acquire_token_silent.return_value = {"access_token": "do-not-print"}
        mailer = self.make_mailer(app)
        with patch("builtins.print") as output:
            mailer.login()
        app.initiate_device_flow.assert_called_once_with(scopes=SCOPES)
        self.assertNotIn("do-not-print", str(output.call_args_list))
        self.assertIn("microsoft.com/devicelogin", str(output.call_args_list))
        app.acquire_token_by_device_flow.return_value = {
            "access_token": "do-not-print", "id_token_claims": {
                "preferred_username": "wrong@hotmail.com", "oid": "wrong-account",
            },
        }
        app.get_accounts.return_value = [
            {"local_account_id": "wrong-account"}, {"local_account_id": "untouched"},
        ]
        with patch("builtins.print"), self.assertRaises(MicrosoftMailError):
            mailer.login()
        app.remove_account.assert_called_once_with({"local_account_id": "wrong-account"})

    def test_device_denial_and_network_errors_do_not_expose_provider_details(self):
        app = MagicMock()
        mailer = self.make_mailer(app)
        app.initiate_device_flow.return_value = {"error_description": "private provider detail"}
        with self.assertRaises(MicrosoftMailError) as caught:
            mailer.login()
        self.assertNotIn("private provider detail", str(caught.exception))
        app.initiate_device_flow.return_value = {"user_code": "TEST-CODE"}
        app.acquire_token_by_device_flow.return_value = {"error": "access_denied"}
        with patch("builtins.print"), self.assertRaises(MicrosoftMailError):
            mailer.login()
        app.get_accounts.side_effect = OSError("secret-token")
        with self.assertRaises(MicrosoftMailError) as caught:
            mailer.access_token()
        self.assertNotIn("secret-token", str(caught.exception))

    @unittest.skipUnless(sys.platform == "win32", "Windows encrypted persistence")
    def test_dpapi_cache_roundtrip_and_public_client_configuration(self):
        from msal_extensions import FilePersistenceWithDataProtection

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tokens.bin"
            persistence = FilePersistenceWithDataProtection(str(path))
            persistence.save("synthetic-test-cache")
            self.assertTrue(persistence.is_encrypted)
            self.assertNotIn(b"synthetic-test-cache", path.read_bytes())
            self.assertEqual("synthetic-test-cache", persistence.load())
            with patch("msal.PublicClientApplication") as public_client:
                build_application(CLIENT_ID, path)
                self.assertEqual(CLIENT_ID, public_client.call_args.args[0])
                self.assertEqual("https://login.microsoftonline.com/consumers",
                                 public_client.call_args.kwargs["authority"])
            with patch("microsoft_mail.sys.platform", "linux"):
                with self.assertRaises(MicrosoftMailError):
                    build_application(CLIENT_ID, path)

    def test_microsoft_configuration_restricts_host_tls_and_password(self):
        env = {"PP_SMTP_AUTH": "microsoft", "PP_SMTP_FROM": SENDER,
               "PP_MICROSOFT_CLIENT_ID": CLIENT_ID}
        with patch.dict(os.environ, env, clear=True), patch("server.configured_mailer") as build:
            config = smtp_configuration()
            self.assertEqual("smtp-mail.outlook.com", config["host"])
            self.assertEqual(587, config["port"])
            self.assertEqual("starttls", config["mode"])
            build.assert_called_once_with(SENDER)
            build.return_value.access_token.assert_called_once()
        for field, value in (("PP_SMTP_HOST", "untrusted.example"),
                             ("PP_SMTP_TLS", "ssl"), ("PP_SMTP_PORT", "465"),
                             ("PP_SMTP_PASSWORD", "must-not-use"),
                             ("PP_SMTP_USER", "other@hotmail.com")):
            with patch.dict(os.environ, {**env, field: value}, clear=True):
                with self.assertRaises(ValueError):
                    smtp_configuration()

    def test_smtp_uses_xoauth2_after_tls_not_password_login(self):
        config = {"host": "smtp-mail.outlook.com", "port": 587, "mode": "starttls",
                  "sender": SENDER, "user": "", "password": "", "microsoft": MagicMock()}
        config["microsoft"].access_token.return_value = "synthetic-token"
        with patch("server.smtplib.SMTP") as factory, patch("server.ssl.create_default_context"):
            smtp = factory.return_value.__enter__.return_value
            smtp.send_message.return_value = {}
            deliver_confirmation(config, {"consumer_id": "synthetic", "number": "1234567890",
                                           "created_at": "2026-10-26", "recipient": "to@example.test"})
            smtp.starttls.assert_called_once()
            smtp.login.assert_not_called()
            self.assertLess(str(smtp.mock_calls).index("starttls"), str(smtp.mock_calls).index("auth("))
            mechanism, callback = smtp.auth.call_args.args
            self.assertEqual("XOAUTH2", mechanism)
            self.assertEqual(f"user={SENDER}\x01auth=Bearer synthetic-token\x01\x01", callback())
            self.assertEqual("", callback(b"challenge"))

    def test_authorization_loss_keeps_selection_and_does_not_send(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "test.sqlite3")
            consumer, _ = store.create_consumer()
            option = store.options(consumer)["options"][0]["id"]
            store.select(consumer, option, email="to@example.test")
            provider = MagicMock()
            provider.access_token.side_effect = MicrosoftMailError("synthetic")
            with patch("server.smtplib.SMTP") as smtp:
                self.assertTrue(process_confirmation(store, {"microsoft": provider}))
                smtp.assert_not_called()
            self.assertEqual("ACTIVE", store.me(consumer)["status"])
            self.assertEqual("FAILED", store.mail_status(consumer)["status"])


if __name__ == "__main__":
    unittest.main()
