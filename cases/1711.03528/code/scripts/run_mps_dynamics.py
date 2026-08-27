#!/usr/bin/env python3
"""Run the paper-scale finite-window MPS comparator for Fig. 2."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mps_dynamics import simulate, validate_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Workspace-relative JSON configuration.")
    parser.add_argument("--output-root", required=True, help="Workspace-relative directory under outputs/.")
    parser.add_argument("--dry-run", action="store_true", help="Validate the contract without starting MPS evolution.")
    return parser.parse_args()


def safe_workspace_ref(value: str, *, root: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != (root,):
        raise ValueError(f"path must be workspace-relative under {root}/: {value!r}")
    return path


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_rows(path: Path, rows: list[dict]) -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row["initial_state"])].append(row)
    palette = {"vacuum": "#ff7f0e", "z2": "#1f77b4", "z3": "#2ca02c", "z4": "#d62728"}
    labels = {"vacuum": "|0>", "z2": "|Z2>", "z3": "|Z3>", "z4": "|Z4>"}
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.0), sharex=True, constrained_layout=True)
    for name, group in sorted(grouped.items()):
        group.sort(key=lambda row: float(row["time"]))
        time = np.asarray([float(row["time"]) for row in group])
        entropy = np.asarray([float(row["entanglement_entropy"]) for row in group])
        axes[0].plot(time, entropy, color=palette[name], label=labels[name])
        if name == "z2":
            slope, intercept = np.polyfit(time, entropy, 1)
            axes[1].plot(time, entropy - (slope * time + intercept), color=palette[name])
            axes[2].plot(
                time,
                [float(row["nearest_neighbor_zz"]) for row in group],
                color=palette[name],
            )
    axes[0].set_title("Fig. 2 PXP dynamics (finite-window MPS)")
    axes[0].set_ylabel("S")
    axes[0].legend(frameon=False, fontsize=8, ncol=2)
    axes[1].set_ylabel("Delta S")
    axes[2].set_ylabel("<Zi Zi+1>")
    axes[2].set_xlabel("time")
    for axis in axes:
        axis.grid(alpha=0.2)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    config_ref = safe_workspace_ref(args.config, root="config")
    output_ref = safe_workspace_ref(args.output_root, root="outputs")
    raw_config = json.loads((ROOT / config_ref).read_text(encoding="utf-8"))
    config = validate_config(raw_config)
    resolved = {
        "system_size": config.system_size,
        "max_bond": config.max_bond,
        "time_step": config.time_step,
        "final_time": config.final_time,
        "sample_interval": config.sample_interval,
        "cutoff": config.cutoff,
        "initial_states": list(config.initial_states),
        "bulk_bonds": config.bulk_bonds,
        "output_root": output_ref.as_posix(),
    }
    if args.dry_run:
        print(json.dumps({"status": "ready", "resolved_run": resolved}, indent=2))
        return 0

    output_root = ROOT / output_ref
    data_dir = output_root / "data"
    check_dir = output_root / "checks"
    figure_dir = output_root / "figures"
    for directory in (data_dir, check_dir, figure_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rows, checks = simulate(config)
    data_path = data_dir / "fig2_mps_dynamics.csv"
    figure_path = figure_dir / "fig2_mps_dynamics.png"
    check_path = check_dir / "mps_dynamics.json"
    write_rows(data_path, rows)
    plot_rows(figure_path, rows)
    checks.update(
        {
            "schema_version": 1,
            "paper_id": "1711.03528",
            "target_id": "T002",
            "method": "finite_window_three_site_mps_trotter",
            "resolved_run": resolved,
            "data": str(data_path.relative_to(ROOT)),
            "figure": str(figure_path.relative_to(ROOT)),
        }
    )
    check_path.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
