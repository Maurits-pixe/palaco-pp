"""Strict, synthetic-only PP recovery security test runner.

Missing suites, skipped tests, unexpected success, failures and errors all
produce nonzero exit status. Intended for CI; no production operations.
"""
from __future__ import annotations

import hashlib
import re
import sys
import unittest
from pathlib import Path

from pp_recovery_ci_inventory import CRITICAL_MODULES, ROOT, audit_security_inventory

class TrackingTextTestResult(unittest.TextTestResult):
    """Record each test actually started by unittest, including repeats."""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.started_test_ids: list[str] = []
        self.started_test_object_ids: list[int] = []
        self.stopped_test_object_ids: list[int] = []
        self.stopped_test_ids: list[str] = []
        self.test_lifecycle_events: list[tuple[str, str]] = []
        self.test_outcome_events: list[tuple[str, str]] = []
        self.test_event_trace: list[tuple[str, str]] = []

    def addSuccess(self, test):
        self.test_outcome_events.append(("success", test.id()))
        self.test_event_trace.append(("success", test.id()))
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.test_outcome_events.append(("failure", test.id()))
        self.test_event_trace.append(("failure", test.id()))
        super().addFailure(test, err)

    def addError(self, test, err):
        self.test_outcome_events.append(("error", test.id()))
        self.test_event_trace.append(("error", test.id()))
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.test_outcome_events.append(("skip", test.id()))
        self.test_event_trace.append(("skip", test.id()))
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.test_outcome_events.append(("expected_failure", test.id()))
        self.test_event_trace.append(("expected_failure", test.id()))
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.test_outcome_events.append(("unexpected_success", test.id()))
        self.test_event_trace.append(("unexpected_success", test.id()))
        super().addUnexpectedSuccess(test)

    def startTest(self, test):
        test_id = test.id()
        self.started_test_ids.append(test_id)
        self.started_test_object_ids.append(id(test))
        self.test_lifecycle_events.append(("start", test_id))
        self.test_event_trace.append(("start", test_id))
        super().startTest(test)

    def stopTest(self, test):
        test_id = test.id()
        self.stopped_test_ids.append(test_id)
        self.stopped_test_object_ids.append(id(test))
        self.test_lifecycle_events.append(("stop", test_id))
        self.test_event_trace.append(("stop", test_id))
        super().stopTest(test)


