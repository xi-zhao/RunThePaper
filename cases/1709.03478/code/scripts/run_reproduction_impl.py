from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.reproduce_spme import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    summary = run(payload["parameters"], Path("."))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
