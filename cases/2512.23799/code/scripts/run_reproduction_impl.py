from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from magic_state_simulation import run_all  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the clean-room proxy suite for 2512.23799.")
    parser.add_argument("--config", help="Workspace-relative JSON config under config/.")
    parser.add_argument("--output-root", help="Workspace-relative output root under outputs/.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def safe_workspace_ref(value: str, *, root: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != (root,):
        raise ValueError(f"path must be workspace-relative under {root}/: {value!r}")
    return path


def main() -> int:
    args = parse_args()
    config: dict[str, object] = {}
    if args.config:
        config_ref = safe_workspace_ref(args.config, root="config")
        config = json.loads((ROOT / config_ref).read_text(encoding="utf-8"))
    output_ref = (
        safe_workspace_ref(args.output_root, root="outputs")
        if args.output_root
        else Path(str(config.get("output_root", "outputs/proxy_suite")))
    )
    output_ref = safe_workspace_ref(output_ref.as_posix(), root="outputs")
    p_grid = config.get("p_grid")
    resolved = {
        "config_path": args.config,
        "output_root": output_ref.as_posix(),
        "p_grid": p_grid if isinstance(p_grid, list) else None,
    }
    if args.dry_run:
        print(json.dumps({"status": "ready", "resolved_run": resolved}, indent=2, ensure_ascii=False))
        return 0
    result = run_all(
        data_dir=ROOT / output_ref / "data",
        check_dir=ROOT / output_ref / "checks",
        p_grid=p_grid if isinstance(p_grid, list) else None,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
