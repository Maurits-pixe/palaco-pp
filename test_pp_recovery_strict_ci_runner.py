"""Synthetic unit checks for CI's fail-closed test-result policy."""
from contextlib import redirect_stdout
from io import StringIO
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch
import unittest

from pp_recovery_strict_ci_runner import SUITES, loaded_test_ids, run, verify_suite_origin


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

    @patch("pp_recovery_strict_ci_runner.verify_suite_origin", return_value=True)
    def test_reject_skipped_security_tests(self, _origin):
        result = unittest.TestResult()
        result.testsRun = len(SUITES)
        result.skipped.append((None, "dependency missing"))
        inventory = {
            "authorization": "HOLD", "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID"] for name in SUITES},
            "testSourceSha256BySuite": {name: "a" * 64 for name in SUITES},
        }
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                       side_effect=lambda _: unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])):
                with patch("pp_recovery_strict_ci_runner.loaded_test_ids", return_value=["SYNTHETIC_ID"]):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run", return_value=result):
                        with redirect_stdout(StringIO()):
                            self.assertEqual(1, run())

    def test_loaded_count_mismatch_is_rejected_before_execution(self):
        inventory = {
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 2 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID_1", "SYNTHETIC_ID_2"] for name in SUITES},
            "testSourceSha256BySuite": {name: "a" * 64 for name in SUITES},
        }
        one = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                       return_value=one):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run") as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("LOADED_TEST_COUNT_MISMATCH", log.getvalue())
                    execute.assert_not_called()

    def test_declared_count_map_missing_is_rejected(self):
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value={"authorization": "HOLD", "accessDecision": "DENY"}):
            with redirect_stdout(StringIO()) as log:
                self.assertEqual(1, run())
            self.assertIn("DECLARED_COUNTS_INVALID", log.getvalue())

    @patch("pp_recovery_strict_ci_runner.verify_suite_origin", return_value=True)
    def test_short_executed_count_cannot_report_pass(self, _origin):
        inventory = {
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID"] for name in SUITES},
            "testSourceSha256BySuite": {name: "a" * 64 for name in SUITES},
        }
        result = unittest.TestResult()
        result.testsRun = 1
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                       side_effect=lambda _: unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])):
                with patch("pp_recovery_strict_ci_runner.loaded_test_ids", return_value=["SYNTHETIC_ID"]):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run", return_value=result):
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn("INCOMPLETE_OR_FAILED", log.getvalue())

    def test_same_count_with_substituted_method_id_fails_closed(self):
        inventory = {
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["EXPECTED_TEST"] for name in SUITES},
            "testSourceSha256BySuite": {name: "a" * 64 for name in SUITES},
        }
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                       side_effect=lambda _: unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])):
                with patch("pp_recovery_strict_ci_runner.loaded_test_ids",
                           return_value=["SUBSTITUTED_TEST"]):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run") as execute:
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn("LOADED_TEST_ID_MISMATCH", log.getvalue())
                        execute.assert_not_called()

    def test_missing_declared_id_inventory_fails_closed(self):
        inventory = {
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
        }
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with redirect_stdout(StringIO()) as log:
                self.assertEqual(1, run())
            self.assertIn("DECLARED_IDS_INVALID", log.getvalue())

    def test_nested_suite_identity_flattening(self):
        class SyntheticTest(unittest.TestCase):
            def test_denied(self):
                self.assertEqual("HOLD", "HOLD")
        case = SyntheticTest("test_denied")
        self.assertEqual([case.id()], loaded_test_ids(
            unittest.TestSuite([unittest.TestSuite([case])])
        ))

    def test_reject_unrelated_or_missing_module_origin(self):
        self.assertFalse(verify_suite_origin("test_unexpected_suite"))
        self.assertFalse(verify_suite_origin("test_review_044_absent"))

    def test_shadowed_module_from_other_directory_is_rejected(self):
        name = SUITES[0]
        with TemporaryDirectory() as temp:
            external = Path(temp) / f"{name}.py"
            external.write_text("def synthetic(): pass\n", encoding="utf-8")
            shadow = ModuleType(name)
            shadow.__file__ = str(external)
            with patch.dict("sys.modules", {name: shadow}):
                self.assertFalse(verify_suite_origin(name))

    def test_real_registered_security_module_origin_is_accepted(self):
        name = "test_review_044_release_boundary_snapshot"
        __import__(name)
        from pp_recovery_ci_inventory import ROOT
        digest = hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest()
        self.assertTrue(verify_suite_origin(name, digest))
        self.assertFalse(verify_suite_origin(name, "f" * 64))

    def test_missing_source_hash_map_rejected(self):
        inventory = {
            "authorization": "HOLD", "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID"] for name in SUITES},
        }
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with redirect_stdout(StringIO()) as log:
                self.assertEqual(1, run())
            self.assertIn("SOURCE_HASHES_INVALID", log.getvalue())

    @patch("pp_recovery_strict_ci_runner.verify_suite_origin", return_value=True)
    def test_no_false_pass_on_zero_executed(self, _origin):
        result = unittest.TestResult()
        inventory = {
            "authorization": "HOLD", "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID"] for name in SUITES},
            "testSourceSha256BySuite": {name: "a" * 64 for name in SUITES},
        }
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                       side_effect=lambda _: unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])):
                with patch("pp_recovery_strict_ci_runner.loaded_test_ids", return_value=["SYNTHETIC_ID"]):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run", return_value=result):
                        with redirect_stdout(StringIO()):
                            self.assertEqual(1, run())


if __name__ == "__main__":
    unittest.main()
