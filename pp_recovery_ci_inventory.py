"""Fail-closed inventory audit of PALACO-PP critical regression coverage.

This checks the explicitly scoped security boundary modules and their
regression-suite registration. It does not claim to discover all historical
repository tests or grant release authority.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CRITICAL_MODULES = (
    "review_044_release_boundary_snapshot",
    "review_044_release_boundary_snapshot_cli",
    "review_044_boundary_reconciliation",
    "review_044_evidence_manifest",
    "review_044_detached_signature_inspection",
    "review_044_trust_anchor_preflight",
    "review_044_proposed_key_binding",
    "review_044_unsigned_revocation_notice",
    "review_044_revocation_signature_inspection",
)
INTEGRATION_SUITES = (
    "test_review_044_contract_parity",
    "test_review_044_recovery_chain_e2e",
)


def audit_security_inventory(
    runner_suites: tuple[str, ...], base: Path = ROOT,
) -> dict:
    """Reject missing source files, tests, duplicate suites and omissions."""
    if (type(runner_suites) is not tuple
            or any(type(name) is not str for name in runner_suites)):
        raise ValueError("PP_CI_INVENTORY_INVALID")
    required = frozenset(
        f"test_{module}" for module in CRITICAL_MODULES
    ) | frozenset(INTEGRATION_SUITES)
    if len(set(runner_suites)) != len(runner_suites):
        raise ValueError("PP_CI_DUPLICATE_SUITE")
    actual = frozenset(runner_suites)
    if required - actual:
        raise ValueError("PP_CI_MISSING_SUITE")
    if actual - required:
        raise ValueError("PP_CI_UNREGISTERED_SUITE")
    for module in CRITICAL_MODULES:
        source_path = base / f"{module}.py"
        if not source_path.is_file():
            raise ValueError("PP_CI_MISSING_SOURCE")
        # A present file is not a valid testable module unless it parses.
        # Parse only; never import, evaluate or execute recovery sources.
        try:
            ast.parse(
                source_path.read_text(encoding="utf-8"),
                filename=str(source_path),
            )
        except (SyntaxError, UnicodeError) as exc:
            raise ValueError("PP_CI_SOURCE_SYNTAX_INVALID") from exc
    for name in runner_suites:
        path = base / f"{name}.py"
        if not path.is_file():
            raise ValueError("PP_CI_MISSING_TEST")
        # Parse all relevant test files without running their imports.
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        # Only methods in a statically recognizable unittest.TestCase
        # subclass are registered here. A plain class with test_* names
        # would satisfy the old AST inventory but be ignored by unittest.
        test_classes = [
            node for node in tree.body
            if isinstance(node, ast.ClassDef)
            and any(
                isinstance(base_class, ast.Attribute)
                and isinstance(base_class.value, ast.Name)
                and base_class.value.id == "unittest"
                and base_class.attr == "TestCase"
                for base_class in node.bases
            )
        ]
        # unittest.TestCase does not await async test methods: an async
        # method may return a coroutine without executing assertions.
        # It is therefore never acceptable as a security regression.
        async_tests = [
            method
            for test_class in test_classes
            for method in test_class.body
            if isinstance(method, ast.AsyncFunctionDef)
            and method.name.startswith("test_")
        ]
        if async_tests:
            raise ValueError("PP_CI_ASYNC_TEST_UNSUPPORTED")
        methods = [
            method
            for test_class in test_classes
            for method in test_class.body
            if isinstance(method, ast.FunctionDef)
            and method.name.startswith("test_")
        ]
        if not methods:
            raise ValueError("PP_CI_SUITE_WITHOUT_DISCOVERABLE_TESTS")
    return {
        "schema": "palaco.pp.recovery-002-ci-inventory-observation.v1",
        "reference": "PP-RECOVERY-002",
        "registeredSuites": len(runner_suites),
        "criticalModules": len(CRITICAL_MODULES),
        "coverageState": "ALL_SCOPED_FILES_PRESENT_NOT_EXECUTION_PROOF",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
