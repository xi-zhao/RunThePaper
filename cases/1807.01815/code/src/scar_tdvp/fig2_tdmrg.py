"""Paper-scale finite-MPS evolution for main Figure 2(b,c).

The physical spin chain is blocked into pairs.  The allowed pair states are
``|00>``, ``|01>``, and ``|10>``; in this basis the periodic three-site PXP
Hamiltonian becomes a nearest-neighbour Hamiltonian on ``L / 2`` three-state
blocks.  This is an exact change of basis, not a proxy model.

The implementation deliberately consumes only the paper-derived configuration.
It never reads author code, author arrays, digitized curves, or figure pixels.
"""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import numpy as np
from scipy.linalg import expm


BLOCK_STATES: tuple[tuple[int, int], ...] = ((0, 0), (0, 1), (1, 0))
BLOCK_INDEX = {state: index for index, state in enumerate(BLOCK_STATES)}
REQUIRED_PROFILES = ("primary", "dt_refined", "bond_refined")
INITIAL_STATES = ("zero", "z2")
ATTRIBUTION_ORDER = (
    "reproduction_defect",
    "parameter_ambiguity",
    "insufficient_compute",
    "inconclusive",
)


def _require_quimb() -> Any:
    try:
        import quimb
        import quimb.tensor as qtn
    except ImportError as error:  # pragma: no cover - exercised without optional env
        raise RuntimeError(
            "Figure 2 paper-scale evolution requires the pinned optional "
            "dependency in requirements-paper-scale.txt"
        ) from error
    return quimb, qtn


def blocked_bond_hamiltonian(omega: float = 1.0) -> np.ndarray:
    """Return the exact two-block Hamiltonian whose periodic sum is PXP.

    For neighbouring blocks ``j`` and ``j+1`` the first term flips the right
    spin of block ``j`` when both adjacent physical spins are zero; the second
    term flips the left spin of block ``j+1`` under the complementary
    constraint.  Each physical spin therefore appears in exactly one bond.
    """

    projector_left_zero = np.diag([1.0, 1.0, 0.0])
    projector_right_zero = np.diag([1.0, 0.0, 1.0])
    flip_left = np.zeros((3, 3), dtype=float)
    flip_right = np.zeros((3, 3), dtype=float)
    flip_left[0, 2] = flip_left[2, 0] = 0.5 * float(omega)
    flip_right[0, 1] = flip_right[1, 0] = 0.5 * float(omega)
    return np.kron(flip_right, projector_left_zero) + np.kron(
        projector_right_zero, flip_left
    )


def blocked_dense_hamiltonian(block_count: int, omega: float = 1.0) -> np.ndarray:
    """Build the small dense blocked Hamiltonian used only by equivalence tests."""

    if block_count < 2:
        raise ValueError("block_count must be at least two")
    local = blocked_bond_hamiltonian(omega)
    dimension = 3**block_count
    result = np.zeros((dimension, dimension), dtype=complex)
    for column in range(dimension):
        digits = []
        value = column
        for _ in range(block_count):
            digits.append(value % 3)
            value //= 3
        digits.reverse()
        for left in range(block_count):
            right = (left + 1) % block_count
            pair_index = 3 * digits[left] + digits[right]
            for output_index, amplitude in enumerate(local[:, pair_index]):
                if amplitude == 0.0:
                    continue
                target = digits.copy()
                target[left] = output_index // 3
                target[right] = output_index % 3
                row = 0
                for digit in target:
                    row = 3 * row + digit
                result[row, column] += amplitude
    return result


def physical_state_to_block_index(state: Iterable[int]) -> int:
    """Map an allowed even-length physical bit string into the blocked basis."""

    values = tuple(int(value) for value in state)
    if len(values) % 2:
        raise ValueError("physical state length must be even")
    index = 0
    for site in range(0, len(values), 2):
        pair = values[site : site + 2]
        if pair not in BLOCK_INDEX:
            raise ValueError(f"state contains a forbidden pair: {pair}")
        index = 3 * index + BLOCK_INDEX[pair]
    return index


