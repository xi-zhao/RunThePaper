from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "cases" / "catalog.json"
COLLECTIONS_PATH = ROOT / "cases" / "collections.json"
CASE_CONTRACT = "paper_reproduction_only_v1"
AUTHORITY_SOURCE = "PRAgent authoritative_reproduction_state schema v3"
README_CATALOG_START = "<!-- case-catalog:start -->"
README_CATALOG_END = "<!-- case-catalog:end -->"


def load_catalog() -> list[dict[str, Any]]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 2
        or payload.get("case_contract") != CASE_CONTRACT
        or payload.get("authority_source") != AUTHORITY_SOURCE
    ):
        raise ValueError(
            "unsupported catalog schema, case contract, or authority source"
        )
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("catalog must contain cases")
    return [item for item in cases if isinstance(item, dict)]


def load_collections(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload = json.loads(COLLECTIONS_PATH.read_text(encoding="utf-8"))
    collections = payload.get("collections")
    if payload.get("schema_version") != 1 or not isinstance(collections, list):
        raise ValueError("cases/collections.json must use schema version 1")

    catalog_ids = {str(case["paper_id"]) for case in cases}
    collection_ids: set[str] = set()
    grouped_ids: list[str] = []
    required_text = (
        "id",
        "title_zh",
        "title_en",
        "description_zh",
        "description_en",
    )
    for collection in collections:
        if not isinstance(collection, dict):
            raise ValueError("every collection must be an object")
        for field in required_text:
            value = collection.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"collection requires non-empty {field}")
        collection_id = str(collection["id"])
        if collection_id in collection_ids:
            raise ValueError(f"duplicate collection id: {collection_id}")
        collection_ids.add(collection_id)

        paper_ids = collection.get("paper_ids")
        if not isinstance(paper_ids, list) or not paper_ids:
            raise ValueError(f"collection {collection_id} must contain paper_ids")
        grouped_ids.extend(str(paper_id) for paper_id in paper_ids)

    if len(grouped_ids) != len(set(grouped_ids)):
        raise ValueError("a paper may appear in only one primary collection")
    grouped_set = set(grouped_ids)
    unknown = sorted(grouped_set - catalog_ids)
    missing = sorted(catalog_ids - grouped_set)
    if unknown or missing:
        raise ValueError(
            f"collection coverage mismatch; unknown={unknown}, missing={missing}"
        )
    return collections


def preprint_reference(case: dict[str, Any]) -> str:
    preprint = case["preprint"]
    if preprint.get("status") == "not_recorded":
        return (
            f"No preprint recorded / 未检索到预印本（checked {preprint['checked_at']}）"
        )
    return f"[{preprint['identifier']}]({preprint['url']})"


def publication_reference(case: dict[str, Any]) -> str:
    publication = case["publication"]
    if publication["status"] == "published":
        return (
            f"[{publication['citation']}]({publication['doi_url']}) · "
            f"DOI `{publication['doi']}`"
        )
    return f"Not recorded / 未检索到正式发表（checked {publication['checked_at']}）"


def paper_reference(case: dict[str, Any]) -> str:
    return f"{preprint_reference(case)}<br>{publication_reference(case)}"


def catalog_focus(case: dict[str, Any]) -> str:
    topic = str(case["topic"]).strip()
    if topic.startswith("Independent scientific reproduction of "):
        return "Independent formula, code, and data reconstruction with explicit remaining boundaries."
    return topic


