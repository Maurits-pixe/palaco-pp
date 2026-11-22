"""Synthetic unit checks for CI's fail-closed test-result policy."""
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
import unittest

from pp_recovery_strict_ci_runner import run


class StrictRunnerPolicyTests(unittest.TestCase):
    def test_reject_arguments(self):
        with redirect_stdout(StringIO()):
            self.assertEqual(2, run(["--unverified"]))

    def test_empty_suites_are_rejected(self):
        with patch(
            "pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
            return_value=unittest.TestSuite(),
        ), redirect_stdout(StringIO()):
            self.assertEqual(1, run())

    def test_reject_skipped_security_tests(self):
        result = unittest.TestResult()
        result.testsRun = 1
        result.skipped.append((None, "dependency missing"))
        with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                   return_value=unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run", return_value=result):
                with redirect_stdout(StringIO()):
                    self.assertEqual(1, run())

    def test_no_false_pass_on_zero_executed(self):
        result = unittest.TestResult()
        with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                   return_value=unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run", return_value=result):
                with redirect_stdout(StringIO()):
                    self.assertEqual(1, run())


if __name__ == "__main__":
    unittest.main()
