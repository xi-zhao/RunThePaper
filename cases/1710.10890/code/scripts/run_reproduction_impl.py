from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from quantum_droplets.reproduction import run_all  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_theory.json")
    args = parser.parse_args()
    config_path = WORKSPACE / args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = run_all(config, WORKSPACE)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["formula_checks"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