def render_readme_catalog(
    cases: list[dict[str, Any]], collections: list[dict[str, Any]]
) -> str:
    cases_by_id = {str(case["paper_id"]): case for case in cases}
    lines = [
        f"**{len(cases)} 篇公开案例，按研究主题进入。** 这里的分类是一条主要阅读路径，",
        "很多论文同时横跨多个方向。",
        "",
        f"**{len(cases)} public cases, organized as research collections.** Each paper is",
        "placed on one primary path even when its ideas cross several fields.",
        "",
        "选择一个主题展开目录，也可以进入 [完整索引](CASES.md) 查看论文身份、分数和复现边界。",
        "",
        "Choose a collection to open its catalog, or use the [detailed index](CASES.md)",
        "for paper identities, scores, and reproduction boundaries.",
        "",
        "**快速入口 / Jump to a collection**",
        "",
    ]
    for collection in collections:
        count = len(collection["paper_ids"])
        lines.append(
            f"- [{collection['title_zh']} / {collection['title_en']}"
            f"（{count}）](#collection-{collection['id']})"
        )

    for collection in collections:
        collection_id = str(collection["id"])
        paper_ids = [str(paper_id) for paper_id in collection["paper_ids"]]
        lines.extend(
            [
                "",
                f'<a id="collection-{collection_id}"></a>',
                "",
                "<details>",
                f"<summary><strong>{collection['title_zh']} / {collection['title_en']}（{len(paper_ids)}）</strong></summary>",
                "",
                str(collection["description_zh"]),
                "",
                str(collection["description_en"]),
                "",
                "| 论文 / Paper | 复现内容 / Reproduced focus | 状态 / Status | 打开 / Open |",
                "| --- | --- | --- | --- |",
            ]
        )
        for paper_id in paper_ids:
            case = cases_by_id[paper_id]
            case_root = f"cases/{paper_id}"
            paper = f"[{case['title']}]({case_root}/README.md)"
            resources = (
                f"[中文]({case_root}/note/reproduction-note.zh-CN.md) · "
                f"[EN]({case_root}/note/reproduction-note.en.md) · "
                f"[Code]({case_root}/code/README.md)"
            )
            lines.append(
                f"| {paper} | {catalog_focus(case)} | {case['status']} | {resources} |"
            )
        lines.extend(["", "</details>"])
    lines.extend(
        [
            "",
            "这里的状态描述复现范围，不是论文排名，也不是完成度奖杯。部分复现、输入缺失、算力阻塞和待独立评审都会照实保留。",
            "",
            "Status describes reproduction scope, not rank. See [how to read reproduction quality](#how-to-read-reproduction-quality) and the [detailed case index](CASES.md) for paper identities, audit scores, generated figures, checks, and explicit boundaries.",
        ]
    )
    return "\n".join(lines)


def render_root_readme(
    cases: list[dict[str, Any]], collections: list[dict[str, Any]]
) -> str:
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")
    if (
        content.count(README_CATALOG_START) != 1
        or content.count(README_CATALOG_END) != 1
    ):
        raise ValueError(
            "README.md must contain exactly one generated case-catalog block"
        )
    start = content.index(README_CATALOG_START) + len(README_CATALOG_START)
    end = content.index(README_CATALOG_END, start)
    generated = "\n" + render_readme_catalog(cases, collections) + "\n"
    return content[:start] + generated + content[end:]


def render_cases_index(cases: list[dict[str, Any]]) -> str:
    lines = [
        "# Published Cases",
        "",
        "Every case provides a public overview, Chinese and English getting-started notes, runnable code, generated data and figures, and an explicit reproduction boundary.",
        "",
        "| Paper ID | Topic | Public status | Audit score |",
        "| --- | --- | --- | ---: |",
    ]
    for case in cases:
        paper_id = str(case["paper_id"])
        lines.append(
            f"| [`{paper_id}`](cases/{paper_id}/README.md) | {case['topic']} | "
            f"{case['status']} | {float(case['audit_score']):.2f} |"
        )
    lines.extend(
        [
            "",
            "The audit score records evidence strength at export time. It is not a visual-style rating, and it does not erase the limitation stated by each case.",
            "It is also not a cross-paper ranking or a publishing threshold: publication readiness comes from satisfying the public case contract and stating the remaining boundary honestly.",
            "",
        ]
    )
    return "\n".join(lines)


