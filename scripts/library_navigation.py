"""Learning routes over the existing public case identities and evidence."""

from __future__ import annotations

from typing import Any


def validate_learning_path(collection: dict[str, Any]) -> None:
    learning = collection.get("learning")
    if not isinstance(learning, dict):
        raise ValueError(f"collection {collection['id']} requires a learning path")
    for field in ("prerequisites_en", "prerequisites_zh"):
        if not isinstance(learning.get(field), str) or not learning[field].strip():
            raise ValueError(f"collection {collection['id']} requires {field}")
    steps = learning.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"collection {collection['id']} requires learning steps")
    seen: set[str] = set()
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("a learning step must be an object")
        for field in ("paper_id", "focus_en", "focus_zh", "exercise_en", "exercise_zh"):
            if not isinstance(step.get(field), str) or not step[field].strip():
                raise ValueError(f"learning step requires {field}")
        paper_id = step["paper_id"]
        if paper_id not in collection["paper_ids"]:
            raise ValueError(f"learning case {paper_id} is outside collection {collection['id']}")
        if paper_id in seen:
            raise ValueError(f"duplicate learning case: {paper_id}")
        seen.add(paper_id)


def render_learning_paths(
    cases: list[dict[str, Any]], collections: list[dict[str, Any]]
) -> str:
    by_id = {str(case["paper_id"]): case for case in cases}
    lines = [
        "# Start Researching / 从这里开始研究",
        "",
        "[English introduction](README.md) · [中文介绍](README.zh-CN.md) · [All papers / 完整目录](CASES.md) · [Paper timeline / 论文年代](HISTORY.md)",
        "",
        "Choose a direction, check the prerequisites, then follow the suggested paper order. These are learning routes, not a ranking of scientific completion.",
        "先选方向、确认基础，再按建议顺序进入论文。这里给出学习路径；案例是否完成复现，仍以各自的证据和评审状态为准。",
        "",
        "## Your first investigation / 第一次动手",
        "",
        "1. Read one derivation and identify its assumptions. / 读一段推导，写清所用假设。",
        "2. Follow the case's run instructions, starting with its documented small run when available. / 按案例说明运行；有小规模配置时，先用它检查环境。",
        "3. Compare an output with its numerical check and explain one discrepancy or limitation. / 对照生成结果和数值检查，解释一处差异或限制。",
        "4. Copy a configuration, change one assumption, and keep the new result separate from the paper reproduction. / 复制配置后只改一个假设，将探索结果与原论文复现结果分开记录。",
        "",
        "The [qDRIFT example](README.md#run-this-example) is the currently verified first run. Other routes link to their case-specific commands and compute boundaries; they do not promise the same runtime or a completed independent review.",
        "[qDRIFT 示例](README.zh-CN.md#运行这个示例)已有首次运行验证。其他路线请按案例说明查看命令与算力需求。运行时间和独立评审状态因案例而异。",
        "",
    ]
    for collection in collections:
        lines.append(
            f"- [{collection['title_zh']} / {collection['title_en']}](#learn-{collection['id']})"
        )
    for collection in collections:
        validate_learning_path(collection)
        learning = collection["learning"]
        lines.extend([
            "", f'<a id="learn-{collection["id"]}"></a>', "",
            f"## {collection['title_zh']} / {collection['title_en']}", "",
            f"**先修知识：** {learning['prerequisites_zh']}", "",
            f"**Prerequisites:** {learning['prerequisites_en']}", "",
        ])
        for number, step in enumerate(learning["steps"], 1):
            case = by_id[step["paper_id"]]
            case_root = f"cases/{case['paper_id']}"
            lines.extend([
                f"### {number}. [{case['title']}]({case_root}/README.md)", "",
                f"{step['focus_zh']} / {step['focus_en']}", "",
                f"**动手任务：** {step['exercise_zh']}", "",
                f"**Try:** {step['exercise_en']}", "",
                f"[中文讲义]({case_root}/note/reproduction-note.zh-CN.md) · "
                f"[English note]({case_root}/note/reproduction-note.en.md) · "
                f"[Derivation / 推导]({case_root}/docs/DERIVATION.md) · "
                f"[Run / 运行]({case_root}/code/README.md)", "",
                f"Recorded status / 已记录状态: **{case['status']}**. "
                f"[Evidence and remaining work / 证据与待完成工作]({case_root}/outputs/checks/completion_assessment.json).", "",
            ])
        lines.extend([
            f"[Continue in this collection / 浏览这个方向的全部论文](CASES.md#collection-{collection['id']})", "",
        ])
    return "\n".join(lines)
