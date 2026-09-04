from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory

from scripts.library_navigation import render_learning_paths, validate_learning_path
from scripts.render_case_catalog import write_if_changed


ROOT = Path(__file__).resolve().parents[1]


class LearningPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collections = json.loads((ROOT / "cases/collections.json").read_text())["collections"]
        self.cases = json.loads((ROOT / "cases/catalog.json").read_text())["cases"]

    def test_learning_order_cannot_change_scientific_status(self) -> None:
        cases = copy.deepcopy(self.cases)
        starter = self.collections[0]["learning"]["steps"][0]["paper_id"]
        for case in cases:
            if case["paper_id"] == starter:
                case["status"] = "Scientific reproduction — invalid"
        text = render_learning_paths(cases, self.collections)
        self.assertIn("**Scientific reproduction — invalid**", text)
        self.assertIn(f"cases/{starter}/outputs/checks/completion_assessment.json", text)

    def test_unknown_or_duplicate_starter_is_rejected(self) -> None:
        for invalid_id in ("missing-case", self.collections[0]["learning"]["steps"][0]["paper_id"]):
            collection = copy.deepcopy(self.collections[0])
            collection["learning"]["steps"][1]["paper_id"] = invalid_id
            with self.subTest(invalid_id=invalid_id), self.assertRaises(ValueError):
                validate_learning_path(collection)

    def test_each_path_requires_prerequisites_and_an_exercise(self) -> None:
        for field in ("prerequisites_en", "prerequisites_zh"):
            collection = copy.deepcopy(self.collections[0])
            del collection["learning"][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_learning_path(collection)
        collection = copy.deepcopy(self.collections[0])
        del collection["learning"]["steps"][0]["exercise_zh"]
        with self.assertRaises(ValueError):
            validate_learning_path(collection)

    def test_unchanged_generation_does_not_touch_the_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nested/page.md"
            self.assertTrue(write_if_changed(path, "content\n"))
            before = path.stat().st_mtime_ns
            self.assertFalse(write_if_changed(path, "content\n"))
            self.assertEqual(before, path.stat().st_mtime_ns)
            self.assertTrue(write_if_changed(path, "updated\n"))
            self.assertEqual("updated\n", path.read_text())
