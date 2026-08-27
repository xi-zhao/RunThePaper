from __future__ import annotations

import ast
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


FORBIDDEN_IMAGE_IMPORT_ROOTS = {
    "PIL",
    "cv2",
    "imageio",
    "skimage",
}
FORBIDDEN_MODULE_NAMES = {"source_digitization"}
FORBIDDEN_IMAGE_CALLS = {
    "imread",
    "Image.open",
    "plt.imread",
    "matplotlib.image.imread",
}
COMPARISON_ONLY_FUNCTIONS = {"render_side_by_side"}
ALLOWED_PROVENANCE_VALUES = {
    "analytic_reference",
    "formula_numerics",
    "independent_numerics",
    "independent_hamiltonian_numerics",
    "independent_many_body_numerics",
}


@dataclass(frozen=True)
class AuditFinding:
    path: str
    line: int
    symbol: str
    reason: str


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


class _SourceVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.function_stack: list[str] = []
        self.forbidden: list[AuditFinding] = []
        self.comparison_only: list[AuditFinding] = []

    def _record(self, node: ast.AST, symbol: str, reason: str) -> None:
        finding = AuditFinding(
            path=self.relative_path,
            line=getattr(node, "lineno", 0),
            symbol=symbol,
            reason=reason,
        )
        if self.function_stack and self.function_stack[-1] in COMPARISON_ONLY_FUNCTIONS:
            self.comparison_only.append(finding)
        else:
            self.forbidden.append(finding)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".", 1)[0]
            if root in FORBIDDEN_IMAGE_IMPORT_ROOTS:
                self._record(node, alias.name, "image-reading dependency in computation source")
            if root in FORBIDDEN_MODULE_NAMES:
                self._record(node, alias.name, "deleted source-digitization module referenced")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".", 1)[0]
        if root in FORBIDDEN_IMAGE_IMPORT_ROOTS:
            self._record(node, module, "image-reading dependency in computation source")
        if root in FORBIDDEN_MODULE_NAMES or any(
            alias.name in FORBIDDEN_MODULE_NAMES for alias in node.names
        ):
            self._record(node, module, "deleted source-digitization module referenced")

    def visit_Call(self, node: ast.Call) -> None:
        name = _dotted_name(node.func)
        if name in FORBIDDEN_IMAGE_CALLS or name.endswith(".imread"):
            self._record(node, name, "image pixels read by Python code")
        self.generic_visit(node)


def _scan_source(path: Path, workspace: Path) -> tuple[list[AuditFinding], list[AuditFinding]]:
    relative_path = str(path.relative_to(workspace))
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = _SourceVisitor(relative_path)
    visitor.visit(tree)
    return visitor.forbidden, visitor.comparison_only


def _computational_sources(workspace: Path) -> list[Path]:
    sources = [
        path
        for path in sorted((workspace / "src").glob("*.py"))
        if path.name != "provenance_audit.py"
    ]
    sources.extend(
        [
            workspace / "scripts" / "run_formula_theory_targets.py",
            workspace / "scripts" / "run_reproduction.py",
        ]
    )
    return sources


def _check_generated_data(workspace: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path in sorted((workspace / "outputs" / "data").glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if "generated_data_provenance" not in (reader.fieldnames or []):
                continue
            values = {
                row["generated_data_provenance"].strip()
                for row in reader
                if row.get("generated_data_provenance", "").strip()
            }
        invalid = sorted(values - ALLOWED_PROVENANCE_VALUES)
        if invalid:
            findings.append(
                AuditFinding(
                    path=str(path.relative_to(workspace)),
                    line=1,
                    symbol=", ".join(invalid),
                    reason="generated data declares a non-formula provenance",
                )
            )
    return findings


def audit_computational_provenance(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    forbidden: list[AuditFinding] = []
    comparison_only: list[AuditFinding] = []
    sources = _computational_sources(workspace)
    for path in sources:
        source_forbidden, source_comparison = _scan_source(path, workspace)
        forbidden.extend(source_forbidden)
        comparison_only.extend(source_comparison)

    forbidden.extend(_check_generated_data(workspace))

    theory_check_path = workspace / "outputs" / "checks" / "formula_theory_targets.json"
    theory_check = json.loads(theory_check_path.read_text(encoding="utf-8"))
    if theory_check.get("source_figure_data_used_as_computational_input") is not False:
        forbidden.append(
            AuditFinding(
                path=str(theory_check_path.relative_to(workspace)),
                line=1,
                symbol="source_figure_data_used_as_computational_input",
                reason="formula-target run does not explicitly deny source-figure inputs",
            )
        )

    forbidden_cache = sorted(
        str(path.relative_to(workspace))
        for path in workspace.glob("src/**/source_digitization*.pyc")
    )
    for relative_path in forbidden_cache:
        forbidden.append(
            AuditFinding(
                path=relative_path,
                line=0,
                symbol="source_digitization bytecode",
                reason="stale digitization bytecode must not remain in the reproducible workspace",
            )
        )

    return {
        "schema_version": 1,
        "status": "passed" if not forbidden else "failed",
        "policy": (
            "Paper-figure pixels may be read only after numerical generation and only "
            "inside the comparison renderer; they are forbidden as computational inputs."
        ),
        "source_figure_data_used_as_computational_input": bool(forbidden),
        "scanned_sources": [str(path.relative_to(workspace)) for path in sources],
        "generated_data_provenance_allowlist": sorted(ALLOWED_PROVENANCE_VALUES),
        "forbidden_findings": [asdict(finding) for finding in forbidden],
        "comparison_only_image_reads": [
            asdict(finding) for finding in comparison_only
        ],
    }
