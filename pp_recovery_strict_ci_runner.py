"""Strict, synthetic-only PP recovery security test runner.

Missing suites, skipped tests, unexpected success, failures and errors all
produce nonzero exit status. Intended for CI; no production operations.
"""
from __future__ import annotations

import sys
import unittest

from pp_recovery_ci_inventory import audit_security_inventory

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
    if (inventory["authorization"] != "HOLD"
            or inventory["accessDecision"] != "DENY"):
        print("PP_CI_INVENTORY_AUTHORIZATION_INVALID / HOLD / DENY")
        return 1
    loader = unittest.defaultTestLoader
    combined = unittest.TestSuite()
    for name in SUITES:
        tests = loader.loadTestsFromName(name)
        if tests.countTestCases() == 0:
            print("PP_CI_EMPTY_SUITE / HOLD / DENY")
            return 1
        combined.addTests(tests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined)
    if (not result.wasSuccessful()
            or result.testsRun == 0
            or result.skipped
            or result.expectedFailures
            or result.unexpectedSuccesses):
        print("PP_CI_INCOMPLETE_OR_FAILED / HOLD / DENY")
        return 1
    print(f"PP_CI_SYNTHETIC_PASS / {result.testsRun} tests / AUTHORIZATION_HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
