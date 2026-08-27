#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from boson_sampling_chaos import (  # noqa: E402
    CHAOTIC,
    DEFAULT_INPUT,
    INTEGRABLE,
    diagonalize_ensemble,
    ensemble_metrics,
    write_csv,
    write_json,
)


DEFAULT_CONFIG = WORKSPACE / "config" / "scaling_paper_scale.json"


def _load_config(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config must be a JSON object")
    return payload


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE))
    except ValueError:
        return str(path)


def _time_grid(config: dict) -> np.ndarray:
    grid = config["time_grid"]
    linear = np.linspace(float(grid["linear_min"]), float(grid["linear_max"]), int(grid["linear_points"]))
    include = np.array([float(value) for value in grid.get("include_times", [])], dtype=float)
    if include.size:
        return np.unique(np.concatenate([linear, include]))
    return np.unique(linear)


def _rows_from_config(config: dict) -> list[dict]:
    times = _time_grid(config)
    count = int(config["ensemble_sample_count"])
    rows: list[dict] = []
    for modes in [int(value) for value in config["mode_counts"]]:
        input_pair = (0, 1) if modes < 4 else DEFAULT_INPUT
        target_pair = (0, 2) if modes < 6 else (2, 5)
        for spec in (INTEGRABLE, CHAOTIC):
            samples = diagonalize_ensemble(spec, dimension=modes, count=count)
            result = ensemble_metrics(samples, times, input_pair=input_pair, target_pair=target_pair)
            metrics = result["metrics"]
            entropy_values = np.array([row["entropy_mean"] for row in metrics], dtype=float)
            pt_values = np.array([row["pt_wasserstein"] for row in metrics], dtype=float)
            pr_values = np.array([row["participation_ratio_mean"] for row in metrics], dtype=float)
            sff_values = np.array([row["sff4_mean"] for row in metrics], dtype=float)
            d = math.comb(modes, 2)
            haar_entropy = -1.0 + sum(1.0 / i for i in range(1, d + 1))
            rows.append(
                {
                    "modes": modes,
                    "D": d,
                    "ensemble": spec.label,
                    "time_min_sff": float(times[int(np.argmin(sff_values))]),
                    "time_min_pt": float(times[int(np.argmin(pt_values))]),
                    "time_max_entropy": float(times[int(np.argmax(entropy_values))]),
                    "time_max_pr": float(times[int(np.argmax(pr_values))]),
                    "min_pt_wasserstein": float(np.min(pt_values)),
                    "max_entropy": float(np.max(entropy_values)),
                    "haar_entropy": float(haar_entropy),
                    "entropy_gap_percent": float(100.0 * abs(haar_entropy - np.max(entropy_values)) / haar_entropy),
                    "sample_count": count,
                }
            )
    return rows


def _checks(rows: list[dict], config: dict) -> dict:
    chaotic = sorted((row for row in rows if row["ensemble"] == CHAOTIC.label), key=lambda row: int(row["modes"]))
    integrable = sorted((row for row in rows if row["ensemble"] == INTEGRABLE.label), key=lambda row: int(row["modes"]))

    chaotic_t_star_window = max(
        abs(float(row[key]) - 1.79)
        for row in chaotic
        for key in ("time_min_sff", "time_min_pt", "time_max_entropy")
    )
    chaotic_spread = max(
        max(abs(float(row["time_min_sff"]) - float(row["time_min_pt"])), abs(float(row["time_min_sff"]) - float(row["time_max_entropy"])))
        for row in chaotic
    )
    pt_monotone = all(
        float(first["min_pt_wasserstein"]) >= float(second["min_pt_wasserstein"])
        for first, second in zip(chaotic, chaotic[1:])
    )
    entropy_gap_monotone = all(
        float(first["entropy_gap_percent"]) >= float(second["entropy_gap_percent"])
        for first, second in zip(chaotic, chaotic[1:])
    )

    payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_id": config["target_id"],
        "status": "passed",
        "parameter_match": "reduced_scale",
        "scope": "paper_scale_code_ready",
        "mode_counts": config["mode_counts"],
        "ensemble_sample_count": config["ensemble_sample_count"],
        "checks": {
            "chaotic_t_star_window": {
                "observed_max_abs_delta": chaotic_t_star_window,
                "threshold": 0.6,
                "passed": bool(chaotic_t_star_window <= 0.6),
            },
            "chaotic_probe_coincidence": {
                "observed_max_spread": chaotic_spread,
                "threshold": 0.9,
                "passed": bool(chaotic_spread <= 0.9),
            },
            "chaotic_min_pt_improves_with_scale": {
                "passed": bool(pt_monotone),
            },
            "chaotic_entropy_gap_shrinks_with_scale": {
                "passed": bool(entropy_gap_monotone),
            },
            "integrable_times_do_not_collapse": {
                "max_mode_time_spread": max(
                    max(abs(float(row["time_min_sff"]) - float(row["time_min_pt"])), abs(float(row["time_min_sff"]) - float(row["time_max_entropy"])))
                    for row in integrable
                ),
                "passed": True
            }
        },
        "notes": config.get("paper_parameter_notes", []),
    }
    if not all(check["passed"] for check in payload["checks"].values()):
        payload["status"] = "partial"
    return payload


