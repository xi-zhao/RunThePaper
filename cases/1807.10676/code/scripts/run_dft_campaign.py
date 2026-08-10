#!/usr/bin/env python3
"""Prepare, preflight, execute, and analyze the paper-scale DFT campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from tbg_topology.dft_campaign import (  # noqa: E402
    CampaignError,
    ExternalAssetError,
    analyze_campaign,
    canonical_json_hash,
    load_config,
    preflight_external_assets,
    prepare_campaign,
    run_campaign_job,
    write_json,
)


def _workspace_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    return candidate if candidate.is_absolute() else WORKSPACE / candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Code-ready VASP campaign for Main Fig. 3 and Supplement Figs. 11-12 "
            "of arXiv:1807.10676. With no action, prepare deterministic decks."
        )
    )
    parser.add_argument(
        "--config", required=True, help="workspace-relative campaign config"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="prepare",
        choices=["prepare", "preflight", "run-job", "analyze"],
    )
    parser.add_argument(
        "--campaign-root",
        default="outputs/checks/dft_paper_scale",
        help="workspace-relative or absolute generated campaign directory",
    )
    parser.add_argument("--job-id", help="job id for run-job")
    parser.add_argument("--vasp-command", help="licensed VASP launch command")
    parser.add_argument("--potcar", help="external carbon LDA POTCAR path")
    parser.add_argument("--available-cpus", type=int)
    parser.add_argument("--available-memory-gib", type=int)
    parser.add_argument(
        "--acknowledge-unpinned-potcar",
        action="store_true",
        help=(
            "acknowledge that the paper omitted the PAW identity; record the supplied "
            "POTCAR hash and label results as non-author-binary-equivalent"
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="skip only stages whose OUTCAR contains VASP's completion marker",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config_path = _workspace_path(args.config).resolve()
    campaign_root = _workspace_path(args.campaign_root).resolve()
    try:
        config = load_config(config_path)
        if args.action == "prepare":
            result = prepare_campaign(config, campaign_root)
        elif args.action == "preflight":
            result = preflight_external_assets(
                config,
                vasp_command=args.vasp_command,
                potcar_path=Path(args.potcar).expanduser() if args.potcar else None,
                acknowledge_unpinned_potcar=args.acknowledge_unpinned_potcar,
                available_cpus=args.available_cpus,
                available_memory_gib=args.available_memory_gib,
            )
            result["config_sha256"] = canonical_json_hash(config)
            write_json(
                campaign_root / "checks" / "external_asset_preflight.json", result
            )
        elif args.action == "run-job":
            if not args.job_id:
                parser.error("run-job requires --job-id")
            preflight = preflight_external_assets(
                config,
                vasp_command=args.vasp_command,
                potcar_path=Path(args.potcar).expanduser() if args.potcar else None,
                acknowledge_unpinned_potcar=args.acknowledge_unpinned_potcar,
                available_cpus=args.available_cpus,
                available_memory_gib=args.available_memory_gib,
            )
            write_json(
                campaign_root / "checks" / "external_asset_preflight.json", preflight
            )
            result = run_campaign_job(
                config,
                campaign_root,
                args.job_id,
                preflight=preflight,
                resume=args.resume,
            )
        else:
            result = analyze_campaign(config, campaign_root, WORKSPACE)
    except ExternalAssetError as error:
        blocked = {
            "schema_version": 1,
            "paper_id": "1807.10676",
            "status": "blocked_external_assets_or_machine",
            "error": str(error),
            "remediation": (
                "Supply licensed VASP/POTCAR outside the repository and a machine meeting "
                "the declared 72-CPU/2048-GiB profile."
            ),
        }
        write_json(campaign_root / "checks" / "external_asset_preflight.json", blocked)
        print(json.dumps(blocked, indent=2), file=sys.stderr)
        return 2
    except CampaignError as error:
        print(
            json.dumps({"status": "failed", "error": str(error)}, indent=2),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") not in {"failed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
