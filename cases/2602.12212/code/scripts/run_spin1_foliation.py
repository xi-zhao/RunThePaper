#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE / ".mplconfig"))
sys.path.insert(0, str(WORKSPACE / "src"))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

import leaf_thermodynamics as leaf  # noqa: E402


TARGET_ID = "T001"
DATA_PATH = WORKSPACE / "outputs" / "data" / "t001_spin1_foliation.csv"
FIGURE_PATH = WORKSPACE / "outputs" / "figures" / "t001_spin1_foliation.png"
CHECK_PATH = WORKSPACE / "outputs" / "checks" / "t001_spin1_foliation.json"
COMPARISON_PATH = (
    WORKSPACE / "outputs" / "comparisons" / "t001_source_vs_reproduction.png"
)
REFERENCE_PATH = (
    WORKSPACE / "references" / "original_figures" / "foliation3d3.png"
)


def build_rows() -> tuple[list[dict[str, float | int | str]], list[dict[str, object]]]:
    transverse_components = np.asarray(
        [0.0, 0.12, 0.24, 0.36, 0.48, 0.60, 0.72, 0.82, 0.90, 0.96]
    )
    betas = np.linspace(-10.0, 10.0, 241)
    rows: list[dict[str, float | int | str]] = []
    leaves: list[dict[str, object]] = []
    for leaf_index, transverse in enumerate(transverse_components):
        vertices = leaf.spin1_leaf_vertices(float(transverse))
        entropy = leaf.spin1_barycenter_entropy(float(transverse))
        canonical = leaf.spin1_leaf_canonical_curve(float(transverse), betas)
        for vertex_index, coordinates in enumerate(vertices):
            rows.append(
                {
                    "target_id": TARGET_ID,
                    "leaf_index": leaf_index,
                    "transverse_component": float(transverse),
                    "incoherence_entropy": entropy,
                    "point_kind": "vertex",
                    "parameter": vertex_index,
                    "n1": float(coordinates[0]),
                    "n3": float(coordinates[1]),
                    "n8": float(coordinates[2]),
                }
            )
        for beta, coordinates in zip(betas, canonical, strict=True):
            rows.append(
                {
                    "target_id": TARGET_ID,
                    "leaf_index": leaf_index,
                    "transverse_component": float(transverse),
                    "incoherence_entropy": entropy,
                    "point_kind": "leaf_canonical",
                    "parameter": float(beta),
                    "n1": float(coordinates[0]),
                    "n3": float(coordinates[1]),
                    "n8": float(coordinates[2]),
                }
            )
        leaves.append(
            {
                "leaf_index": leaf_index,
                "transverse_component": float(transverse),
                "incoherence_entropy": entropy,
                "vertices": vertices,
                "canonical": canonical,
            }
        )
    return rows, leaves


def write_data(rows: list[dict[str, float | int | str]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def render(leaves: list[dict[str, object]]) -> None:
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    palette = LinearSegmentedColormap.from_list(
        "paper_leaf",
        ["#fff3c4", "#ddc392", "#8b6240"],
    )
    entropy_max = np.log(3.0)
    fig = plt.figure(figsize=(10.8, 5.2), constrained_layout=True)
    views = [(21, -58), (19, 34)]
    for panel, (elevation, azimuth) in enumerate(views, start=1):
        axis = fig.add_subplot(1, 2, panel, projection="3d")
        for item in leaves:
            vertices = np.asarray(item["vertices"])
            canonical = np.asarray(item["canonical"])
            entropy = float(item["incoherence_entropy"])
            coherence_fraction = 1.0 - entropy / entropy_max
            color = palette(np.clip(coherence_fraction, 0.0, 1.0))
            surface = Poly3DCollection(
                [vertices],
                facecolors=[color],
                edgecolors="none",
                alpha=0.42,
            )
            axis.add_collection3d(surface)
            closed = np.vstack([vertices, vertices[0]])
            axis.plot(*closed.T, color="#6d553f", linewidth=0.45, alpha=0.7)
            axis.plot(*canonical.T, color="black", linewidth=1.0)
        axis.set_xlim(-0.04, 1.03)
        axis.set_ylim(-1.03, 1.03)
        axis.set_zlim(-2.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0))
        axis.view_init(elev=elevation, azim=azimuth)
        axis.set_box_aspect((1.0, 1.5, 1.5))
        axis.set_axis_off()
    fig.suptitle(
        "Spin-1 minimum-variance leaves and leaf-canonical curves",
        fontsize=13,
    )
    fig.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def render_comparison() -> None:
    if not REFERENCE_PATH.exists():
        return
    source = plt.imread(REFERENCE_PATH)
    generated = plt.imread(FIGURE_PATH)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), constrained_layout=True)
    axes[0].imshow(source)
    axes[0].set_title("Paper source (reference only)")
    axes[1].imshow(generated)
    axes[1].set_title("Independent analytic reconstruction")
    for axis in axes:
        axis.set_axis_off()
    fig.suptitle("Main Fig. 1 — geometry/feature comparison")
    COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(COMPARISON_PATH, dpi=180, facecolor="white")
    plt.close(fig)


