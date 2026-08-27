from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SCRIPTS = WORKSPACE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gen_fig1 import main as run_t101  # noqa: E402
from gen_fig2 import main as run_t201  # noqa: E402
from gen_fig3 import main as run_t301  # noqa: E402
from gen_fig4 import main as run_t401  # noqa: E402


TARGET_RUNNERS = {
    "T101": run_t101,
    "T201": run_t201,
    "T301": run_t301,
    "T401": run_t401,
}


def _workspace_path(value: str, *, root: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != (root,):
        raise ValueError(f"path must be workspace-relative under {root}/")
    return WORKSPACE / relative


def run_campaign(parameters: dict, output_root: Path) -> dict:
    if parameters.get("profile") != "paper_scale_all":
        raise ValueError("paper-scale campaign requires profile=paper_scale_all")
    common = parameters.get("common")
    if common != {"alpha": "1/3", "N": 3, "tau": 2.0, "initial_state": "site l=0"}:
        raise ValueError("common CDHM boundary does not match the frozen paper model")

    results = {}
    for target_id, runner in TARGET_RUNNERS.items():
        target_parameters = parameters.get(target_id)
        if not isinstance(target_parameters, dict):
            raise ValueError(f"missing parameter object for {target_id}")
        results[target_id] = runner(target_parameters, render=False)

    status = "passed" if all(row.get("status") == "passed" for row in results.values()) else "failed"
    summary = {
        "schema_version": 1,
        "status": status,
        "profile": parameters["profile"],
        "target_results": results,
        "scientific_boundary": {
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "source_pixels_used_as_numeric_inputs": False,
            "reference_figures_used_by_runner": False,
            "rendering_executed": False,
        },
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all four paper-scale CDHM targets.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    config = json.loads(_workspace_path(args.config, root="config").read_text(encoding="utf-8"))
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("config.parameters must be an object")
    output_root = _workspace_path(args.output_root, root="outputs")
    result = run_campaign(parameters, output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
