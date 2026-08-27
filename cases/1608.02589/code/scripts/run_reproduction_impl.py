from __future__ import annotations

import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dtc_feature_sim import run_case  # noqa: E402


def main() -> None:
    run_case(WORKSPACE)


if __name__ == "__main__":
    main()
