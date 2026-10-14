from __future__ import annotations

import json
import hashlib
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "cases" / "catalog.json"
CASE_CONTRACT = "paper_reproduction_only_v1"
TEXT_SUFFIXES = {
    ".csv",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".qasm",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
FORBIDDEN_PATH_PARTS = {
    "original_figures",
    "reference_curves",
    "source_figures",
    "source_vs_generated",
}
FORBIDDEN_TEXT = {
    "/Users/",
    "/home/jovyan",
    "agent/harness",
    "raw/source",
    "references/original_figures",
    "outputs/reference_curves",
    "outputs/source_figures",
    "outputs/comparisons",
    "source_vs_generated",
    "workspace/",
}
SECRET_PATTERNS = {
    "GitHub token": re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
DOI = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
AUTHORITY_SOURCE = "PRAgent authoritative_reproduction_state schema v3"
RESULT_REQUIRED_STATUSES = {
    "complete",
    "review_pending",
    "visual_pending",
    "paper_error_candidate",
}


def load_catalog() -> list[dict[str, Any]]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if (
        payload.get("schema_version") != 2
        or payload.get("case_contract") != CASE_CONTRACT
        or payload.get("authority_source") != AUTHORITY_SOURCE
        or not isinstance(cases, list)
    ):
        raise ValueError(
            "cases/catalog.json does not match schema version 2 and the "
            f"{CASE_CONTRACT} contract with {AUTHORITY_SOURCE} authority"
        )
    return cases


def text_files(case_dir: Path) -> list[Path]:
    return [
        path
        for path in case_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    ]


def scientific_python_files(case_dir: Path) -> list[Path]:
    """Return implementations, excluding package markers and artifact-only checks."""

    return [
        path
        for path in (case_dir / "code").rglob("*.py")
        if path.name not in {"__init__.py", "verify_public_artifacts.py"}
    ]


def requires_generated_results(case: dict[str, Any]) -> bool:
    """Require frozen data and figures only when the lifecycle claims results.

    A partial case may be published precisely to expose a failed or objectively
    blocked attempt.  Requiring successful result artifacts from that state
    would either reject honest cases or encourage placeholder outputs.
    """

    return str(case.get("authoritative_status", "")) in RESULT_REQUIRED_STATUSES


def validate_markdown_links(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for raw_target in MARKDOWN_LINK.findall(text):
        target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = target.split("#", 1)[0]
        if "/" not in target and "." not in target:
            # Avoid interpreting adjacent LaTeX expressions such as ``[...](1,1)``
            # as Markdown links.
            continue
        if not (path.parent / target).resolve().exists():
            errors.append(
                f"broken Markdown link in {path.relative_to(ROOT)}: {raw_target}"
            )


def validate_paper_identity(case: dict[str, Any], errors: list[str]) -> None:
    paper_id = str(case.get("paper_id", "<missing>"))
    preprint = case.get("preprint")
    publication = case.get("publication")
    preprint_identified = (
        isinstance(preprint, dict)
        and preprint.get("status") != "not_recorded"
        and all(
            isinstance(preprint.get(field), str) and preprint[field].strip()
            for field in ("identifier", "title", "url")
        )
    )
    publication_identified = (
        isinstance(publication, dict)
        and publication.get("status") == "published"
        and all(
            isinstance(publication.get(field), str) and publication[field].strip()
            for field in ("title", "venue", "citation", "doi", "doi_url", "locator")
        )
    )
    if not (preprint_identified or publication_identified):
        errors.append(
            f"{paper_id} is not an identifiable paper reproduction: "
            "both preprint and formal publication identities are unverified"
        )

    if not isinstance(preprint, dict):
        errors.append(f"{paper_id} has no preprint identity")
    elif preprint.get("status") == "not_recorded":
        checked_at = preprint.get("checked_at")
        if not isinstance(checked_at, str) or not DATE.match(checked_at):
            errors.append(
                f"{paper_id} not_recorded preprint requires checked_at YYYY-MM-DD"
            )
    else:
        for field in ("identifier", "title", "url"):
            if not isinstance(preprint.get(field), str) or not preprint[field].strip():
                errors.append(f"{paper_id} has no preprint.{field}")

    if not isinstance(publication, dict):
        errors.append(f"{paper_id} has no formal publication status")
        return
    status = publication.get("status")
    if status == "published":
        for field in ("title", "venue", "citation", "doi", "doi_url", "locator"):
            if (
                not isinstance(publication.get(field), str)
                or not publication[field].strip()
            ):
                errors.append(f"{paper_id} has no publication.{field}")
        doi = publication.get("doi", "")
        if isinstance(doi, str) and doi and not DOI.match(doi):
            errors.append(f"{paper_id} has invalid publication DOI: {doi}")
        if publication.get("doi_url") != f"https://doi.org/{doi}":
            errors.append(f"{paper_id} DOI URL does not match publication DOI")
    elif status == "not_recorded":
        checked_at = publication.get("checked_at")
        if not isinstance(checked_at, str) or not DATE.match(checked_at):
            errors.append(
                f"{paper_id} not_recorded status requires checked_at YYYY-MM-DD"
            )
    else:
        errors.append(f"{paper_id} has invalid publication status: {status!r}")


def validate_authority_projection(
    case: dict[str, Any], case_dir: Path, errors: list[str]
) -> None:
    """Require public lifecycle metadata to agree with its PRAgent projection."""

    paper_id = str(case.get("paper_id", ""))
    if case.get("registry_scope") != "paper_reproduction":
        errors.append(f"{paper_id} registry_scope is not paper_reproduction")
    authoritative_status = case.get("authoritative_status")
    if not isinstance(authoritative_status, str) or not authoritative_status.strip():
        errors.append(f"{paper_id} has no authoritative_status")
    complete = case.get("complete")
    if not isinstance(complete, bool):
        errors.append(f"{paper_id} complete must be boolean")
    elif complete is not (authoritative_status == "complete"):
        errors.append(f"{paper_id} complete flag disagrees with authoritative_status")
    master_git_sha = case.get("master_git_sha")
    if not isinstance(master_git_sha, str) or not GIT_SHA.fullmatch(master_git_sha):
        errors.append(f"{paper_id} has invalid master_git_sha")

    completion_path = case_dir / "outputs/checks/completion_assessment.json"
    provenance_path = case_dir / "outputs/checks/publication_provenance.json"
    for label, path in (
        ("completion assessment", completion_path),
        ("publication provenance", provenance_path),
    ):
        if not path.is_file():
            errors.append(f"missing {label}: {path.relative_to(ROOT)}")
            return
    try:
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid authority projection for {paper_id}: {exc}")
        return
    for label, payload in (("completion", completion), ("provenance", provenance)):
        if payload.get("paper_id") != paper_id:
            errors.append(f"{paper_id} {label} paper_id mismatch")
        if payload.get("authoritative_status") != authoritative_status:
            errors.append(f"{paper_id} {label} authoritative_status mismatch")
        if payload.get("complete") is not complete:
            errors.append(f"{paper_id} {label} complete flag mismatch")
    if provenance.get("master_git_sha") != master_git_sha:
        errors.append(f"{paper_id} provenance master_git_sha mismatch")
    if (case.get("authority_mode") == "native"
            or completion.get("authority_mode") == "native"
            or provenance.get("authority_mode") == "native"
            or completion.get("format") == "pragent.public-native-assessment.v1"
            or any("source_run_id" in p or "source_version" in p
                   for p in (completion, provenance))):
        validate_native_publication(case, case_dir, completion, provenance, errors)


def validate_native_publication(case, case_dir, completion, provenance, errors):
    """Package admission is separate from scientific completion and source access."""
    paper_id = case["paper_id"]
    for label, payload in (("catalog", case), ("completion", completion),
                           ("provenance", provenance)):
        if payload.get("authority_mode") != "native":
            errors.append(f"{paper_id} {label} authority_mode mismatch")
    if completion.get("assessment_freshness") != "current":
        errors.append(f"{paper_id} native assessment is not current")
    if completion.get("integrity") != "valid":
        errors.append(f"{paper_id} native assessment integrity is not valid")
    for field in ("source_run_id", "source_version", "source_snapshot_sha256"):
        value = completion.get(field)
        valid = (isinstance(value, int) and not isinstance(value, bool) and value > 0
                 if field == "source_version" else
                 isinstance(value, str) and bool(re.fullmatch(
                     r"[0-9a-f]{64}" if field == "source_snapshot_sha256"
                     else r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", value)))
        if (not valid or provenance.get(field) != value
                or type(provenance.get(field)) is not type(value)):
            errors.append(f"{paper_id} missing or inconsistent {field}")
    if completion.get("master_git_sha") != case.get("master_git_sha"):
        errors.append(f"{paper_id} completion master_git_sha mismatch")
    manifest_path = case_dir / "outputs/checks/publication_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (manifest.get("format") != "runthepaper.publication-manifest.v1"
                or manifest.get("paper_id") != paper_id
                or manifest.get("master_git_sha") != case.get("master_git_sha")):
            raise ValueError("manifest identity mismatch")
        files = manifest["files"]
        if not isinstance(files, dict) or not files:
            raise ValueError("empty manifest")
        generated = {"README.md", "code/README.md", "note/reproduction-note.md"}
        excluded = generated | {"outputs/checks/publication_manifest.json"}
        actual = {p.relative_to(case_dir).as_posix() for p in case_dir.rglob("*")
                  if p.is_file() and p.suffix != ".pyc" and p.name != ".DS_Store"}
        if set(files) != actual - excluded:
            errors.append(f"{paper_id} publication file inventory mismatch")
        for name, expected in files.items():
            path = case_dir / name
            if (not isinstance(name, str) or not name or Path(name).is_absolute()
                    or ".." in Path(name).parts or path.is_symlink()
                    or not path.resolve().is_relative_to(case_dir.resolve())):
                errors.append(f"{paper_id} unsafe manifest path")
                continue
            if (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected)
                    or not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
                errors.append(f"{paper_id} publication hash mismatch: {name}")
        lineage = provenance.get("files")
        if not isinstance(lineage, list) or not lineage:
            raise ValueError("missing source lineage")
        seen = set()
        for row in lineage:
            name = row["public_path"]
            if (name in seen or name not in files
                    or row.get("public_sha256") != files[name]
                    or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("source_sha256", "")))):
                errors.append(f"{paper_id} invalid source lineage: {name}")
            seen.add(name)
            if row.get("transformation") not in {"byte-for-byte", "path-only adaptation/redaction"}:
                errors.append(f"{paper_id} unknown source transformation: {name}")
            if (row.get("transformation") == "byte-for-byte"
                    and row.get("source_sha256") != row.get("public_sha256")):
                errors.append(f"{paper_id} byte-for-byte source hash mismatch: {name}")
        derived = provenance.get("generated_checks")
        if (not isinstance(derived, list) or len(set(derived)) != len(derived)
                or any(not isinstance(p, str) or not p.startswith("outputs/checks/")
                       or not p.endswith(".json") or p not in files for p in derived)):
            errors.append(f"{paper_id} invalid generated-check inventory")
        elif set(files) != seen | set(derived) | {"outputs/checks/publication_provenance.json"}:
            errors.append(f"{paper_id} source lineage does not cover the publication")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        errors.append(f"{paper_id} invalid publication manifest: {exc}")


def validate_scorecard(case: dict[str, Any], scorecard: dict[str, Any]) -> None:
    catalog_score = case["audit_score"]
    scorecard_score = scorecard["overall_score"]
    if catalog_score is None or scorecard_score is None:
        if not (catalog_score is None and scorecard_score is None
                and scorecard.get("score_status") == "not_assessed"
                and isinstance(scorecard.get("reason"), str)
                and scorecard["reason"].strip()):
            raise ValueError("unscored cases require matching null scores and an explicit not_assessed reason")
        return
    left, right = float(catalog_score), float(scorecard_score)
    if not all(math.isfinite(v) and 0 <= v <= 100 for v in (left, right)):
        raise ValueError("scores must be finite and between 0 and 100")
    if abs(left-right) > 0.005:
        raise ValueError(f"catalog/scorecard mismatch: {left} != {right}")


def validate_case(case: dict[str, Any], errors: list[str]) -> None:
    paper_id = str(case.get("paper_id", ""))
    case_dir = ROOT / "cases" / paper_id
    required_files = [
        case_dir / "README.md",
        case_dir / "code" / "README.md",
        case_dir / "note" / "reproduction-note.md",
        case_dir / "note" / "reproduction-note.zh-CN.md",
        case_dir / "note" / "reproduction-note.en.md",
        case_dir / "outputs" / "checks" / "similarity_scorecard.json",
        case_dir / "outputs" / "checks" / "completion_assessment.json",
        case_dir / "outputs" / "checks" / "publication_provenance.json",
    ]
    for path in required_files:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")
    validate_authority_projection(case, case_dir, errors)
    for note_name in ("reproduction-note.zh-CN.md", "reproduction-note.en.md"):
        note = case_dir / "note" / note_name
        if note.is_file() and len(note.read_text(encoding="utf-8").strip()) < 200:
            errors.append(f"note is too short to be useful: {note.relative_to(ROOT)}")

    for resource in case.get("additional_resources", []):
        if not isinstance(resource, dict) or not all(
            isinstance(resource.get(field), str) and resource[field].strip()
            for field in ("label", "path")
        ):
            errors.append(f"invalid additional resource for {paper_id}: {resource!r}")
            continue
        resource_path = (case_dir / resource["path"]).resolve()
        if (
            case_dir.resolve() not in resource_path.parents
            or not resource_path.is_file()
        ):
            errors.append(
                f"missing additional resource for {paper_id}: {resource['path']}"
            )

    required_groups = {
        "scientific Python implementation": scientific_python_files(case_dir),
        "machine-readable check": [
            p for p in (case_dir / "outputs" / "checks").rglob("*.json") if p.is_file()
        ],
    }
    if requires_generated_results(case):
        required_groups.update(
            {
                "generated data": [
                    p
                    for p in (case_dir / "outputs" / "data").rglob("*")
                    if p.is_file()
                ],
                "generated figure": [
                    p
                    for p in (case_dir / "outputs" / "figures").rglob("*")
                    if p.is_file()
                ],
            }
        )
    for label, paths in required_groups.items():
        if not paths:
            errors.append(f"{paper_id} has no {label}")

    for script in [*case.get("run_scripts", []), *case.get("full_run_scripts", [])]:
        path = case_dir / "code" / "scripts" / str(script)
        if not path.is_file():
            errors.append(
                f"catalog run script does not exist: {path.relative_to(ROOT)}"
            )

    for result in case.get("featured_results", []):
        if not isinstance(result, dict):
            errors.append(f"invalid featured result for {paper_id}: {result!r}")
            continue
        for field, directory in (("figure", "figures"), ("check", "checks")):
            name = str(result.get(field, ""))
            path = case_dir / "outputs" / directory / name
            if not name or not path.is_file():
                errors.append(
                    f"featured result {field} does not exist for {paper_id}: "
                    f"{path.relative_to(ROOT)}"
                )

    scorecard_path = case_dir / "outputs" / "checks" / "similarity_scorecard.json"
    if scorecard_path.is_file():
        try:
            scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
            validate_scorecard(case, scorecard)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid scorecard contract for {paper_id}: {exc}")

    for path in case_dir.rglob("*"):
        relative = path.relative_to(case_dir)
        if path.is_symlink():
            errors.append(f"symlink is not allowed: {path.relative_to(ROOT)}")
        if any(part in FORBIDDEN_PATH_PARTS for part in relative.parts):
            errors.append(f"forbidden public path: {path.relative_to(ROOT)}")
        if path.is_file() and (
            path.suffix.lower() == ".eps" or path.name == "paper.pdf"
        ):
            errors.append(
                f"source publication asset is not allowed: {path.relative_to(ROOT)}"
            )
        if (
            path.is_file()
            and path.suffix.lower() == ".pdf"
            and path.name != "paper.pdf"
        ):
            is_derived_note = (
                relative.parent == Path("note")
                and path.name.startswith("reproduction-note")
                and path.with_suffix(".md").is_file()
            )
            is_derived_document = (
                relative.parent == Path("docs") and path.with_suffix(".md").is_file()
            )
            if not (is_derived_note or is_derived_document):
                errors.append(
                    f"source publication asset is not allowed: {path.relative_to(ROOT)}"
                )
            elif path.stat().st_size < 1024 or not path.read_bytes().startswith(
                b"%PDF-"
            ):
                errors.append(f"invalid derived PDF: {path.relative_to(ROOT)}")

    for path in text_files(case_dir):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_TEXT:
            if token in text:
                errors.append(f"forbidden token {token!r} in {path.relative_to(ROOT)}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"possible {label} in {path.relative_to(ROOT)}")
        if path.suffix.lower() == ".md":
            validate_markdown_links(path, errors)

    for path in case_dir.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")


def main() -> int:
    errors: list[str] = []
    cases = load_catalog()
    seen: set[str] = set()
    for case in cases:
        paper_id = str(case.get("paper_id", ""))
        if not paper_id or paper_id in seen:
            errors.append(f"missing or duplicate paper_id: {paper_id!r}")
        seen.add(paper_id)
        validate_paper_identity(case, errors)
        validate_case(case, errors)
    case_dirs = {path.name for path in (ROOT / "cases").iterdir() if path.is_dir()}
    missing_catalog_entries = sorted(case_dirs - seen)
    stale_catalog_entries = sorted(seen - case_dirs)
    if missing_catalog_entries:
        errors.append(
            f"case folders missing from catalog: {', '.join(missing_catalog_entries)}"
        )
    if stale_catalog_entries:
        errors.append(
            f"catalog entries without case folders: {', '.join(stale_catalog_entries)}"
        )
    for root_doc in sorted(ROOT.glob("*.md")):
        if root_doc.is_file():
            validate_markdown_links(root_doc, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"public case validation failed with {len(errors)} error(s)")
        return 1
    print(f"validated {len(cases)} public cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
