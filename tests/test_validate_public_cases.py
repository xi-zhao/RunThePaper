from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_public_cases import (
    requires_generated_results,
    scientific_python_files,
    validate_authority_projection,
    validate_paper_identity,
)
from scripts.render_case_catalog import CHINESE_STATUS


class PublicStatusRenderingTests(unittest.TestCase):
    def test_visual_review_pending_has_chinese_label(self) -> None:
        self.assertEqual(
            "科学复现，待视觉评审",
            CHINESE_STATUS["Scientific reproduction — visual review pending"],
        )


class LifecycleEvidenceRequirementTests(unittest.TestCase):
    def test_partial_case_may_publish_without_success_artifacts(self) -> None:
        self.assertFalse(
            requires_generated_results({"authoritative_status": "partial"})
        )

    def test_result_claiming_states_require_data_and_figures(self) -> None:
        for status in (
            "complete",
            "review_pending",
            "visual_pending",
            "paper_error_candidate",
        ):
            with self.subTest(status=status):
                self.assertTrue(
                    requires_generated_results({"authoritative_status": status})
                )


class PaperIdentityValidationTests(unittest.TestCase):
    def test_rejects_case_without_any_verified_paper_identity(self) -> None:
        errors: list[str] = []
        validate_paper_identity(
            {
                "paper_id": "benchmark-only",
                "preprint": {
                    "status": "not_recorded",
                    "checked_at": "2026-08-04",
                },
                "publication": {
                    "status": "not_recorded",
                    "checked_at": "2026-08-04",
                },
            },
            errors,
        )

        self.assertIn(
            "benchmark-only is not an identifiable paper reproduction: "
            "both preprint and formal publication identities are unverified",
            errors,
        )

    def test_accepts_verified_preprint_without_formal_publication(self) -> None:
        errors: list[str] = []
        validate_paper_identity(
            {
                "paper_id": "2607.00001",
                "preprint": {
                    "identifier": "arXiv:2607.00001",
                    "title": "A paper",
                    "url": "https://arxiv.org/abs/2607.00001",
                },
                "publication": {
                    "status": "not_recorded",
                    "checked_at": "2026-08-04",
                },
            },
            errors,
        )

        self.assertEqual([], errors)

    def test_accepts_formal_publication_without_preprint(self) -> None:
        errors: list[str] = []
        validate_paper_identity(
            {
                "paper_id": "10.1234-paper",
                "preprint": {
                    "status": "not_recorded",
                    "checked_at": "2026-08-04",
                },
                "publication": {
                    "status": "published",
                    "title": "A published paper",
                    "venue": "Journal",
                    "citation": "Journal 1, 1 (2026)",
                    "doi": "10.1234/paper",
                    "doi_url": "https://doi.org/10.1234/paper",
                    "locator": "1",
                },
            },
            errors,
        )

        self.assertEqual([], errors)


class ScientificImplementationValidationTests(unittest.TestCase):
    def test_artifact_verifier_is_not_a_scientific_implementation(self) -> None:
        with TemporaryDirectory() as directory:
            case_dir = Path(directory)
            scripts = case_dir / "code" / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "verify_public_artifacts.py").write_text("", encoding="utf-8")

            self.assertEqual([], scientific_python_files(case_dir))

    def test_scientific_runner_satisfies_the_implementation_gate(self) -> None:
        with TemporaryDirectory() as directory:
            case_dir = Path(directory)
            scripts = case_dir / "code" / "scripts"
            scripts.mkdir(parents=True)
            runner = scripts / "run_reproduction.py"
            runner.write_text("", encoding="utf-8")

            self.assertEqual([runner], scientific_python_files(case_dir))


class AuthorityProjectionValidationTests(unittest.TestCase):
    def test_accepts_consistent_pragent_projection(self) -> None:
        with TemporaryDirectory() as directory:
            case_dir = Path(directory)
            checks = case_dir / "outputs/checks"
            checks.mkdir(parents=True)
            status = {
                "paper_id": "paper",
                "authoritative_status": "partial",
                "complete": False,
            }
            (checks / "completion_assessment.json").write_text(
                json.dumps(status), encoding="utf-8"
            )
            (checks / "publication_provenance.json").write_text(
                json.dumps({**status, "master_git_sha": "a" * 40}),
                encoding="utf-8",
            )
            errors: list[str] = []

            validate_authority_projection(
                {
                    **status,
                    "registry_scope": "paper_reproduction",
                    "master_git_sha": "a" * 40,
                },
                case_dir,
                errors,
            )

            self.assertEqual([], errors)

    def test_rejects_status_drift(self) -> None:
        with TemporaryDirectory() as directory:
            case_dir = Path(directory)
            checks = case_dir / "outputs/checks"
            checks.mkdir(parents=True)
            (checks / "completion_assessment.json").write_text(
                '{"paper_id":"paper","authoritative_status":"complete","complete":true}',
                encoding="utf-8",
            )
            (checks / "publication_provenance.json").write_text(
                '{"paper_id":"paper","authoritative_status":"partial","complete":false,'
                '"master_git_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
                encoding="utf-8",
            )
            errors: list[str] = []

            validate_authority_projection(
                {
                    "paper_id": "paper",
                    "registry_scope": "paper_reproduction",
                    "authoritative_status": "partial",
                    "complete": False,
                    "master_git_sha": "a" * 40,
                },
                case_dir,
                errors,
            )

            self.assertTrue(
                any("completion authoritative_status mismatch" in e for e in errors)
            )


if __name__ == "__main__":
    unittest.main()
