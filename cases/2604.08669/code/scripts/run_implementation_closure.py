from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from implementation_closure import run_campaign  # noqa: E402


def _workspace_path(value: str, *, root: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != (root,):
        raise ValueError(f"path must be workspace-relative under {root}/")
    return WORKSPACE / relative


def main() -> int:
    parser = argparse.ArgumentParser(description="Attest the runnable Fig. 3/Fig. 4 implementation paths.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    config = json.loads(_workspace_path(args.config, root="config").read_text(encoding="utf-8"))
    output_root = _workspace_path(args.output_root, root="outputs")
    output_root.mkdir(parents=True, exist_ok=True)
    result = run_campaign(config, output_root)
    (output_root / "campaign_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
