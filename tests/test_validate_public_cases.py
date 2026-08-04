from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_public_cases import scientific_python_files, validate_paper_identity


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

if __name__ == "__main__":
    unittest.main()
