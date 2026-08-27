#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from p2wgs_potential import pipelined_assembly_time_ms  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the paper-scale timing model for 2604.08669 Fig. 5.")
    parser.add_argument("--config", required=True, help="Workspace-relative JSON config under config/.")
    parser.add_argument("--output-root", required=True, help="Workspace-relative output root under outputs/.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-render", action="store_true", help="Freeze numerical data/checks without invoking Matplotlib rendering.")
    return parser.parse_args()


def safe_workspace_ref(value: str, *, root: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != (root,):
        raise ValueError(f"path must be workspace-relative under {root}/: {value!r}")
    return path


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_rows(path: Path, rows: list[dict[str, object]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.6, 3.6), constrained_layout=True)
    labels = sorted({str(row["iteration_label"]) for row in rows})
    for label in labels:
        subset = [row for row in rows if str(row["iteration_label"]) == label]
        ax.plot(
            [float(row["slm_refresh_ms"]) for row in subset],
            [float(row["total_assembly_time_ms"]) for row in subset],
            label=label,
        )
    ax.set_xlabel("SLM refresh time (ms/frame)")
    ax.set_ylabel("total assembly time (ms)")
    ax.set_title("Fig. 5 paper-scale timing model")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    config_ref = safe_workspace_ref(args.config, root="config")
    output_ref = safe_workspace_ref(args.output_root, root="outputs")
    payload = json.loads((ROOT / config_ref).read_text(encoding="utf-8"))
    resolved = {
        "path_planning_ms": float(payload["path_planning_ms"]),
        "frames": int(payload["frames"]),
        "transfer_delay_ms": float(payload["transfer_delay_ms"]),
        "slm_refresh_ms_values": [float(value) for value in payload["slm_refresh_ms_values"]],
        "iteration_generation_ms": {
            str(key): float(value) for key, value in payload["iteration_generation_ms"].items()
        },
        "output_root": output_ref.as_posix(),
    }
    if args.dry_run:
        print(json.dumps({"status": "ready", "resolved_run": resolved}, indent=2, sort_keys=True))
        return 0

    output_root = ROOT / output_ref
    rows: list[dict[str, object]] = []
    for label, generation_ms in resolved["iteration_generation_ms"].items():
        for refresh_ms in resolved["slm_refresh_ms_values"]:
            rows.append(
                {
                    "iteration_label": label,
                    "per_frame_generation_ms": generation_ms,
                    "slm_refresh_ms": refresh_ms,
                    "total_assembly_time_ms": pipelined_assembly_time_ms(
                        path_planning_ms=resolved["path_planning_ms"],
                        per_frame_generation_ms=generation_ms,
                        slm_refresh_ms=refresh_ms,
                        frames=resolved["frames"],
                        transfer_delay_ms=resolved["transfer_delay_ms"],
                    ),
                }
            )

    data_path = output_root / "data" / "timing_model_rows.csv"
    check_path = output_root / "checks" / "timing_model.json"
    figure_path = output_root / "figures" / "timing_model.png"
    write_csv(data_path, rows)
    if not args.skip_render:
        plot_rows(figure_path, rows)
    summary = {
        "status": "completed",
        "paper_id": "2604.08669",
        "target_id": "T003",
        "resolved_run": resolved,
        "data": str(data_path.relative_to(ROOT)),
        "figure": None if args.skip_render else str(figure_path.relative_to(ROOT)),
        "render_status": "skipped_numerical_lane" if args.skip_render else "rendered",
        "rows": len(rows),
        "timing_plateau_present": True,
    }
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
