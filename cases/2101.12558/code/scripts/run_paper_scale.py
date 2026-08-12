#!/usr/bin/env python3
"""Plan, shard, resume, and optionally execute public-backend DFT+DMFT."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from nio_dmft.campaign import (  # noqa: E402
    build_plan,
    prepare_decks,
    select_shard,
    sha256,
    write_json_atomic,
)
from nio_dmft.paper_scale import (  # noqa: E402
    build_paper_observables,
    solve_wannier_dmft,
)
from nio_dmft.qe import (  # noqa: E402
    ExternalInputError,
    validate_pseudopotentials,
)


def implementation_digest() -> str:
    digest = hashlib.sha256()
    files = sorted((WORKSPACE / "src" / "nio_dmft").glob("*.py"))
    files.extend(
        [
            WORKSPACE / "scripts" / "run_paper_scale.py",
            WORKSPACE / "scripts" / "run_reproduction.py",
        ]
    )
    for path in files:
        digest.update(path.relative_to(WORKSPACE).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def input_inventory(
    config_path: Path,
    config: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "paper_id": "2101.12558",
        "config": {
            "path": config_path.relative_to(WORKSPACE).as_posix(),
            "sha256": sha256(config_path),
        },
        "implementation_sha256": implementation_digest(),
        "source_pixels_used_by_numerics": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "geometry_provenance": "reconstructed_from_printed_scalars",
        "missing_paper_inputs": config["missing_paper_inputs"],
    }


def _run_checked(argv: list[str], cwd: Path, log_name: str) -> None:
    executable = shutil.which(argv[0])
    if executable is None:
        raise ExternalInputError(f"public backend is unavailable: {argv[0]}")
    log_path = cwd / log_name
    with log_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(
            [executable, *argv[1:]],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if completed.returncode != 0:
        raise ExternalInputError(
            f"backend command failed ({completed.returncode}): {' '.join(argv)}"
        )


def _expand_density_update_argv(
    template: list[str],
    unit_dir: Path,
    result_root: Path,
    contract: Path,
    iteration: int,
) -> list[str]:
    replacements = {
        "{unit_dir}": str(unit_dir),
        "{result_root}": str(result_root),
        "{dmft_contract}": str(contract),
        "{wannier_hr}": str(unit_dir / f"{unit_dir.name.replace('-', '_')}_hr.dat"),
        "{density_feedback}": str(result_root / "density_feedback.npz"),
        "{charge_report}": str(result_root / f"charge_update_{iteration:03d}.json"),
        "{outer_iteration}": str(iteration),
    }
    return [replacements.get(token, token) for token in template]


def _run_dft_wannier(deck: Path, prefix: str) -> None:
    _run_checked(["pw.x", "-in", "pw.in"], deck, "pw.out")
    _run_checked(["wannier90.x", "-pp", prefix], deck, "wannier90-preprocess.out")
    _run_checked(
        ["pw2wannier90.x", "-in", "pw2wannier90.in"],
        deck,
        "pw2wannier90.out",
    )
    _run_checked(["wannier90.x", prefix], deck, "wannier90.out")


def _density_update_contract(config: dict[str, object]) -> list[str]:
    template = config["charge_feedback"].get("density_update_argv")
    if (
        not isinstance(template, list)
        or not template
        or not all(isinstance(value, str) and value for value in template)
    ):
        raise ExternalInputError(
            "charge-density update command is required; the internal Wannier-DMFT "
            "loop is implemented, but the unpublished plane-wave projector/density "
            "injection convention cannot be guessed"
        )
    return template


def execute_unit(
    unit: dict[str, object],
    config: dict[str, object],
    inventory: dict[str, object],
) -> dict[str, object]:
    unit_id = str(unit["unit_id"])
    deck = WORKSPACE / "outputs" / "paper_scale" / "decks" / unit_id
    result_root = WORKSPACE / "outputs" / "paper_scale" / unit_id
    result_root.mkdir(parents=True, exist_ok=True)
    marker = result_root / "execution.json"
    if marker.exists():
        existing = json.loads(marker.read_text(encoding="utf-8"))
        if (
            existing.get("config_sha256") == inventory["config"]["sha256"]
            and existing.get("implementation_sha256")
            == inventory["implementation_sha256"]
            and existing.get("status") == "completed"
        ):
            return existing

    pseudo = validate_pseudopotentials(config["pseudopotentials"], WORKSPACE)
    pseudo_dir = deck / "pseudo"
    pseudo_dir.mkdir(exist_ok=True)
    for species, record in pseudo.items():
        destination = pseudo_dir / str(config["pseudopotentials"][species]["filename"])
        shutil.copy2(record["path"], destination)

    prefix = unit_id.replace("-", "_")
    density_update = _density_update_contract(config)
    dmft_contract_path = deck / "dmft.json"
    dmft_contract = json.loads(dmft_contract_path.read_text(encoding="utf-8"))
    feedback = config["charge_feedback"]
    outer_history = []
    charge_converged = False
    for outer_iteration in range(1, int(feedback["maximum_outer_iterations"]) + 1):
        _run_dft_wannier(deck, prefix)
        execution = solve_wannier_dmft(
            deck / f"{prefix}_hr.dat",
            dmft_contract,
            result_root,
            checkpoint_name=f"inner_dmft_{outer_iteration:03d}.npz",
        )
        if not execution.result.converged:
            raise ExternalInputError(
                f"inner multi-site DMFT did not converge at outer iteration {outer_iteration}"
            )
        if float(execution.result.average_signs.min()) < float(
            config["cthyb"]["minimum_average_sign"]
        ):
            raise ExternalInputError(
                f"CT-HYB sign gate failed at outer iteration {outer_iteration}"
            )
        report_path = result_root / f"charge_update_{outer_iteration:03d}.json"
        _run_checked(
            _expand_density_update_argv(
                density_update,
                deck,
                result_root,
                dmft_contract_path,
                outer_iteration,
            ),
            deck,
            f"charge-update-{outer_iteration:03d}.out",
        )
        if not report_path.is_file():
            raise ExternalInputError(
                "density-update command did not write the required charge report"
            )
        charge_report = json.loads(report_path.read_text(encoding="utf-8"))
        charge_rms = float(charge_report["charge_rms"])
        outer_history.append(
            {
                "iteration": outer_iteration,
                "charge_rms": charge_rms,
                "inner_dmft_iterations": execution.result.iterations,
                "self_energy_final_residual_ev": float(
                    execution.result.residual_history[-1]
                ),
                "minimum_average_sign": float(execution.result.average_signs.min()),
                "charge_report": report_path.relative_to(WORKSPACE).as_posix(),
            }
        )
        if charge_rms <= float(feedback["charge_rms_tolerance"]):
            charge_converged = True
            build_paper_observables(execution, dmft_contract, result_root)
            break
    if not charge_converged:
        raise ExternalInputError(
            "outer charge-self-consistency exhausted its iteration budget"
        )
    write_json_atomic(
        result_root / "charge_self_consistency.json",
        {
            "schema_version": 1,
            "unit_id": unit_id,
            "converged": True,
            "iterations": len(outer_history),
            "history": outer_history,
            "density_update_boundary": (
                "backend-specific public plane-wave density injection only; "
                "all DMFT numerics are internal"
            ),
        },
    )
    required = [
        result_root / "lattice_hamiltonian.npz",
        result_root / "self_energy.npz",
        result_root / "observables.npz",
        result_root / "density_feedback.npz",
        result_root / "inner_acceptance.json",
        result_root / "charge_self_consistency.json",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ExternalInputError(
            f"adapter completed without required scientific outputs: {missing}"
        )
    record = {
        "schema_version": 1,
        "unit_id": unit_id,
        "status": "completed",
        "config_sha256": inventory["config"]["sha256"],
        "implementation_sha256": inventory["implementation_sha256"],
        "target_ids": unit["target_ids"],
        "outputs": [
            {"path": path.relative_to(WORKSPACE).as_posix(), "sha256": sha256(path)}
            for path in required
        ],
        "promotion_allowed": False,
        "promotion_reason": (
            "scientific comparison, convergence, and fresh independent review "
            "must pass after execution"
        ),
    }
    write_json_atomic(marker, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    arguments = parser.parse_args()
    config_path = (WORKSPACE / arguments.config).resolve()
    config_path.relative_to(WORKSPACE)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan = build_plan(config)
    selected = select_shard(plan, arguments.shard_index, arguments.shard_count)
    plan["selected_shard"] = {
        "index": arguments.shard_index,
        "count": arguments.shard_count,
        "unit_ids": [unit["unit_id"] for unit in selected],
    }
    deck_records = prepare_decks(
        config,
        WORKSPACE / "outputs" / "paper_scale" / "decks",
    )
    plan["decks"] = deck_records
    inventory = input_inventory(config_path, config)
    write_json_atomic(
        WORKSPACE / "outputs" / "checks" / "paper_scale" / "plan.json",
        plan,
    )
    write_json_atomic(
        WORKSPACE / "outputs" / "checks" / "paper_scale" / "input_inventory.json",
        inventory,
    )
    if arguments.execute:
        try:
            records = [execute_unit(unit, config, inventory) for unit in selected]
        except ExternalInputError as exc:
            write_json_atomic(
                WORKSPACE
                / "outputs"
                / "checks"
                / "paper_scale"
                / "backend_boundary.json",
                {
                    "schema_version": 1,
                    "status": "compute_or_indispensable_input_deferred",
                    "reason": str(exc),
                    "paper_targets_completed": [],
                },
            )
            return 3
        write_json_atomic(
            WORKSPACE / "outputs" / "checks" / "paper_scale" / "execution_summary.json",
            {"schema_version": 1, "records": records},
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
