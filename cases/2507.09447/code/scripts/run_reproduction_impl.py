from __future__ import annotations

from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from reproduce_2507_09447 import run_feature_case  # noqa: E402


def main() -> None:
    result = run_feature_case(WORKSPACE)
    print(result["status"])


if __name__ == "__main__":
    main()
