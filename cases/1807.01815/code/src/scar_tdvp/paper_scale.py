"""Paper-scale campaigns for the main numerical figures of arXiv:1807.01815.

This module independently evaluates the printed Hamiltonian and TDVP equations.
It never reads paper figures, digitized curves, author arrays, or author code.

The exact-quench path is deliberately streaming: only the current Krylov state
and scalar observables are retained.  This avoids the multi-terabyte trajectory
array that a batched ``expm_multiply`` call would create at the printed sizes.
Each physical lane has a digest-bound checkpoint and each level-statistics size
is an independent resumable work unit.
"""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.sparse.linalg import expm_multiply

from .constrained import ReducedConstrainedChain, thermal_magnetization
from .tdvp import VariationalManifold, integrate_orbit_segment, tdvp_flow


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def config_digest(config: dict[str, Any]) -> str:
    """Return the scientific-configuration digest used by every checkpoint."""

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
    """Apply the explicit smoke override without mutating the paper contract."""

    result = deepcopy(config)
    if smoke:
        override = result.pop("smoke_override")
        result = _deep_merge(result, override)
        result["run_id"] = f"{config['run_id']}-smoke"
        result["scope"] = "algorithm_smoke_not_paper_evidence"
    else:
        result.pop("smoke_override", None)
    return result


def _positive(value: object, name: str) -> float:
    number = float(value)
    if not np.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return number


def _validate_unit_ids(rows: Iterable[dict[str, Any]], label: str) -> set[str]:
    result: set[str] = set()
    for row in rows:
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id:
            raise ValueError(f"{label} unit_id must be a non-empty string")
        if unit_id in result:
            raise ValueError(f"duplicate work unit: {unit_id}")
        result.add(unit_id)
    return result


def validate_config(
    config: dict[str, Any], *, require_paper_scale: bool = True
) -> None:
    """Fail closed on incomplete or silently changed production parameters."""

    if config.get("paper_id") != "1807.01815":
        raise ValueError("paper_id must be 1807.01815")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")

    tdvp_rows = parameters.get("tdvp")
    quench_rows = parameters.get("quenches")
    level_block = parameters.get("level_statistics")
    if not isinstance(tdvp_rows, list) or not tdvp_rows:
        raise ValueError("parameters.tdvp must be non-empty")
    if not isinstance(quench_rows, list) or not quench_rows:
        raise ValueError("parameters.quenches must be non-empty")
    if not isinstance(level_block, dict) or not isinstance(
        level_block.get("units"), list
    ):
        raise ValueError("parameters.level_statistics.units must be an array")
    level_rows = level_block["units"]
    if not level_rows:
        raise ValueError("parameters.level_statistics.units must be non-empty")

    seen = _validate_unit_ids(tdvp_rows, "tdvp")
    for unit_id in _validate_unit_ids(quench_rows, "quench"):
        if unit_id in seen:
            raise ValueError(f"duplicate work unit: {unit_id}")
        seen.add(unit_id)
    for unit_id in _validate_unit_ids(level_rows, "level_statistics"):
        if unit_id in seen:
            raise ValueError(f"duplicate work unit: {unit_id}")
        seen.add(unit_id)

    for row in tdvp_rows:
        spin = _positive(row["spin"], "tdvp spin")
        if spin not in {0.5, 1.0, 2.0}:
            raise ValueError("TDVP spin must be 0.5, 1, or 2")
        rings = [int(value) for value in row.get("ring_lengths", [])]
        if (
            len(rings) < 2
            or rings != sorted(set(rings))
            or any(value % 2 for value in rings)
        ):
            raise ValueError(
                "TDVP ring_lengths must be two or more increasing even sizes"
            )
        if int(row["grid_points"]) < 5 or int(row["orbit_samples"]) < 24:
            raise ValueError(
                "TDVP grids are too small to define the requested observable"
            )

    quench_keys: set[tuple[float, int, str]] = set()
    for row in quench_rows:
        spin = _positive(row["spin"], "quench spin")
        length = int(row["length"])
        initial_state = str(row["initial_state"])
        if spin not in {0.5, 1.0, 2.0} or length < 6 or length % 2:
            raise ValueError("quench spin/length is outside the supported even ring")
        if initial_state not in {"zero", "z2"}:
            raise ValueError("quench initial_state must be zero or z2")
        time_max = _positive(row["time_max"], "quench time_max")
        time_step = _positive(row["time_step"], "quench time_step")
        if not np.isclose(time_max / time_step, round(time_max / time_step)):
            raise ValueError("quench time_max must be an integer multiple of time_step")
        key = (spin, length, initial_state)
        if key in quench_keys:
            raise ValueError(f"duplicate quench lane: {key}")
        quench_keys.add(key)

    for row in level_rows:
        spin = _positive(row["spin"], "level-statistics spin")
        length = int(row["length"])
        if spin not in {0.5, 1.0, 2.0} or length < 4 or length % 2:
            raise ValueError("level-statistics spin/length is invalid")
        if row.get("symmetry") != "dihedral_k0_inversion_even":
            raise ValueError("Fig. 2(a) requires the named k=0 inversion-even sector")

    if int(config.get("checkpoint_every_samples", 0)) < 1:
        raise ValueError("checkpoint_every_samples must be positive")
    if int(config.get("tdvp_checkpoint_rows", 0)) < 1:
        raise ValueError("tdvp_checkpoint_rows must be positive")
    for key in ("output_root", "checkpoint_root"):
        value = Path(str(config.get(key, "")))
        if value.is_absolute() or ".." in value.parts or not value.parts:
            raise ValueError(f"{key} must be workspace-relative")

    if require_paper_scale:
        if config.get("scope") != "paper_scale_code_ready_not_executed":
            raise ValueError(
                "production config must remain paper_scale_code_ready_not_executed"
            )
        expected_quenches = {
            (0.5, 30, "zero"),
            (0.5, 30, "z2"),
            (0.5, 32, "zero"),
            (0.5, 32, "z2"),
            (1.0, 20, "zero"),
            (1.0, 20, "z2"),
            (1.0, 22, "zero"),
            (1.0, 22, "z2"),
            (2.0, 14, "zero"),
            (2.0, 14, "z2"),
            (2.0, 16, "zero"),
            (2.0, 16, "z2"),
        }
        if quench_keys != expected_quenches:
            raise ValueError(
                "production quench lanes must match every frozen candidate size"
            )
        if any(float(row["time_max"]) != 300.0 for row in quench_rows):
            raise ValueError("all production quench lanes must cover t*Omega=300")
        if level_block.get("paper_size_sequence_status") != "not_reported":
            raise ValueError("Fig. 2(a) size ambiguity must remain explicit")


