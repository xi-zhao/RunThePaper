from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.library_history import recorded_paper_date, render_history


ROOT = Path(__file__).resolve().parents[1]


class PaperHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = {
            "paper_id": "1811.08017",
            "title": "Example paper",
            "status": "Partial scientific reproduction",
            "preprint": {
                "status": "available", "identifier": "arXiv:1811.08017v2",
                "url": "https://arxiv.org/abs/1811.08017",
            },
            "publication": {"status": "not_recorded", "checked_at": "2026-08-17"},
        }

    def test_preprint_formats_keep_original_submission_year(self) -> None:
        for identifier, year in (
            ("arXiv:1811.08017v2", 2018), ("physics/9712001v3", 1997),
            ("arXiv:cond-mat/0503511", 2005), ("0704.0001", 2007),
        ):
            self.case["preprint"]["identifier"] = identifier
            with self.subTest(identifier=identifier):
                date = recorded_paper_date(self.case)
                self.assertIsNotNone(date)
                self.assertEqual((date.year, date.basis), (year, "preprint"))

    def test_earlier_formal_publication_controls_date_and_source(self) -> None:
        for year in (1687, 1976):
            self.case["publication"] = {
                "status": "published", "citation": f"Example journal 1, 2001 ({year})",
                "doi_url": "https://doi.org/example",
            }
            with self.subTest(year=year):
                date = recorded_paper_date(self.case)
                self.assertEqual((date.year, date.basis, date.url), (year, "publication", "https://doi.org/example"))
        self.case["publication"]["citation"] = "Example journal 1, 2001 (2019)"
        self.assertEqual(recorded_paper_date(self.case).year, 2018)

    def test_missing_dates_are_not_guessed_from_audit_date_or_page_numbers(self) -> None:
        self.case["preprint"] = {"status": "not_recorded", "checked_at": "2026-08-17"}
        self.assertIsNone(recorded_paper_date(self.case))
        for citation in ("Example journal 19, 2018-2020", "Example (2018); correction (2019)"):
            self.case["publication"] = {
                "status": "published", "citation": citation, "doi_url": "https://doi.org/example",
            }
            with self.subTest(citation=citation):
                self.assertIsNone(recorded_paper_date(self.case))

    def test_malformed_or_out_of_period_identifiers_remain_undated(self) -> None:
        for identifier in ("1813.08017", "1800.08017", "0703.0001", "quant-ph/0704001", "not-an-arxiv-id"):
            self.case["preprint"]["identifier"] = identifier
            with self.subTest(identifier=identifier):
                self.assertIsNone(recorded_paper_date(self.case))

    def test_timeline_keeps_unknown_cases_and_scientific_state(self) -> None:
        undated = copy.deepcopy(self.case)
        undated["paper_id"] = "undated-case"
        undated["preprint"] = {"status": "not_recorded"}
        rendered = render_history([undated, self.case])
        self.assertLess(rendered.index('id="decade-2010"'), rendered.index('id="undated"'))
        self.assertEqual(rendered.count("Partial scientific reproduction"), 2)
        self.assertIn("cases/undated-case/outputs/checks/completion_assessment.json", rendered)

    def test_catalog_is_covered_once_and_generation_is_order_independent(self) -> None:
        cases = json.loads((ROOT / "cases/catalog.json").read_text())["cases"]
        rendered = render_history(cases)
        self.assertEqual(rendered, render_history(list(reversed(cases))))
        for case in cases:
            with self.subTest(paper_id=case["paper_id"]):
                self.assertEqual(rendered.count(f"](cases/{case['paper_id']}/README.md)"), 1)
