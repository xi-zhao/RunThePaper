from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nonreciprocal_pb.reproduction import run_reproduction  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce all numerical targets for arXiv:1807.10084")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    result = run_reproduction(Path(args.config))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
