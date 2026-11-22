"""CI-only parity checks between recovery producer and fail-closed boundary.

Reads Python source as AST without executing the multi-module recovery chain,
accessing real evidence, or importing account/database integrations. Any
unexpected or dynamic contract expression fails instead of being evaluated.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

from review_044_release_boundary_snapshot import (
    EXPECTED_CHECK_IDS, EXPECTED_GATES, EXPECTED_GLOBAL_BLOCKERS,
)

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "decision": "review_044_recovery_decision.py",
    "plan": "review_044_verification_plan.py",
    "readiness": "review_044_release_readiness.py",
}


def static_assignment(source: str, variable: str):
    """Return a literal top-level assignment. No exec/eval/import side effects."""
    tree = ast.parse(source)
    matches = []
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == variable):
            matches.append(node.value)
    if len(matches) != 1:
        raise ValueError("PP_CONTRACT_MISSING_OR_AMBIGUOUS")
    try:
        return ast.literal_eval(matches[0])
    except (ValueError, TypeError, RecursionError, MemoryError) as exc:
        raise ValueError("PP_CONTRACT_NOT_STATIC") from exc


def production_contract(sources: dict[str, str]):
    """Reconstruct only the static, security-relevant producer declarations."""
    requirements = static_assignment(sources["decision"], "REQUIREMENTS")
    checks = static_assignment(sources["plan"], "CHECKS")
    prerequisites = static_assignment(sources["plan"], "GATE_PREREQUISITES")
    actions = static_assignment(sources["readiness"], "_NEXT_ACTIONS")
    blockers = static_assignment(sources["readiness"], "GLOBAL_BLOCKERS")
    if (type(requirements) is not tuple or type(checks) is not tuple
            or type(prerequisites) is not dict or type(actions) is not dict
            or type(blockers) is not tuple):
        raise ValueError("PP_CONTRACT_WRONG_TYPES")
    if set(prerequisites) != {name for name, _ in requirements}:
        raise ValueError("PP_CONTRACT_GATE_DRIFT")
    if set(actions) != set(prerequisites):
        raise ValueError("PP_CONTRACT_ACTION_DRIFT")
    gates = tuple(
        (name, description, prerequisites[name], actions[name])
        for name, description in requirements
    )
    check_ids = tuple(check[0] for check in checks)
    return gates, check_ids, blockers


def verify_parity(sources: dict[str, str]) -> bool:
    gates, check_ids, blockers = production_contract(sources)
    return (gates == EXPECTED_GATES
            and check_ids == EXPECTED_CHECK_IDS
            and blockers == EXPECTED_GLOBAL_BLOCKERS)


class RecoveryContractParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            label: (ROOT / path).read_text(encoding="utf-8")
            for label, path in SOURCES.items()
        }

    def test_actual_producer_matches_release_boundary(self):
        self.assertTrue(verify_parity(self.sources))

    def test_changed_gate_name_is_detected(self):
        changed = dict(self.sources)
        changed["decision"] = changed["decision"].replace(
            '"SOURCE_ATTESTATION", "Independent attestation',
            '"SOURCE_AUTHENTICATION", "Independent attestation', 1,
        )
        self.assertFalse(verify_parity(changed))

    def test_changed_check_id_is_detected(self):
        changed = dict(self.sources)
        changed["plan"] = changed["plan"].replace(
            '"ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED"',
            '"ORIGINAL_EVIDENCE_ALREADY_CHECKED"', 1,
        )
        self.assertFalse(verify_parity(changed))

    def test_changed_global_blocker_is_detected(self):
        changed = dict(self.sources)
        changed["readiness"] = changed["readiness"].replace(
            '"ORIGINAL_SOURCE_ATTESTATION_ABSENT"',
            '"ORIGINAL_SOURCE_ATTESTATION_VERIFIED"', 1,
        )
        self.assertFalse(verify_parity(changed))

    def test_changed_manual_action_is_detected(self):
        changed = dict(self.sources)
        changed["readiness"] = changed["readiness"].replace(
            '"OBTAIN_INDEPENDENT_SOURCE_ATTESTATION"',
            '"AUTO_APPROVE_SOURCE"', 1,
        )
        self.assertFalse(verify_parity(changed))

    def test_dynamic_code_not_executed(self):
        text = 'REQUIREMENTS = __import__("os").system("echo SHOULD_NOT_RUN")'
        with self.assertRaises(ValueError):
            static_assignment(text, "REQUIREMENTS")

    def test_duplicate_or_missing_declaration_fails(self):
        with self.assertRaises(ValueError):
            static_assignment("X = 1\nX = 2", "X")
        with self.assertRaises(ValueError):
            static_assignment("OTHER = 1", "X")


if __name__ == "__main__":
    unittest.main()
