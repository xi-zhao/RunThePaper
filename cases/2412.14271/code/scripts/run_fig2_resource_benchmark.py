from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from src.fig2_resource_benchmark import run_benchmark, write_result  # noqa: E402


def _workspace_path(value: str, *, root: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != (root,):
        raise ValueError(f"path must be workspace-relative under {root}/")
    return WORKSPACE / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--data-output", required=True)
    parser.add_argument("--check-output", required=True)
    args = parser.parse_args()
    config = json.loads(
        _workspace_path(args.config, root="config").read_text(encoding="utf-8")
    )
    result = run_benchmark(config)
    write_result(_workspace_path(args.data_output, root="outputs"), result)
    write_result(
        _workspace_path(args.check_output, root="outputs"),
        {
            key: result[key]
            for key in (
                "schema_version",
                "paper_id",
                "target_id",
                "status",
                "benchmark_kind",
                "host_memory_bytes",
                "safe_memory_bytes",
                "models",
                "paper_cutoff_projections",
                "measured_paper_cutoffs",
                "blocked_paper_cutoffs",
                "paper_scale_complete",
                "resource_boundary_confirmed",
                "code_fault_excluded",
                "clean_room_boundary",
            )
        },
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
