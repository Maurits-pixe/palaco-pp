import os
import sys
import unittest
from unittest.mock import Mock, patch

from start_microsoft import main


CLIENT_ID = "12345678-1234-1234-1234-123456789abc"
SENDER = "synthetic@hotmail.com"


class MicrosoftStarterTests(unittest.TestCase):
    def setUp(self):
        self.argv = ["start_microsoft.py", "--client-id", CLIENT_ID, "--sender", SENDER]

    def test_login_only_preserves_parent_environment_and_running_server(self):
        original = {"PP_SMTP_AUTH": "password", "PP_SMTP_PASSWORD": "synthetic-secret"}
        with patch.dict(os.environ, original, clear=True), \
                patch.object(sys, "argv", self.argv + ["--login-only"]), \
                patch("start_microsoft.sys.platform", "win32"), \
                patch("start_microsoft.socket.socket") as socket, \
                patch("start_microsoft.subprocess.run", return_value=Mock(returncode=0)) as run, \
                patch("builtins.print"):
            self.assertEqual(0, main())
            socket.assert_not_called()
            self.assertEqual(2, run.call_count)
            self.assertIn("--microsoft-login", run.call_args.args[0])
            environment = run.call_args.kwargs["env"]
            self.assertEqual("microsoft", environment["PP_SMTP_AUTH"])
            self.assertEqual(SENDER, environment["PP_SMTP_FROM"])
            self.assertEqual(CLIENT_ID, environment["PP_MICROSOFT_CLIENT_ID"])
            self.assertEqual("smtp-mail.outlook.com", environment["PP_SMTP_HOST"])
            self.assertEqual("starttls", environment["PP_SMTP_TLS"])
            self.assertNotIn("PP_SMTP_PASSWORD", environment)
            self.assertNotIn("PP_SMTP_USER", environment)
            self.assertEqual(original, dict(os.environ))

    def test_first_start_logs_in_before_server_and_reuses_current_python(self):
        with patch.object(sys, "argv", self.argv), \
                patch("start_microsoft.sys.platform", "win32"), \
                patch("start_microsoft.socket.socket"), \
                patch("start_microsoft.Path.is_file", return_value=False), \
                patch("start_microsoft.subprocess.run", return_value=Mock(returncode=0)) as run, \
                patch("builtins.print"):
            self.assertEqual(0, main())
            self.assertEqual(3, run.call_count)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertIn("--microsoft-login", commands[1])
            self.assertEqual(["--port", "8765"], commands[2][-2:])
            self.assertTrue(all(command[0] == sys.executable for command in commands))

    def test_existing_cache_skips_interactive_login_unless_reauthenticate(self):
        for flags, count in (([], 2), (["--reauthenticate"], 3)):
            with self.subTest(flags=flags), patch.object(sys, "argv", self.argv + flags), \
                    patch("start_microsoft.sys.platform", "win32"), \
                    patch("start_microsoft.socket.socket"), \
                    patch("start_microsoft.Path.is_file", return_value=True), \
                    patch("start_microsoft.subprocess.run", return_value=Mock(returncode=0)) as run, \
                    patch("builtins.print"):
                self.assertEqual(0, main())
                self.assertEqual(count, run.call_count)

    def test_occupied_port_blocks_before_signin_and_never_stops_processes(self):
        with patch.object(sys, "argv", self.argv), \
                patch("start_microsoft.sys.platform", "win32"), \
                patch("start_microsoft.socket.socket") as socket, \
                patch("start_microsoft.subprocess.run") as run, patch("builtins.print"):
            socket.return_value.__enter__.return_value.bind.side_effect = OSError()
            self.assertEqual(1, main())
            run.assert_not_called()

    def test_failures_are_explicit_and_block_following_steps(self):
        for returncodes in ([1], [0, 1], [0, 0, 1]):
            with self.subTest(returncodes=returncodes), patch.object(sys, "argv", self.argv), \
                    patch("start_microsoft.sys.platform", "win32"), \
                    patch("start_microsoft.socket.socket"), \
                    patch("start_microsoft.Path.is_file", return_value=False), \
                    patch("start_microsoft.subprocess.run",
                          side_effect=[Mock(returncode=code) for code in returncodes]) as run, \
                    patch("builtins.print"):
                self.assertEqual(1, main())
                self.assertEqual(len(returncodes), run.call_count)

    def test_invalid_input_is_rejected_without_subprocess(self):
        for options in (["--client-id", "invalid", "--sender", SENDER],
                        ["--client-id", CLIENT_ID, "--sender", "invalid"],
                        ["--client-id", CLIENT_ID, "--sender", SENDER, "--port", "0"]):
            with self.subTest(options=options), \
                    patch.object(sys, "argv", ["start_microsoft.py", *options]), \
                    patch("start_microsoft.subprocess.run") as run, \
                    patch("sys.stderr"), self.assertRaises(SystemExit):
                main()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