def edge_coloring(block_count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Greedily partition the periodic bonds into disjoint matchings."""

    if block_count < 3:
        raise ValueError("periodic TEBD needs at least three blocks")
    groups: list[list[tuple[int, int]]] = []
    for edge in ((site, (site + 1) % block_count) for site in range(block_count)):
        edge_sites = set(edge)
        for group in groups:
            if all(edge_sites.isdisjoint(existing) for existing in group):
                group.append(edge)
                break
        else:
            groups.append([edge])
    return tuple(tuple(group) for group in groups)


@lru_cache(maxsize=32)
def _gate(omega: float, duration: float) -> np.ndarray:
    return expm(-1j * float(duration) * blocked_bond_hamiltonian(float(omega)))


def product_mps(block_count: int, initial_state: str) -> Any:
    """Create the open-boundary MPS representation used for the periodic ring."""

    _, qtn = _require_quimb()
    if initial_state == "zero":
        block_value = 0
    elif initial_state == "z2":
        # Physical convention inherited from constrained.py: (0, 1) per block.
        block_value = 1
    else:
        raise ValueError(f"unknown initial state: {initial_state}")
    local = np.zeros(3, dtype=complex)
    local[block_value] = 1.0
    return qtn.MPS_product_state([local.copy() for _ in range(block_count)])


def second_order_step(
    psi: Any,
    *,
    time_step: float,
    omega: float,
    max_bond: int,
    cutoff: float,
) -> None:
    """Apply a symmetric product formula over disjoint periodic bond groups."""

    groups = edge_coloring(int(psi.L))
    schedule = [*(zip(groups[:-1], [0.5] * (len(groups) - 1))), (groups[-1], 1.0)]
    schedule.extend(zip(reversed(groups[:-1]), [0.5] * (len(groups) - 1)))
    information: dict[str, Any] = {"cur_orthog": "calc"}
    for group, fraction in schedule:
        gate = _gate(float(omega), float(time_step) * float(fraction))
        for sites in group:
            # The sole ring-closing bond is non-local in the OBC storage order.
            # Quimb moves it through the chain with SVD-controlled swaps and
            # restores the original physical ordering after the gate.
            psi.gate_with_auto_swap_(
                gate,
                where=sites,
                info=information,
                swap_back=True,
                max_bond=int(max_bond),
                cutoff=float(cutoff),
                cutoff_mode="sum2",
            )


def evolve_to(
    psi: Any,
    current_time: float,
    target_time: float,
    *,
    time_step: float,
    omega: float,
    max_bond: int,
    cutoff: float,
) -> float:
    """Advance to an exact requested output time without overshooting it."""

    current = float(current_time)
    target = float(target_time)
    tolerance = 1e-12 * max(1.0, abs(target))
    while current < target - tolerance:
        step = min(float(time_step), target - current)
        second_order_step(
            psi,
            time_step=step,
            omega=omega,
            max_bond=max_bond,
            cutoff=cutoff,
        )
        current += step
    return target


def _entropy_from_density(density: np.ndarray) -> float:
    hermitian = 0.5 * (density + density.conj().T)
    eigenvalues = np.linalg.eigvalsh(hermitian)
    eigenvalues = eigenvalues[eigenvalues > 1e-14]
    return float(-np.sum(eigenvalues * np.log2(eigenvalues)))


def _left_physical_density(block_density: np.ndarray) -> np.ndarray:
    result = np.zeros((2, 2), dtype=complex)
    for row, (left_row, right_row) in enumerate(BLOCK_STATES):
        for column, (left_column, right_column) in enumerate(BLOCK_STATES):
            if right_row == right_column:
                result[left_row, left_column] += block_density[row, column]
    return result


def observe_entropies(psi: Any, six_site_blocks: int) -> tuple[float, float]:
    """Return six-physical-site and one-physical-site base-2 entropies."""

    six_density = np.asarray(
        psi.partial_trace_to_dense_canonical(
            tuple(range(int(six_site_blocks))), normalized=True
        )
    )
    block_density = np.asarray(
        psi.partial_trace_to_dense_canonical((0,), normalized=True)
    )
    return _entropy_from_density(six_density), _entropy_from_density(
        _left_physical_density(block_density)
    )


def energy_expectation(psi: Any, omega: float) -> float:
    """Evaluate the full periodic blocked Hamiltonian expectation value."""

    local = blocked_bond_hamiltonian(float(omega))
    total = 0.0
    for left in range(int(psi.L)):
        right = (left + 1) % int(psi.L)
        value = psi.local_expectation_canonical(
            local, where=(left, right), normalized=True
        )
        total += float(np.real(value))
    return total


def constraint_violation(psi: Any) -> float:
    """Return total weight on forbidden adjacent physical excitations.

    The exact blocked Hamiltonian preserves the constrained subspace. Generic
    MPS truncation is not quantum-number aware, so this observable independently
    checks that compression has not leaked into the unused part of the
    three-state tensor-product basis.
    """

    right_excited = np.diag([0.0, 1.0, 0.0])
    left_excited = np.diag([0.0, 0.0, 1.0])
    forbidden_pair = np.kron(right_excited, left_excited)
    total = 0.0
    for left in range(int(psi.L)):
        right = (left + 1) % int(psi.L)
        value = psi.local_expectation_canonical(
            forbidden_pair, where=(left, right), normalized=True
        )
        total += float(np.real(value))
    return total


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def config_digest(config: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(config).encode("utf-8")).hexdigest()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def effective_config(config: dict[str, Any], *, smoke: bool = False) -> dict[str, Any]:
    result = deepcopy(config)
    if smoke:
        override = result.pop("smoke_override")
        result = _deep_merge(result, override)
        result["run_id"] = f"{config['run_id']}-smoke"
        result["scope"] = "algorithm_smoke_not_paper_evidence"
    else:
        result.pop("smoke_override", None)
    return result


def _positive_number(value: object, name: str) -> float:
    number = float(value)
    if not np.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return number


def validate_config(config: dict[str, Any], *, require_paper_scale: bool = True) -> None:
    if config.get("paper_id") != "1807.01815":
        raise ValueError("paper_id must be 1807.01815")
    parameters = config["parameters"]
    physical_length = int(parameters["physical_length"])
    if physical_length < 6 or physical_length % 2:
        raise ValueError("physical_length must be even and at least six")
    if parameters.get("boundary_condition") != "periodic":
        raise ValueError("Figure 2 requires the paper's periodic boundary condition")
    if tuple(parameters.get("block_basis", ())) != ("00", "01", "10"):
        raise ValueError("block_basis must be the exact constrained pair basis")
    if int(parameters["six_site_subsystem"]) != 6:
        raise ValueError("Figure 2(b) requires six contiguous physical sites")
    _positive_number(parameters["omega"], "omega")
    panel_b_max = _positive_number(parameters["panel_b_time_max"], "panel_b_time_max")
    panel_c_max = _positive_number(parameters["panel_c_time_max"], "panel_c_time_max")
    sample_step = _positive_number(parameters["sample_time_step"], "sample_time_step")
    checkpoint_interval = _positive_number(
        parameters["checkpoint_time_interval"], "checkpoint_time_interval"
    )
    diagnostic_interval = _positive_number(
        parameters["diagnostic_time_interval"], "diagnostic_time_interval"
    )
    if panel_b_max > panel_c_max:
        raise ValueError("panel_b_time_max cannot exceed panel_c_time_max")
    for name, value in (
        ("checkpoint_time_interval", checkpoint_interval),
        ("diagnostic_time_interval", diagnostic_interval),
    ):
        ratio = value / sample_step
        if not np.isclose(ratio, round(ratio), atol=1e-10):
            raise ValueError(f"{name} must be an integer multiple of sample_time_step")
    profiles = parameters["profiles"]
    if tuple(profiles) != REQUIRED_PROFILES:
        raise ValueError(f"profiles must be ordered as {REQUIRED_PROFILES}")
    for profile_name, profile in profiles.items():
        if int(profile["max_bond"]) < 2:
            raise ValueError(f"{profile_name}.max_bond must be at least two")
        time_step = _positive_number(profile["time_step"], f"{profile_name}.time_step")
        cutoff = _positive_number(profile["cutoff"], f"{profile_name}.cutoff")
        if time_step > sample_step:
            raise ValueError(f"{profile_name}.time_step cannot exceed sample_time_step")
        if cutoff >= 1.0:
            raise ValueError(f"{profile_name}.cutoff must be below one")
    primary = profiles["primary"]
    if profiles["dt_refined"]["time_step"] >= primary["time_step"]:
        raise ValueError("dt_refined must use a smaller time step than primary")
    if profiles["bond_refined"]["max_bond"] <= primary["max_bond"]:
        raise ValueError("bond_refined must use a larger bond dimension than primary")
    if require_paper_scale:
        if physical_length != 30 or panel_b_max != 100.0 or panel_c_max != 120.0:
            raise ValueError("paper-scale Fig. 2(b,c) requires L=30 and t=100/120")
        if "smoke_override" not in config:
            raise ValueError("paper config must include a separately labelled smoke override")
    acceptance = config["acceptance"]
    for name in (
        "norm_drift_max",
        "energy_drift_max",
        "constraint_violation_max",
        "dt_refinement_max_abs",
        "bond_refinement_max_abs",
        "product_entropy_max",
    ):
        _positive_number(acceptance[name], f"acceptance.{name}")
    for path_name in ("output_root", "checkpoint_root"):
        path = Path(config[path_name])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{path_name} must stay workspace-relative")


def load_config(path: Path, *, smoke: bool = False) -> tuple[dict[str, Any], str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    validate_config(raw, require_paper_scale=True)
    effective = effective_config(raw, smoke=smoke)
    # The raw contract above is the paper-scale gate.  The effective form
    # intentionally drops ``smoke_override`` before it is digested, so its
    # second validation checks the numerical invariants without requiring the
    # now-consumed wrapper field.
    validate_config(effective, require_paper_scale=False)
    return effective, config_digest(effective)


def _resolve_under(workspace: Path, relative: str) -> Path:
    root = workspace.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"path escapes workspace: {relative}")
    return path


def work_units(config: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        f"{initial_state}_{profile}"
        for initial_state in INITIAL_STATES
        for profile in config["parameters"]["profiles"]
    )


def _atomic_savez(path: Path, **arrays: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp.npz")
    np.savez_compressed(temporary, **arrays)
    os.replace(temporary, path)


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@dataclass
class LaneState:
    psi: Any
    times: list[float]
    six_entropy: list[float]
    one_entropy: list[float]
    raw_norms: list[float]
    max_bonds: list[int]
    energy_times: list[float]
    energies: list[float]
    constraint_times: list[float]
    constraint_violations: list[float]
    cumulative_norm_loss: float
    max_raw_norm_drift: float


def _new_lane_state(config: dict[str, Any], initial_state: str) -> LaneState:
    parameters = config["parameters"]
    psi = product_mps(int(parameters["physical_length"]) // 2, initial_state)
    six, one = observe_entropies(psi, int(parameters["six_site_subsystem"]) // 2)
    energy = energy_expectation(psi, float(parameters["omega"]))
    violation = constraint_violation(psi)
    return LaneState(
        psi=psi,
        times=[0.0],
        six_entropy=[six],
        one_entropy=[one],
        raw_norms=[1.0],
        max_bonds=[int(psi.max_bond())],
        energy_times=[0.0],
        energies=[energy],
        constraint_times=[0.0],
        constraint_violations=[violation],
        cumulative_norm_loss=0.0,
        max_raw_norm_drift=0.0,
    )


def _checkpoint_payload(
    state: LaneState, *, lane_id: str, digest: str, config: dict[str, Any]
) -> dict[str, object]:
    state.psi.permute_arrays("lrp")
    arrays = [np.asarray(array) for array in state.psi.arrays]
    metadata = {
        "schema_version": 1,
        "lane_id": lane_id,
        "config_digest": digest,
        "run_id": config["run_id"],
        "current_time": state.times[-1],
        "tensor_count": len(arrays),
        "cumulative_norm_loss": state.cumulative_norm_loss,
        "max_raw_norm_drift": state.max_raw_norm_drift,
    }
    payload: dict[str, object] = {
        "metadata_json": np.asarray(_canonical_json(metadata)),
        "times": np.asarray(state.times, dtype=float),
        "six_entropy": np.asarray(state.six_entropy, dtype=float),
        "one_entropy": np.asarray(state.one_entropy, dtype=float),
        "raw_norms": np.asarray(state.raw_norms, dtype=float),
        "max_bonds": np.asarray(state.max_bonds, dtype=np.int64),
        "energy_times": np.asarray(state.energy_times, dtype=float),
        "energies": np.asarray(state.energies, dtype=float),
        "constraint_times": np.asarray(state.constraint_times, dtype=float),
        "constraint_violations": np.asarray(
            state.constraint_violations, dtype=float
        ),
    }
    payload.update({f"tensor_{index:03d}": array for index, array in enumerate(arrays)})
    return payload


def _load_checkpoint(path: Path, *, lane_id: str, digest: str) -> LaneState:
    _, qtn = _require_quimb()
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata_json"].item()))
        if metadata["lane_id"] != lane_id or metadata["config_digest"] != digest:
            raise ValueError("checkpoint does not match lane/config digest")
        arrays = [
            np.asarray(archive[f"tensor_{index:03d}"])
            for index in range(int(metadata["tensor_count"]))
        ]
        psi = qtn.MatrixProductState(arrays, shape="lrp")
        return LaneState(
            psi=psi,
            times=np.asarray(archive["times"], dtype=float).tolist(),
            six_entropy=np.asarray(archive["six_entropy"], dtype=float).tolist(),
            one_entropy=np.asarray(archive["one_entropy"], dtype=float).tolist(),
            raw_norms=np.asarray(archive["raw_norms"], dtype=float).tolist(),
            max_bonds=np.asarray(archive["max_bonds"], dtype=int).tolist(),
            energy_times=np.asarray(archive["energy_times"], dtype=float).tolist(),
            energies=np.asarray(archive["energies"], dtype=float).tolist(),
            constraint_times=np.asarray(
                archive["constraint_times"], dtype=float
            ).tolist(),
            constraint_violations=np.asarray(
                archive["constraint_violations"], dtype=float
            ).tolist(),
            cumulative_norm_loss=float(metadata["cumulative_norm_loss"]),
            max_raw_norm_drift=float(metadata["max_raw_norm_drift"]),
        )


def _lane_output_path(output_root: Path, lane_id: str) -> Path:
    return output_root / "lanes" / f"{lane_id}.npz"


def _check_lane_output(path: Path, *, lane_id: str, digest: str) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata_json"].item()))
    if metadata["lane_id"] != lane_id or metadata["config_digest"] != digest:
        raise ValueError("lane output does not match lane/config digest")
    return metadata


def run_lane(
    config: dict[str, Any],
    workspace: Path,
    *,
    lane_id: str,
    digest: str,
    resume: bool,
    stop_after_checkpoints: int | None = None,
) -> dict[str, Any]:
    initial_state, profile_name = lane_id.split("_", 1)
    if initial_state not in INITIAL_STATES or profile_name not in REQUIRED_PROFILES:
        raise ValueError(f"unknown lane: {lane_id}")
    parameters = config["parameters"]
    profile = parameters["profiles"][profile_name]
    output_root = _resolve_under(workspace, config["output_root"])
    checkpoint_root = _resolve_under(workspace, config["checkpoint_root"])
    output_path = _lane_output_path(output_root, lane_id)
    checkpoint_path = checkpoint_root / digest[:16] / lane_id / "checkpoint.npz"
    if output_path.exists():
        if not resume:
            raise FileExistsError(f"lane output exists; use --resume: {output_path}")
        metadata = _check_lane_output(output_path, lane_id=lane_id, digest=digest)
        return {"lane_id": lane_id, "status": "complete", "resume_skip": True, **metadata}
    if checkpoint_path.exists() and resume:
        state = _load_checkpoint(checkpoint_path, lane_id=lane_id, digest=digest)
        resumed_from = state.times[-1]
    else:
        state = _new_lane_state(config, initial_state)
        resumed_from = None

    sample_step = float(parameters["sample_time_step"])
    final_time = float(parameters["panel_c_time_max"])
    sample_times = np.arange(0.0, final_time + 0.5 * sample_step, sample_step)
    if len(state.times) > len(sample_times) or not np.allclose(
        state.times, sample_times[: len(state.times)], atol=1e-10
    ):
        raise ValueError("checkpoint times are not a prefix of the configured grid")
    checkpoint_interval = float(parameters["checkpoint_time_interval"])
    diagnostic_interval = float(parameters["diagnostic_time_interval"])
    checkpoints_written = 0
    for target_time in sample_times[len(state.times) :]:
        current = evolve_to(
            state.psi,
            state.times[-1],
            float(target_time),
            time_step=float(profile["time_step"]),
            omega=float(parameters["omega"]),
            max_bond=int(profile["max_bond"]),
            cutoff=float(profile["cutoff"]),
        )
        raw_norm = float(np.real(state.psi.H @ state.psi))
        if not np.isfinite(raw_norm) or raw_norm <= 0.0:
            raise RuntimeError(f"non-positive/non-finite MPS norm in {lane_id}")
        drift = abs(raw_norm - 1.0)
        state.max_raw_norm_drift = max(state.max_raw_norm_drift, drift)
        state.cumulative_norm_loss += drift
        state.psi.normalize()
        six, one = observe_entropies(
            state.psi, int(parameters["six_site_subsystem"]) // 2
        )
        state.times.append(current)
        state.six_entropy.append(six)
        state.one_entropy.append(one)
        state.raw_norms.append(raw_norm)
        state.max_bonds.append(int(state.psi.max_bond()))
        diagnostic_ratio = current / diagnostic_interval
        if np.isclose(diagnostic_ratio, round(diagnostic_ratio), atol=1e-9) or np.isclose(
            current, final_time
        ):
            state.energy_times.append(current)
            state.energies.append(
                energy_expectation(state.psi, float(parameters["omega"]))
            )
            state.constraint_times.append(current)
            state.constraint_violations.append(constraint_violation(state.psi))
        checkpoint_ratio = current / checkpoint_interval
        checkpoint_due = np.isclose(
            checkpoint_ratio, round(checkpoint_ratio), atol=1e-9
        ) or np.isclose(current, final_time)
        if checkpoint_due:
            _atomic_savez(
                checkpoint_path,
                **_checkpoint_payload(
                    state, lane_id=lane_id, digest=digest, config=config
                ),
            )
            checkpoints_written += 1
            if (
                stop_after_checkpoints is not None
                and checkpoints_written >= stop_after_checkpoints
                and current < final_time
            ):
                return {
                    "lane_id": lane_id,
                    "status": "checkpointed_partial",
                    "current_time": current,
                    "resumed_from": resumed_from,
                }

    metadata = {
        "schema_version": 1,
        "lane_id": lane_id,
        "config_digest": digest,
        "run_id": config["run_id"],
        "initial_state": initial_state,
        "profile": profile_name,
        "physical_length": int(parameters["physical_length"]),
        "boundary_condition": parameters["boundary_condition"],
        "time_step": float(profile["time_step"]),
        "max_bond_limit": int(profile["max_bond"]),
        "cutoff": float(profile["cutoff"]),
        "final_time": state.times[-1],
        "max_bond_reached": max(state.max_bonds),
        "max_raw_norm_drift": state.max_raw_norm_drift,
        "cumulative_norm_loss": state.cumulative_norm_loss,
        "max_abs_energy_drift": max(
            abs(value - state.energies[0]) for value in state.energies
        ),
        "max_abs_constraint_violation": max(
            abs(value) for value in state.constraint_violations
        ),
        "resumed_from": resumed_from,
    }
    _atomic_savez(
        output_path,
        metadata_json=np.asarray(_canonical_json(metadata)),
        times=np.asarray(state.times, dtype=float),
        six_entropy=np.asarray(state.six_entropy, dtype=float),
        one_entropy=np.asarray(state.one_entropy, dtype=float),
        raw_norms=np.asarray(state.raw_norms, dtype=float),
        max_bonds=np.asarray(state.max_bonds, dtype=np.int64),
        energy_times=np.asarray(state.energy_times, dtype=float),
        energies=np.asarray(state.energies, dtype=float),
        constraint_times=np.asarray(state.constraint_times, dtype=float),
        constraint_violations=np.asarray(state.constraint_violations, dtype=float),
    )
    return {"lane_id": lane_id, "status": "complete", "resume_skip": False, **metadata}


def _load_lane(path: Path, *, lane_id: str, digest: str) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata_json"].item()))
        if metadata["lane_id"] != lane_id or metadata["config_digest"] != digest:
            raise ValueError("lane output does not match lane/config digest")
        return {
            "metadata": metadata,
            "times": np.asarray(archive["times"], dtype=float),
            "six_entropy": np.asarray(archive["six_entropy"], dtype=float),
            "one_entropy": np.asarray(archive["one_entropy"], dtype=float),
            "raw_norms": np.asarray(archive["raw_norms"], dtype=float),
            "max_bonds": np.asarray(archive["max_bonds"], dtype=int),
            "energy_times": np.asarray(archive["energy_times"], dtype=float),
            "energies": np.asarray(archive["energies"], dtype=float),
            "constraint_times": np.asarray(
                archive["constraint_times"], dtype=float
            ),
            "constraint_violations": np.asarray(
                archive["constraint_violations"], dtype=float
            ),
        }


def _criterion(status: bool | None, value: object, threshold: object) -> dict[str, object]:
    if status is None:
        status_text = "not_applicable"
    else:
        status_text = "passed" if status else "failed"
    return {"status": status_text, "value": value, "threshold": threshold}


def _failure_attribution(criteria: dict[str, dict[str, object]]) -> dict[str, object]:
    failed = [name for name, record in criteria.items() if record["status"] == "failed"]
    if not failed:
        assignment = "none_all_acceptance_criteria_passed"
        assignment_status = "not_needed"
    elif any(
        name
        in {
            "time_coverage",
            "entropy_bounds",
            "product_state_entropy",
            "norm_conservation",
            "energy_conservation",
            "constraint_preservation",
        }
        for name in failed
    ):
        assignment = ATTRIBUTION_ORDER[0]
        assignment_status = "assigned_for_repair_before_scientific_comparison"
    elif any(name in {"time_step_refinement", "bond_refinement"} for name in failed):
        assignment = "inconclusive"
        assignment_status = "assigned_requires_converged_rerun"
    else:
        assignment = "parameter_ambiguity"
        assignment_status = (
            "assigned_pending_resolution_of_omitted_numerical_controls"
        )
    return {
        "protocol": "paper_claim_falsification_v2",
        "stable_difference_outcomes": list(ATTRIBUTION_ORDER),
        "failed_criteria": failed,
        "current_assignment": assignment,
        "assignment_status": assignment_status,
        "paper_or_source_is_never_blamed_automatically": True,
        "paper_error_candidate_rule": {
            "required_gates": [
                "paper_exact",
                "converged",
                "independent_cross_checks_at_least_two",
                "source_pinpoint",
                "fresh_independent_review",
            ],
            "rule": "all_required_gates_must_pass",
            "eligible": False,
            "blockers": [
                "paper_exact",
                "fresh_independent_review",
            ],
        },
        "known_missing_method_input": (
            "The paper specifies L=30 and plotted time ranges but does not "
            "report a tDMRG/TEBD time step, bond dimension, or truncation cutoff; "
            "this campaign therefore uses explicit refinement lanes."
        ),
    }


def aggregate_campaign(
    config: dict[str, Any], workspace: Path, *, digest: str
) -> dict[str, Any]:
    output_root = _resolve_under(workspace, config["output_root"])
    lanes = {
        lane_id: _load_lane(
            _lane_output_path(output_root, lane_id), lane_id=lane_id, digest=digest
        )
        for lane_id in work_units(config)
    }
    reference_times = lanes["zero_primary"]["times"]
    if any(not np.array_equal(lane["times"], reference_times) for lane in lanes.values()):
        raise ValueError("lane time grids differ")
    primary = {state: lanes[f"{state}_primary"] for state in INITIAL_STATES}
    dt_refined = {state: lanes[f"{state}_dt_refined"] for state in INITIAL_STATES}
    bond_refined = {state: lanes[f"{state}_bond_refined"] for state in INITIAL_STATES}
    dt_difference = max(
        float(np.max(np.abs(primary[state][observable] - dt_refined[state][observable])))
        for state in INITIAL_STATES
        for observable in ("six_entropy", "one_entropy")
    )
    bond_difference = max(
        float(np.max(np.abs(primary[state][observable] - bond_refined[state][observable])))
        for state in INITIAL_STATES
        for observable in ("six_entropy", "one_entropy")
    )
    parameters = config["parameters"]
    acceptance = config["acceptance"]
    panel_b_mask = reference_times <= float(parameters["panel_b_time_max"]) + 1e-12
    six_zero = primary["zero"]["six_entropy"][panel_b_mask]
    six_z2 = primary["z2"]["six_entropy"][panel_b_mask]
    one_zero = primary["zero"]["one_entropy"]
    one_z2 = primary["z2"]["one_entropy"]
    late_six_start = max(1, int(0.75 * len(six_zero)))
    late_one_start = max(1, int(0.5 * len(one_zero)))
    six_late_gap = float(np.mean(six_zero[late_six_start:]) - np.mean(six_z2[late_six_start:]))
    one_late_std_gap = float(
        np.std(one_z2[late_one_start:]) - np.std(one_zero[late_one_start:])
    )
    all_six_entropy = np.concatenate([lane["six_entropy"] for lane in lanes.values()])
    all_one_entropy = np.concatenate([lane["one_entropy"] for lane in lanes.values()])
    max_norm_drift = max(
        float(lane["metadata"]["max_raw_norm_drift"]) for lane in lanes.values()
    )
    max_energy_drift = max(
        float(lane["metadata"]["max_abs_energy_drift"])
        for lane in lanes.values()
    )
    max_constraint_violation = max(
        float(lane["metadata"]["max_abs_constraint_violation"])
        for lane in lanes.values()
    )
    require_features = bool(acceptance["require_paper_features"])
    criteria = {
        "time_coverage": _criterion(
            bool(np.isclose(reference_times[-1], float(parameters["panel_c_time_max"]))),
            float(reference_times[-1]),
            float(parameters["panel_c_time_max"]),
        ),
        "entropy_bounds": _criterion(
            bool(
                np.min(all_six_entropy) >= -1e-8
                and np.max(all_six_entropy) <= 6.0 + 1e-8
                and np.min(all_one_entropy) >= -1e-8
                and np.max(all_one_entropy) <= 1.0 + 1e-8
            ),
            {
                "six_site_min": float(np.min(all_six_entropy)),
                "six_site_max": float(np.max(all_six_entropy)),
                "one_site_min": float(np.min(all_one_entropy)),
                "one_site_max": float(np.max(all_one_entropy)),
            },
            "0 <= S_1 <= 1 and 0 <= S_6 <= 6",
        ),
        "product_state_entropy": _criterion(
            bool(
                max(
                    primary[state]["six_entropy"][0]
                    for state in INITIAL_STATES
                )
                <= float(acceptance["product_entropy_max"])
                and max(
                    primary[state]["one_entropy"][0]
                    for state in INITIAL_STATES
                )
                <= float(acceptance["product_entropy_max"])
            ),
            {
                state: {
                    "six": float(primary[state]["six_entropy"][0]),
                    "one": float(primary[state]["one_entropy"][0]),
                }
                for state in INITIAL_STATES
            },
            float(acceptance["product_entropy_max"]),
        ),
        "norm_conservation": _criterion(
            max_norm_drift <= float(acceptance["norm_drift_max"]),
            max_norm_drift,
            float(acceptance["norm_drift_max"]),
        ),
        "energy_conservation": _criterion(
            max_energy_drift <= float(acceptance["energy_drift_max"]),
            max_energy_drift,
            float(acceptance["energy_drift_max"]),
        ),
        "constraint_preservation": _criterion(
            max_constraint_violation
            <= float(acceptance["constraint_violation_max"]),
            max_constraint_violation,
            float(acceptance["constraint_violation_max"]),
        ),
        "time_step_refinement": _criterion(
            dt_difference <= float(acceptance["dt_refinement_max_abs"]),
            dt_difference,
            float(acceptance["dt_refinement_max_abs"]),
        ),
        "bond_refinement": _criterion(
            bond_difference <= float(acceptance["bond_refinement_max_abs"]),
            bond_difference,
            float(acceptance["bond_refinement_max_abs"]),
        ),
        "six_site_slow_scar_growth": _criterion(
            six_late_gap >= float(acceptance["six_site_late_gap_min"])
            if require_features
            else None,
            six_late_gap,
            float(acceptance["six_site_late_gap_min"]),
        ),
        "one_site_scar_oscillations": _criterion(
            one_late_std_gap >= float(acceptance["one_site_std_gap_min"])
            if require_features
            else None,
            one_late_std_gap,
            float(acceptance["one_site_std_gap_min"]),
        ),
    }
    passed = all(record["status"] != "failed" for record in criteria.values())
    aggregate_path = output_root / "data" / "T_FIG2BC_tdmrg.npz"
    _atomic_savez(
        aggregate_path,
        config_digest=np.asarray(digest),
        times_panel_b=reference_times[panel_b_mask],
        times_panel_c=reference_times,
        six_zero=six_zero,
        six_z2=six_z2,
        one_zero=one_zero,
        one_z2=one_z2,
        dt_refinement_max_abs=np.asarray(dt_difference),
        bond_refinement_max_abs=np.asarray(bond_difference),
    )
    checks = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "config_digest": digest,
        "status": "passed" if passed else "failed",
        "scope": config["scope"],
        "criteria": criteria,
        "failure_attribution": _failure_attribution(criteria),
        "paper_parameter_mapping": {
            "physical_length": 30,
            "boundary_condition": "periodic",
            "six_site_time_range": [0.0, 100.0],
            "one_site_time_range": [0.0, 120.0],
            "source": "main Figure 2 caption and main Eq. (1)",
        },
        "author_inputs": {
            "author_code_used": False,
            "author_arrays_used": False,
            "digitized_curves_used": False,
            "source_or_pdf_pixels_used_as_numeric_input": False,
        },
    }
    checks_path = output_root / "checks" / "fig2_tdmrg_checks.json"
    _atomic_json(checks_path, checks)
    manifest_files = [
        *[_lane_output_path(output_root, lane_id) for lane_id in work_units(config)],
        aggregate_path,
        checks_path,
    ]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if passed else "failed",
        "generated_data_provenance": "independent_numerics",
        "author_code_or_arrays_used": False,
        "source_pixels_used_as_numeric_input": False,
        "files": [
            {
                "path": str(path.relative_to(workspace)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for path in manifest_files
        ],
    }
    _atomic_json(output_root / "checks" / "generated_data_manifest.json", manifest)
    return {
        "status": "passed" if passed else "failed",
        "aggregate": str(aggregate_path.relative_to(workspace)),
        "checks": str(checks_path.relative_to(workspace)),
        "dt_refinement_max_abs": dt_difference,
        "bond_refinement_max_abs": bond_difference,
    }


def run_campaign(
    config: dict[str, Any],
    workspace: Path,
    *,
    digest: str,
    resume: bool,
    lanes: Iterable[str] | None = None,
    shard_index: int | None = None,
    shard_count: int | None = None,
    stop_after_checkpoints: int | None = None,
) -> dict[str, Any]:
    units = work_units(config)
    selected = set(units if lanes is None else lanes)
    unknown = selected.difference(units)
    if unknown:
        raise ValueError(f"unknown lanes: {sorted(unknown)}")
    if (shard_index is None) != (shard_count is None):
        raise ValueError("shard-index and shard-count must be supplied together")
    if shard_count is not None:
        if shard_count <= 0 or shard_index is None or not 0 <= shard_index < shard_count:
            raise ValueError("invalid shard index/count")
        selected = {
            unit for index, unit in enumerate(units) if index % shard_count == shard_index
        }.intersection(selected)
    lane_results = []
    for lane_id in units:
        if lane_id not in selected:
            continue
        lane_results.append(
            run_lane(
                config,
                workspace,
                lane_id=lane_id,
                digest=digest,
                resume=resume,
                stop_after_checkpoints=stop_after_checkpoints,
            )
        )
    output_root = _resolve_under(workspace, config["output_root"])
    completed = [
        lane_id
        for lane_id in units
        if _lane_output_path(output_root, lane_id).exists()
        and _check_lane_output(
            _lane_output_path(output_root, lane_id), lane_id=lane_id, digest=digest
        )
    ]
    missing = [lane_id for lane_id in units if lane_id not in completed]
    state = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "config_digest": digest,
        "work_units": list(units),
        "selected_units": [unit for unit in units if unit in selected],
        "completed_units": completed,
        "missing_units": missing,
    }
    _atomic_json(output_root / "checks" / "campaign_state.json", state)
    if missing:
        return {"status": "partial", "lanes": lane_results, **state}
    aggregate = aggregate_campaign(config, workspace, digest=digest)
    return {"status": aggregate["status"], "lanes": lane_results, **state, **aggregate}
