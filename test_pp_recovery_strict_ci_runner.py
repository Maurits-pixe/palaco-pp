"""Synthetic unit checks for CI's fail-closed test-result policy."""
from contextlib import redirect_stdout
from io import StringIO
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch
import unittest

from pp_recovery_strict_ci_runner import (SUITES, loaded_test_ids, run,
    verify_suite_origin, verify_critical_source_integrity, verify_test_source_integrity, TrackingTextTestResult)
from pp_recovery_ci_inventory import CRITICAL_MODULES, ROOT


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
        result.started_test_ids = ["SYNTHETIC_ID"] * len(SUITES)
        inventory = {
            "authorization": "HOLD", "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID"] for name in SUITES},
            "testSourceSha256BySuite": {name: hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest() for name in SUITES},
            "criticalSourceSha256ByModule": {name: hashlib.sha256(
                (ROOT / f"{name}.py").read_bytes()).hexdigest()
                for name in CRITICAL_MODULES},
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
            "testSourceSha256BySuite": {name: hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest() for name in SUITES},
            "criticalSourceSha256ByModule": {name: hashlib.sha256(
                (ROOT / f"{name}.py").read_bytes()).hexdigest()
                for name in CRITICAL_MODULES},
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
            "testSourceSha256BySuite": {name: hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest() for name in SUITES},
            "criticalSourceSha256ByModule": {name: hashlib.sha256(
                (ROOT / f"{name}.py").read_bytes()).hexdigest()
                for name in CRITICAL_MODULES},
        }
        result = unittest.TestResult()
        result.testsRun = 1
        result.started_test_ids = ["SYNTHETIC_ID"] * len(SUITES)
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.defaultTestLoader.loadTestsFromName",
                       side_effect=lambda _: unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])):
                with patch("pp_recovery_strict_ci_runner.loaded_test_ids", return_value=["SYNTHETIC_ID"]):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run", return_value=result):
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn("INCOMPLETE_OR_FAILED", log.getvalue())

    def test_tracking_result_records_exact_test_ids(self):
        class SyntheticCase(unittest.TestCase):
            def test_hold(self):
                self.assertEqual("HOLD", "HOLD")
        stream = StringIO()
        case = SyntheticCase("test_hold")
        result = TrackingTextTestResult(stream, True, 2)
        result.startTest(case)
        result.stopTest(case)
        self.assertEqual([case.id()], result.started_test_ids)
        self.assertEqual(1, result.testsRun)

    def test_substituted_executed_id_is_rejected_despite_matching_count(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        result = unittest.TestResult()
        total = sum(inventory["declaredTestMethodsBySuite"].values())
        result.testsRun = total
        expected = [test for name in SUITES
                    for test in inventory["declaredTestIdsBySuite"][name]]
        result.started_test_ids = expected[:-1] + ["test_fake.Swapped.test_fake"]
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("EXECUTED_TEST_ID_MISMATCH", log.getvalue())

    def test_missing_execution_identity_records_fail_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        result = unittest.TestResult()
        result.testsRun = sum(inventory["declaredTestMethodsBySuite"].values())
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("EXECUTED_TEST_ID_MISMATCH", log.getvalue())

    def test_same_count_with_substituted_method_id_fails_closed(self):
        inventory = {
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["EXPECTED_TEST"] for name in SUITES},
            "testSourceSha256BySuite": {name: hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest() for name in SUITES},
            "criticalSourceSha256ByModule": {name: hashlib.sha256(
                (ROOT / f"{name}.py").read_bytes()).hexdigest()
                for name in CRITICAL_MODULES},
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

    def test_critical_module_digest_verification(self):
        expected = {
            name: hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest()
            for name in CRITICAL_MODULES
        }
        self.assertTrue(verify_critical_source_integrity(expected))
        changed = dict(expected)
        changed[CRITICAL_MODULES[0]] = "0" * 64
        self.assertFalse(verify_critical_source_integrity(changed))
        self.assertFalse(verify_critical_source_integrity({}))

    def test_critical_module_tampering_after_inventory_rejected(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            expected = {}
            for name in CRITICAL_MODULES:
                content = b"AUTHORIZATION = 'HOLD'\n"
                (root / f"{name}.py").write_bytes(content)
                expected[name] = hashlib.sha256(content).hexdigest()
            self.assertTrue(verify_critical_source_integrity(expected, root))
            (root / f"{CRITICAL_MODULES[0]}.py").write_bytes(
                b"AUTHORIZATION = 'ALLOW'\n"
            )
            self.assertFalse(verify_critical_source_integrity(expected, root))

    def test_missing_critical_source_hash_inventory_rejected(self):
        inventory = {
            "authorization": "HOLD", "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID"] for name in SUITES},
            "testSourceSha256BySuite": {name: hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest() for name in SUITES},
        }
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with redirect_stdout(StringIO()) as log:
                self.assertEqual(1, run())
            self.assertIn("CRITICAL_SOURCE_INTEGRITY_FAILED", log.getvalue())

    def test_test_source_digests_detect_change_and_symlink(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = b"import unittest\n"
            hashes = {}
            for name in SUITES:
                path = root / f"{name}.py"
                path.write_bytes(baseline)
                hashes[name] = hashlib.sha256(baseline).hexdigest()
            self.assertTrue(verify_test_source_integrity(hashes, root))
            target = root / f"{SUITES[0]}.py"
            target.write_bytes(baseline + b"# tampered\n")
            self.assertFalse(verify_test_source_integrity(hashes, root))
            target.unlink()
            replacement = root / "other.py"
            replacement.write_bytes(baseline)
            target.symlink_to(replacement)
            self.assertFalse(verify_test_source_integrity(hashes, root))

    def test_test_source_digests_reject_incomplete_map(self):
        digests = {name: hashlib.sha256(
            (ROOT / f"{name}.py").read_bytes()
        ).hexdigest() for name in SUITES}
        self.assertTrue(verify_test_source_integrity(digests))
        self.assertFalse(verify_test_source_integrity({}))
        self.assertFalse(verify_test_source_integrity({
            **digests, "extra_unreviewed": "a" * 64,
        }))
        self.assertFalse(verify_test_source_integrity({
            **digests, SUITES[0]: "not-a-digest",
        }))

    def test_test_source_changed_during_load_rejects_before_execution(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.verify_test_source_integrity",
                       side_effect=[True, False]) as integrity:
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run") as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("TEST_SOURCE_CHANGED_DURING_LOAD", log.getvalue())
                    self.assertEqual(2, integrity.call_count)
                    execute.assert_not_called()

    def test_test_source_changed_during_run_rejects_even_successful_tests(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        result = unittest.TestResult()
        result.testsRun = sum(inventory["declaredTestMethodsBySuite"].values())
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.verify_test_source_integrity",
                       side_effect=[True, True, False]) as integrity:
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           return_value=result) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("TEST_SOURCE_CHANGED_DURING_RUN", log.getvalue())
                    self.assertEqual(3, integrity.call_count)
                    execute.assert_called_once()

    def test_critical_source_changed_during_load_blocks_execution(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.verify_critical_source_integrity",
                       side_effect=[True, False]) as integrity:
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run") as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("CRITICAL_SOURCE_CHANGED_DURING_LOAD", log.getvalue())
                    self.assertEqual(2, integrity.call_count)
                    execute.assert_not_called()

    def test_critical_source_changed_during_run_rejects_success_result(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        result = unittest.TestResult()
        result.testsRun = sum(inventory["declaredTestMethodsBySuite"].values())
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.verify_critical_source_integrity",
                       side_effect=[True, True, False]) as integrity:
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           return_value=result) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("CRITICAL_SOURCE_CHANGED_DURING_RUN", log.getvalue())
                    self.assertEqual(3, integrity.call_count)
                    execute.assert_called_once()

    @patch("pp_recovery_strict_ci_runner.verify_suite_origin", return_value=True)
    def test_no_false_pass_on_zero_executed(self, _origin):
        result = unittest.TestResult()
        inventory = {
            "authorization": "HOLD", "accessDecision": "DENY",
            "declaredTestMethodsBySuite": {name: 1 for name in SUITES},
            "declaredTestIdsBySuite": {name: ["SYNTHETIC_ID"] for name in SUITES},
            "testSourceSha256BySuite": {name: hashlib.sha256((ROOT / f"{name}.py").read_bytes()).hexdigest() for name in SUITES},
            "criticalSourceSha256ByModule": {name: hashlib.sha256(
                (ROOT / f"{name}.py").read_bytes()).hexdigest()
                for name in CRITICAL_MODULES},
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
