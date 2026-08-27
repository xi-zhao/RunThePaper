#!/usr/bin/env python3
"""Guarded final-reproduction runner for one frozen theory target."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
RUNTIME_CACHE = WORKSPACE / ".matplotlib"
RUNTIME_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME_CACHE))
os.environ.setdefault("XDG_CACHE_HOME", str(RUNTIME_CACHE / "xdg"))
sys.path.insert(0, str(WORKSPACE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src.wigner_model import physical_checks, scan_target  # noqa: E402


PROJECT_PATH = WORKSPACE / "physics_reproduction_project.json"
GUARDED_TARGET_ENV = "PRAGENT_GUARDED_TARGET_ID"
GUARDED_STAGE_ENV = "PRAGENT_GUARDED_STAGE"

ARTIFACT_STEMS = {
    "T-FIG003": "fig003_theory",
    "T-FIG004": "fig004_theory",
    "T-FIG005A": "fig005a_theory",
    "T-FIG005B": "fig005b_theory",
}

PLOT_CONTRACTS = {
    "T-FIG003": {
        "figsize": (1604 / 160.0, 982 / 160.0),
        "ylim": (-0.183, 1.047),
        "xlabel": r"$\phi$ (°)",
        "margins": {
            "left": 0.06235,
            "right": 0.99,
            "top": 0.9837,
            "bottom": 0.2312,
        },
        "legend": True,
    },
    "T-FIG004": {
        "figsize": (1621 / 160.0, 982 / 160.0),
        "ylim": (-0.168, 0.534),
        "xlabel": r"$\Theta$ (°)",
        "margins": {
            "left": 0.07218,
            "right": 0.99,
            "top": 0.9837,
            "bottom": 0.2312,
        },
        "legend": True,
    },
    "T-FIG005A": {
        "figsize": (1621 / 160.0, 851 / 160.0),
        "ylim": (-0.232, 0.845),
        "xlabel": r"$\Theta_{\mathrm{Bob}}$ (°)",
        "margins": {
            "left": 0.07218,
            "right": 0.99,
            "top": 0.9806,
            "bottom": 0.1128,
        },
        "legend": False,
    },
    "T-FIG005B": {
        "figsize": (1621 / 160.0, 982 / 160.0),
        "ylim": (-0.229, 0.658),
        "xlabel": r"$\Theta_{\mathrm{Alice}}$ (°)",
        "margins": {
            "left": 0.07218,
            "right": 0.99,
            "top": 0.9837,
            "bottom": 0.2312,
        },
        "legend": True,
    },
}


def _load_target(target_id: str) -> dict[str, object]:
    project = json.loads(PROJECT_PATH.read_text(encoding="utf-8"))
    matches = [
        item
        for item in project["figure_targets"]
        if item.get("target_id") == target_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one target {target_id}")
    return matches[0]


def _require_guard(target_id: str) -> str:
    guarded_target = os.environ.get(GUARDED_TARGET_ENV)
    guarded_stage = os.environ.get(GUARDED_STAGE_ENV)
    if guarded_target != target_id:
        raise RuntimeError(
            f"guarded target mismatch: env={guarded_target!r}, requested={target_id!r}"
        )
    if guarded_stage != "final_reproduction":
        raise RuntimeError(
            "this reader-facing runner requires the final_reproduction guard"
        )
    return guarded_stage


def _write_csv(path: Path, result: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "angle_deg",
                "p_ab",
                "p_bc",
                "p_ac",
                "wigner",
                "w_limit",
            ]
        )
        for row in zip(
            result.angle_deg,
            result.p_ab,
            result.p_bc,
            result.p_ac,
            result.wigner,
            result.w_limit,
            strict=True,
        ):
            writer.writerow([f"{float(value):.15g}" for value in row])


def _render_figure(path: Path, target_id: str, result: object) -> None:
    contract = PLOT_CONTRACTS[target_id]
    fig, ax = plt.subplots(figsize=contract["figsize"], dpi=160)
    ax.axhspan(contract["ylim"][0], 0.0, color="#ff6b6b", alpha=0.28, zorder=0)
    ax.plot(
        result.angle_deg,
        result.wigner,
        color="#0000ff",
        linewidth=1.55,
        label="Calculated Wigner Value",
        zorder=5,
    )
    ax.plot(
        result.angle_deg,
        result.w_limit,
        color="#ff4d4d",
        linewidth=1.1,
        linestyle=":",
        label=f"Theoretical Violation Limit at {result.w_limit[0]:.3f}",
        zorder=4,
    )
    ax.plot(
        result.angle_deg,
        result.p_ab,
        color="#f5a623",
        linewidth=1.05,
        alpha=0.82,
        label=r"Modelled $P_{++}^{\hat a\hat b'}$",
        zorder=3,
    )
    ax.plot(
        result.angle_deg,
        result.p_bc,
        color="#9acd32",
        linewidth=1.05,
        alpha=0.82,
        label=r"Modelled $P_{++}^{\hat b\hat c'}$",
        zorder=3,
    )
    ax.plot(
        result.angle_deg,
        result.p_ac,
        color="#e78ac3",
        linewidth=1.05,
        alpha=0.82,
        label=r"Modelled $P_{++}^{\hat a\hat c'}$",
        zorder=3,
    )
    ax.set_xlim(-5.0, 365.0)
    ax.set_ylim(*contract["ylim"])
    ax.set_xticks(np.arange(0.0, 361.0, 20.0))
    ax.set_xlabel(contract["xlabel"], fontsize=14)
    ax.set_ylabel("Wigner Value (1)", fontsize=13)
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(True, color="#b0b0b0", linewidth=0.65, alpha=0.55)
    if contract["legend"]:
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.14),
            ncol=3,
            fontsize=8.5,
            frameon=True,
            columnspacing=1.4,
            handlelength=2.6,
        )
    fig.subplots_adjust(**contract["margins"])
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        required=True,
        choices=sorted(ARTIFACT_STEMS),
    )
    args = parser.parse_args()
    stage = _require_guard(args.target)
    target = _load_target(args.target)
    params = target["parameter_set"]["generated"]

    started = time.perf_counter()
    result = scan_target(args.target, params)
    check = physical_checks(result)
    elapsed = time.perf_counter() - started
    if check["status"] != "passed":
        raise AssertionError(
            f"scientific checks failed for {args.target}: {check}"
        )

    stem = ARTIFACT_STEMS[args.target]
    data_path = WORKSPACE / "outputs" / "data" / f"{stem}.csv"
    figure_path = WORKSPACE / "outputs" / "figures" / f"{stem}.png"
    check_path = WORKSPACE / "outputs" / "checks" / f"{stem}_scientific.json"
    _write_csv(data_path, result)
    _render_figure(figure_path, args.target, result)

    payload = {
        "schema_version": 1,
        "paper_id": "2606.30255",
        "target_id": args.target,
        "status": "passed",
        "artifact_stage": stage,
        "parameter_match": target["parameter_set"]["parameter_match"],
        "paper_parameters": target["parameter_set"]["paper"],
        "generated_parameters": params,
        "generated_data_provenance": "independent_numerics",
        "scientific_role": "theory_numerical",
        "formula_dependencies": target["formula_refs"],
        "method_dependencies": target["method_refs"],
        "checks": check["assertions"],
        "metrics": check["metrics"],
        "runtime": {
            "elapsed_seconds": elapsed,
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "outputs": {
            "data": str(data_path.relative_to(WORKSPACE)),
            "figure": str(figure_path.relative_to(WORKSPACE)),
            "check": str(check_path.relative_to(WORKSPACE)),
        },
        "reference_inputs_read": [],
    }
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
