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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--t005-data-output", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    result = run_campaign(config)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    t005_data = {
        "schema_version": 1,
        "paper_id": result["paper_id"],
        "target_id": "T005",
        "claim_ids": ["C06-AD-HPTP-DIM-12", "C31-AD-CIRCUIT-KAPPA-5"],
        "evidence_status": "author_evidence_awaiting_fresh_review",
        "protocol": result["target_checks"]["T005"]["amplitude_damping_protocol"],
    }
    t005_output = Path(args.t005_data_output)
    t005_output.parent.mkdir(parents=True, exist_ok=True)
    t005_output.write_text(json.dumps(t005_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
