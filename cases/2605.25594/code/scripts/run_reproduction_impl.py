from __future__ import annotations

import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from anderson_sensitivity import run_case  # noqa: E402


def main() -> None:
    checks = run_case(WORKSPACE)
    print(checks["status"])


if __name__ == "__main__":
    main()
