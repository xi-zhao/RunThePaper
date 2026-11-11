#!/usr/bin/env python3
"""Read frozen public archives; never import case code or rerun scientific checks."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any
from validate_plan import SOURCE_COMMIT, validate, validate_repository_source

HERE = Path(__file__).resolve().parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class Archive:
    """Read Git objects at one immutable revision, never the live case tree."""
    def __init__(self, root: Path, revision: str = SOURCE_COMMIT):
        self.root, self.revision = root.resolve(), revision
        tree = subprocess.run(["git", "ls-tree", "-rz", revision, "--", "cases", "evaluation/claim-first-100/data"], cwd=self.root, check=True, capture_output=True).stdout
        self.blobs = {}
        for entry in tree.split(b"\0"):
            if not entry:
                continue
            metadata, path = entry.split(b"\t", 1)
            mode, kind, oid = metadata.decode().split()
            if kind == "blob" and mode == "100644":
                self.blobs[path.decode()] = oid
            elif kind == "blob" and mode == "100755":
                self.blobs[path.decode()] = oid
        self.reads = {}
        self.cache = {}

    def read(self, path: str) -> bytes | None:
        if path not in self.blobs:
            return None
        if path not in self.cache:
            data = subprocess.run(["git", "cat-file", "blob", self.blobs[path]], cwd=self.root, check=True, capture_output=True).stdout
            self.reads[path] = {"path": path, "git_blob_sha1": self.blobs[path], "sha256": sha256(data), "bytes": len(data)}
            # Cache metadata only; large arrays are hashed once without retaining their bytes.
            if len(data) < 2_000_000:
                self.cache[path] = data
            return data
        return self.cache[path]

    def json(self, path: str) -> dict:
        data = self.read(path)
        return json.loads(data) if data else {}

    def record(self, path: str) -> dict:
        if path not in self.reads:
            self.read(path)
        return self.reads.get(path, {"path": path, "availability": "not_in_frozen_public_archive"})


def resolve_reference(case_prefix: str, reference: str, blobs: dict) -> str | None:
    # Public projection moves source/config to code/, while outputs stay at the case root.
    lexical = reference.split("::", 1)[0].split("#", 1)[0]
    if lexical.startswith("workspace/"):
        lexical = lexical[len("workspace/"):]
    path = PurePosixPath(lexical)
    if path.is_absolute() or ".." in path.parts or not lexical:
        return None
    for candidate in (f"{case_prefix}/{lexical}", f"{case_prefix}/code/{lexical}", f"{case_prefix}/docs/{lexical}"):
        if candidate in blobs:
            return candidate
    return None


def as_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def scale_relation(value: str | None) -> str:
    return {"paper_exact": "paper_conditions", "reduced_scale": "reduced_scale", "paper_subset": "partial_domain", "proxy_model": "proxy"}.get(value, "unknown")


def build(archive: Archive, cohort: dict) -> dict[str, Any]:
    rows = list(csv.DictReader(io.StringIO(archive.read("evaluation/claim-first-100/data/papers.csv").decode("utf-8-sig"))))
    titles = {row["paper_id"]: row["title"] for row in rows}
    catalog = {row["paper_id"]: row for row in archive.json("cases/catalog.json").get("cases", [])}
    papers, results = [], []
    for pid in cohort["retained_historical_ids"]:
        prefix = f"cases/{pid}"
        checks = f"{prefix}/outputs/checks"
        inventory = archive.json(f"{checks}/figure_coverage.json")
        scorecard = archive.json(f"{checks}/similarity_scorecard.json")
        completion = archive.json(f"{checks}/completion_assessment.json")
        provenance = archive.json(f"{checks}/publication_provenance.json")
        review = archive.json(f"{checks}/independent_review.json")
        targets = {row["target_id"]: row for row in scorecard.get("targets", [])}
        items = list(inventory.get("items", []))
        mapped = {tid for item in items for tid in item.get("target_ids", [])}
        unmapped = sorted(set(targets) - mapped)
        # These are flagged recovery rows, not extra independent paper results.
        items += [{"item_id": f"unmapped-target:{tid}", "item_type": "unmapped_archived_target", "target_ids": [tid], "scientific_object": targets[tid].get("label"), "source_ref": "; ".join(as_strings(targets[tid].get("figure_refs"))), "kind": "unknown"} for tid in unmapped]
        seen = set()
        for index, item in enumerate(items):
            iid = item.get("item_id")
            if not iid or iid in seen:
                raise ValueError(f"Missing or duplicate archived object: {pid}/{iid}")
            seen.add(iid)
            linked, refs, unavailable = [], set(), set()
            for tid in item.get("target_ids", []):
                target = targets.get(tid)
                if target is None:
                    unavailable.add(f"target:{tid}")
                    continue
                evaluation = target.get("evaluation", {})
                linked.append({"target_id": tid, "label": target.get("label"), "archived_parameter_match": evaluation.get("parameter_match"), "archived_scale_relation": scale_relation(evaluation.get("parameter_match")), "archived_generated_data_provenance": evaluation.get("generated_data_provenance"), "archived_formula_gate": evaluation.get("formula_gate"), "archived_reference_comparison": evaluation.get("reference_comparison"), "archived_failure_type": evaluation.get("failure_type"), "remaining_gap": target.get("remaining_gap"), "source_pointer": f"{checks}/similarity_scorecard.json#/targets/{list(targets).index(tid)}"})
                for value in as_strings(target.get("evidence")) + as_strings(target.get("primary_metric", {}).get("evidence")):
                    resolved = resolve_reference(prefix, value, archive.blobs)
                    if resolved:
                        refs.add(resolved)
                    elif not PurePosixPath(value).is_absolute():
                        unavailable.add(value)
            evidence = []
            for path in sorted(refs):
                metadata = dict(archive.record(path))
                kind = "generated_data" if "/outputs/data/" in path else "stored_check" if "/outputs/checks/" in path else "implementation_or_document"
                metadata.update({"kind": kind, "inspection": "bytes_hashed", "scientific_contents_reverified": False})
                evidence.append(metadata)
            # A passing historical file is not a new scientific verdict.
            limits = ["Original paper scope and scientific values have not been rechecked by this extraction.", "Archived target labels are source declarations, not newly accepted conclusions."]
            if unmapped and item["item_type"] == "unmapped_archived_target":
                limits.append("Target absent from archived original-object inventory; reconcile before counting results.")
            if unavailable:
                limits.append("Referenced evidence is absent from this public projection; no claim about private archives.")
            row = {"record_type": "archive_evidence_record", "paper_id": pid, "cohort_group": "historical_97", "result_id": iid, "record_origin": "unmapped_archived_target" if index >= len(inventory.get("items", [])) else "archived_original_object", "source": {"paper_version": None, "locator": item.get("source_ref"), "scope_complete": None, "scientific_object": item.get("scientific_object"), "kind": item.get("kind"), "item_type": item.get("item_type"), "inventory_pointer": f"{checks}/figure_coverage.json#/items/{index}" if index < len(inventory.get("items", [])) else None}, "archived_scope": {key: item.get(key) for key in ["decision", "reason", "denominator_role", "scientific_role", "claim_refs", "target_ids"]}, "actual_conditions": {"model": None, "parameters": None, "scale_relation": "unknown", "method_provenance": None}, "archived_targets": linked, "artifacts": evidence, "unresolved_public_references": sorted(unavailable), "comparison": {key: None for key in ["reference", "metric", "observed_value", "reference_value", "uncertainty", "tolerance", "tolerance_basis"]}, "existing_checks": [x["path"] for x in evidence if x["kind"] == "stored_check"], "review": {"basis": "archive_metadata_and_bytes_inspected", "outcome": "not_evaluated", "limits": limits, "reviewed_files": [x["path"] for x in evidence]}, "execution": {"system_version": None, "model": None, "human_interventions": None, "record_ref": None, "new_scientific_execution": False}, "count_as_independent_result": False}
            results.append(row)
        paper_files = sorted(path for path in archive.blobs if path.startswith(prefix + "/"))
        papers.append({"paper_id": pid, "title": titles[pid], "cohort_group": "historical_97", "preprint": catalog.get(pid, {}).get("preprint"), "publication": catalog.get(pid, {}).get("publication"), "master_git_sha": provenance.get("master_git_sha"), "archived_case_status": completion.get("authoritative_status"), "archived_dimensions": completion.get("dimensions", {}), "original_inventory_rows": len(inventory.get("items", [])), "unmapped_archived_target_rows": len(unmapped), "evidence_rows": len(items), "original_scope_rechecked": False, "new_scientific_execution": False, "model": None, "human_interventions": None, "public_code_files": sum('/code/' in x and x.endswith('.py') for x in paper_files), "public_data_files": sum('/outputs/data/' in x for x in paper_files), "public_check_files": sum('/outputs/checks/' in x for x in paper_files), "stored_review_available": bool(review), "stored_review_status": review.get("status"), "archived_review_currentness": completion.get("dimensions", {}).get("independent_review"), "source_refs": [f"{checks}/figure_coverage.json", f"{checks}/similarity_scorecard.json", f"{checks}/completion_assessment.json", f"{checks}/publication_provenance.json"], "next_action": "Reconcile original objects and read source/derivation/data values; preserve all unresolved rows."})
    if len(papers) != 97:
        raise ValueError("Fixed historical population must contain 97 papers")
    summary = {"schema_version": 1, "source_repository": "xi-zhao/RunThePaper", "source_commit": archive.revision, "scope": "historical_archive_extraction_not_scientific_reassessment", "historical_papers": len(papers), "original_inventory_rows": sum(p["original_inventory_rows"] for p in papers), "unmapped_target_rows": sum(p["unmapped_archived_target_rows"] for p in papers), "evidence_records": len(results), "records_with_referenced_public_artifacts": sum(bool(r["artifacts"]) for r in results), "records_with_unresolved_public_references": sum(bool(r["unresolved_public_references"]) for r in results), "archived_status_counts": dict(sorted(Counter(p["archived_case_status"] for p in papers).items())), "original_scope_rechecked_papers": 0, "new_scientific_executions": 0, "new_scientific_verdicts": 0, "headline_success_rate": None, "H1_status": "archive_extraction_complete_source_semantic_review_pending", "new_papers": [{"paper_id": r["paper_id"], "execution_status": r["execution_status"]} for r in cohort["prospective_additions"]]}
    return {"papers": papers, "results": results, "summary": summary, "inputs": [archive.reads[p] for p in sorted(archive.reads)]}


def write_outputs(output: Path, product: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for key in ["papers", "results", "inputs"]:
        (output / (key + ".jsonl")).write_text("".join(dumps(row) + "\n" for row in product[key]), encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(product["summary"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "papers.csv").open("w", encoding="utf-8", newline="") as stream:
        keys = ["paper_id", "title", "archived_case_status", "original_inventory_rows", "unmapped_archived_target_rows", "evidence_rows", "public_code_files", "public_data_files", "public_check_files", "stored_review_available", "archived_review_currentness", "original_scope_rechecked", "new_scientific_execution"]
        writer = csv.DictWriter(stream, fieldnames=keys, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(product["papers"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=HERE.parents[1])
    parser.add_argument("--output", type=Path, default=HERE / "data")
    args = parser.parse_args()
    cohort = json.loads((HERE / "cohort.json").read_text())
    validate(cohort, json.loads((HERE / "RESULT_RECORD_TEMPLATE.json").read_text()))
    validate_repository_source(cohort, args.repository_root)
    product = build(Archive(args.repository_root), cohort)
    if args.output.resolve().is_relative_to((args.repository_root / "cases").resolve()):
        raise ValueError("Analysis output must not modify historical cases")
    write_outputs(args.output, product)
    print(json.dumps(product["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
