from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent
sys.path.insert(0, str(WORKSPACE / "src"))

from benchmark_release import (  # noqa: E402
    ARCHIVE_FILENAME,
    ARCHIVE_RECORD_URL,
    ARCHIVE_SHA256,
    RANDOM_PANEL_ORDER,
    RELEASE_PREFIX,
    validate_archive,
)
from independent_tn import (  # noqa: E402
    TensorNetwork,
    build_qsim_network,
    build_structured_network,
    optimize_network,
)


PRESETS = {
    "smoke": {"greedy_trials": 2, "anneal_steps": 10_000, "polish_steps": 2_000},
    "balanced": {"greedy_trials": 4, "anneal_steps": 100_000, "polish_steps": 20_000},
    "full": {"greedy_trials": 10, "anneal_steps": 600_000, "polish_steps": 60_000},
}


def _default_archive() -> Path:
    internal = CASE_ROOT / "raw" / "benchmarks" / ARCHIVE_FILENAME
    public = CASE_ROOT / "inputs" / ARCHIVE_FILENAME
    return internal if internal.is_file() else public


def _default_output_dir() -> Path:
    output_root = (
        WORKSPACE / "outputs"
        if (WORKSPACE / "metadata").is_dir()
        else CASE_ROOT / "outputs"
    )
    return output_root / "data" / "independent_python"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _structured_family(name: str) -> str:
    if name.startswith("ct_"):
        return "Clifford+T"
    if name.startswith("qaoa_"):
        return "QAOA"
    if name.startswith("vqe_"):
        return "VQE"
    raise ValueError(f"Unrecognized structured benchmark name: {name}")


def load_networks(
    archive_path: Path,
    *,
    member_audit: list[str] | None = None,
) -> list[TensorNetwork]:
    """Read only raw circuit inputs, never author plans or result studies.

    ``member_audit`` makes the clean-room boundary observable: it records every
    ZIP payload opened by the primary loader. Merely listing the ZIP central
    directory is not counted as consuming an author-generated artifact.
    """

    networks: list[TensorNetwork] = []
    with zipfile.ZipFile(archive_path) as release:
        def read_member(member: str) -> bytes:
            if member_audit is not None:
                member_audit.append(member)
            return release.read(member)

        for name in RANDOM_PANEL_ORDER:
            member = f"{RELEASE_PREFIX}circuits/{name}.txt"
            text = read_member(member).decode("utf-8")
            networks.append(build_qsim_network(name, "random", text))

        input_prefix = f"{RELEASE_PREFIX}experiments/structured-v1/formal-inputs/"
        circuit_members = sorted(
            member
            for member in release.namelist()
            if member.startswith(input_prefix)
            and member.endswith(".circuit.json")
            and not Path(member).name.startswith("val_")
        )
        for member in circuit_members:
            name = Path(member).name.removesuffix(".circuit.json")
            circuit = json.loads(read_member(member))
            observable_member = f"{input_prefix}{name}.op"
            observable = read_member(observable_member).decode("utf-8")
            networks.append(
                build_structured_network(
                    name,
                    _structured_family(name),
                    circuit,
                    observable,
                )
            )
    if len(networks) != 67:
        raise ValueError(f"Expected 67 benchmark networks, built {len(networks)}")
    return networks


def _configuration(args: argparse.Namespace) -> dict[str, Any]:
    preset = dict(PRESETS[args.preset])
    for name in ("greedy_trials", "anneal_steps", "polish_steps"):
        value = getattr(args, name)
        if value is not None:
            preset[name] = value
    return {
        "preset": args.preset,
        **preset,
        "seed": args.seed,
        "initializer": "cotengra-0.7.5 generic FLOP search",
        "optimizer": "independent Python NNI simulated annealing",
        "temperature": {"start": 1.0, "end": 0.005},
        "polish_temperature": {"start": 0.02, "end": 0.0002},
    }