def load_config(path: Path, *, smoke: bool = False) -> tuple[dict[str, Any], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config must be a JSON object")
    config = effective_config(payload, smoke=smoke)
    validate_config(config, require_paper_scale=not smoke)
    return config, config_digest(config)


def work_units(config: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Return deterministic, scheduler-safe work units."""

    parameters = config["parameters"]
    rows: list[dict[str, Any]] = []
    for kind, values in (
        ("tdvp", parameters["tdvp"]),
        ("quench", parameters["quenches"]),
        ("level_statistics", parameters["level_statistics"]["units"]),
    ):
        for value in values:
            rows.append({"kind": kind, **deepcopy(value)})
    return tuple(rows)


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _atomic_npz(path: Path, **arrays: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)


def _scalar(archive: Any, name: str) -> str:
    return str(np.asarray(archive[name]).item())


def _lane_matches(path: Path, *, digest: str, unit_id: str) -> bool:
    if not path.is_file():
        return False
    try:
        with np.load(path, allow_pickle=False) as archive:
            return (
                _scalar(archive, "config_digest") == digest
                and _scalar(archive, "unit_id") == unit_id
                and bool(np.asarray(archive["complete"]).item())
            )
    except (KeyError, OSError, ValueError):
        return False


def _energy(state: np.ndarray, model: ReducedConstrainedChain) -> float:
    return float(np.real(np.vdot(state, model.hamiltonian @ state)))


def _quench_checkpoint(
    path: Path,
    *,
    digest: str,
    unit_id: str,
    sample_index: int,
    state: np.ndarray,
    times: np.ndarray,
    magnetization: np.ndarray,
    norms: np.ndarray,
    energies: np.ndarray,
) -> None:
    _atomic_npz(
        path,
        config_digest=np.asarray(digest),
        unit_id=np.asarray(unit_id),
        sample_index=np.asarray(sample_index, dtype=np.int64),
        state=state,
        times=times[: sample_index + 1],
        magnetization=magnetization[: sample_index + 1],
        norms=norms[: sample_index + 1],
        energies=energies[: sample_index + 1],
    )


def _run_quench(
    row: dict[str, Any],
    *,
    workspace: Path,
    config: dict[str, Any],
    digest: str,
    resume: bool,
    stop_after_checkpoints: int | None,
) -> bool:
    unit_id = row["unit_id"]
    lane_path = workspace / config["output_root"] / "lanes" / f"{unit_id}.npz"
    if resume and _lane_matches(lane_path, digest=digest, unit_id=unit_id):
        return True

    spin = float(row["spin"])
    length = int(row["length"])
    initial_state = str(row["initial_state"])
    time_step = float(row["time_step"])
    time_max = float(row["time_max"])
    times = np.linspace(0.0, time_max, int(round(time_max / time_step)) + 1)
    model = ReducedConstrainedChain(length, spin)
    observable = model.sublattice_magnetization()
    checkpoint_path = workspace / config["checkpoint_root"] / digest / f"{unit_id}.npz"

    magnetization = np.empty(len(times), dtype=float)
    norms = np.empty(len(times), dtype=float)
    energies = np.empty(len(times), dtype=float)
    sample_index = 0
    state = model.initial_vector(initial_state)

    if resume and checkpoint_path.is_file():
        try:
            with np.load(checkpoint_path, allow_pickle=False) as archive:
                if (
                    _scalar(archive, "config_digest") == digest
                    and _scalar(archive, "unit_id") == unit_id
                ):
                    sample_index = int(np.asarray(archive["sample_index"]).item())
                    state = np.asarray(archive["state"], dtype=complex)
                    if state.shape != (model.dimension,):
                        raise ValueError("checkpoint state dimension mismatch")
                    saved_times = np.asarray(archive["times"], dtype=float)
                    if not np.array_equal(saved_times, times[: sample_index + 1]):
                        raise ValueError("checkpoint time grid mismatch")
                    magnetization[: sample_index + 1] = archive["magnetization"]
                    norms[: sample_index + 1] = archive["norms"]
                    energies[: sample_index + 1] = archive["energies"]
        except (KeyError, OSError, ValueError):
            sample_index = 0
            state = model.initial_vector(initial_state)

    if sample_index == 0:
        probabilities = np.abs(state) ** 2
        magnetization[0] = float(probabilities @ observable)
        norms[0] = float(np.vdot(state, state).real)
        energies[0] = _energy(state, model)

    checkpoint_count = 0
    checkpoint_every = int(config["checkpoint_every_samples"])
    for index in range(sample_index + 1, len(times)):
        delta = float(times[index] - times[index - 1])
        state = np.asarray(
            expm_multiply(-1j * model.hamiltonian * delta, state, traceA=0.0),
            dtype=complex,
        )
        probabilities = np.abs(state) ** 2
        magnetization[index] = float(probabilities @ observable)
        norms[index] = float(np.vdot(state, state).real)
        energies[index] = _energy(state, model)
        if index % checkpoint_every == 0 or index == len(times) - 1:
            _quench_checkpoint(
                checkpoint_path,
                digest=digest,
                unit_id=unit_id,
                sample_index=index,
                state=state,
                times=times,
                magnetization=magnetization,
                norms=norms,
                energies=energies,
            )
            checkpoint_count += 1
            if (
                stop_after_checkpoints is not None
                and checkpoint_count >= stop_after_checkpoints
                and index < len(times) - 1
            ):
                return False

    _atomic_npz(
        lane_path,
        config_digest=np.asarray(digest),
        unit_id=np.asarray(unit_id),
        kind=np.asarray("quench"),
        complete=np.asarray(True),
        spin=np.asarray(spin),
        length=np.asarray(length, dtype=np.int64),
        initial_state=np.asarray(initial_state),
        dimension=np.asarray(model.dimension, dtype=np.int64),
        times=times,
        magnetization=magnetization,
        norms=norms,
        energies=energies,
    )
    return True


def _tdvp_checkpoint(
    path: Path,
    *,
    digest: str,
    unit_id: str,
    leakages: np.ndarray,
    product_residuals: np.ndarray,
    rings_complete: int,
    gamma: np.ndarray,
    heatmap_rows_complete: int,
) -> None:
    _atomic_npz(
        path,
        config_digest=np.asarray(digest),
        unit_id=np.asarray(unit_id),
        leakages=leakages,
        product_residuals=product_residuals,
        rings_complete=np.asarray(rings_complete, dtype=np.int64),
        gamma=gamma,
        heatmap_rows_complete=np.asarray(heatmap_rows_complete, dtype=np.int64),
    )


def _run_tdvp(
    row: dict[str, Any],
    *,
    workspace: Path,
    config: dict[str, Any],
    digest: str,
    resume: bool,
) -> bool:
    unit_id = row["unit_id"]
    lane_path = workspace / config["output_root"] / "lanes" / f"{unit_id}.npz"
    if resume and _lane_matches(lane_path, digest=digest, unit_id=unit_id):
        return True

    spin = float(row["spin"])
    rings = np.asarray(row["ring_lengths"], dtype=np.int64)
    grid = np.linspace(
        -np.pi + float(row["grid_endpoint_cutoff"]),
        np.pi - float(row["grid_endpoint_cutoff"]),
        int(row["grid_points"]),
    )
    orbit_times, orbit, period = integrate_orbit_segment(
        spin, samples=int(row["orbit_samples"])
    )
    leakages = np.full(len(rings), np.nan, dtype=float)
    product_residuals = np.full(len(rings), np.nan, dtype=float)
    gamma = np.full((len(grid), len(grid)), np.nan, dtype=float)
    rings_complete = 0
    heatmap_rows_complete = 0
    checkpoint_path = workspace / config["checkpoint_root"] / digest / f"{unit_id}.npz"

    if resume and checkpoint_path.is_file():
        try:
            with np.load(checkpoint_path, allow_pickle=False) as archive:
                if (
                    _scalar(archive, "config_digest") == digest
                    and _scalar(archive, "unit_id") == unit_id
                ):
                    leakages = np.asarray(archive["leakages"], dtype=float)
                    product_residuals = np.asarray(
                        archive["product_residuals"], dtype=float
                    )
                    gamma = np.asarray(archive["gamma"], dtype=float)
                    rings_complete = int(np.asarray(archive["rings_complete"]).item())
                    heatmap_rows_complete = int(
                        np.asarray(archive["heatmap_rows_complete"]).item()
                    )
                    if leakages.shape != rings.shape or gamma.shape != (
                        len(grid),
                        len(grid),
                    ):
                        raise ValueError("TDVP checkpoint shape mismatch")
        except (KeyError, OSError, ValueError):
            leakages.fill(np.nan)
            product_residuals.fill(np.nan)
            gamma.fill(np.nan)
            rings_complete = 0
            heatmap_rows_complete = 0

    for index in range(rings_complete, len(rings)):
        manifold = VariationalManifold(int(rings[index]), spin)
        orbit_gamma = np.asarray([manifold.residual(even, odd) for even, odd in orbit])
        leakages[index] = float(2.0 * np.trapezoid(orbit_gamma, orbit_times))
        product_residuals[index] = manifold.residual(-np.pi + 1e-5, 0.0)
        rings_complete = index + 1
        _tdvp_checkpoint(
            checkpoint_path,
            digest=digest,
            unit_id=unit_id,
            leakages=leakages,
            product_residuals=product_residuals,
            rings_complete=rings_complete,
            gamma=gamma,
            heatmap_rows_complete=heatmap_rows_complete,
        )

    finest = VariationalManifold(int(rings[-1]), spin)
    row_interval = int(config["tdvp_checkpoint_rows"])
    for row_index in range(heatmap_rows_complete, len(grid)):
        theta_odd = float(grid[row_index])
        for column, theta_even in enumerate(grid):
            try:
                gamma[row_index, column] = finest.residual(float(theta_even), theta_odd)
            except (FloatingPointError, ValueError):
                gamma[row_index, column] = np.nan
        heatmap_rows_complete = row_index + 1
        if heatmap_rows_complete % row_interval == 0 or row_index == len(grid) - 1:
            _tdvp_checkpoint(
                checkpoint_path,
                digest=digest,
                unit_id=unit_id,
                leakages=leakages,
                product_residuals=product_residuals,
                rings_complete=rings_complete,
                gamma=gamma,
                heatmap_rows_complete=heatmap_rows_complete,
            )

    even, odd = np.meshgrid(grid, grid)
    orbit_gamma = np.asarray([finest.residual(x, y) for x, y in orbit])
    _atomic_npz(
        lane_path,
        config_digest=np.asarray(digest),
        unit_id=np.asarray(unit_id),
        kind=np.asarray("tdvp"),
        complete=np.asarray(True),
        spin=np.asarray(spin),
        ring_lengths=rings,
        grid=grid,
        gamma=gamma,
        flow_even=tdvp_flow(even, odd, spin),
        flow_odd=tdvp_flow(odd, even, spin),
        orbit_times=orbit_times,
        orbit=orbit,
        orbit_gamma=orbit_gamma,
        period=np.asarray(period),
        leakages=leakages,
        product_residuals=product_residuals,
    )
    return True


def _gap_ratio(eigenvalues: np.ndarray) -> float:
    gaps = np.diff(np.asarray(eigenvalues, dtype=float))
    scale = max(float(np.max(np.abs(eigenvalues))), 1.0)
    gaps = gaps[gaps > 1e-10 * scale]
    if len(gaps) < 3:
        return float("nan")
    ratios = np.minimum(gaps[1:], gaps[:-1]) / np.maximum(gaps[1:], gaps[:-1])
    return float(np.mean(ratios))


def _run_level_statistics(
    row: dict[str, Any],
    *,
    workspace: Path,
    config: dict[str, Any],
    digest: str,
    resume: bool,
) -> bool:
    unit_id = row["unit_id"]
    lane_path = workspace / config["output_root"] / "lanes" / f"{unit_id}.npz"
    if resume and _lane_matches(lane_path, digest=digest, unit_id=unit_id):
        return True

    spin = float(row["spin"])
    length = int(row["length"])
    model = ReducedConstrainedChain(length, spin, symmetry="dihedral")
    matrix = model.hamiltonian.toarray()
    hermiticity_max_abs = float(np.max(np.abs(matrix - matrix.T)))
    eigenvalues = np.linalg.eigvalsh(matrix)
    _atomic_npz(
        lane_path,
        config_digest=np.asarray(digest),
        unit_id=np.asarray(unit_id),
        kind=np.asarray("level_statistics"),
        complete=np.asarray(True),
        spin=np.asarray(spin),
        length=np.asarray(length, dtype=np.int64),
        dimension=np.asarray(model.dimension, dtype=np.int64),
        estimated_dense_bytes=np.asarray(matrix.nbytes, dtype=np.int64),
        hermiticity_max_abs=np.asarray(hermiticity_max_abs),
        gap_ratio=np.asarray(_gap_ratio(eigenvalues)),
        eigenvalues=eigenvalues,
    )
    return True


def backend_parity() -> dict[str, Any]:
    """Compare the streaming Krylov path with the existing batched oracle."""

    model = ReducedConstrainedChain(6, 0.5)
    times = np.linspace(0.0, 0.3, 4)
    batched = model.magnetization_dynamics("z2", times)
    state = model.initial_vector("z2")
    observable = model.sublattice_magnetization()
    streamed = [float(np.abs(state) ** 2 @ observable)]
    for left, right in zip(times[:-1], times[1:]):
        state = np.asarray(
            expm_multiply(
                -1j * model.hamiltonian * float(right - left), state, traceA=0.0
            )
        )
        streamed.append(float(np.abs(state) ** 2 @ observable))
    maximum = float(np.max(np.abs(batched - np.asarray(streamed))))
    asymmetry = model.hamiltonian - model.hamiltonian.T
    hermiticity = float(np.max(np.abs(asymmetry.data))) if asymmetry.nnz else 0.0
    return {
        "schema_version": 1,
        "check": "paper_scale_backend_parity",
        "status": "passed" if maximum <= 2e-12 and hermiticity <= 1e-12 else "failed",
        "streaming_vs_batched_max_abs": maximum,
        "reduced_hamiltonian_hermiticity_max_abs": hermiticity,
        "oracle_length": 6,
        "oracle_spin": 0.5,
    }


def _load_lane(path: Path, *, digest: str, unit_id: str) -> dict[str, np.ndarray]:
    if not _lane_matches(path, digest=digest, unit_id=unit_id):
        raise ValueError(f"lane is missing or stale: {unit_id}")
    with np.load(path, allow_pickle=False) as archive:
        return {name: np.asarray(archive[name]) for name in archive.files}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_aggregate_npz(path: Path, payload: dict[str, object]) -> None:
    _atomic_npz(path, **payload)


def aggregate_campaign(
    config: dict[str, Any], workspace: Path, *, digest: str
) -> dict[str, Any]:
    """Aggregate only hash-valid complete lanes and evaluate acceptance."""

    output_root = workspace / config["output_root"]
    lanes = {
        row["unit_id"]: _load_lane(
            output_root / "lanes" / f"{row['unit_id']}.npz",
            digest=digest,
            unit_id=row["unit_id"],
        )
        for row in work_units(config)
    }
    data_root = output_root / "data"
    checks_root = output_root / "checks"

    tdvp_rows = config["parameters"]["tdvp"]
    tdvp_by_spin = {float(row["spin"]): lanes[row["unit_id"]] for row in tdvp_rows}
    if 0.5 in tdvp_by_spin:
        lane = tdvp_by_spin[0.5]
        _write_aggregate_npz(
            data_root / "T_FIG1A_tdvp.npz",
            {name: value for name, value in lane.items() if name not in {"complete"}},
        )
    higher_spins: dict[str, object] = {}
    for spin, label in ((1.0, "spin1"), (2.0, "spin2")):
        if spin not in tdvp_by_spin:
            continue
        for name, value in tdvp_by_spin[spin].items():
            if name not in {"complete", "config_digest", "unit_id", "kind"}:
                higher_spins[f"{name}_{label}"] = value
    if higher_spins:
        higher_spins["config_digest"] = np.asarray(digest)
        _write_aggregate_npz(data_root / "T_FIG4AC_tdvp.npz", higher_spins)

    quench_rows = config["parameters"]["quenches"]
    quench_lanes = [(row, lanes[row["unit_id"]]) for row in quench_rows]
    for spin, filename in (
        (0.5, "T_FIG1B_quench.npz"),
        (1.0, "T_FIG4B_quench.npz"),
        (2.0, "T_FIG4D_quench.npz"),
    ):
        rows = [(row, lane) for row, lane in quench_lanes if float(row["spin"]) == spin]
        if not rows:
            continue
        lengths = sorted({int(row["length"]) for row, _ in rows})
        times = rows[0][1]["times"]
        payload: dict[str, object] = {
            "config_digest": np.asarray(digest),
            "times": times,
            "lengths": np.asarray(lengths, dtype=np.int64),
            "thermal": np.asarray(thermal_magnetization(spin)),
        }
        for initial_state in ("zero", "z2"):
            payload[initial_state] = np.asarray(
                [
                    next(
                        lane["magnetization"]
                        for row, lane in rows
                        if int(row["length"]) == length
                        and row["initial_state"] == initial_state
                    )
                    for length in lengths
                ]
            )
        _write_aggregate_npz(data_root / filename, payload)

    level_rows = config["parameters"]["level_statistics"]["units"]
    level_table = np.asarray(
        [
            [
                float(row["spin"]),
                int(row["length"]),
                int(lanes[row["unit_id"]]["dimension"].item()),
                float(lanes[row["unit_id"]]["gap_ratio"].item()),
                float(lanes[row["unit_id"]]["hermiticity_max_abs"].item()),
            ]
            for row in level_rows
        ],
        dtype=float,
    )
    _write_aggregate_npz(
        data_root / "T_FIG2A_level_statistics.npz",
        {
            "config_digest": np.asarray(digest),
            "rows_spin_length_dimension_r_hermiticity": level_table,
            "paper_size_sequence_status": np.asarray(
                config["parameters"]["level_statistics"]["paper_size_sequence_status"]
            ),
        },
    )

    acceptance = config["acceptance"]
    criteria: dict[str, dict[str, Any]] = {}
    parity = backend_parity()
    criteria["backend_parity"] = {
        "status": parity["status"],
        "streaming_vs_batched_max_abs": parity["streaming_vs_batched_max_abs"],
    }

    tdvp_failures: list[str] = []
    for row in tdvp_rows:
        lane = lanes[row["unit_id"]]
        period_error = abs(
            float(lane["period"].item()) - float(row["paper_period"])
        ) / float(row["paper_period"])
        leakage_error = abs(float(lane["leakages"][-1]) - float(row["paper_leakage"]))
        convergence = abs(float(lane["leakages"][-1] - lane["leakages"][-2]))
        if (
            period_error > float(acceptance["tdvp_period_relative_max"])
            or leakage_error > float(acceptance["tdvp_leakage_absolute_max"])
            or convergence > float(acceptance["tdvp_ring_convergence_max"])
            or float(np.max(lane["product_residuals"]))
            > float(acceptance["tdvp_product_residual_max"])
        ):
            tdvp_failures.append(row["unit_id"])
    criteria["tdvp"] = {
        "status": "passed" if not tdvp_failures else "failed",
        "failed_units": tdvp_failures,
    }

    quench_failures: list[str] = []
    for row, lane in quench_lanes:
        norm_drift = float(np.max(np.abs(lane["norms"] - 1.0)))
        energy_drift = float(np.max(np.abs(lane["energies"] - lane["energies"][0])))
        if norm_drift > float(
            acceptance["quench_norm_drift_max"]
        ) or energy_drift > float(acceptance["quench_energy_drift_max"]):
            quench_failures.append(row["unit_id"])
    feature_failures: list[str] = []
    for spin_text, threshold in acceptance["z2_range_min_by_spin"].items():
        spin = float(spin_text)
        spin_rows = [
            (row, lane) for row, lane in quench_lanes if float(row["spin"]) == spin
        ]
        if not spin_rows:
            continue
        largest = max(int(row["length"]) for row, _ in spin_rows)
        zero = next(
            lane["magnetization"]
            for row, lane in spin_rows
            if int(row["length"]) == largest and row["initial_state"] == "zero"
        )
        z2 = next(
            lane["magnetization"]
            for row, lane in spin_rows
            if int(row["length"]) == largest and row["initial_state"] == "z2"
        )
        late_zero = float(np.mean(zero[len(zero) // 2 :]))
        if float(np.ptp(z2)) < float(threshold) or abs(
            late_zero - thermal_magnetization(spin)
        ) > float(acceptance["zero_thermal_absolute_max"]):
            feature_failures.append(f"spin_{spin}")
    criteria["quenches"] = {
        "status": (
            "passed" if not quench_failures and not feature_failures else "failed"
        ),
        "failed_units": quench_failures,
        "failed_features": feature_failures,
        "paper_exact_eligible": False,
        "paper_exact_blocker": "parameter_ambiguity_missing_fig1_fig4_quench_L_values",
    }

    level_failures: list[str] = []
    for row in level_rows:
        lane = lanes[row["unit_id"]]
        ratio = float(lane["gap_ratio"].item())
        if not 0.0 <= ratio <= 1.0 or float(lane["hermiticity_max_abs"].item()) > float(
            acceptance["level_hermiticity_max"]
        ):
            level_failures.append(row["unit_id"])
    if bool(acceptance["require_level_trend"]):
        for spin in sorted(set(level_table[:, 0])):
            rows = level_table[level_table[:, 0] == spin]
            rows = rows[np.argsort(rows[:, 2])]
            if abs(rows[-1, 3] - 0.53) > abs(rows[0, 3] - 0.53) + float(
                acceptance["level_trend_tolerance"]
            ):
                level_failures.append(f"spin_{spin}_trend")
    criteria["level_statistics"] = {
        "status": "passed" if not level_failures else "failed",
        "failed_units": level_failures,
        "paper_size_sequence_status": config["parameters"]["level_statistics"][
            "paper_size_sequence_status"
        ],
        "paper_exact_eligible": False,
        "paper_exact_blocker": "parameter_ambiguity_missing_plotted_L_sequence",
    }

    status = (
        "passed"
        if all(row["status"] == "passed" for row in criteria.values())
        else "failed"
    )
    acceptance_payload = {
        "schema_version": 1,
        "check": "paper_scale_acceptance",
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "scope": config["scope"],
        "status": status,
        "criteria": criteria,
        "paper_error_candidate": {
            "eligible": False,
            "reason": "Execution alone cannot satisfy protocol-v2 fresh review and source-exact gates.",
        },
    }
    acceptance_path = checks_root / "paper_scale_acceptance.json"
    parity_path = checks_root / "backend_parity.json"
    _atomic_json(acceptance_path, acceptance_payload)
    _atomic_json(parity_path, parity)

    generated_paths = sorted(
        [*data_root.glob("*.npz"), acceptance_path, parity_path],
        key=lambda path: path.as_posix(),
    )
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "config_digest": digest,
        "scope": config["scope"],
        "numerical_input_policy": {
            "author_code": False,
            "author_numeric_arrays": False,
            "digitized_curves": False,
            "source_figure_pixels": False,
            "pdf_pixels": False,
        },
        "outputs": [
            {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": _sha256(path),
            }
            for path in generated_paths
        ],
    }
    _atomic_json(checks_root / "generated_data_manifest.json", manifest)
    return acceptance_payload


def run_campaign(
    config: dict[str, Any],
    workspace: Path,
    *,
    digest: str,
    resume: bool,
    aggregate: bool = True,
    aggregate_only: bool = False,
    shard_index: int | None = None,
    shard_count: int | None = None,
    unit_ids: Iterable[str] | None = None,
    stop_after_checkpoints: int | None = None,
) -> dict[str, Any]:
    """Execute selected units, resume hash-valid work, and optionally aggregate."""

    validate_config(
        config,
        require_paper_scale=config.get("scope")
        == "paper_scale_code_ready_not_executed",
    )
    units = list(work_units(config))
    known_ids = {row["unit_id"] for row in units}
    requested_ids = set(unit_ids) if unit_ids is not None else known_ids
    unknown = sorted(requested_ids - known_ids)
    if unknown:
        raise ValueError(f"unknown work units: {unknown}")
    units = [row for row in units if row["unit_id"] in requested_ids]

    if (shard_index is None) != (shard_count is None):
        raise ValueError("shard_index and shard_count must be provided together")
    if shard_count is not None:
        if shard_count < 1 or shard_index is None or not 0 <= shard_index < shard_count:
            raise ValueError("invalid shard selection")
        all_units = list(work_units(config))
        selected_ids = {
            row["unit_id"]
            for index, row in enumerate(all_units)
            if index % shard_count == shard_index
        }
        units = [row for row in units if row["unit_id"] in selected_ids]

    parity = backend_parity()
    checks_root = workspace / config["output_root"] / "checks"
    _atomic_json(checks_root / "backend_parity.json", parity)
    if parity["status"] != "passed":
        raise RuntimeError("streaming backend parity failed")

    completed_now: list[str] = []
    partial_units: list[str] = []
    if not aggregate_only:
        remaining_stop = stop_after_checkpoints
        for row in units:
            kwargs = {
                "workspace": workspace,
                "config": config,
                "digest": digest,
                "resume": resume,
            }
            if row["kind"] == "quench":
                complete = _run_quench(
                    row,
                    **kwargs,
                    stop_after_checkpoints=remaining_stop,
                )
                if remaining_stop is not None:
                    remaining_stop = 0
            elif row["kind"] == "tdvp":
                complete = _run_tdvp(row, **kwargs)
            else:
                complete = _run_level_statistics(row, **kwargs)
            if complete:
                completed_now.append(row["unit_id"])
            else:
                partial_units.append(row["unit_id"])
                break

    lane_root = workspace / config["output_root"] / "lanes"
    missing = [
        row["unit_id"]
        for row in work_units(config)
        if not _lane_matches(
            lane_root / f"{row['unit_id']}.npz",
            digest=digest,
            unit_id=row["unit_id"],
        )
    ]
    acceptance_payload: dict[str, Any] | None = None
    if aggregate and not missing:
        acceptance_payload = aggregate_campaign(config, workspace, digest=digest)
    status = (
        acceptance_payload["status"] if acceptance_payload is not None else "partial"
    )
    state = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "scope": config["scope"],
        "config_digest": digest,
        "status": status,
        "completed_now": completed_now,
        "partial_units": partial_units,
        "missing_units": missing,
        "aggregate_written": acceptance_payload is not None,
    }
    _atomic_json(checks_root / "campaign_state.json", state)
    return state
