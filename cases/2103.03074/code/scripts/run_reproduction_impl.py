from __future__ import annotations

import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from big_batch_feature_sim import run_reproduction  # noqa: E402


def main() -> None:
    run_reproduction(WORKSPACE)


if __name__ == "__main__":
    main()