def _config_hash(configuration: dict[str, Any]) -> str:
    payload = json.dumps(configuration, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _select_networks(networks: list[TensorNetwork], args: argparse.Namespace) -> list[TensorNetwork]:
    selected = networks
    if args.scope == "random":
        selected = [network for network in selected if network.family == "random"]
    elif args.scope == "structured":
        selected = [network for network in selected if network.family != "random"]
    if args.circuit:
        requested = set(args.circuit)
        selected = [network for network in selected if network.name in requested]
        missing = sorted(requested - {network.name for network in selected})
        if missing:
            raise ValueError(f"Unknown or out-of-scope circuits: {missing}")
    return selected


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Independently reimplement the numerical optimization for Figures 8/9; "
            "the authors' Rust crates and contraction plans are never executed or read."
        )
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=_default_archive(),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
    )
    parser.add_argument("--scope", choices=("all", "random", "structured"), default="all")
    parser.add_argument("--circuit", action="append", help="Run one named circuit; repeat as needed.")
    parser.add_argument("--preset", choices=tuple(PRESETS), default="balanced")
    parser.add_argument("--greedy-trials", type=int)
    parser.add_argument("--anneal-steps", type=int)
    parser.add_argument("--polish-steps", type=int)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true", help="Recompute matching completed records.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive_info = validate_archive(args.archive)
    if archive_info["sha256"] != ARCHIVE_SHA256:
        raise ValueError("Unexpected benchmark archive")
    configuration = _configuration(args)
    configuration_hash = _config_hash(configuration)
    input_members: list[str] = []
    networks = _select_networks(
        load_networks(args.archive, member_audit=input_members),
        args,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    campaign_started = time.perf_counter()
    completed: list[str] = []
    skipped: list[str] = []
    for position, network in enumerate(networks, start=1):
        output_path = args.output_dir / f"{network.name}.json"
        if output_path.is_file() and not args.force:
            prior = json.loads(output_path.read_text(encoding="utf-8"))
            if (
                prior.get("configuration_sha256") == configuration_hash
                and prior.get("network", {}).get("topology_sha256") == network.topology_sha256
                and prior.get("status") == "completed"
            ):
                skipped.append(network.name)
                print(f"[{position:02d}/{len(networks):02d}] skip {network.name}", flush=True)
                continue

        print(
            f"[{position:02d}/{len(networks):02d}] optimize {network.name} "
            f"({len(network.leaves)} leaves, {network.green_leaves} green)",
            flush=True,
        )
        started = time.perf_counter()
        result = optimize_network(
            network,
            greedy_trials=int(configuration["greedy_trials"]),
            anneal_steps=int(configuration["anneal_steps"]),
            polish_steps=int(configuration["polish_steps"]),
            seed=int(configuration["seed"]),
        )
        convert = result["convert_only"]
        polish = result["polished"]
        full = result["full_anneal"]
        result.update(
            {
                "schema_version": 1,
                "paper_id": "2608.03987",
                "evidence_stage": "independent_reimplementation",
                "status": "completed",
                "generated_at": _utc_now(),
                "configuration": configuration,
                "configuration_sha256": configuration_hash,
                "runtime_seconds": time.perf_counter() - started,
                "input_archive": {
                    "sha256": archive_info["sha256"],
                    "filename": args.archive.name,
                    "record_url": ARCHIVE_RECORD_URL,
                },
                "integrity_boundary": (
                    "Built from raw circuit/qsim inputs. No author Rust crate, published "
                    "contraction tree, optimizer study, or result CSV is read. Cotengra is "
                    "used only as an unrelated generic contraction-tree initializer."
                ),
                "pipeline": {
                    "relative_overhead_gap": abs(convert["overhead"] - full["overhead"])
                    / full["overhead"],
                    "polish_overhead_gap": abs(polish["overhead"] - full["overhead"])
                    / full["overhead"],
                    "relative_real_cost_gap": abs(convert["real_volume"] - full["real_volume"])
                    / full["real_volume"],
                    "polish_real_cost_gap": abs(polish["real_volume"] - full["real_volume"])
                    / full["real_volume"],
                },
            }
        )
        _write_json(output_path, result)
        completed.append(network.name)
        print(
            f"    overhead convert/full={convert['overhead']:.6f}/{full['overhead']:.6f}; "
            f"gap={result['pipeline']['relative_overhead_gap']:.3e}; "
            f"{result['runtime_seconds']:.1f}s",
            flush=True,
        )

    records = sorted(
        path
        for path in args.output_dir.glob("*.json")
        if path.name != "campaign_manifest.json"
    )
    records_runtime_seconds_total = sum(
        float(json.loads(path.read_text(encoding="utf-8")).get("runtime_seconds", 0.0))
        for path in records
    )
    manifest = {
        "schema_version": 1,
        "paper_id": "2608.03987",
        "evidence_stage": "independent_reimplementation",
        "generated_at": _utc_now(),
        "configuration": configuration,
        "configuration_sha256": configuration_hash,
        "scope": args.scope,
        "selected_circuits": len(networks),
        "completed_this_invocation": completed,
        "skipped_this_invocation": skipped,
        "records_present": len(records),
        "records_runtime_seconds_total": records_runtime_seconds_total,
        "runtime_seconds": time.perf_counter() - campaign_started,
        "python": sys.version,
        "platform": platform.platform(),
        "source_policy": "raw circuits only; no author implementation or plans",
        "input_member_audit": {
            "payloads_read": len(input_members),
            "allowed_prefixes": [
                f"{RELEASE_PREFIX}circuits/",
                f"{RELEASE_PREFIX}experiments/structured-v1/formal-inputs/",
            ],
            "members": input_members,
            "author_results_or_plans_read": False,
        },
    }
    _write_json(args.output_dir / "campaign_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
