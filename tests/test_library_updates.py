from __future__ import annotations

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.library_updates import classify_changes, collect_updates, render_updates


class ChangeClassificationTests(unittest.TestCase):
    def test_code_and_data_update_is_one_case_even_when_catalog_is_unchanged(self) -> None:
        catalog = {"paper-a": {"paper_id": "paper-a", "title": "A"}}
        changes = classify_changes(catalog, catalog, [
            "cases/paper-a/code/model.py", "cases/paper-a/outputs/data/result.csv",
        ])
        self.assertEqual(1, len(changes))
        self.assertEqual("updated", changes[0].kind)
        self.assertEqual(("code", "data"), changes[0].areas)

    def test_addition_removal_and_metadata_update_stay_separate(self) -> None:
        before = {"a": {"title": "A"}, "b": {"title": "B", "status": "passed"}}
        after = {"b": {"title": "B", "status": "failed"}, "c": {"title": "C"}}
        changes = classify_changes(before, after, [])
        self.assertEqual({"a": "removed", "b": "updated", "c": "added"}, {c.paper_id: c.kind for c in changes})

    def test_navigation_changes_do_not_create_scientific_updates(self) -> None:
        catalog = {"a": {"title": "A"}}
        self.assertEqual((), classify_changes(catalog, catalog, ["README.md", "cases/collections.json"]))


class GitHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.catalog = self.root / "cases/catalog.json"
        self.catalog.parent.mkdir()
        self.catalog.write_text(json.dumps({"cases": [{"paper_id": "a", "title": "Paper A"}]}))
        self.data = self.root / "cases/a/outputs/data/result.csv"
        self.data.parent.mkdir(parents=True)
        self.data.write_text("x,y\n1,2\n")
        self.first = self.commit("Add a paper")

    def git(self, *args: str) -> str:
        return subprocess.run([
            "git", "-C", str(self.root), "-c", "user.name=Library Test",
            "-c", "user.email=library-test@example.invalid", "-c", "commit.gpgsign=false", *args,
        ], check=True, text=True, capture_output=True).stdout.strip()

    def commit(self, message: str) -> str:
        self.git("add", "cases")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def test_history_is_immutable_and_excludes_navigation_and_uncommitted_edits(self) -> None:
        self.data.write_text("x,y\n1,3\n")
        second = self.commit("Correct generated data")
        (self.root / "cases/collections.json").write_text("{}\n")
        self.commit("Organize the library")
        self.data.write_text("uncommitted work\n")
        updates = collect_updates(self.root)
        self.assertEqual([second, self.first], [u.revision for u in updates])
        self.assertEqual("updated", updates[0].changes[0].kind)
        self.assertEqual(("data",), updates[0].changes[0].areas)
        self.assertEqual("added", updates[1].changes[0].kind)
        self.assertEqual(updates, collect_updates(self.root))
        self.assertEqual([second], [u.revision for u in collect_updates(self.root, limit=1)])

    def test_removed_case_links_to_the_revision_that_still_contains_it(self) -> None:
        self.catalog.write_text('{"cases": []}\n')
        self.git("rm", "-r", "cases/a")
        self.commit("Withdraw a paper")
        updates = collect_updates(self.root)
        self.assertEqual("removed", updates[0].changes[0].kind)
        self.assertIn(f"/tree/{self.first}/cases/a", render_updates(updates[:1]))

    def test_invalid_historical_catalog_is_not_treated_as_an_empty_catalog(self) -> None:
        self.catalog.write_text("not json")
        self.commit("Broken metadata")
        with self.assertRaises(json.JSONDecodeError):
            collect_updates(self.root)
