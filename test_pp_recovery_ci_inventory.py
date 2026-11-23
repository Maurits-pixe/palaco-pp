"""Synthetic checks for PP critical-suite coverage inventory."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pp_recovery_ci_inventory import (
    CRITICAL_MODULES, INTEGRATION_SUITES,
    ROOT, audit_security_inventory,
)
from pp_recovery_strict_ci_runner import SUITES


class RecoveryCiInventoryTests(unittest.TestCase):
    def test_current_explicit_scope_is_complete_and_denied(self):
        result = audit_security_inventory(SUITES, ROOT)
        self.assertEqual(len(CRITICAL_MODULES), result["criticalModules"])
        self.assertEqual(len(SUITES), result["registeredSuites"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("BLOCKED", result["deployment"])

    def test_missing_suite_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "MISSING_SUITE"):
            audit_security_inventory(SUITES[:-1], ROOT)

    def test_missing_and_unknown_suite_fail_closed(self):
        # An unknown suite must never compensate for a missing required one.
        replaced = SUITES[:-1] + ("test_fake_automatic_release",)
        with self.assertRaisesRegex(ValueError, "MISSING_SUITE"):
            audit_security_inventory(replaced, ROOT)
        with self.assertRaisesRegex(ValueError, "UNREGISTERED_SUITE"):
            audit_security_inventory(SUITES + ("test_fake_automatic_release",), ROOT)

    def test_duplicate_suite_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SUITE"):
            audit_security_inventory(SUITES + (SUITES[0],), ROOT)

    def test_unknown_suite_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNREGISTERED"):
            audit_security_inventory(SUITES + ("test_fake_automatic_release",), ROOT)

    def test_missing_source_is_rejected_without_executing_imports(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            for module in CRITICAL_MODULES[1:]:
                (base / f"{module}.py").write_text("", encoding="utf-8")
            for suite in SUITES:
                (base / f"{suite}.py").write_text(
                    "class Tests:\n    def test_guard(self):\n        pass\n",
                    encoding="utf-8",
                )
            with self.assertRaisesRegex(ValueError, "MISSING_SOURCE"):
                audit_security_inventory(SUITES, base)

    def test_malformed_critical_source_fails_before_suite_loading(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            for module in CRITICAL_MODULES:
                (base / f"{module}.py").write_text(
                    "DENY = 'HOLD'\n", encoding="utf-8",
                )
            for suite in SUITES:
                (base / f"{suite}.py").write_text(
                    "import unittest\nclass Tests(unittest.TestCase):\n"
                    "    def test_guard(self):\n        pass\n",
                    encoding="utf-8",
                )
            (base / f"{CRITICAL_MODULES[0]}.py").write_text(
                "from import BROKEN\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "SOURCE_SYNTAX_INVALID"):
                audit_security_inventory(SUITES, base)

    def test_malformed_security_suite_is_not_accepted(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            for module in CRITICAL_MODULES:
                (base / f"{module}.py").write_text(
                    "DENY = 'HOLD'\n", encoding="utf-8",
                )
            for suite in SUITES:
                (base / f"{suite}.py").write_text(
                    "import unittest\nclass Tests(unittest.TestCase):\n"
                    "    def test_guard(self):\n        pass\n",
                    encoding="utf-8",
                )
            (base / f"{SUITES[0]}.py").write_text(
                "import unittest\nclass Broken(\n", encoding="utf-8",
            )
            with self.assertRaises(SyntaxError):
                audit_security_inventory(SUITES, base)

    def test_plain_class_test_method_does_not_count_as_coverage(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            for module in CRITICAL_MODULES:
                (base / f"{module}.py").write_text(
                    "AUTHORIZATION = 'HOLD'\n", encoding="utf-8",
                )
            for suite in SUITES:
                (base / f"{suite}.py").write_text(
                    "import unittest\n"
                    "class Valid(unittest.TestCase):\n"
                    "    def test_denial(self):\n"
                    "        self.assertEqual('HOLD', 'HOLD')\n",
                    encoding="utf-8",
                )
            (base / f"{SUITES[0]}.py").write_text(
                "class FakeTests:\n"
                "    def test_should_run(self):\n"
                "        raise AssertionError('NOT_DISCOVERED')\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "WITHOUT_DISCOVERABLE_TESTS"):
                audit_security_inventory(SUITES, base)

    def test_async_unittest_method_is_rejected(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            for module in CRITICAL_MODULES:
                (base / f"{module}.py").write_text(
                    "DENY = 'HOLD'\n", encoding="utf-8",
                )
            for suite in SUITES:
                (base / f"{suite}.py").write_text(
                    "import unittest\n"
                    "class Tests(unittest.TestCase):\n"
                    "    def test_guard(self):\n        pass\n",
                    encoding="utf-8",
                )
            (base / f"{SUITES[0]}.py").write_text(
                "import unittest\n"
                "class Tests(unittest.TestCase):\n"
                "    async def test_false_pass(self):\n"
                "        raise AssertionError('ASYNC_ASSERTION_NEVER_AWAITED')\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "ASYNC_TEST_UNSUPPORTED"):
                audit_security_inventory(SUITES, base)

    def test_mixed_sync_async_suite_is_rejected(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            for module in CRITICAL_MODULES:
                (base / f"{module}.py").write_text(
                    "DENY = 'HOLD'\n", encoding="utf-8",
                )
            for suite in SUITES:
                (base / f"{suite}.py").write_text(
                    "import unittest\n"
                    "class Tests(unittest.TestCase):\n"
                    "    def test_guard(self):\n        pass\n",
                    encoding="utf-8",
                )
            (base / f"{SUITES[0]}.py").write_text(
                "import unittest\n"
                "class Tests(unittest.TestCase):\n"
                "    def test_sync(self):\n        pass\n"
                "    async def test_async(self):\n        assert False\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "ASYNC_TEST_UNSUPPORTED"):
                audit_security_inventory(SUITES, base)

    def test_empty_test_file_rejected(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            for module in CRITICAL_MODULES:
                (base / f"{module}.py").write_text("", encoding="utf-8")
            for suite in SUITES:
                (base / f"{suite}.py").write_text(
                    "class Tests:\n    def test_guard(self):\n        pass\n",
                    encoding="utf-8",
                )
            (base / f"{INTEGRATION_SUITES[0]}.py").write_text(
                "class Tests:\n    pass\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "WITHOUT_DISCOVERABLE_TESTS"):
                audit_security_inventory(SUITES, base)


if __name__ == "__main__":
    unittest.main()
