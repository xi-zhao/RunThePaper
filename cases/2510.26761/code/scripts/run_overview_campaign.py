#!/usr/bin/env python3
"""Run the Fig. 1 scientific arrays without any rendering or reference input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.overview_campaign import evaluate_overview_campaign  # noqa: E402


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config_path = Path(args.config)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    fields, result = evaluate_overview_campaign(payload["parameters"])

    data_path = Path("outputs/data/t001_scientific_fields.npz")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(data_path, **fields)
    metrics_path = Path("outputs/data/t001_scientific_metrics.json")
    check_path = Path("outputs/checks/t001_scientific_closure.json")
    _write_json(metrics_path, result["metrics"])
    _write_json(check_path, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
