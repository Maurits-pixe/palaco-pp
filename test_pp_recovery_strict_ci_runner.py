"""Synthetic unit checks for CI's fail-closed test-result policy."""
import copy
from contextlib import redirect_stdout
from io import StringIO
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch
import unittest

from pp_recovery_strict_ci_runner import (SUITES, loaded_test_ids, loaded_test_objects, run,
    verify_suite_origin, verify_critical_source_integrity, verify_test_source_integrity,
    verify_imported_critical_module_origins, verify_loaded_test_class_bindings,
    snapshot_loaded_test_methods, verify_loaded_test_method_snapshot,
    snapshot_test_method_code, verify_test_method_code_snapshot,
    TrackingTextTestResult)
from pp_recovery_ci_inventory import CRITICAL_MODULES, ROOT

BOUNDARY_METADATA = {
    "schema": "palaco.pp.recovery-002-ci-inventory-observation.v1",
    "reference": "PP-RECOVERY-002",
    "coverageState": "ALL_SCOPED_FILES_PRESENT_NOT_EXECUTION_PROOF",
    "registeredSuites": len(SUITES),
    "criticalModules": len(CRITICAL_MODULES),
    "issuance": "NOT_AUTHORIZED",
    "deployment": "BLOCKED",
}


class StrictRunnerPolicyTests(unittest.TestCase):
    def test_unauthorized_issuance_or_unblocked_deployment_fails_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        for field, invalid in (("issuance", "AUTHORIZED"),
                               ("issuance", None),
                               ("deployment", "READY"),
                               ("deployment", None)):
            with self.subTest(field=field, invalid=invalid):
                inventory = audit_security_inventory(SUITES)
                inventory[field] = invalid
                with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                           return_value=inventory):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run") as execute:
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn("INVENTORY_AUTHORIZATION_INVALID", log.getvalue())
                        execute.assert_not_called()

    def test_mismatched_provenance_or_coverage_metadata_fails_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        cases = (
            ("schema", "unknown.schema"),
            ("reference", "OTHER-RECOVERY"),
            ("coverageState", "EXECUTION_PROVEN"),
            ("registeredSuites", len(SUITES) - 1),
            ("criticalModules", len(CRITICAL_MODULES) + 1),
        )
        for field, invalid in cases:
            with self.subTest(field=field):
                inventory = audit_security_inventory(SUITES)
                inventory[field] = invalid
                with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                           return_value=inventory):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run") as execute:
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn("INVENTORY_BOUNDARY_INVALID", log.getvalue())
                        execute.assert_not_called()

    def test_missing_boundary_field_fails_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        for field in ("issuance", "deployment", "schema", "coverageState"):
            with self.subTest(field=field):
                inventory = audit_security_inventory(SUITES)
                del inventory[field]
                with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                           return_value=inventory):
                    with redirect_stdout(StringIO()):
                        self.assertEqual(1, run())

    def test_critical_import_origin_valid_for_real_module(self):
        name = CRITICAL_MODULES[0]
        module = ModuleType(name)
        module.__file__ = str(ROOT / f"{name}.py")
        digests = {
            item: hashlib.sha256((ROOT / f"{item}.py").read_bytes()).hexdigest()
            for item in CRITICAL_MODULES
        }
        with patch.dict("sys.modules", {name: module}):
            self.assertTrue(verify_imported_critical_module_origins(digests))

    def test_shadowed_critical_import_with_same_bytes_is_rejected(self):
        name = CRITICAL_MODULES[0]
        digests = {
            item: hashlib.sha256((ROOT / f"{item}.py").read_bytes()).hexdigest()
            for item in CRITICAL_MODULES
        }
        with TemporaryDirectory() as temporary:
            external = Path(temporary) / f"{name}.py"
            external.write_bytes((ROOT / f"{name}.py").read_bytes())
            counterfeit = ModuleType(name)
            counterfeit.__file__ = str(external)
            with patch.dict("sys.modules", {name: counterfeit}):
                self.assertFalse(
                    verify_imported_critical_module_origins(digests)
                )

    def test_import_origin_absent_or_invalid_hash_map_fails_closed(self):
        name = CRITICAL_MODULES[0]
        digests = {
            item: hashlib.sha256((ROOT / f"{item}.py").read_bytes()).hexdigest()
            for item in CRITICAL_MODULES
        }
        counterfeit = ModuleType(name)
        with patch.dict("sys.modules", {name: counterfeit}):
            self.assertFalse(
                verify_imported_critical_module_origins(digests)
            )
        self.assertFalse(verify_imported_critical_module_origins({}))

    def test_shadowed_critical_import_blocks_runner_execution(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        name = CRITICAL_MODULES[0]
        with TemporaryDirectory() as temporary:
            external = Path(temporary) / f"{name}.py"
            external.write_bytes((ROOT / f"{name}.py").read_bytes())
            counterfeit = ModuleType(name)
            counterfeit.__file__ = str(external)
            with patch.dict("sys.modules", {name: counterfeit}):
                with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                           return_value=inventory):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run") as execute:
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn("CRITICAL_IMPORT_ORIGIN_MISMATCH", log.getvalue())
                        execute.assert_not_called()

    def test_critical_import_shadowed_during_run_fails_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        name = CRITICAL_MODULES[0]
        with TemporaryDirectory() as temporary:
            external = Path(temporary) / f"{name}.py"
            external.write_bytes((ROOT / f"{name}.py").read_bytes())
            counterfeit = ModuleType(name)
            counterfeit.__file__ = str(external)
            with patch.dict("sys.modules", {}):
                def inject_shadow(_suite):
                    import sys
                    sys.modules[name] = counterfeit
                    return unittest.TestResult()
                with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                           return_value=inventory):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                               side_effect=inject_shadow) as execute:
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn(
                            "CRITICAL_IMPORT_CHANGED_DURING_RUN",
                            log.getvalue(),
                        )
                        execute.assert_called_once()

    def test_same_origin_import_object_replacement_during_run_fails_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        import sys
        inventory = audit_security_inventory(SUITES)
        name = CRITICAL_MODULES[0]
        original = ModuleType(name)
        original.__file__ = str(ROOT / f"{name}.py")
        substitute = ModuleType(name)
        substitute.__file__ = original.__file__
        # Import real test suites before installing a synthetic module.
        # Otherwise Python's first suite import can fail at discovery
        # instead of exercising the intended post-run gate.
        for suite_name in SUITES:
            __import__(suite_name)
        with patch.dict("sys.modules", {name: original}):
            def replace_module(_suite):
                sys.modules[name] = substitute
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=replace_module) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn(
                        "CRITICAL_IMPORT_OBJECT_CHANGED_DURING_RUN",
                        log.getvalue(),
                    )
                    execute.assert_called_once()

    def test_critical_import_disappearing_during_run_fails_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        import sys
        inventory = audit_security_inventory(SUITES)
        name = CRITICAL_MODULES[0]
        original = ModuleType(name)
        original.__file__ = str(ROOT / f"{name}.py")
        # Import real test suites before installing a synthetic module.
        # Otherwise Python's first suite import can fail at discovery
        # instead of exercising the intended post-run gate.
        for suite_name in SUITES:
            __import__(suite_name)
        with patch.dict("sys.modules", {name: original}):
            def remove_module(_suite):
                sys.modules.pop(name, None)
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=remove_module):
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn(
                        "CRITICAL_IMPORT_OBJECT_CHANGED_DURING_RUN",
                        log.getvalue(),
                    )

    def test_security_suite_module_replacement_during_run_is_denied(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        import sys
        inventory = audit_security_inventory(SUITES)
        for suite_name in SUITES:
            __import__(suite_name)
        name = SUITES[0]
        original = sys.modules[name]
        substitute = ModuleType(name)
        substitute.__file__ = original.__file__
        with patch.dict("sys.modules", {name: original}):
            def replace_module(_suite):
                sys.modules[name] = substitute
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=replace_module) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn(
                        "TEST_IMPORT_OBJECT_CHANGED_DURING_RUN",
                        log.getvalue(),
                    )
                    execute.assert_called_once()

    def test_security_suite_module_disappearing_during_run_is_denied(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        import sys
        inventory = audit_security_inventory(SUITES)
        for suite_name in SUITES:
            __import__(suite_name)
        name = SUITES[0]
        original = sys.modules[name]
        with patch.dict("sys.modules", {name: original}):
            def remove_module(_suite):
                sys.modules.pop(name, None)
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=remove_module) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn(
                        "TEST_IMPORT_OBJECT_CHANGED_DURING_RUN",
                        log.getvalue(),
                    )
                    execute.assert_called_once()

    def test_security_suite_origin_changed_without_object_swap_is_denied(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        import sys
        inventory = audit_security_inventory(SUITES)
        for suite_name in SUITES:
            __import__(suite_name)
        name = SUITES[0]
        module = sys.modules[name]
        original_file = module.__file__
        with TemporaryDirectory() as temporary:
            external = Path(temporary) / f"{name}.py"
            external.write_bytes((ROOT / f"{name}.py").read_bytes())
            def redirect_origin(_suite):
                module.__file__ = str(external)
                return unittest.TestResult()
            try:
                with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                           return_value=inventory):
                    with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                               side_effect=redirect_origin) as execute:
                        with redirect_stdout(StringIO()) as log:
                            self.assertEqual(1, run())
                        self.assertIn(
                            "TEST_IMPORT_ORIGIN_CHANGED_DURING_RUN",
                            log.getvalue(),
                        )
                        execute.assert_called_once()
            finally:
                module.__file__ = original_file

    def test_real_loaded_security_classes_are_bound_to_suite_modules(self):
        for suite_name in SUITES:
            __import__(suite_name)
        cases = [
            case for suite_name in SUITES
            for case in loaded_test_objects(
                unittest.defaultTestLoader.loadTestsFromName(suite_name)
            )
        ]
        self.assertTrue(verify_loaded_test_class_bindings(cases))

    def test_same_name_unregistered_test_class_is_denied(self):
        import sys
        name = SUITES[0]
        module = __import__(name)
        case = loaded_test_objects(
            unittest.defaultTestLoader.loadTestsFromName(name)
        )[0]
        cls = type(case)
        replacement = type(cls.__name__, (unittest.TestCase,), {
            "__module__": name,
            case._testMethodName: lambda self: None,
        })
        self.assertEqual(cls.__name__, replacement.__name__)
        self.assertFalse(verify_loaded_test_class_bindings([replacement(
            case._testMethodName
        )]))
        with patch.object(module, cls.__name__, replacement):
            self.assertFalse(verify_loaded_test_class_bindings([case]))
        self.assertTrue(verify_loaded_test_class_bindings([case]))

    def test_security_test_class_rebinding_during_run_is_denied(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        for suite_name in SUITES:
            __import__(suite_name)
        name = SUITES[0]
        module = __import__(name)
        case = loaded_test_objects(
            unittest.defaultTestLoader.loadTestsFromName(name)
        )[0]
        cls = type(case)
        with patch.object(module, cls.__name__, cls):
            def swap_class(_suite):
                setattr(module, cls.__name__, unittest.TestCase)
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=swap_class) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn(
                        "TEST_CLASS_BINDING_CHANGED_DURING_RUN",
                        log.getvalue(),
                    )
                    execute.assert_called_once()

    def test_real_security_test_method_snapshots_are_stable(self):
        for name in SUITES:
            __import__(name)
        cases = [
            case for name in SUITES
            for case in loaded_test_objects(
                unittest.defaultTestLoader.loadTestsFromName(name)
            )
        ]
        snapshot = snapshot_loaded_test_methods(cases)
        self.assertIsNotNone(snapshot)
        self.assertTrue(verify_loaded_test_method_snapshot(snapshot))

    def test_instance_overridden_test_method_is_denied(self):
        name = SUITES[0]
        __import__(name)
        case = loaded_test_objects(
            unittest.defaultTestLoader.loadTestsFromName(name)
        )[0]
        with patch.object(case, case._testMethodName, lambda: None):
            self.assertIsNone(snapshot_loaded_test_methods([case]))

    def test_class_method_rebinding_during_execution_is_denied(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        for name in SUITES:
            __import__(name)
        case = loaded_test_objects(
            unittest.defaultTestLoader.loadTestsFromName(SUITES[0])
        )[0]
        cls = type(case)
        method = case._testMethodName
        original = vars(cls)[method]
        def substitute(self):
            return None
        substitute.__module__ = cls.__module__
        with patch.object(cls, method, original):
            def swap(_suite):
                setattr(cls, method, substitute)
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=swap) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("TEST_METHOD_CHANGED_DURING_RUN", log.getvalue())
                    execute.assert_called_once()

    def test_class_method_deletion_during_execution_is_denied(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        for name in SUITES:
            __import__(name)
        case = loaded_test_objects(
            unittest.defaultTestLoader.loadTestsFromName(SUITES[0])
        )[0]
        cls = type(case)
        method = case._testMethodName
        original = vars(cls)[method]
        try:
            def delete(_suite):
                delattr(cls, method)
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=delete) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("TEST_METHOD_CHANGED_DURING_RUN", log.getvalue())
                    execute.assert_called_once()
        finally:
            setattr(cls, method, original)

    def test_test_method_code_snapshot_accepts_authentic_methods(self):
        for name in SUITES:
            __import__(name)
        cases = [
            case for name in SUITES
            for case in loaded_test_objects(
                unittest.defaultTestLoader.loadTestsFromName(name)
            )
        ]
        methods = snapshot_loaded_test_methods(cases)
        snapshot = snapshot_test_method_code(methods)
        self.assertIsNotNone(snapshot)
        self.assertTrue(verify_test_method_code_snapshot(snapshot))

    def test_in_place_code_replacement_during_run_fails_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        for name in SUITES:
            __import__(name)
        case = loaded_test_objects(
            unittest.defaultTestLoader.loadTestsFromName(SUITES[0])
        )[0]
        function = vars(type(case))[case._testMethodName]
        original_code = function.__code__
        # Replacing __code__ does not change the function or class identity.
        def replacement(self):
            return None
        try:
            def swap_code(_suite):
                function.__code__ = replacement.__code__
                return unittest.TestResult()
            with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                       return_value=inventory):
                with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                           side_effect=swap_code) as execute:
                    with redirect_stdout(StringIO()) as log:
                        self.assertEqual(1, run())
                    self.assertIn("TEST_CODE_CHANGED_DURING_RUN", log.getvalue())
                    execute.assert_called_once()
        finally:
            function.__code__ = original_code

    def test_code_snapshot_rejects_missing_or_invalid_metadata(self):
        self.assertIsNone(snapshot_test_method_code({}))
        self.assertFalse(verify_test_method_code_snapshot(None))
        self.assertFalse(verify_test_method_code_snapshot({}))
        self.assertFalse(verify_test_method_code_snapshot({
            ("Fake", "test_guard"): ("not-a-function", None)
        }))

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
        result.stopped_test_ids = ["SYNTHETIC_ID"] * len(SUITES)
        result.test_outcome_events = [("success", "SYNTHETIC_ID")] * len(SUITES)
        result.test_event_trace = [
            event for _ in SUITES
            for event in (
                ("start", "SYNTHETIC_ID"),
                ("success", "SYNTHETIC_ID"),
                ("stop", "SYNTHETIC_ID"),
            )
        ]
        result.test_lifecycle_events = [
            item
            for _ in SUITES
            for item in (("start", "SYNTHETIC_ID"), ("stop", "SYNTHETIC_ID"))
        ]
        inventory = {
            **BOUNDARY_METADATA, "authorization": "HOLD", "accessDecision": "DENY",
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
            **BOUNDARY_METADATA, "authorization": "HOLD",
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
                   return_value={**BOUNDARY_METADATA, "authorization": "HOLD", "accessDecision": "DENY"}):
            with redirect_stdout(StringIO()) as log:
                self.assertEqual(1, run())
            self.assertIn("DECLARED_COUNTS_INVALID", log.getvalue())

    @patch("pp_recovery_strict_ci_runner.verify_suite_origin", return_value=True)
    @patch("pp_recovery_strict_ci_runner.verify_loaded_test_class_bindings", return_value=True)
    @patch("pp_recovery_strict_ci_runner.snapshot_loaded_test_methods", return_value={})
    @patch("pp_recovery_strict_ci_runner.verify_loaded_test_method_snapshot", return_value=True)
    @patch("pp_recovery_strict_ci_runner.snapshot_test_method_code", return_value={})
    @patch("pp_recovery_strict_ci_runner.verify_test_method_code_snapshot", return_value=True)
    def test_short_executed_count_cannot_report_pass(self, _code_verification, _code_snapshot, _method_verification, _method_snapshot, _class_binding, _origin):
        inventory = {
            **BOUNDARY_METADATA, "authorization": "HOLD",
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
        result.stopped_test_ids = ["SYNTHETIC_ID"] * len(SUITES)
        result.test_outcome_events = [("success", "SYNTHETIC_ID")] * len(SUITES)
        result.test_event_trace = [
            event for _ in SUITES
            for event in (
                ("start", "SYNTHETIC_ID"),
                ("success", "SYNTHETIC_ID"),
                ("stop", "SYNTHETIC_ID"),
            )
        ]
        result.test_lifecycle_events = [
            item
            for _ in SUITES
            for item in (("start", "SYNTHETIC_ID"), ("stop", "SYNTHETIC_ID"))
        ]
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
        result = unittest.TextTestRunner(
            stream=stream, verbosity=2, resultclass=TrackingTextTestResult
        ).run(unittest.TestSuite([case]))
        self.assertEqual([case.id()], result.started_test_ids)
        self.assertEqual([id(case)], result.started_test_object_ids)
        self.assertEqual([id(case)], result.stopped_test_object_ids)
        self.assertEqual([case.id()], result.stopped_test_ids)
        self.assertEqual([("success", case.id())], result.test_outcome_events)
        self.assertEqual(
            [("start", case.id()), ("success", case.id()),
             ("stop", case.id())],
            result.test_event_trace,
        )
        self.assertEqual(
            [("start", case.id()), ("stop", case.id())],
            result.test_lifecycle_events,
        )
        self.assertEqual(1, result.testsRun)

    def test_nested_loaded_suite_preserves_original_object_references(self):
        class SyntheticCase(unittest.TestCase):
            def test_hold(self):
                self.assertEqual("HOLD", "HOLD")
        case = SyntheticCase("test_hold")
        nested = unittest.TestSuite([unittest.TestSuite([case])])
        self.assertIs(case, loaded_test_objects(nested)[0])

    def test_same_named_substitute_test_objects_fail_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)

        def replace_actual_objects(suite):
            original = loaded_test_objects(suite)
            substitutes = [copy.copy(case) for case in original]
            self.assertEqual([case.id() for case in original],
                             [case.id() for case in substitutes])
            self.assertTrue(all(first is not second for first, second
                                in zip(original, substitutes)))
            result = unittest.TestResult()
            ids = [case.id() for case in original]
            result.testsRun = len(ids)
            result.started_test_ids = ids
            result.stopped_test_ids = ids
            result.test_lifecycle_events = [
                event for test_id in ids
                for event in (("start", test_id), ("stop", test_id))
            ]
            result.test_outcome_events = [
                ("success", test_id) for test_id in ids
            ]
            result.test_event_trace = [
                event for test_id in ids
                for event in (("start", test_id), ("success", test_id),
                              ("stop", test_id))
            ]
            result.started_test_object_ids = [id(case) for case in substitutes]
            result.stopped_test_object_ids = [id(case) for case in substitutes]
            return result

        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       side_effect=replace_actual_objects):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("EXECUTED_TEST_OBJECT_MISMATCH", log.getvalue())

    def test_missing_object_identity_records_fail_closed(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        def synthetic_result(suite):
            cases = loaded_test_objects(suite)
            ids = [case.id() for case in cases]
            result = unittest.TestResult()
            result.testsRun = len(ids)
            result.started_test_ids = ids
            result.stopped_test_ids = ids
            result.test_lifecycle_events = [
                event for test_id in ids
                for event in (("start", test_id), ("stop", test_id))
            ]
            result.test_outcome_events = [
                ("success", test_id) for test_id in ids
            ]
            result.test_event_trace = [
                event for test_id in ids
                for event in (("start", test_id), ("success", test_id),
                              ("stop", test_id))
            ]
            return result
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       side_effect=synthetic_result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("EXECUTED_TEST_OBJECT_MISMATCH", log.getvalue())

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

    def test_missing_stop_event_rejected_even_when_test_count_matches(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids[:-1]
        result.test_lifecycle_events = [
            event for test_id in ids
            for event in (("start", test_id), ("stop", test_id))
        ][:-1]
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_LIFECYCLE_MISMATCH", log.getvalue())

    def test_reordered_stop_event_rejected_with_identical_counts(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids
        result.test_lifecycle_events = (
            [("start", ids[0]), ("start", ids[1]),
             ("stop", ids[0]), ("stop", ids[1])]
            + [event for test_id in ids[2:]
               for event in (("start", test_id), ("stop", test_id))]
        )
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_LIFECYCLE_MISMATCH", log.getvalue())

    def test_missing_lifecycle_metadata_rejected(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_LIFECYCLE_MISMATCH", log.getvalue())

    def test_missing_success_outcome_rejected_with_complete_lifecycle(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids
        result.test_lifecycle_events = [
            event for test_id in ids
            for event in (("start", test_id), ("stop", test_id))
        ]
        result.test_outcome_events = [("success", test_id) for test_id in ids[:-1]]
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_OUTCOME_MISMATCH", log.getvalue())

    def test_double_success_outcome_rejected_with_complete_lifecycle(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids
        result.test_lifecycle_events = [
            event for test_id in ids
            for event in (("start", test_id), ("stop", test_id))
        ]
        result.test_outcome_events = (
            [("success", test_id) for test_id in ids]
            + [("success", ids[-1])]
        )
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_OUTCOME_MISMATCH", log.getvalue())

    def test_false_success_label_rejected_even_when_unittest_was_successful(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids
        result.test_lifecycle_events = [
            event for test_id in ids
            for event in (("start", test_id), ("stop", test_id))
        ]
        result.test_outcome_events = [
            ("failure" if index == 0 else "success", test_id)
            for index, test_id in enumerate(ids)
        ]
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_OUTCOME_MISMATCH", log.getvalue())

    def test_success_recorded_after_stop_is_rejected(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids
        result.test_lifecycle_events = [
            event for test_id in ids
            for event in (("start", test_id), ("stop", test_id))
        ]
        result.test_outcome_events = [("success", test_id) for test_id in ids]
        result.test_event_trace = [
            event for test_id in ids
            for event in (("start", test_id), ("success", test_id),
                          ("stop", test_id))
        ]
        result.test_event_trace[:3] = [
            ("start", ids[0]), ("stop", ids[0]), ("success", ids[0])
        ]
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_EVENT_ORDER_MISMATCH", log.getvalue())

    def test_mismatched_chronological_success_rejected(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids
        result.test_lifecycle_events = [
            event for test_id in ids
            for event in (("start", test_id), ("stop", test_id))
        ]
        result.test_outcome_events = [("success", test_id) for test_id in ids]
        result.test_event_trace = [
            event for test_id in ids
            for event in (("start", test_id), ("success", test_id),
                          ("stop", test_id))
        ]
        result.test_event_trace[1] = ("success", ids[1])
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_EVENT_ORDER_MISMATCH", log.getvalue())

    def test_missing_chronological_trace_rejected(self):
        from pp_recovery_ci_inventory import audit_security_inventory
        inventory = audit_security_inventory(SUITES)
        ids = [item for name in SUITES
               for item in inventory["declaredTestIdsBySuite"][name]]
        result = unittest.TestResult()
        result.testsRun = len(ids)
        result.started_test_ids = ids
        result.stopped_test_ids = ids
        result.test_lifecycle_events = [
            event for test_id in ids
            for event in (("start", test_id), ("stop", test_id))
        ]
        result.test_outcome_events = [("success", test_id) for test_id in ids]
        with patch("pp_recovery_strict_ci_runner.audit_security_inventory",
                   return_value=inventory):
            with patch("pp_recovery_strict_ci_runner.unittest.TextTestRunner.run",
                       return_value=result):
                with redirect_stdout(StringIO()) as log:
                    self.assertEqual(1, run())
                self.assertIn("TEST_EVENT_ORDER_MISMATCH", log.getvalue())

    def test_same_count_with_substituted_method_id_fails_closed(self):
        inventory = {
            **BOUNDARY_METADATA, "authorization": "HOLD",
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
            **BOUNDARY_METADATA, "authorization": "HOLD",
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
            **BOUNDARY_METADATA, "authorization": "HOLD", "accessDecision": "DENY",
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
            **BOUNDARY_METADATA, "authorization": "HOLD", "accessDecision": "DENY",
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
            **BOUNDARY_METADATA, "authorization": "HOLD", "accessDecision": "DENY",
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
