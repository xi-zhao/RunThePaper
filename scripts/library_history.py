"""Paper chronology derived from recorded identities, separate from case updates."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class PaperDate:
    year: int
    basis: str
    url: str


def recorded_paper_date(case: dict[str, Any]) -> PaperDate | None:
    """Use the earliest recorded preprint/publication year, never an audit date."""
    dates: list[PaperDate] = []
    preprint = case.get("preprint", {})
    if preprint.get("status") == "available":
        identifier = preprint.get("identifier", "").removeprefix("arXiv:")
        modern = re.fullmatch(r"(\d{2})(\d{2})\.\d{4,5}(?:v\d+)?", identifier)
        legacy = re.fullmatch(r"[a-z-]+/(\d{2})(\d{2})\d{3}(?:v\d+)?", identifier)
        match = modern or legacy
        if match:
            year_part, month = int(match[1]), int(match[2])
            year = 1900 + year_part if legacy and year_part >= 91 else 2000 + year_part
            if modern:
                period_valid = (year, month) >= (2007, 4)
            else:
                period_valid = (1991, 8) <= (year, month) < (2007, 4)
            if 1 <= month <= 12 and period_valid:
                dates.append(PaperDate(year, "preprint", preprint["url"]))

    publication = case.get("publication", {})
    if publication.get("status") == "published":
        # Require an explicit citation year; page numbers and checked_at are not dates.
        years = set(re.findall(r"\(([12]\d{3})\)", publication.get("citation", "")))
        if len(years) == 1:
            dates.append(PaperDate(int(years.pop()), "publication", publication["doi_url"]))
    return min(dates, key=lambda date: date.year) if dates else None


def render_history(cases: list[dict[str, Any]]) -> str:
    dated = [(recorded_paper_date(case), case) for case in cases]
    dated.sort(key=lambda item: (item[0].year if item[0] else 10000, str(item[1]["paper_id"])))
    known = [date.year for date, _ in dated if date]
    lines = [
        "# An Executable History of Science / 可执行的科学史",
        "",
        "[English introduction](README.md) · [中文介绍](README.zh-CN.md) · [Research collections / 学科目录](CASES.md) · [Learning paths / 学习路径](LEARNING_PATHS.md)",
        "",
        "Follow the recorded paper years, then open a case to explore its derivation, implementation, and evidence. The current collection focuses on physics and quantum science.",
        "沿论文年代回看研究，进入案例重走推导、实现和验证的过程。当前收录以物理学和量子科学为主。",
        "",
        "This is a chronology of the papers currently included. Curated accounts of how discoveries and methods connect are future work; dates alone do not establish influence or priority.",
        "这里呈现已收录论文的年代顺序。发现与方法之间的联系还需要逐条考证和编写，不能仅由时间先后推断。",
        "",
        "Each entry uses the earlier year of its recorded arXiv identifier or an explicit year in parentheses in its publication citation, with a source link. Ambiguous or missing years remain undated. Paper dates and [case update dates](UPDATES.md) have separate records.",
        "每项取已记录 arXiv 编号年份与正式引文中明确标注的括号年份中较早者，并链接到依据。缺失或有歧义的年份列入待补充。论文年代与[复现材料更新日期](UPDATES.md)分别记录。",
        "",
    ]
    if known:
        lines.extend([
            f"**{len(cases)} paper cases / 篇论文案例 · recorded years / 已记录年代 {min(known)}–{max(known)}**", "",
        ])
    decades = sorted({year // 10 * 10 for year in known})
    lines.extend(f"- [{decade}s / {decade} 年代](#decade-{decade})" for decade in decades)
    if any(date is None for date, _ in dated):
        lines.append("- [Year not recorded / 年代待补充](#undated)")
    previous_group: int | str | None = None
    for date, case in dated:
        group = date.year // 10 * 10 if date else "undated"
        if group != previous_group:
            heading = f"{group}s / {group} 年代" if date else "Year not recorded / 年代待补充"
            anchor = f"decade-{group}" if date else "undated"
            lines.extend([
                "", f'<a id="{anchor}"></a>', "", f"## {heading}", "",
                "| Year / 年代 | Paper / 论文 | Recorded status / 已记录状态 | Explore / 动手研究 |",
                "| --- | --- | --- | --- |",
            ])
            previous_group = group
        case_root = f"cases/{case['paper_id']}"
        if date:
            basis = "preprint / 预印本" if date.basis == "preprint" else "publication / 发表"
            year_label = f"{date.year}<br>[{basis}]({date.url})"
        else:
            year_label = "Not recorded / 待补充"
        lines.append(
            f"| {year_label} | [{case['title']}]({case_root}/README.md) "
            f"| {case['status']} | [Derivation / 推导]({case_root}/docs/DERIVATION.md) · "
            f"[Code / 代码]({case_root}/code/README.md) · "
            f"[Evidence / 证据]({case_root}/outputs/checks/completion_assessment.json) |"
        )
    lines.append("")
    return "\n".join(lines)
