from __future__ import annotations

import json
import sys
import time
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
sys.path.insert(0, str(CODE_ROOT / "src"))

from cavity_transport.artifacts import write_json  # noqa: E402
from cavity_transport.checks import run_scientific_checks  # noqa: E402


def main() -> int:
    started = time.perf_counter()
    payload = run_scientific_checks()
    payload["runtime_seconds"] = time.perf_counter() - started
    path = write_json(
        CASE_ROOT / "outputs" / "checks" / "scientific_acceptance.json", payload
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote {path}")
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
