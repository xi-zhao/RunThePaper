from __future__ import annotations

import argparse
import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the paper-scale external-asset contract for 2103.03074."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=WORKSPACE / "config" / "paper_scale_contract.json",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=WORKSPACE / "outputs" / "paper_scale_contract",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the contract/asset manifest without attempting any large-scale numerics.",
    )
    return parser.parse_args()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output_root = args.output_root.resolve()

    local_assets = []
    for relative in config["required_inputs"]["circuit_assets"]:
        asset_path = CASE_ROOT / relative
        local_assets.append(
            {
                "path": relative,
                "exists": asset_path.exists(),
                "kind": "local_case_asset",
            }
        )

    external_assets = []
    for description in config["required_inputs"]["external_assets_expected"]:
        external_assets.append(
            {
                "description": description,
                "status": "missing_from_case",
            }
        )

    manifest_payload = {
        "status": "asset_contract_ready_missing_source_input",
        "dry_run": bool(args.dry_run),
        "paper_id": config["paper_id"],
        "artifact_stage": config["artifact_stage"],
        "implementation_kind": config["implementation_kind"],
        "targets": config["paper_targets"],
        "paper_parameters": config["paper_parameters"],
        "local_assets": local_assets,
        "external_assets": external_assets,
        "direct_reason": "The case does not yet contain the paper-scale Sycamore circuit instances or an independently derived contraction and slicing plan needed to recompute the printed Table III bitstrings.",
        "root_reason": "The published paper explains the method, but the current case lacks the large-scale source inputs needed to execute the 53-qubit tensor-network contract independently.",
        "next_execution_boundary": "Once those assets are added, the paper-scale runner must be replaced by a true isolated numerical contraction pipeline before any figure is promoted beyond reduced_scale.",
    }
    _write_json(output_root / "checks" / "paper_scale_contract.json", manifest_payload)

    table_manifest = {
        "status": "asset_contract_ready_missing_source_input",
        "paper_item": "Table III",
        "required_target_examples": config["paper_parameters"]["table3_examples"],
        "missing_inputs": [entry["description"] for entry in external_assets],
    }
    _write_json(output_root / "data" / "table3_targets_manifest.json", table_manifest)

    target_manifest = {
        "status": "asset_contract_ready_missing_source_input",
        "paper_items": [target["paper_item"] for target in config["paper_targets"]],
        "note": "This planning manifest reserves the missing paper-scale targets; no scientific data are generated.",
    }
    _write_json(output_root / "targets" / "paper_scale_targets_manifest.json", target_manifest)

    print(json.dumps(manifest_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