def render_case_readme(case: dict[str, Any], case_dir: Path) -> str:
    paper_id = str(case["paper_id"])
    preprint = case["preprint"]
    publication = case["publication"]
    figures = sorted((case_dir / "outputs" / "figures").glob("*.png"))
    featured_results = [
        item for item in case.get("featured_results", []) if isinstance(item, dict)
    ]
    comparison_results = [
        item for item in case.get("comparison_results", []) if isinstance(item, dict)
    ]
    if preprint.get("status") == "not_recorded":
        preprint_line = (
            f"Preprint: **No preprint recorded as of {preprint['checked_at']}**"
        )
    else:
        preprint_line = f"Preprint: [{preprint['identifier']} — {preprint['title']}]({preprint['url']})"
    lines = [
        f"# {paper_id}: {case['title']}",
        "",
        preprint_line,
        "",
    ]
    if publication["status"] == "published":
        lines.extend(
            [
                f"Published as: [{publication['title']}]({publication['doi_url']})",
                "",
                f"Formal citation: {publication['citation']} · DOI `{publication['doi']}` · Locator `{publication['locator']}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"Formal publication: **Not recorded as of {publication['checked_at']}**",
                "",
            ]
        )
    lines.extend(
        [
            f"Public status: **{case['status']}** · Audit score: **{float(case['audit_score']):.2f}/100**",
            "",
            str(case["summary"]),
            "",
            "## Start Here / 从这里开始",
            "",
            "- [中文复现 Note](note/reproduction-note.zh-CN.md)",
            "- [English reproduction note](note/reproduction-note.en.md)",
        ]
    )
    for resource in case.get("additional_resources", []):
        lines.append(f"- [{resource['label']}]({resource['path']})")
    lines.extend(
        [
            "- [Code and run commands](code/README.md)",
            "- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)",
        ]
    )
    if (case_dir / "outputs" / "checks" / "completion_assessment.json").is_file():
        lines.append(
            "- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)"
        )
    if (case_dir / "note" / "reproduction-note.zh-CN.pdf").is_file():
        lines.append("- [中文复现 Note PDF](note/reproduction-note.zh-CN.pdf)")
    if (case_dir / "docs" / "DERIVATION.md").is_file():
        lines.append("- [Derivation (equations)](docs/DERIVATION.md)")
    lines.extend(
        [
            "- [Numerical methods](docs/NUMERICAL_METHODS.md)",
            "- [Lessons learned](docs/LESSONS_LEARNED.md)",
            "",
        ]
    )
    if featured_results:
        lines.extend(
            [
                "## Main Reproduced Results",
                "",
                "| Paper item | Reproduced result | Figure | Check |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in featured_results:
            figure = str(item["figure"])
            check = str(item["check"])
            lines.append(
                f"| {item['paper_item']} | {item['result']} | "
                f"[PNG](outputs/figures/{figure}) | [JSON](outputs/checks/{check}) |"
            )
        lines.append("")
    if comparison_results:
        if publication.get("status") == "published":
            cite = f"[{publication['citation']}]({publication['doi_url']})"
        else:
            cite = preprint_reference(case)
        comparison_note = case.get(
            "comparison_note",
            f"The left column in each panel is a limited excerpt from {case['comparison_attribution']}, {cite}; the right column is generated independently from this case. These comparisons validate physical structure and key numerical features, not author-data-level or point-for-point equivalence.",
        )
        lines.extend(
            [
                "## Paper Reference vs Independent Reproduction",
                "",
                str(comparison_note),
                "",
            ]
        )
        for item in comparison_results:
            lines.extend(
                [
                    f"### {item['paper_item']} comparison",
                    "",
                    f"![{item['paper_item']} paper reference versus independent reproduction](docs/comparisons/{item['figure']})",
                    "",
                ]
            )
    if featured_results:
        for item in featured_results:
            figure = str(item["figure"])
            lines.extend(
                [
                    f"### {item['paper_item']}: {item['result']}",
                    "",
                    f"![{item['paper_item']} reproduction](outputs/figures/{figure})",
                    "",
                ]
            )
    lines.extend(
        [
            "## Quick Run",
            "",
            "```bash",
            "python -m venv .venv",
            "source .venv/bin/activate",
            "pip install -r requirements.txt",
        ]
    )
    extras = [str(item) for item in case.get("extra_dependencies", [])]
    if extras:
        lines.append("pip install " + " ".join(extras))
    lines.append(f"cd cases/{paper_id}/code")
    for script in case.get("run_scripts", []):
        lines.append(render_script_command(str(script), case.get("script_arguments")))
    lines.extend(["```", ""])
    full_run_scripts = [str(item) for item in case.get("full_run_scripts", [])]
    if full_run_scripts:
        full_run_heading = str(
            case.get("full_run_heading", "Full paper-scale rerun")
        ).strip()
        lines.extend(
            [
                f"### {full_run_heading}",
                "",
                str(case["full_run_note"]),
                "",
                "```bash",
                f"cd cases/{paper_id}/code",
                *[
                    render_script_command(
                        str(script), case.get("full_run_script_arguments")
                    )
                    for script in full_run_scripts
                ],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).",
            "",
            "## Reproduction Boundary",
            "",
        ]
    )
    if comparison_results:
        lines.extend(
            [
                f"This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and {len(comparison_results)} limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.",
                "",
            ]
        )
    lines.extend(
        [
            f"Remaining limitation: {case['limitation']}",
            "",
            "Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.",
            "",
        ]
    )
    if not featured_results:
        lines.extend(["## Generated Figures", ""])
        for figure in figures:
            label = figure.stem.replace("_", " ")
            lines.extend([f"![{label}](outputs/figures/{figure.name})", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_script_command(script: str, arguments: dict[str, Any] | None = None) -> str:
    suffix = str((arguments or {}).get(script, "")).strip()
    command = f"python scripts/{script}"
    return f"{command} {suffix}" if suffix else command


def render_code_readme(case: dict[str, Any]) -> str:
    paper_id = str(case["paper_id"])
    extras = [str(item) for item in case.get("extra_dependencies", [])]
    lines = [
        f"# Runnable code for {paper_id}",
        "",
        "Run commands from the repository root unless a command below changes directory.",
        "",
        "```bash",
        "python -m venv .venv",
        "source .venv/bin/activate",
        "pip install -r requirements.txt",
    ]
    if extras:
        lines.append("pip install " + " ".join(extras))
    lines.extend([f"cd cases/{paper_id}/code"])
    run_arguments = case.get("script_arguments")
    if run_arguments is not None and not isinstance(run_arguments, dict):
        raise ValueError(f"{paper_id} script_arguments must be an object")
    for script in case.get("run_scripts", []):
        lines.append(render_script_command(str(script), run_arguments))
    lines.extend(["```", ""])
    full_run_scripts = [str(item) for item in case.get("full_run_scripts", [])]
    if full_run_scripts:
        full_run_heading = str(
            case.get("full_run_heading", "Full paper-scale rerun")
        ).strip()
        lines.extend(
            [
                f"## {full_run_heading}",
                "",
                str(case["full_run_note"]),
                "",
                "```bash",
                f"cd cases/{paper_id}/code",
                *[
                    render_script_command(
                        str(script), case.get("full_run_script_arguments")
                    )
                    for script in full_run_scripts
                ],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.",
            "",
            f"Boundary: {case['limitation']}",
            "",
        ]
    )
    return "\n".join(lines)


def render_note_index(case: dict[str, Any], case_dir: Path) -> str:
    lines = [
        f"# {case['paper_id']} reproduction notes / 复现讲义",
        "",
        "请选择语言 / Choose a language:",
        "",
        "- [中文上手讲义](reproduction-note.zh-CN.md)",
    ]
    if (case_dir / "note" / "reproduction-note.zh-CN.pdf").is_file():
        lines.append("- [中文复现讲义 PDF](reproduction-note.zh-CN.pdf)")
    lines.extend(
        [
            "- [English getting-started note](reproduction-note.en.md)",
            "",
            "Case overview: [../README.md](../README.md)",
            "",
        ]
    )
    return "\n".join(lines)


def expected_files(
    cases: list[dict[str, Any]], collections: list[dict[str, Any]]
) -> dict[Path, str]:
    rendered = {
        ROOT / "README.md": render_root_readme(cases, collections),
        ROOT / "CASES.md": render_cases_index(cases),
    }
    for case in cases:
        case_dir = ROOT / "cases" / str(case["paper_id"])
        if not case_dir.exists():
            raise FileNotFoundError(case_dir)
        rendered[case_dir / "README.md"] = render_case_readme(case, case_dir)
        rendered[case_dir / "code" / "README.md"] = render_code_readme(case)
        rendered[case_dir / "note" / "reproduction-note.md"] = render_note_index(
            case, case_dir
        )
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render public case navigation from the catalog."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated navigation is stale instead of rewriting it",
    )
    args = parser.parse_args()
    cases = load_catalog()
    collections = load_collections(cases)
    stale: list[Path] = []
    for path, content in expected_files(cases, collections).items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path.relative_to(ROOT))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if stale:
        for path in stale:
            print(f"stale generated file: {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
