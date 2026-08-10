from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reproduction import run_reproduction  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reproduce both numerical panels of arXiv:1910.08980"
    )
    parser.add_argument("--config", required=True)
    arguments = parser.parse_args()
    result = run_reproduction(Path(arguments.config))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_targets_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
