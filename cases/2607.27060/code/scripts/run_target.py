#!/usr/bin/env python3
"""Guarded one-target runner for the frozen Fig. 2/3 panels."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))
os.environ.setdefault(
    "MPLCONFIGDIR", str(WORKSPACE / "outputs" / ".matplotlib-cache")
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from trotter_bounds import (  # noqa: E402
    TARGET_SPECS,
    generate_rows,
    scientific_checks,
    target_slug,
    write_json,
    write_rows_csv,
)


def render_panel(path: Path, spec, rows: list[dict[str, object]]) -> None:
    """Render an independent panel before any source-pixel inspection."""

    path.parent.mkdir(parents=True, exist_ok=True)
    m_values = [row["M"] for row in rows]
    fig, axis = plt.subplots(figsize=(6.2, 4.55), dpi=180)
    series = (
        ("N_analytic", r"$N^{analytic}$", "#4338ca", "o", "-"),
        ("N_min", r"$N^{min}$", "#0f766e", "s", "-"),
        ("g_analytic", r"$g^{analytic}$", "#7c3aed", "^", "--"),
        ("g_min", r"$g^{min}$", "#16a34a", "D", "--"),
    )
    for key, label, color, marker, linestyle in series:
        axis.plot(
            m_values,
            [row[key] for row in rows],
            label=label,
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=1.35,
            markersize=3.8,
        )
    axis.set_yscale("log")
    axis.set_xticks(m_values)
    axis.set_xlabel(r"Number of Liouvillian Terms, $M$")
    axis.set_ylabel("Trotter Steps and Gate Complexity")
    axis.set_title(spec.title, fontsize=10)
    axis.grid(True, which="both", alpha=0.28, linewidth=0.55)
    axis.legend(loc="upper left", fontsize=7.5, frameon=True)
    fig.tight_layout(pad=0.8)
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=sorted(TARGET_SPECS))
    args = parser.parse_args()

    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE")
    if guarded_target != args.target:
        raise SystemExit(
            f"guard mismatch: requested {args.target}, environment authorizes "
            f"{guarded_target!r}"
        )
    if guarded_stage != "final_reproduction":
        raise SystemExit(
            "this runner writes reader-facing artifacts and requires "
            "PRAGENT_GUARDED_STAGE=final_reproduction"
        )

    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    spec = TARGET_SPECS[args.target]
    slug = target_slug(args.target)
    data_path = WORKSPACE / "outputs" / "data" / f"{slug}.csv"
    check_path = WORKSPACE / "outputs" / "checks" / "targets" / f"{slug}.json"
    figure_path = WORKSPACE / "outputs" / "figures" / f"{slug}.png"

    rows = generate_rows(spec)
    checks = scientific_checks(spec, rows)
    if not checks["all_passed"]:
        raise SystemExit(json.dumps(checks, indent=2))
    write_rows_csv(data_path, rows)
    render_panel(figure_path, spec, rows)

    elapsed_wall = time.perf_counter() - started_wall
    elapsed_cpu = time.process_time() - started_cpu
    model = spec.model
    payload = {
        "schema_version": 1,
        "status": "passed",
        "target_id": spec.target_id,
        "figure_id": spec.figure_id,
        "panel": spec.panel,
        "artifact_stage": "final_reproduction",
        "generated_data_provenance": "independent_numerics",
        "formula_dependencies": [
            "EQ-PRECISION-FUNCTIONS",
            "EQ-ANALYTIC-BOUNDS",
            "EQ-GATE-COMPLEXITY",
            "EQ-LAMBERT-W-CROSSCHECK",
            "EQ-MODEL-TERM-COUNTS",
        ],
        "method_dependencies": ["MTH-BINARY-SEARCH", "MTH-PANEL-RENDER"],
        "parameters": {
            "model": model.model_id,
            "t": model.t,
            "lambda": model.lam,
            "epsilon": model.epsilon,
            "M": list(model.m_values),
            model.size_name: list(model.size_values),
            **model.extra_parameters,
        },
        "observable": {
            "x": "number of Liouvillian terms M",
            "series": ["N_analytic", "N_min", "g_analytic", "g_min"],
            "y_scale": "logarithmic",
        },
        "scientific_checks": checks,
        "physics_assertions": [
            {
                "assertion_id": f"{spec.figure_id}-MINIMALITY",
                "tier": "numeric",
                "essential": True,
                "status": "passed",
                "claim": "Every N_min satisfies epsilon_hat(N)<=epsilon while N_min-1 does not.",
                "evidence": f"outputs/checks/targets/{slug}.json#scientific_checks",
            },
            {
                "assertion_id": f"{spec.figure_id}-ANALYTIC-SUFFICIENCY",
                "tier": "analytic",
                "essential": True,
                "status": "passed",
                "claim": "Every sufficient analytic bound satisfies the target precision.",
                "evidence": f"outputs/checks/targets/{slug}.json#scientific_checks",
            },
        ],
        "rows": rows,
        "outputs": {
            "data": f"outputs/data/{slug}.csv",
            "figure": f"outputs/figures/{slug}.png",
            "check": f"outputs/checks/targets/{slug}.json",
        },
        "timing": {
            "wall_seconds": elapsed_wall,
            "cpu_seconds": elapsed_cpu,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "matplotlib": matplotlib.__version__,
        },
    }
    write_json(check_path, payload)
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": spec.target_id,
                "data": str(data_path),
                "figure": str(figure_path),
                "check": str(check_path),
                "wall_seconds": elapsed_wall,
                "cpu_seconds": elapsed_cpu,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
