"""Render case updates from committed public history, without a second registry."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any


PUBLIC_REPOSITORY = "https://github.com/xi-zhao/runthepaper"
KINDS = {"added": "Added / 新增", "updated": "Updated / 更新", "removed": "Removed / 移出"}
AREAS = {
    "catalog": "Catalog / 目录信息",
    "code": "Code / 代码",
    "notes": "Derivation and notes / 推导与讲义",
    "data": "Data / 数据",
    "figures": "Figures / 图片",
    "checks": "Checks and provenance / 检查与来源",
    "other": "Other case files / 其他案例文件",
}


@dataclass(frozen=True)
class CaseChange:
    paper_id: str
    title: str
    kind: str
    areas: tuple[str, ...]


@dataclass(frozen=True)
class LibraryUpdate:
    revision: str
    parent: str | None
    date: str
    subject: str
    changes: tuple[CaseChange, ...]


def classify_changes(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    changed_paths: list[str],
) -> tuple[CaseChange, ...]:
    """Count identities once; file changes never imply scientific improvement."""
    areas: dict[str, set[str]] = {}
    for paper_id in before.keys() | after.keys():
        if before.get(paper_id) != after.get(paper_id):
            areas[paper_id] = {"catalog"}
    for name in changed_paths:
        parts = Path(name).parts
        if len(parts) < 3 or parts[0] != "cases":
            continue
        paper_id = parts[1]
        if paper_id not in before and paper_id not in after:
            continue
        area = "other"
        if parts[2] == "code":
            area = "code"
        elif parts[2] in {"note", "docs", "README.md"}:
            area = "notes"
        elif len(parts) > 3 and parts[2] == "outputs" and parts[3] in AREAS:
            area = parts[3]
        areas.setdefault(paper_id, set()).add(area)
    changes = []
    for paper_id, changed_areas in sorted(areas.items()):
        kind = "added" if paper_id not in before else "removed" if paper_id not in after else "updated"
        case = after.get(paper_id) or before[paper_id]
        changes.append(CaseChange(paper_id, str(case.get("title", paper_id)), kind, tuple(sorted(changed_areas))))
    return tuple(changes)


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments], check=True, capture_output=True, text=True,
    ).stdout


def _catalog_at(root: Path, revision: str | None) -> dict[str, dict[str, Any]]:
    if revision is None:
        return {}
    # Early history may predate the catalog. Missing files are different from bad JSON.
    exists = _git(root, "ls-tree", "--name-only", revision, "--", "cases/catalog.json")
    if not exists.strip():
        return {}
    payload = json.loads(_git(root, "show", f"{revision}:cases/catalog.json"))
    return {str(case["paper_id"]): case for case in payload["cases"]}


def collect_updates(root: Path, limit: int = 5) -> list[LibraryUpdate]:
    if limit < 1:
        raise ValueError("update limit must be positive")
    if _git(root, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise ValueError("Update history requires a full Git clone; fetch the missing history before regenerating it.")
    revisions = _git(root, "log", "--first-parent", "--format=%H", "--", "cases").splitlines()
    updates: list[LibraryUpdate] = []
    for revision in revisions:
        parents = _git(root, "rev-list", "--parents", "-n", "1", revision).split()[1:]
        parent = parents[0] if parents else None
        if parent is None:
            paths = _git(root, "diff-tree", "--root", "--no-commit-id", "--name-only", "--no-renames", "-r", "-z", revision, "--", "cases")
        else:
            paths = _git(root, "diff", "--name-only", "--no-renames", "-z", parent, revision, "--", "cases")
        changes = classify_changes(_catalog_at(root, parent), _catalog_at(root, revision), paths.strip("\0").split("\0"))
        if not changes:
            continue
        date, subject = _git(root, "show", "-s", "--format=%cs%n%s", revision).rstrip("\n").split("\n", 1)
        updates.append(LibraryUpdate(revision, parent, date, subject, changes))
        if len(updates) == limit:
            break
    return updates


def _markdown_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")


def render_updates(updates: list[LibraryUpdate]) -> str:
    lines = [
        "# Case Updates / 案例增量更新", "",
        "[Library / 论文目录](CASES.md) · [Learning paths / 学习路径](LEARNING_PATHS.md) · [Paper timeline / 论文年代](HISTORY.md)", "",
        "Recent case changes from committed Git history, newest first. Each entry links the exact revision; a file update does not assert a successful reproduction or improved score.",
        "按时间倒序列出已提交的案例变更，区分新增、更新和移出，并链接到对应版本。代码、数据或证据文件的更新不自动意味着复现完成或分数提高。", "",
        "This page records repository history, including any local commits awaiting publication. Uncommitted edits, top-level navigation, and learning-route definitions are excluded. Regenerating unchanged content creates no update.",
        "这里记录仓库提交历史，可能包含尚未推送的本地提交；未提交改动、顶层导航和学习路径定义不计入。重新生成相同内容不会产生案例更新。", "",
    ]
    if not updates:
        lines.extend(["No committed case changes are available. / 暂无已提交的案例变更。", ""])
    for update in updates:
        counts = Counter(change.kind for change in update.changes)
        lines.extend([
            f"## {update.date} — {_markdown_text(update.subject)}", "",
            f"[Commit / 提交 {update.revision[:7]}]({PUBLIC_REPOSITORY}/commit/{update.revision}) · "
            f"Added / 新增 {counts['added']} · Updated / 更新 {counts['updated']} · Removed / 移出 {counts['removed']}", "",
        ])
        if len(update.changes) > 8:
            lines.extend(["<details>", f"<summary>View {len(update.changes)} affected papers / 查看涉及的论文</summary>", ""])
        lines.extend(["| Paper / 论文 | Change / 变更 | Files affected / 涉及内容 |", "| --- | --- | --- |"])
        for change in update.changes:
            revision = update.parent if change.kind == "removed" else update.revision
            link = f"{PUBLIC_REPOSITORY}/tree/{revision}/cases/{change.paper_id}"
            lines.append(
                f"| [{_markdown_text(change.title)}]({link}) | {KINDS[change.kind]} "
                f"| {'; '.join(AREAS[area] for area in change.areas)} |"
            )
        if len(update.changes) > 8:
            lines.extend(["", "</details>"])
        lines.append("")
    lines.extend([
        "## Refreshing this page / 如何更新", "",
        "After the validated case projection is committed, run `python scripts/render_case_catalog.py`. The same command refreshes the directory, learning paths, paper timeline, and this history. Scientific state is always imported from PRAgent; it is never inferred from this changelog.",
        "案例投影通过检查并提交后，运行 `python scripts/render_case_catalog.py`，即可同步刷新目录、学习路径、论文时间线与本页。科学状态始终来自 PRAgent 的案例证据，不由更新日志裁决。", "",
    ])
    return "\n".join(lines)