def build_check(leaves: list[dict[str, object]]) -> dict[str, object]:
    common_corner = np.asarray([0.0, 0.0, -2.0 / np.sqrt(3.0)])
    common_corner_error = max(
        float(np.linalg.norm(np.asarray(item["vertices"])[2] - common_corner))
        for item in leaves
    )
    endpoint_bloch_errors = []
    canonical_hull_violations = []
    for item in leaves:
        transverse = float(item["transverse_component"])
        vertices = np.asarray(item["vertices"])
        endpoint_bloch_errors.extend(
            [
                abs(vertices[0, 0] ** 2 + vertices[0, 1] ** 2 - 1.0),
                abs(vertices[1, 0] ** 2 + vertices[1, 1] ** 2 - 1.0),
            ]
        )
        canonical = np.asarray(item["canonical"])
        canonical_hull_violations.append(
            max(
                0.0,
                float(np.max(canonical[:, 0] - transverse)),
                float(np.max(-canonical[:, 0])),
                float(np.max(canonical[:, 2] - 1.0 / np.sqrt(3.0))),
                float(np.max(-2.0 / np.sqrt(3.0) - canonical[:, 2])),
            )
        )
    entropies = [
        float(item["incoherence_entropy"])
        for item in leaves
    ]
    passed = (
        common_corner_error < 1e-14
        and max(endpoint_bloch_errors) < 1e-14
        and max(canonical_hull_violations) < 1e-12
        and all(np.diff(entropies) < 0.0)
    )
    return {
        "schema_version": 1,
        "paper_id": "2602.12212",
        "target_id": TARGET_ID,
        "status": "passed" if passed else "failed",
        "artifact_state": "final_reproduction" if passed else "exploratory",
        "parameter_match": "paper_exact",
        "paper_parameters": {
            "spin": 1,
            "constrained_gell_mann_components": [2, 4, 5, 6, 7],
            "constrained_values": 0,
            "hamiltonian": "lambda3/2 + 3*sqrt(3)*lambda8/2",
        },
        "generated_parameters": {
            "spin": 1,
            "constrained_gell_mann_components": [2, 4, 5, 6, 7],
            "constrained_values": 0,
            "hamiltonian": "lambda3/2 + 3*sqrt(3)*lambda8/2",
            "transverse_components": [
                float(item["transverse_component"]) for item in leaves
            ],
            "beta_range": [-10.0, 10.0],
            "beta_points": 241,
        },
        "checks": {
            "common_corner_max_error": common_corner_error,
            "pure_endpoint_bloch_radius_max_error": max(endpoint_bloch_errors),
            "canonical_curve_hull_max_violation": max(canonical_hull_violations),
            "incoherence_entropy_strictly_decreases_with_coherence": all(
                np.diff(entropies) < 0.0
            ),
        },
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "source_figure_visual",
        "data_path": str(DATA_PATH.relative_to(WORKSPACE)),
        "figure_path": str(FIGURE_PATH.relative_to(WORKSPACE)),
        "comparison_path": str(COMPARISON_PATH.relative_to(WORKSPACE)),
        "claim_boundary": "Validates the leaf geometry, common vertex, entropy ordering, and canonical trajectories; it does not claim pixel registration to the source rendering.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reference-comparison", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows, leaves = build_rows()
    write_data(rows)
    render(leaves)
    if not args.no_reference_comparison:
        render_comparison()
    payload = build_check(leaves)
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
