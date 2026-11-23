"""Offline regression tests for matrix artifact post-processing."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pp_recovery_ci_receipt import STEPS, build_receipt, encode_receipt
from pp_recovery_ci_matrix_gate import (
    EXPECTED_FILES, verify_matrix_artifacts,
)
from review_044_release_boundary_snapshot import BoundaryInputError

SHA = "a" * 40
RUN = "79123"


def write_pair(root: Path, *, second_outcome: str = "success",
               second_run: str = RUN, second_sha: str = SHA,
               second_attempt: str = "1") -> None:
    for version, path in zip(("3.11", "3.12"), EXPECTED_FILES):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        receipt = build_receipt(
            {step: ("success" if version == "3.11"
                    else second_outcome) for step in STEPS},
            commit_sha=SHA if version == "3.11" else second_sha,
            run_id=RUN if version == "3.11" else second_run,
            run_attempt="1" if version == "3.11" else second_attempt,
            python_version=version,
        )
        target.write_bytes(encode_receipt(receipt))


class CiMatrixGateTests(unittest.TestCase):
    def test_valid_matrix_remains_non_authorizing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            result = verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)
            self.assertEqual("BOTH_RECORDED_SUCCESS_UNTRUSTED", result["syntheticExecution"])
            self.assertEqual("HOLD", result["authorization"])
            self.assertEqual("DENY", result["accessDecision"])
            self.assertEqual("NOT_AUTHORIZED", result["issuance"])

    def test_reject_missing_artifacts(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            (root / EXPECTED_FILES[1]).unlink()
            with self.assertRaises(BoundaryInputError):
                verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_failure_skipped_or_unknown(self):
        for outcome in ("failure", "skipped", "cancelled", "unknown"):
            with self.subTest(outcome=outcome), TemporaryDirectory() as tmp:
                root = Path(tmp)
                write_pair(root, second_outcome=outcome)
                with self.assertRaises(BoundaryInputError):
                    verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_cross_run_or_cross_commit_artifacts(self):
        for changes in ({"second_run": "5"}, {"second_sha": "b" * 40},
                        {"second_attempt": "2"}):
            with self.subTest(changes=changes), TemporaryDirectory() as tmp:
                root = Path(tmp)
                write_pair(root, **changes)
                with self.assertRaises(BoundaryInputError):
                    verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_wrong_workflow_context(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            for kwargs in (
                {"expected_sha": "b" * 40, "expected_run_id": RUN},
                {"expected_sha": SHA, "expected_run_id": "4"},
            ):
                with self.subTest(kwargs=kwargs):
                    with self.assertRaises(BoundaryInputError):
                        verify_matrix_artifacts(root, **kwargs)

    def test_reject_extra_artifact_directory(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            extra = root / "pp-recovery-receipt-py3.13"
            extra.mkdir()
            (extra / "pp-recovery-ci-receipt.json").write_bytes(b"{}")
            with self.assertRaises(BoundaryInputError):
                verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_extra_file_in_artifact_directory(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            (root / EXPECTED_FILES[0].parent / "unexpected.json").write_bytes(b"{}")
            with self.assertRaises(BoundaryInputError):
                verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_symlinked_parent_artifact_directory(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "matrix"
            root.mkdir()
            write_pair(root)
            directory = root / EXPECTED_FILES[1].parent
            real = Path(tmp) / "saved-directory"
            directory.rename(real)
            directory.symlink_to(real, target_is_directory=True)
            with self.assertRaises(BoundaryInputError):
                verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)

    def test_reject_oversized_or_symlinked_artifact(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pair(root)
            (root / EXPECTED_FILES[1]).write_bytes(b"x" * 8193)
            with self.assertRaises(BoundaryInputError):
                verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)
            (root / EXPECTED_FILES[1]).unlink()
            (root / EXPECTED_FILES[1]).symlink_to(root / EXPECTED_FILES[0])
            with self.assertRaises(BoundaryInputError):
                verify_matrix_artifacts(root, expected_sha=SHA, expected_run_id=RUN)


if __name__ == "__main__":
    unittest.main()