def loaded_test_objects(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    """Retain actual loaded objects while unittest runs; refuse other items."""
    objects = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            objects.extend(loaded_test_objects(item))
        elif isinstance(item, unittest.TestCase):
            objects.append(item)
        else:
            raise ValueError("PP_CI_UNEXPECTED_LOADED_ITEM")
    return objects


def verify_loaded_test_class_bindings(cases: object) -> bool:
    """Each loaded TestCase class must be the named class in its suite module."""
    if type(cases) is not list or not cases:
        return False
    for case in cases:
        if not isinstance(case, unittest.TestCase):
            return False
        cls = type(case)
        suite_name = cls.__module__
        if suite_name not in SUITES:
            return False
        module = sys.modules.get(suite_name)
        if (module is None or getattr(module, cls.__name__, None) is not cls
                or cls.__qualname__ != cls.__name__):
            return False
        method = getattr(case, "_testMethodName", None)
        if (type(method) is not str or not method.startswith("test_")
                or not callable(getattr(cls, method, None))):
            return False
    return True


def loaded_test_ids(suite: unittest.TestSuite) -> list[str]:
    """Flatten unittest's actual test cases without running any tests."""
    ids = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            ids.extend(loaded_test_ids(item))
        elif isinstance(item, unittest.TestCase):
            ids.append(item.id())
        else:
            raise ValueError("PP_CI_UNEXPECTED_LOADED_ITEM")
    return ids



def verify_suite_origin(name: str, expected_sha256: str | None = None) -> bool:
    """Reject an imported security suite outside the checked source tree."""
    if type(name) is not str or not name.startswith("test_review_044_"):
        return False
    module = sys.modules.get(name)
    origin = getattr(module, "__file__", None)
    if type(origin) is not str:
        return False
    try:
        root = ROOT.resolve(strict=True)
        expected = root / f"{name}.py"
        supplied = Path(origin)
        if not (
            expected.is_file()
            and not expected.is_symlink()
            and supplied.is_file()
            and not supplied.is_symlink()
            and supplied.resolve(strict=True) == expected.resolve(strict=True)
        ):
            return False
        if expected_sha256 is None:
            return True  # Standalone origin check; CI always passes a digest.
        if (type(expected_sha256) is not str
                or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
            return False
        return hashlib.sha256(supplied.read_bytes()).hexdigest() == expected_sha256
    except (OSError, ValueError, RuntimeError):
        return False




def verify_imported_critical_module_origins(hashes: object) -> bool:
    """Reject imported critical modules shadowed by another file.

    Absence from sys.modules is allowed: not all review modules need importing.
    This is an in-process origin check, not code execution provenance.
    """
    if (type(hashes) is not dict or set(hashes) != set(CRITICAL_MODULES)
            or any(type(hashes.get(name)) is not str
                   or re.fullmatch(r"[0-9a-f]{64}", hashes[name]) is None
                   for name in CRITICAL_MODULES)):
        return False
    try:
        root = ROOT.resolve(strict=True)
        for name in CRITICAL_MODULES:
            if name not in sys.modules:
                continue
            module = sys.modules[name]
            origin = getattr(module, "__file__", None)
            if type(origin) is not str:
                return False
            expected = root / f"{name}.py"
            imported = Path(origin)
            if (not expected.is_file() or expected.is_symlink()
                    or not imported.is_file() or imported.is_symlink()
                    or imported.resolve(strict=True)
                    != expected.resolve(strict=True)
                    or hashlib.sha256(imported.read_bytes()).hexdigest()
                    != hashes[name]):
                return False
    except (OSError, ValueError, RuntimeError):
        return False
    return True


def verify_critical_source_integrity(hashes: object, root: Path = ROOT) -> bool:
    """Compare current security source bytes to inventory; never import them."""
    if (type(hashes) is not dict or set(hashes) != set(CRITICAL_MODULES)
            or any(type(hashes.get(name)) is not str
                   or re.fullmatch(r"[0-9a-f]{64}", hashes[name]) is None
                   for name in CRITICAL_MODULES)):
        return False
    try:
        for name in CRITICAL_MODULES:
            path = root / f"{name}.py"
            if (path.is_symlink() or not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest()
                    != hashes[name]):
                return False
    except (OSError, ValueError, RuntimeError):
        return False
    return True



def verify_test_source_integrity(hashes: object, root: Path = ROOT) -> bool:
    """Refuse test-source changes since the scoped inventory snapshot."""
    if (type(hashes) is not dict or set(hashes) != set(SUITES)
            or any(type(hashes.get(name)) is not str
                   or re.fullmatch(r"[0-9a-f]{64}", hashes[name]) is None
                   for name in SUITES)):
        return False
    try:
        for name in SUITES:
            path = root / f"{name}.py"
            if (path.is_symlink() or not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest()
                    != hashes[name]):
                return False
    except (OSError, ValueError, RuntimeError):
        return False
    return True



SUITES = (
    "test_review_044_contract_parity",
    "test_review_044_recovery_chain_e2e",
    "test_review_044_release_boundary_snapshot",
    "test_review_044_release_boundary_snapshot_cli",
    "test_review_044_boundary_reconciliation",
    "test_review_044_evidence_manifest",
    "test_review_044_detached_signature_inspection",
    "test_review_044_trust_anchor_preflight",
    "test_review_044_proposed_key_binding",
    "test_review_044_unsigned_revocation_notice",
    "test_review_044_revocation_signature_inspection",
)


def run(argv: list[str] | None = None) -> int:
    arguments = [] if argv is None else argv
    if arguments:
        print("PP_CI_INVALID_ARGUMENTS / HOLD / DENY")
        return 2
    try:
        inventory = audit_security_inventory(SUITES)
    except (ValueError, OSError, SyntaxError) as exc:
        print(f"PP_CI_INVENTORY_FAILED: {type(exc).__name__} / HOLD / DENY")
        return 1
    if (type(inventory) is not dict
            or inventory.get("authorization") != "HOLD"
            or inventory.get("accessDecision") != "DENY"
            or inventory.get("issuance") != "NOT_AUTHORIZED"
            or inventory.get("deployment") != "BLOCKED"):
        print("PP_CI_INVENTORY_AUTHORIZATION_INVALID / HOLD / DENY")
        return 1
    if (inventory.get("schema")
            != "palaco.pp.recovery-002-ci-inventory-observation.v1"
            or inventory.get("reference") != "PP-RECOVERY-002"
            or inventory.get("coverageState")
            != "ALL_SCOPED_FILES_PRESENT_NOT_EXECUTION_PROOF"
            or type(inventory.get("registeredSuites")) is not int
            or inventory["registeredSuites"] != len(SUITES)
            or type(inventory.get("criticalModules")) is not int
            or inventory["criticalModules"] != len(CRITICAL_MODULES)):
        print("PP_CI_INVENTORY_BOUNDARY_INVALID / HOLD / DENY")
        return 1
    declared = inventory.get("declaredTestMethodsBySuite")
    if (type(declared) is not dict or set(declared) != set(SUITES)
            or any(type(declared.get(name)) is not int
                   or declared[name] < 1 for name in SUITES)):
        print("PP_CI_DECLARED_COUNTS_INVALID / HOLD / DENY")
        return 1
    expected_ids = inventory.get("declaredTestIdsBySuite")
    if (type(expected_ids) is not dict or set(expected_ids) != set(SUITES)
            or any(type(expected_ids.get(name)) is not list
                   or len(expected_ids[name]) != declared[name]
                   or any(type(item) is not str for item in expected_ids[name])
                   or len(set(expected_ids[name])) != len(expected_ids[name])
                   for name in SUITES)):
        print("PP_CI_DECLARED_IDS_INVALID / HOLD / DENY")
        return 1
    hashes = inventory.get("testSourceSha256BySuite")
    if (type(hashes) is not dict or set(hashes) != set(SUITES)
            or any(type(hashes.get(name)) is not str
                   or re.fullmatch(r"[0-9a-f]{64}", hashes[name]) is None
                   for name in SUITES)):
        print("PP_CI_SOURCE_HASHES_INVALID / HOLD / DENY")
        return 1
    if not verify_test_source_integrity(hashes):
        print("PP_CI_TEST_SOURCE_INTEGRITY_FAILED / HOLD / DENY")
        return 1
    critical_hashes = inventory.get("criticalSourceSha256ByModule")
    if not verify_critical_source_integrity(critical_hashes):
        print("PP_CI_CRITICAL_SOURCE_INTEGRITY_FAILED / HOLD / DENY")
        return 1
    loader = unittest.defaultTestLoader
    combined = unittest.TestSuite()
    expected_started_ids = []
    expected_test_objects = []
    for name in SUITES:
        tests = loader.loadTestsFromName(name)
        actual_count = tests.countTestCases()
        if actual_count == 0:
            print("PP_CI_EMPTY_SUITE / HOLD / DENY")
            return 1
        if actual_count != declared[name]:
            print("PP_CI_LOADED_TEST_COUNT_MISMATCH / HOLD / DENY")
            return 1
        try:
            loaded_ids = loaded_test_ids(tests)
        except (ValueError, TypeError):
            print("PP_CI_LOADED_TEST_ID_INVALID / HOLD / DENY")
            return 1
        if sorted(loaded_ids) != sorted(expected_ids[name]):
            print("PP_CI_LOADED_TEST_ID_MISMATCH / HOLD / DENY")
            return 1
        if not verify_suite_origin(name, hashes[name]):
            print("PP_CI_SUITE_ORIGIN_MISMATCH / HOLD / DENY")
            return 1
        try:
            cases = loaded_test_objects(tests)
        except (TypeError, ValueError):
            print("PP_CI_LOADED_OBJECT_INVALID / HOLD / DENY")
            return 1
        if len(cases) != actual_count:
            print("PP_CI_LOADED_OBJECT_COUNT_MISMATCH / HOLD / DENY")
            return 1
        expected_test_objects.extend(cases)
        expected_started_ids.extend(expected_ids[name])
        combined.addTests(tests)
    if not verify_loaded_test_class_bindings(expected_test_objects):
        print("PP_CI_LOADED_TEST_CLASS_BINDING_INVALID / HOLD / DENY")
        return 1
    # Pin every loaded security-suite module, not just each TestCase.
    # The module must remain the audited import for the whole test run.
    if any(not verify_suite_origin(name, hashes[name]) for name in SUITES):
        print("PP_CI_TEST_IMPORT_ORIGIN_MISMATCH / HOLD / DENY")
        return 1
    loaded_suite_modules = {name: sys.modules[name] for name in SUITES}
    if not verify_imported_critical_module_origins(critical_hashes):
        print("PP_CI_CRITICAL_IMPORT_ORIGIN_MISMATCH / HOLD / DENY")
        return 1
    # Retain the imported module objects: a same-path substitute would
    # otherwise pass the byte and location checks after execution.
    loaded_critical_modules = {
        name: sys.modules[name]
        for name in CRITICAL_MODULES if name in sys.modules
    }
    # Check every suite, including those loaded earlier in the loop.
    if not verify_test_source_integrity(hashes):
        print("PP_CI_TEST_SOURCE_CHANGED_DURING_LOAD / HOLD / DENY")
        return 1
    # Detect changes occurring while the loader imported the test modules.
    if not verify_critical_source_integrity(critical_hashes):
        print("PP_CI_CRITICAL_SOURCE_CHANGED_DURING_LOAD / HOLD / DENY")
        return 1
    runner = unittest.TextTestRunner(verbosity=2, resultclass=TrackingTextTestResult)
    result = runner.run(combined)
    if not verify_test_source_integrity(hashes):
        print("PP_CI_TEST_SOURCE_CHANGED_DURING_RUN / HOLD / DENY")
        return 1
    # A successful test run is invalid when the audited code changed mid-run.
    if not verify_critical_source_integrity(critical_hashes):
        print("PP_CI_CRITICAL_SOURCE_CHANGED_DURING_RUN / HOLD / DENY")
        return 1
    if any(sys.modules.get(name) is not module
           for name, module in loaded_suite_modules.items()):
        print("PP_CI_TEST_IMPORT_OBJECT_CHANGED_DURING_RUN / HOLD / DENY")
        return 1
    if any(not verify_suite_origin(name, hashes[name]) for name in SUITES):
        print("PP_CI_TEST_IMPORT_ORIGIN_CHANGED_DURING_RUN / HOLD / DENY")
        return 1
    if not verify_loaded_test_class_bindings(expected_test_objects):
        print("PP_CI_TEST_CLASS_BINDING_CHANGED_DURING_RUN / HOLD / DENY")
        return 1
    if not verify_imported_critical_module_origins(critical_hashes):
        print("PP_CI_CRITICAL_IMPORT_CHANGED_DURING_RUN / HOLD / DENY")
        return 1
    if any(sys.modules.get(name) is not module
           for name, module in loaded_critical_modules.items()):
        print("PP_CI_CRITICAL_IMPORT_OBJECT_CHANGED_DURING_RUN / HOLD / DENY")
        return 1
    # A count alone cannot detect duplicated or substituted executions.
    started = getattr(result, "started_test_ids", None)
    if (type(started) is not list
            or any(type(item) is not str for item in started)
            or sorted(started) != sorted(expected_started_ids)):
        print("PP_CI_EXECUTED_TEST_ID_MISMATCH / HOLD / DENY")
        return 1
    # Each test must also finish exactly once. Equal start/stop multisets
    # are insufficient if lifecycle events are misordered or interleaved.
    stopped = getattr(result, "stopped_test_ids", None)
    events = getattr(result, "test_lifecycle_events", None)
    expected_events = [
        event
        for test_id in started
        for event in (("start", test_id), ("stop", test_id))
    ]
    if (type(stopped) is not list
            or any(type(item) is not str for item in stopped)
            or stopped != started
            or type(events) is not list
            or events != expected_events):
        print("PP_CI_TEST_LIFECYCLE_MISMATCH / HOLD / DENY")
        return 1
    # Every started test must produce exactly one successful unittest
    # outcome, in the same order. A start/stop pair by itself is not a PASS.
    outcomes = getattr(result, "test_outcome_events", None)
    expected_outcomes = [("success", test_id) for test_id in started]
    if type(outcomes) is not list or outcomes != expected_outcomes:
        print("PP_CI_TEST_OUTCOME_MISMATCH / HOLD / DENY")
        return 1
    # Reconcile the actual chronological callbacks, not just independent
    # start/stop and success lists. Each successful test is a triplet.
    trace = getattr(result, "test_event_trace", None)
    expected_trace = [
        event
        for test_id in started
        for event in (("start", test_id), ("success", test_id), ("stop", test_id))
    ]
    if type(trace) is not list or trace != expected_trace:
        print("PP_CI_TEST_EVENT_ORDER_MISMATCH / HOLD / DENY")
        return 1
    if (not result.wasSuccessful()
            or result.testsRun != sum(declared.values())
            or result.testsRun == 0
            or result.skipped
            or result.expectedFailures
            or result.unexpectedSuccesses):
        print("PP_CI_INCOMPLETE_OR_FAILED / HOLD / DENY")
        return 1
    # Same name is not the same loaded TestCase instance. Retain strong
    # references above so Python cannot reuse an object identity mid-run.
    expected_object_ids = [id(case) for case in expected_test_objects]
    started_objects = getattr(result, "started_test_object_ids", None)
    stopped_objects = getattr(result, "stopped_test_object_ids", None)
    if (type(started_objects) is not list
            or type(stopped_objects) is not list
            or started_objects != expected_object_ids
            or stopped_objects != expected_object_ids):
        print("PP_CI_EXECUTED_TEST_OBJECT_MISMATCH / HOLD / DENY")
        return 1
    print(f"PP_CI_SYNTHETIC_PASS / {result.testsRun} tests / AUTHORIZATION_HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