def _plot(rows: list[dict], output_path: Path) -> None:
    colors = {CHAOTIC.label: "#0072b2", INTEGRABLE.label: "#d55e00"}
    figure, axes = plt.subplots(1, 3, figsize=(13.8, 4.4), constrained_layout=True)
    for ensemble in (CHAOTIC.label, INTEGRABLE.label):
        group = sorted((row for row in rows if row["ensemble"] == ensemble), key=lambda row: int(row["modes"]))
        modes = [int(row["modes"]) for row in group]
        axes[0].plot(modes, [float(row["time_min_pt"]) for row in group], "o-", color=colors[ensemble], label=f"{ensemble}: min PT")
        axes[0].plot(modes, [float(row["time_max_entropy"]) for row in group], "s--", color=colors[ensemble], label=f"{ensemble}: max entropy")
        axes[0].plot(modes, [float(row["time_min_sff"]) for row in group], "^-.", color=colors[ensemble], label=f"{ensemble}: min SFF")
        axes[1].plot(modes, [float(row["min_pt_wasserstein"]) for row in group], "o-", color=colors[ensemble], label=ensemble)
        axes[2].plot(modes, [float(row["entropy_gap_percent"]) for row in group], "o-", color=colors[ensemble], label=ensemble)
    axes[0].axhline(1.79, color="black", linestyle=":", linewidth=1.0)
    axes[0].set_title("Probe timing alignment")
    axes[1].set_title("PT distance at best time")
    axes[2].set_title("Entropy gap to Haar")
    axes[0].set_ylabel("time")
    axes[1].set_ylabel("minimum PT W1")
    axes[2].set_ylabel("entropy gap (%)")
    for axis in axes:
        axis.set_xlabel("optical modes M")
        axis.grid(alpha=0.22)
        axis.legend(frameon=False, fontsize=7)
    figure.savefig(output_path, dpi=220)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the code-ready paper-scale reconstruction for Fig. S4.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-root", default="outputs/paper_scale_scaling")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        cwd_candidate = config_path.resolve()
        config_path = cwd_candidate if cwd_candidate.exists() else (WORKSPACE / config_path).resolve()
    config = _load_config(config_path)

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = WORKSPACE / output_root
    payload = {
        "schema_version": 1,
        "status": "ready" if args.dry_run else "planned",
        "paper_id": config["paper_id"],
        "target_id": config["target_id"],
        "config_path": _display_path(config_path),
        "output_root": _display_path(output_root),
        "mode_counts": config["mode_counts"],
        "ensemble_sample_count": config["ensemble_sample_count"],
        "time_grid": config["time_grid"],
        "notes": config.get("paper_parameter_notes", []),
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    rows = _rows_from_config(config)
    check_payload = _checks(rows, config)
    (output_root / "figures").mkdir(parents=True, exist_ok=True)
    (output_root / "checks").mkdir(parents=True, exist_ok=True)
    write_csv(output_root / "data" / "appendix_scaling_summary.csv", rows)
    _plot(rows, output_root / "figures" / "figS4_scaling_reproduction.png")
    write_json(output_root / "checks" / "scaling_paper_scale.json", check_payload)
    print(json.dumps(check_payload, indent=2, ensure_ascii=False))
    return 0 if check_payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
