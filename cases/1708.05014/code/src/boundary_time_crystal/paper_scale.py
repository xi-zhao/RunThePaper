"""Resumable paper-scale campaign for every numerical target in 1708.05014.

The campaign is deliberately data-first.  Each physical parameter tuple is an
immutable job with a configuration hash, an atomic result, and a completion
marker.  Array generation never reads the paper, source figures, digitized
curves, author code, or author arrays.  Rendering and source comparison remain
downstream of the frozen outputs produced here.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import resource
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import scipy
from scipy.linalg import eigvals as scipy_eigvals
from scipy.optimize import linear_sum_assignment

from .model import (
    conserved_r_omega_z,
    expectation,
    leading_spectrum,
    liouvillian,
    magnetization_dynamics,
    qp_coordinates,
    semiclassical_trajectory,
    spin_operators,
    spin_x_coherent_density,
    steady_state,
    variance,
    vectorize_density,
)
from .paper_scale_kernels import (
    magnetization_dynamics_chunk,
    steady_state_shifted_jump,
)

TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 25))
FAMILY_TARGETS: dict[str, tuple[str, ...]] = {
    "parity": TARGET_IDS,
    "dynamics": ("T001", "T008", "T009"),
    "full_spectrum": ("T002", "T003", "T004", "T005"),
    "scaling": ("T006", "T007", "T010", "T013", "T014"),
    "imaginary_gap": ("T015",),
    "steady_state": ("T011", "T012"),
    "phase_portrait": (
        "T016",
        "T017",
        "T018",
        "T019",
        "T021",
        "T022",
        "T023",
        "T024",
    ),
    "branch": ("T020",),
}

TARGET_OUTPUTS: dict[str, tuple[str, ...]] = {
    "T001": ("main_fig1_dynamics.csv",),
    "T002": ("main_fig2_spectrum.csv",),
    "T003": ("main_fig2_spectrum.csv",),
    "T004": ("main_fig2_spectrum.csv",),
    "T005": ("main_fig2_spectrum.csv",),
    "T006": ("main_fig3_scaling.csv",),
    "T007": ("main_fig3_scaling.csv",),
    "T008": ("main_fig4_fourier.csv",),
    "T009": ("main_fig4_fourier.csv",),
    "T010": ("main_fig4_decay.csv",),
    "T011": ("supp_phase_diagram.csv",),
    "T012": ("supp_phase_diagram.csv",),
    "T013": ("supp_real_scaling_strong.csv",),
    "T014": ("main_fig3_scaling.csv",),
    "T015": ("supp_imaginary_gap.csv",),
    "T016": ("supp_phase_trajectories.csv",),
    "T017": ("supp_phase_trajectories.csv",),
    "T018": ("supp_phase_trajectories.csv",),
    "T019": ("supp_phase_trajectories.csv",),
    "T020": ("supp_branch_surface.csv", "supp_branch_trajectories.csv"),
    "T021": ("supp_phase_trajectories.csv",),
    "T022": ("supp_phase_trajectories.csv",),
    "T023": ("supp_phase_trajectories.csv",),
    "T024": ("supp_phase_trajectories.csv",),
}


@dataclass(frozen=True)
class PaperScaleJob:
    """One independently resumable physical parameter tuple."""

    job_id: str
    family: str
    target_ids: tuple[str, ...]
    parameters: dict[str, Any]


def _json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _slug(value: float) -> str:
    return f"{value:.12g}".replace("-", "m").replace(".", "p")


def _grid(specification: Mapping[str, Any]) -> np.ndarray:
    minimum = float(specification["minimum"])
    maximum = float(specification["maximum"])
    points = int(specification["points"])
    if points < 2 or maximum <= minimum:
        raise ValueError("grid needs points >= 2 and maximum > minimum")
    return np.linspace(minimum, maximum, points)


def _safe_output_root(workspace: Path, value: str) -> Path:
    relative = Path(value)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or relative.parts[0] != "outputs"
    ):
        raise ValueError("output_root must be workspace-relative under outputs/")
    return workspace / relative


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_paper_scale_config(config_path: Path) -> dict[str, Any]:
    """Load and validate a complete 24-target campaign contract."""

    config_path = config_path.resolve()
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and payload.get("base_config") is not None:
        base_relative = Path(str(payload["base_config"]))
        if (
            base_relative.is_absolute()
            or ".." in base_relative.parts
            or len(base_relative.parts) != 1
        ):
            raise ValueError("base_config must name a JSON file in config")
        base_path = config_path.parent / base_relative
        base_payload = json.loads(base_path.read_text(encoding="utf-8"))
        if not isinstance(base_payload, dict) or base_payload.get("base_config"):
            raise ValueError("base_config must be a non-derived JSON object")
        payload = _deep_merge(
            base_payload,
            {key: value for key, value in payload.items() if key != "base_config"},
        )
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("paper-scale config must be a schema_version=1 JSON object")
    if payload.get("paper_id") != "1708.05014":
        raise ValueError("paper-scale config has the wrong paper_id")
    if payload.get("profile") not in {"paper_scale", "smoke"}:
        raise ValueError("profile must be paper_scale or smoke")
    if not isinstance(payload.get("run_id"), str) or not payload["run_id"].strip():
        raise ValueError("run_id must be a non-empty string")
    _safe_output_root(config_path.parents[1], str(payload.get("output_root", "")))

    families = payload.get("families")
    missing_families = set(FAMILY_TARGETS) - set(families or {})
    if not isinstance(families, dict) or missing_families:
        raise ValueError(f"missing campaign families: {sorted(missing_families)}")
    targets = payload.get("targets")
    if not isinstance(targets, dict) or set(targets) != set(TARGET_IDS):
        raise ValueError("targets must contain exactly T001 through T024")
    for target_id, contract in targets.items():
        if not isinstance(contract, dict):
            raise ValueError(f"{target_id} contract must be an object")
        for field in (
            "paper_region",
            "parameter_scope",
            "paper_parameter_source",
            "acceptance_criteria",
        ):
            if not contract.get(field):
                raise ValueError(f"{target_id} is missing {field}")
        criteria = contract["acceptance_criteria"]
        if not isinstance(criteria, list) or not all(
            isinstance(item, str) and item.strip() for item in criteria
        ):
            raise ValueError(f"{target_id} acceptance_criteria must be strings")

    resource_contract = payload.get("resource_contract")
    if not isinstance(resource_contract, dict):
        raise ValueError("resource_contract must be an object")
    for field in (
        "recommended_machine",
        "scheduler",
        "checkpoint_policy",
        "unexecuted_boundary",
    ):
        if not resource_contract.get(field):
            raise ValueError(f"resource_contract is missing {field}")
    return payload


def config_fingerprint(config: Mapping[str, Any]) -> str:
    return _sha256_bytes(_json_bytes(config))


def implementation_fingerprint() -> str:
    """Hash numerical implementation files so resume cannot mix code versions."""

    module_directory = Path(__file__).resolve().parent
    workspace = module_directory.parents[1]
    digest = hashlib.sha256()
    for path in (
        module_directory / "model.py",
        module_directory / "paper_scale_kernels.py",
        Path(__file__).resolve(),
        workspace / "scripts" / "run_paper_scale.py",
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def plan_jobs(config: Mapping[str, Any]) -> list[PaperScaleJob]:
    """Expand the declarative config into a deterministic immutable job list."""

    families = config["families"]
    jobs: list[PaperScaleJob] = [
        PaperScaleJob("parity__cpu", "parity", TARGET_IDS, dict(families["parity"]))
    ]

    dynamics = families["dynamics"]
    for number_spins in dynamics["finite_N"]:
        jobs.append(
            PaperScaleJob(
                f"dynamics__finite_N{int(number_spins):04d}",
                "dynamics",
                ("T001", "T008"),
                {
                    "kind": "finite",
                    "N": int(number_spins),
                    "omega0_over_kappa": float(dynamics["omega0_over_kappa"]),
                    "time": dict(dynamics["time"]),
                    "chunk_points": int(dynamics["chunk_points"]),
                },
            )
        )
    jobs.append(
        PaperScaleJob(
            "dynamics__thermodynamic",
            "dynamics",
            ("T001", "T009"),
            {
                "kind": "thermodynamic",
                "omega0_over_kappa": float(dynamics["omega0_over_kappa"]),
                "time": dict(dynamics["time"]),
            },
        )
    )

    spectrum = families["full_spectrum"]
    for ratio in spectrum["omega0_over_kappa"]:
        target_ids = ("T002", "T003") if float(ratio) < 1.0 else ("T004", "T005")
        jobs.append(
            PaperScaleJob(
                f"full_spectrum__ratio_{_slug(float(ratio))}",
                "full_spectrum",
                target_ids,
                {
                    "N": int(spectrum["N"]),
                    "omega0_over_kappa": float(ratio),
                    "backend": str(spectrum["backend"]),
                },
            )
        )

    scaling = families["scaling"]
    for phase in ("strong", "btc"):
        ratio = float(scaling["omega0_over_kappa"][phase])
        target_ids = (
            ("T013",)
            if phase == "strong"
            else (
                "T006",
                "T007",
                "T010",
                "T014",
            )
        )
        for number_spins in scaling["N"]:
            jobs.append(
                PaperScaleJob(
                    f"scaling__{phase}_N{int(number_spins):04d}",
                    "scaling",
                    target_ids,
                    {
                        "phase": phase,
                        "N": int(number_spins),
                        "omega0_over_kappa": ratio,
                        "eigenvalues": int(scaling["eigenvalues"]),
                        "nu_maximum": float(scaling["nu_maximum"]),
                    },
                )
            )

    gap = families["imaginary_gap"]
    for number_spins in gap["N"]:
        for ratio in _grid(gap["omega0_over_kappa"]):
            jobs.append(
                PaperScaleJob(
                    f"imaginary_gap__N{int(number_spins):04d}_ratio_{_slug(float(ratio))}",
                    "imaginary_gap",
                    ("T015",),
                    {
                        "N": int(number_spins),
                        "omega0_over_kappa": float(ratio),
                        "eigenvalues": int(gap["eigenvalues"]),
                    },
                )
            )

    stationary = families["steady_state"]
    for ratio in _grid(stationary["omega0_over_kappa"]):
        jobs.append(
            PaperScaleJob(
                f"steady_state__ratio_{_slug(float(ratio))}",
                "steady_state",
                ("T011", "T012"),
                {
                    "N": int(stationary["N"]),
                    "omega0_over_kappa": float(ratio),
                    "backend": str(stationary["backend"]),
                },
            )
        )

    portraits = families["phase_portrait"]
    target_by_panel = {
        "S5a": "T016",
        "S5b": "T017",
        "S5c": "T018",
        "S5d": "T019",
        "S7a": "T021",
        "S7b": "T022",
        "S7c": "T023",
        "S7d": "T024",
    }
    for panel in portraits["panels"]:
        panel_id = str(panel["panel_id"])
        if panel_id not in target_by_panel:
            raise ValueError(f"unknown phase portrait panel: {panel_id}")
        jobs.append(
            PaperScaleJob(
                f"phase_portrait__{panel_id}",
                "phase_portrait",
                (target_by_panel[panel_id],),
                {
                    **dict(panel),
                    "time": dict(portraits["time"]),
                    "initial_conditions": int(portraits["initial_conditions"]),
                },
            )
        )

    branch = families["branch"]
    jobs.append(PaperScaleJob("branch__S6", "branch", ("T020",), dict(branch)))
    jobs.sort(key=lambda item: (item.family != "parity", item.job_id))
    if len({job.job_id for job in jobs}) != len(jobs):
        raise ValueError("paper-scale job ids must be unique")
    covered = {target for job in jobs for target in job.target_ids}
    if covered != set(TARGET_IDS):
        raise ValueError(
            f"job plan does not cover all targets: {sorted(set(TARGET_IDS) - covered)}"
        )
    return jobs


def select_shard(
    jobs: Sequence[PaperScaleJob],
    *,
    shard_index: int,
    shard_count: int,
    families: set[str] | None = None,
) -> list[PaperScaleJob]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("shard_index must satisfy 0 <= index < shard_count")
    filtered = [job for job in jobs if families is None or job.family in families]
    return [
        job for index, job in enumerate(filtered) if index % shard_count == shard_index
    ]


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)


def _atomic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w+b", dir=path.parent, delete=False
    ) as handle:
        np.savez_compressed(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def _write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)


def _metadata_array(payload: Mapping[str, Any]) -> np.ndarray:
    return np.asarray(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def _metadata_from_result(result: Mapping[str, np.ndarray]) -> dict[str, Any]:
    raw = result["metadata"]
    return json.loads(str(raw.item()))


def _nonstationary(values: np.ndarray, tolerance: float = 1e-7) -> np.ndarray:
    return values[np.abs(values) > tolerance]


def _ranked_by_real(values: np.ndarray) -> np.ndarray:
    values = _nonstationary(np.asarray(values, dtype=np.complex128))
    return values[np.argsort(values.real)[::-1]]


def _lowest_oscillatory(values: np.ndarray) -> complex:
    ranked = _ranked_by_real(values)
    oscillatory = ranked[np.abs(ranked.imag) > 1e-6]
    return complex(oscillatory[0]) if oscillatory.size else 0.0 + 0.0j


def _conjugate_distance(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.complex128)
    if not values.size:
        return float("inf")
    distances = np.abs(values[:, None] - values.conj()[None, :])
    return float(max(np.min(distances, axis=1)))


def _matched_spectrum_distance(first: np.ndarray, second: np.ndarray) -> float:
    first = np.asarray(first, dtype=np.complex128)
    second = np.asarray(second, dtype=np.complex128)
    if first.size != second.size:
        return float("inf")
    costs = np.abs(first[:, None] - second[None, :])
    rows, columns = linear_sum_assignment(costs)
    return float(np.max(costs[rows, columns], initial=0.0))


def _initial_conditions(count: int) -> list[np.ndarray]:
    """Deterministic equal-area sphere grid; no source-figure coordinates."""

    if count < 1:
        raise ValueError("initial_conditions must be positive")
    golden_angle = np.pi * (3.0 - np.sqrt(5.0))
    conditions: list[np.ndarray] = []
    for index in range(count):
        mz = 1.0 - 2.0 * (index + 0.5) / count
        radius = np.sqrt(max(1.0 - mz * mz, 0.0))
        angle = golden_angle * index
        conditions.append(
            np.asarray([radius * np.cos(angle), radius * np.sin(angle), mz])
        )
    return conditions


def _run_backend_parity(
    parameters: Mapping[str, Any],
    *,
    kappa: float,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Independent small-N checks for every numerical backend family."""

    number_spins = int(parameters["N"])
    ratios = [float(value) for value in parameters["omega0_over_kappa"]]
    tolerances = parameters["tolerances"]

    steady_density_distance = 0.0
    steady_observable_distance = 0.0
    steady_residual = 0.0
    for ratio in ratios:
        direct, direct_residual = steady_state(number_spins, ratio * kappa, kappa)
        shifted, diagnostics = steady_state_shifted_jump(
            number_spins, ratio * kappa, kappa
        )
        steady_density_distance = max(
            steady_density_distance, float(np.linalg.norm(direct - shifted))
        )
        steady_residual = max(
            steady_residual,
            direct_residual,
            float(diagnostics["liouvillian_residual"]),
        )
        operators = spin_operators(number_spins)
        for operator in (operators.sx, operators.sy, operators.sz):
            steady_observable_distance = max(
                steady_observable_distance,
                abs(expectation(operator, direct) - expectation(operator, shifted)),
                abs(variance(operator, direct) - variance(operator, shifted)),
            )

    ratio = ratios[-1]
    dense_operator = liouvillian(number_spins, ratio * kappa, kappa).toarray()
    numpy_values = np.linalg.eigvals(dense_operator.copy())
    scipy_values = scipy_eigvals(
        dense_operator.copy(), overwrite_a=True, check_finite=False
    )
    dense_backend_distance = _matched_spectrum_distance(numpy_values, scipy_values)

    sparse_values, sparse_residual, sparse_converged = leading_spectrum(
        number_spins,
        ratio * kappa,
        kappa,
        count=min(int(parameters["leading_eigenvalues"]), numpy_values.size - 2),
        tolerance=float(parameters["eigen_tolerance"]),
    )
    dense_ranked = numpy_values[np.argsort(numpy_values.real)[::-1]]
    sparse_to_dense_distance = float(
        max(np.min(np.abs(value - dense_ranked)) for value in sparse_values)
    )

    times = _grid(parameters["dynamics_time"])
    monolithic = magnetization_dynamics(number_spins, ratio * kappa, times, kappa)
    split = max(2, times.size // 2)
    first_times = times[: split + 1] - times[0]
    first, state, first_diagnostics = magnetization_dynamics_chunk(
        number_spins, ratio * kappa, first_times, kappa
    )
    second_times = times[split:] - times[split]
    second, _, second_diagnostics = magnetization_dynamics_chunk(
        number_spins,
        ratio * kappa,
        second_times,
        kappa,
        initial_vector=state,
    )
    chunked = np.concatenate([first, second[1:]])
    dynamics_distance = float(np.max(np.abs(monolithic - chunked)))

    checks = {
        "steady_density_parity": steady_density_distance
        <= float(tolerances["steady_density_atol"]),
        "steady_observable_parity": steady_observable_distance
        <= float(tolerances["steady_observable_atol"]),
        "steady_residual": steady_residual
        <= float(tolerances["steady_residual_maximum"]),
        "dense_backend_parity": dense_backend_distance
        <= float(tolerances["dense_spectrum_atol"]),
        "sparse_dense_parity": sparse_to_dense_distance
        <= float(tolerances["leading_spectrum_atol"]),
        "sparse_residual": sparse_residual
        <= float(tolerances["eigen_residual_maximum"]),
        "sparse_converged": bool(sparse_converged),
        "chunked_dynamics_parity": dynamics_distance
        <= float(tolerances["dynamics_atol"]),
        "chunk_trace": max(
            first_diagnostics["maximum_trace_error"],
            second_diagnostics["maximum_trace_error"],
        )
        <= float(tolerances["trace_error_maximum"]),
    }
    metrics = {
        "steady_density_distance": steady_density_distance,
        "steady_observable_distance": steady_observable_distance,
        "steady_residual": steady_residual,
        "dense_backend_distance": dense_backend_distance,
        "sparse_to_dense_distance": sparse_to_dense_distance,
        "sparse_eigen_residual": sparse_residual,
        "chunked_dynamics_distance": dynamics_distance,
        "chunk_trace_error": max(
            first_diagnostics["maximum_trace_error"],
            second_diagnostics["maximum_trace_error"],
        ),
    }
    metadata = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "metrics": metrics,
        "N": number_spins,
        "ratios": ratios,
        "backends": {
            "dense": ["numpy.linalg.eigvals", "scipy.linalg.eigvals"],
            "leading": "scipy.sparse.linalg.eigs",
            "steady": ["trace_constrained_spsolve", "shifted_jump_gram"],
            "dynamics": ["monolithic_expm_multiply", "chunked_expm_multiply"],
        },
    }
    if metadata["status"] != "passed":
        raise RuntimeError(f"backend parity failed: {checks}")
    return {"metadata": _metadata_array(metadata)}, metadata


def _run_dynamics_job(
    job: PaperScaleJob,
    *,
    kappa: float,
    progress_path: Path,
    config_hash: str,
    implementation_hash: str,
    resume: bool,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    parameters = job.parameters
    times = _grid(parameters["time"])
    omega_0 = float(parameters["omega0_over_kappa"]) * kappa
    if parameters["kind"] == "thermodynamic":
        trajectory, norm_drift = semiclassical_trajectory(
            np.asarray([1.0, 0.0, 0.0]),
            times,
            omega_0=omega_0,
            kappa=kappa,
        )
        metadata = {
            "kind": "thermodynamic",
            "N": "infinity",
            "omega0_over_kappa": omega_0 / kappa,
            "maximum_norm_drift": norm_drift,
        }
        return {
            "time": times,
            "magnetization": trajectory[:, 2] / 2.0,
            "metadata": _metadata_array(metadata),
        }, metadata

    number_spins = int(parameters["N"])
    chunk_points = int(parameters["chunk_points"])
    if chunk_points < 1:
        raise ValueError("dynamics chunk_points must be positive")

    if progress_path.exists():
        if not resume:
            raise RuntimeError(
                f"partial checkpoint exists for {job.job_id}; pass --resume"
            )
        progress = _load_npz(progress_path)
        if str(progress["config_hash"].item()) != config_hash:
            raise RuntimeError(f"checkpoint config hash mismatch for {job.job_id}")
        if str(progress["implementation_hash"].item()) != implementation_hash:
            raise RuntimeError(
                f"checkpoint implementation hash mismatch for {job.job_id}"
            )
        next_index = int(progress["next_index"].item())
        state = np.asarray(progress["state"], dtype=np.complex128)
        magnetization = np.asarray(progress["magnetization"], dtype=np.float64).tolist()
        maximum_trace_error = float(progress["maximum_trace_error"].item())
        maximum_imaginary = float(progress["maximum_imaginary"].item())
    else:
        state = vectorize_density(spin_x_coherent_density(number_spins))
        operators = spin_operators(number_spins)
        initial_magnetization = (
            expectation(operators.sz, spin_x_coherent_density(number_spins))
            / number_spins
        )
        magnetization = [initial_magnetization]
        next_index = 1
        maximum_trace_error = 0.0
        maximum_imaginary = 0.0

    while next_index < times.size:
        stop_index = min(next_index + chunk_points - 1, times.size - 1)
        local_times = times[next_index - 1 : stop_index + 1] - times[next_index - 1]
        values, state, diagnostics = magnetization_dynamics_chunk(
            number_spins,
            omega_0,
            local_times,
            kappa,
            initial_vector=state,
        )
        magnetization.extend(values[1:].tolist())
        next_index = stop_index + 1
        maximum_trace_error = max(
            maximum_trace_error, diagnostics["maximum_trace_error"]
        )
        maximum_imaginary = max(
            maximum_imaginary,
            diagnostics["maximum_imaginary_magnetization"],
        )
        _atomic_npz(
            progress_path,
            {
                "config_hash": np.asarray(config_hash),
                "implementation_hash": np.asarray(implementation_hash),
                "next_index": np.asarray(next_index),
                "state": state,
                "magnetization": np.asarray(magnetization),
                "maximum_trace_error": np.asarray(maximum_trace_error),
                "maximum_imaginary": np.asarray(maximum_imaginary),
            },
        )

    values = np.asarray(magnetization, dtype=np.float64)
    if values.shape != times.shape:
        raise RuntimeError(f"dynamics checkpoint length mismatch for {job.job_id}")
    metadata = {
        "kind": "finite",
        "N": number_spins,
        "omega0_over_kappa": omega_0 / kappa,
        "maximum_trace_error": maximum_trace_error,
        "maximum_imaginary_magnetization": maximum_imaginary,
        "chunks_completed": int(np.ceil((times.size - 1) / chunk_points)),
        "state_checkpoint_retained": str(progress_path),
    }
    return {
        "time": times,
        "magnetization": values,
        "final_vector": state,
        "metadata": _metadata_array(metadata),
    }, metadata


def _run_full_spectrum_job(
    job: PaperScaleJob, *, kappa: float
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    parameters = job.parameters
    number_spins = int(parameters["N"])
    ratio = float(parameters["omega0_over_kappa"])
    backend = str(parameters["backend"])
    operator = liouvillian(number_spins, ratio * kappa, kappa)
    if backend == "scipy_dense":
        values = scipy_eigvals(operator.toarray(), overwrite_a=True, check_finite=False)
    elif backend == "numpy_dense":
        values = np.linalg.eigvals(operator.toarray())
    else:
        raise ValueError(f"unsupported full spectrum backend: {backend}")
    values = values[np.argsort(values.real)[::-1]]
    metadata = {
        "N": number_spins,
        "omega0_over_kappa": ratio,
        "backend": backend,
        "liouville_dimension": int(operator.shape[0]),
        "stationary_eigenvalue_absolute": float(np.min(np.abs(values))),
        "maximum_positive_real_part": float(max(np.max(values.real), 0.0)),
        "conjugate_pair_distance": _conjugate_distance(values),
        "finite": bool(np.all(np.isfinite(values))),
    }
    return {
        "eigenvalues": np.asarray(values, dtype=np.complex128),
        "metadata": _metadata_array(metadata),
    }, metadata


def _run_scaling_job(
    job: PaperScaleJob,
    *,
    kappa: float,
    eigen_tolerance: float,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    parameters = job.parameters
    number_spins = int(parameters["N"])
    ratio = float(parameters["omega0_over_kappa"])
    values, residual, converged = leading_spectrum(
        number_spins,
        ratio * kappa,
        kappa,
        count=int(parameters["eigenvalues"]),
        tolerance=eigen_tolerance,
    )
    ranked = _ranked_by_real(values)
    nu = np.square(np.arange(1, ranked.size + 1, dtype=np.float64)) / number_spins
    metadata = {
        "phase": str(parameters["phase"]),
        "N": number_spins,
        "omega0_over_kappa": ratio,
        "maximum_eigen_residual": residual,
        "arpack_converged": bool(converged),
        "nu_maximum": float(parameters["nu_maximum"]),
        "retained_under_nu_threshold": int(
            np.count_nonzero(nu <= float(parameters["nu_maximum"]))
        ),
    }
    return {
        "eigenvalues": ranked,
        "nu": nu,
        "metadata": _metadata_array(metadata),
    }, metadata


def _run_imaginary_gap_job(
    job: PaperScaleJob,
    *,
    kappa: float,
    eigen_tolerance: float,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    parameters = job.parameters
    number_spins = int(parameters["N"])
    ratio = float(parameters["omega0_over_kappa"])
    values, residual, converged = leading_spectrum(
        number_spins,
        ratio * kappa,
        kappa,
        count=int(parameters["eigenvalues"]),
        tolerance=eigen_tolerance,
    )
    ranked = _ranked_by_real(values)
    if ranked.size < 2:
        raise RuntimeError("imaginary-gap job returned fewer than two excitations")
    frequency = abs(ranked[1].imag) / kappa
    metadata = {
        "N": number_spins,
        "omega0_over_kappa": ratio,
        "lowest_imag_lambda_over_kappa": float(frequency),
        "maximum_eigen_residual": residual,
        "arpack_converged": bool(converged),
    }
    return {
        "eigenvalues": ranked,
        "metadata": _metadata_array(metadata),
    }, metadata


def _run_steady_state_job(
    job: PaperScaleJob, *, kappa: float
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    parameters = job.parameters
    number_spins = int(parameters["N"])
    ratio = float(parameters["omega0_over_kappa"])
    if parameters["backend"] != "shifted_jump_gram":
        raise ValueError("paper-scale steady state requires shifted_jump_gram")
    density, diagnostics = steady_state_shifted_jump(number_spins, ratio * kappa, kappa)
    operators = spin_operators(number_spins)
    names = ("sx", "sy", "sz")
    means = []
    centered_variances = []
    second_moments = []
    for name in names:
        operator = getattr(operators, name)
        mean = expectation(operator, density)
        centered = variance(operator, density)
        means.append(mean)
        centered_variances.append(centered)
        second_moments.append(centered + mean * mean)
    metadata = {
        **diagnostics,
        "N": number_spins,
        "omega0_over_kappa": ratio,
        "backend": "shifted_jump_gram",
        "positivity_certificate": "rho=B B^dagger/Tr(B B^dagger)",
    }
    return {
        "means": np.asarray(means),
        "centered_variances": np.asarray(centered_variances),
        "second_moments": np.asarray(second_moments),
        "metadata": _metadata_array(metadata),
    }, metadata


def _run_phase_portrait_job(
    job: PaperScaleJob,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    parameters = job.parameters
    times = _grid(parameters["time"])
    conditions = _initial_conditions(int(parameters["initial_conditions"]))
    trajectories = []
    maximum_norm_drift = 0.0
    for initial in conditions:
        trajectory, drift = semiclassical_trajectory(
            initial,
            times,
            omega_0=float(parameters["omega_0"]),
            kappa=float(parameters["kappa"]),
            omega_x=float(parameters["omega_x"]),
            omega_z=float(parameters["omega_z"]),
        )
        trajectories.append(trajectory)
        maximum_norm_drift = max(maximum_norm_drift, drift)
    values = np.asarray(trajectories)
    q_coordinate = values[:, :, 2]
    p_coordinate = 0.5 * np.arctan2(values[:, :, 1], values[:, :, 0])
    metadata = {
        "panel_id": str(parameters["panel_id"]),
        "omega_0": float(parameters["omega_0"]),
        "kappa": float(parameters["kappa"]),
        "omega_x": float(parameters["omega_x"]),
        "omega_z": float(parameters["omega_z"]),
        "initial_conditions": len(conditions),
        "maximum_norm_drift": maximum_norm_drift,
        "initial_condition_source": "deterministic_equal_area_formula_grid",
    }
    return {
        "time": times,
        "Q": q_coordinate,
        "P_over_pi": p_coordinate / np.pi,
        "metadata": _metadata_array(metadata),
    }, metadata


def _run_branch_job(
    job: PaperScaleJob,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    parameters = job.parameters
    omega_0 = float(parameters["omega_0"])
    kappa = float(parameters["kappa"])
    omega_z = float(parameters["omega_z"])
    q_values = _grid(parameters["Q"])
    p_values = _grid(parameters["P_over_pi"]) * np.pi
    q_mesh, p_mesh = np.meshgrid(q_values, p_values, indexing="ij")
    radius = np.sqrt(np.maximum(1.0 - q_mesh * q_mesh, 0.0))
    mx = radius * np.cos(2.0 * p_mesh)
    my = radius * np.sin(2.0 * p_mesh)
    conserved = conserved_r_omega_z(
        mx, my, omega_0=omega_0, kappa=kappa, omega_z=omega_z
    )
    branch_argument = kappa * my + 2.0 * omega_z * mx - omega_0

    times = _grid(parameters["trajectory_time"])
    trajectory_q = []
    trajectory_p = []
    maximum_norm_drift = 0.0
    for initial in _initial_conditions(int(parameters["initial_conditions"])):
        trajectory, drift = semiclassical_trajectory(
            initial,
            times,
            omega_0=omega_0,
            kappa=kappa,
            omega_x=0.0,
            omega_z=omega_z,
        )
        q_coordinate, p_coordinate = qp_coordinates(trajectory)
        trajectory_q.append(q_coordinate)
        trajectory_p.append(p_coordinate / np.pi)
        maximum_norm_drift = max(maximum_norm_drift, drift)
    metadata = {
        "panel_id": "S6",
        "omega_0": omega_0,
        "kappa": kappa,
        "omega_z": omega_z,
        "maximum_norm_drift": maximum_norm_drift,
        "field_grid_points": int(q_mesh.size),
        "initial_conditions": int(parameters["initial_conditions"]),
        "conserved_field_finite": bool(np.all(np.isfinite(conserved))),
        "branch_cut_is_formula_evaluated": True,
    }
    return {
        "field_Q": q_mesh,
        "field_P_over_pi": p_mesh / np.pi,
        "field_R_over_2pi_kappa": conserved / (2.0 * np.pi * kappa),
        "branch_argument": branch_argument,
        "trajectory_time": times,
        "trajectory_Q": np.asarray(trajectory_q),
        "trajectory_P_over_pi": np.asarray(trajectory_p),
        "metadata": _metadata_array(metadata),
    }, metadata


def _result_path(output_root: Path, job: PaperScaleJob) -> Path:
    return output_root / "shards" / job.family / f"{job.job_id}.npz"


def _marker_path(output_root: Path, job: PaperScaleJob) -> Path:
    return output_root / "checkpoints" / f"{job.job_id}.json"


def _progress_path(output_root: Path, job: PaperScaleJob) -> Path:
    return output_root / "checkpoints" / f"{job.job_id}.state.npz"


def _completed_marker_is_valid(
    marker_path: Path,
    result_path: Path,
    *,
    config_hash: str,
    implementation_hash: str,
) -> bool:
    if not marker_path.is_file() or not result_path.is_file():
        return False
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(
        marker.get("status") == "complete"
        and marker.get("config_hash") == config_hash
        and marker.get("implementation_hash") == implementation_hash
        and marker.get("result_sha256") == _sha256_file(result_path)
    )


def _execute_job(
    job: PaperScaleJob,
    *,
    config: Mapping[str, Any],
    output_root: Path,
    config_hash: str,
    implementation_hash: str,
    resume: bool,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    kappa = float(config["parameters"]["kappa"])
    eigen_tolerance = float(config["parameters"]["solver"]["eigen_tolerance"])
    if job.family == "parity":
        return _run_backend_parity(job.parameters, kappa=kappa)
    if job.family == "dynamics":
        return _run_dynamics_job(
            job,
            kappa=kappa,
            progress_path=_progress_path(output_root, job),
            config_hash=config_hash,
            implementation_hash=implementation_hash,
            resume=resume,
        )
    if job.family == "full_spectrum":
        return _run_full_spectrum_job(job, kappa=kappa)
    if job.family == "scaling":
        return _run_scaling_job(job, kappa=kappa, eigen_tolerance=eigen_tolerance)
    if job.family == "imaginary_gap":
        return _run_imaginary_gap_job(job, kappa=kappa, eigen_tolerance=eigen_tolerance)
    if job.family == "steady_state":
        return _run_steady_state_job(job, kappa=kappa)
    if job.family == "phase_portrait":
        return _run_phase_portrait_job(job)
    if job.family == "branch":
        return _run_branch_job(job)
    raise ValueError(f"unsupported paper-scale family: {job.family}")


def _machine_snapshot() -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cpu_count": os.cpu_count(),
        "thread_environment": {
            name: os.environ.get(name)
            for name in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
            )
        },
    }


def _maximum_resident_set_kib() -> int:
    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return raw // 1024 if platform.system() == "Darwin" else raw


def run_campaign(
    config_path: Path,
    *,
    shard_index: int = 0,
    shard_count: int = 1,
    families: set[str] | None = None,
    resume: bool = False,
    output_root_override: Path | None = None,
) -> dict[str, Any]:
    """Run one deterministic campaign shard and atomically freeze each job."""

    config_path = config_path.resolve()
    config = load_paper_scale_config(config_path)
    workspace = config_path.parents[1]
    output_root = (
        output_root_override.resolve()
        if output_root_override is not None
        else _safe_output_root(workspace, str(config["output_root"]))
    )
    output_root.mkdir(parents=True, exist_ok=True)
    config_hash = config_fingerprint(config)
    implementation_hash = implementation_fingerprint()
    jobs = select_shard(
        plan_jobs(config),
        shard_index=shard_index,
        shard_count=shard_count,
        families=families,
    )
    summary: dict[str, Any] = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "profile": config["profile"],
        "config_hash": config_hash,
        "implementation_hash": implementation_hash,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "selected_families": sorted(families) if families else ["all"],
        "jobs_selected": len(jobs),
        "jobs_completed": 0,
        "jobs_resumed": 0,
        "jobs": [],
        "machine": _machine_snapshot(),
    }
    started = time.perf_counter()
    for job in jobs:
        result_path = _result_path(output_root, job)
        marker_path = _marker_path(output_root, job)
        if _completed_marker_is_valid(
            marker_path,
            result_path,
            config_hash=config_hash,
            implementation_hash=implementation_hash,
        ):
            summary["jobs_resumed"] += 1
            summary["jobs"].append({"job_id": job.job_id, "status": "already_complete"})
            continue
        if marker_path.exists() or result_path.exists():
            if not resume:
                raise RuntimeError(
                    f"incomplete or mismatched artifacts exist for {job.job_id}; pass --resume after inspection"
                )
            if marker_path.exists():
                try:
                    stale_marker = json.loads(marker_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as error:
                    raise RuntimeError(f"invalid marker for {job.job_id}") from error
                if stale_marker.get("config_hash") not in {None, config_hash}:
                    raise RuntimeError(f"marker config hash mismatch for {job.job_id}")
                if stale_marker.get("implementation_hash") not in {
                    None,
                    implementation_hash,
                }:
                    raise RuntimeError(
                        f"marker implementation hash mismatch for {job.job_id}"
                    )

        job_started = time.perf_counter()
        _atomic_json(
            marker_path,
            {
                "schema_version": 1,
                "status": "running",
                "paper_id": config["paper_id"],
                "run_id": config["run_id"],
                "config_hash": config_hash,
                "implementation_hash": implementation_hash,
                "job_id": job.job_id,
                "family": job.family,
                "target_ids": list(job.target_ids),
                "parameters": job.parameters,
                "machine": _machine_snapshot(),
            },
        )
        arrays, diagnostics = _execute_job(
            job,
            config=config,
            output_root=output_root,
            config_hash=config_hash,
            implementation_hash=implementation_hash,
            resume=resume,
        )
        _atomic_npz(result_path, arrays)
        elapsed = time.perf_counter() - job_started
        marker = {
            "schema_version": 1,
            "status": "complete",
            "paper_id": config["paper_id"],
            "run_id": config["run_id"],
            "profile": config["profile"],
            "config_hash": config_hash,
            "implementation_hash": implementation_hash,
            "job_id": job.job_id,
            "family": job.family,
            "target_ids": list(job.target_ids),
            "parameters": job.parameters,
            "result_path": str(result_path.relative_to(output_root)),
            "result_sha256": _sha256_file(result_path),
            "elapsed_seconds": elapsed,
            "maximum_resident_set_kib": _maximum_resident_set_kib(),
            "diagnostics": diagnostics,
            "machine": _machine_snapshot(),
            "source_pixels_read": False,
            "author_code_used": False,
            "author_arrays_used": False,
        }
        _atomic_json(marker_path, marker)
        summary["jobs_completed"] += 1
        summary["jobs"].append(
            {"job_id": job.job_id, "status": "complete", "elapsed_seconds": elapsed}
        )
    summary["elapsed_seconds"] = time.perf_counter() - started
    summary["status"] = "passed"
    summary_path = (
        output_root
        / "run_summaries"
        / (f"shard_{shard_index:04d}_of_{shard_count:04d}.json")
    )
    _atomic_json(summary_path, summary)
    return summary


def _load_complete_results(
    config: Mapping[str, Any], output_root: Path
) -> tuple[dict[str, dict[str, np.ndarray]], list[dict[str, Any]]]:
    config_hash = config_fingerprint(config)
    implementation_hash = implementation_fingerprint()
    results: dict[str, dict[str, np.ndarray]] = {}
    markers: list[dict[str, Any]] = []
    missing: list[str] = []
    for job in plan_jobs(config):
        result_path = _result_path(output_root, job)
        marker_path = _marker_path(output_root, job)
        if not _completed_marker_is_valid(
            marker_path,
            result_path,
            config_hash=config_hash,
            implementation_hash=implementation_hash,
        ):
            missing.append(job.job_id)
            continue
        results[job.job_id] = _load_npz(result_path)
        markers.append(json.loads(marker_path.read_text(encoding="utf-8")))
    if missing:
        preview = ", ".join(missing[:12])
        if len(missing) > 12:
            preview += f", ... (+{len(missing) - 12})"
        raise RuntimeError(f"cannot aggregate; incomplete jobs: {preview}")
    return results, markers


def _aggregate_dynamics(
    jobs: Sequence[PaperScaleJob],
    results: Mapping[str, Mapping[str, np.ndarray]],
    data_dir: Path,
    *,
    kappa: float,
    paper_sizes: Sequence[int],
    fourier_maximum: float,
    profile: str,
) -> None:
    dynamics_rows: list[dict[str, Any]] = []
    fourier_rows: list[dict[str, Any]] = []
    for job in jobs:
        if job.family != "dynamics":
            continue
        result = results[job.job_id]
        metadata = _metadata_from_result(result)
        times = np.asarray(result["time"], dtype=np.float64)
        values = np.asarray(result["magnetization"], dtype=np.float64)
        finite = metadata["kind"] == "finite"
        series_id = f"finite_N_{metadata['N']}" if finite else "thermodynamic_limit"
        for time_value, magnetization in zip(times, values):
            dynamics_rows.append(
                {
                    "series_id": series_id,
                    "time_kappa": f"{time_value * kappa:.17g}",
                    "sz_over_N": f"{magnetization:.17g}",
                    "generated_N": metadata["N"],
                    "paper_series_N": ",".join(str(value) for value in paper_sizes)
                    + ",infinity",
                    "execution_profile": profile,
                    "generated_data_provenance": "independent_numerics",
                }
            )
        centered = values - np.mean(values)
        time_step = float(times[1] - times[0])
        transform = np.abs(np.fft.rfft(centered)) / centered.size
        frequencies = 2.0 * np.pi * np.fft.rfftfreq(centered.size, d=time_step)
        for frequency, amplitude in zip(frequencies, transform):
            if frequency <= fourier_maximum:
                fourier_rows.append(
                    {
                        "series_id": series_id,
                        "omega_over_kappa": f"{frequency / kappa:.17g}",
                        "fft_sz_over_N": f"{amplitude:.17g}",
                        "generated_N": metadata["N"],
                        "execution_profile": profile,
                        "generated_data_provenance": "independent_numerics",
                    }
                )
    _write_csv(
        data_dir / "main_fig1_dynamics.csv", list(dynamics_rows[0]), dynamics_rows
    )
    _write_csv(data_dir / "main_fig4_fourier.csv", list(fourier_rows[0]), fourier_rows)


def _aggregate_spectra(
    jobs: Sequence[PaperScaleJob],
    results: Mapping[str, Mapping[str, np.ndarray]],
    data_dir: Path,
    *,
    kappa: float,
    profile: str,
) -> None:
    full_rows: list[dict[str, Any]] = []
    scaling_rows: list[dict[str, Any]] = []
    decay_rows: list[dict[str, Any]] = []
    strong_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    for job in jobs:
        result = results[job.job_id]
        metadata = _metadata_from_result(result)
        if job.family == "full_spectrum":
            phase = "strong" if metadata["omega0_over_kappa"] < 1.0 else "btc"
            for index, value in enumerate(result["eigenvalues"]):
                full_rows.append(
                    {
                        "phase": phase,
                        "omega0_over_kappa": metadata["omega0_over_kappa"],
                        "eigen_index": index,
                        "real_lambda_over_kappa": f"{value.real / kappa:.17g}",
                        "imag_lambda_over_kappa": f"{value.imag / kappa:.17g}",
                        "generated_N": metadata["N"],
                        "execution_profile": profile,
                        "generated_data_provenance": "independent_numerics",
                    }
                )
        elif job.family == "scaling":
            values = np.asarray(result["eigenvalues"], dtype=np.complex128)
            nu_values = np.asarray(result["nu"], dtype=np.float64)
            target_rows = strong_rows if metadata["phase"] == "strong" else scaling_rows
            for rank, (value, nu) in enumerate(zip(values, nu_values), start=1):
                row = {
                    "N": metadata["N"],
                    "inverse_N": f"{1.0 / metadata['N']:.17g}",
                    "rank": rank,
                    "minus_real_lambda_over_kappa": f"{-value.real / kappa:.17g}",
                    "abs_imag_lambda_over_kappa": f"{abs(value.imag) / kappa:.17g}",
                    "nu": f"{nu:.17g}",
                    "selected_under_nu_threshold": bool(nu <= metadata["nu_maximum"]),
                    "omega0_over_kappa": metadata["omega0_over_kappa"],
                    "execution_profile": profile,
                    "generated_data_provenance": "independent_numerics",
                }
                target_rows.append(row)
            if metadata["phase"] == "btc":
                ranked = _ranked_by_real(values)
                oscillatory = _lowest_oscillatory(ranked)
                first_two = ranked[:2]
                decay_rows.append(
                    {
                        "N": metadata["N"],
                        "inverse_N": f"{1.0 / metadata['N']:.17g}",
                        "eta_from_oscillatory_mode": f"{-oscillatory.real / kappa:.17g}",
                        "minus_real_lambda_1": f"{-first_two[0].real / kappa:.17g}",
                        "minus_real_lambda_2": f"{-first_two[1].real / kappa:.17g}",
                        "execution_profile": profile,
                        "generated_data_provenance": "independent_numerics",
                    }
                )
        elif job.family == "imaginary_gap":
            gap_rows.append(
                {
                    "N": metadata["N"],
                    "omega0_over_kappa": f"{metadata['omega0_over_kappa']:.17g}",
                    "lowest_imag_lambda_over_kappa": f"{metadata['lowest_imag_lambda_over_kappa']:.17g}",
                    "residual": f"{metadata['maximum_eigen_residual']:.17g}",
                    "execution_profile": profile,
                    "generated_data_provenance": "independent_numerics",
                }
            )
    _write_csv(data_dir / "main_fig2_spectrum.csv", list(full_rows[0]), full_rows)
    _write_csv(data_dir / "main_fig3_scaling.csv", list(scaling_rows[0]), scaling_rows)
    _write_csv(data_dir / "main_fig4_decay.csv", list(decay_rows[0]), decay_rows)
    _write_csv(
        data_dir / "supp_real_scaling_strong.csv", list(strong_rows[0]), strong_rows
    )
    _write_csv(data_dir / "supp_imaginary_gap.csv", list(gap_rows[0]), gap_rows)


def _aggregate_steady_state(
    jobs: Sequence[PaperScaleJob],
    results: Mapping[str, Mapping[str, np.ndarray]],
    data_dir: Path,
    *,
    profile: str,
) -> None:
    rows: list[dict[str, Any]] = []
    for job in jobs:
        if job.family != "steady_state":
            continue
        result = results[job.job_id]
        metadata = _metadata_from_result(result)
        means = np.asarray(result["means"])
        centered = np.asarray(result["centered_variances"])
        second = np.asarray(result["second_moments"])
        number_spins = int(metadata["N"])
        row: dict[str, Any] = {
            "omega0_over_kappa": f"{metadata['omega0_over_kappa']:.17g}",
            "generated_N": number_spins,
            "execution_profile": profile,
            "steady_residual": f"{metadata['liouvillian_residual']:.17g}",
            "trace_error": f"{metadata['trace_error']:.17g}",
            "hermiticity_error": f"{metadata['hermiticity_error']:.17g}",
            "generated_data_provenance": "independent_numerics",
        }
        for index, name in enumerate(("sx", "sy", "sz")):
            sign = -1.0 if name == "sy" else 1.0
            row[f"mean_{name}_over_N"] = f"{means[index] / number_spins:.17g}"
            row[f"centered_variance_{name}_over_N2"] = (
                f"{centered[index] / number_spins**2:.17g}"
            )
            row[f"paper_mean_tilde_{name}_over_N"] = (
                f"{sign * 2.0 * means[index] / number_spins:.17g}"
            )
            row[f"paper_squared_mean_tilde_{name}_over_N2"] = (
                f"{4.0 * means[index] ** 2 / number_spins**2:.17g}"
            )
            row[f"paper_second_moment_tilde_{name}_over_N2"] = (
                f"{4.0 * second[index] / number_spins**2:.17g}"
            )
        rows.append(row)
    rows.sort(key=lambda row: float(row["omega0_over_kappa"]))
    _write_csv(data_dir / "supp_phase_diagram.csv", list(rows[0]), rows)


def _aggregate_phase_space(
    jobs: Sequence[PaperScaleJob],
    results: Mapping[str, Mapping[str, np.ndarray]],
    data_dir: Path,
    *,
    profile: str,
) -> None:
    trajectory_rows: list[dict[str, Any]] = []
    branch_surface_rows: list[dict[str, Any]] = []
    branch_trajectory_rows: list[dict[str, Any]] = []
    for job in jobs:
        result = results[job.job_id]
        metadata = _metadata_from_result(result)
        if job.family == "phase_portrait":
            for trajectory_id in range(result["Q"].shape[0]):
                for time_value, q_value, p_value in zip(
                    result["time"],
                    result["Q"][trajectory_id],
                    result["P_over_pi"][trajectory_id],
                ):
                    trajectory_rows.append(
                        {
                            "panel_id": metadata["panel_id"],
                            "trajectory_id": trajectory_id,
                            "time": f"{time_value:.17g}",
                            "Q": f"{q_value:.17g}",
                            "P_over_pi": f"{p_value:.17g}",
                            "omega_0": metadata["omega_0"],
                            "kappa": metadata["kappa"],
                            "omega_x": metadata["omega_x"],
                            "omega_z": metadata["omega_z"],
                            "execution_profile": profile,
                            "generated_data_provenance": "independent_numerics",
                        }
                    )
        elif job.family == "branch":
            for q_value, p_value, conserved, branch_argument in zip(
                result["field_Q"].ravel(),
                result["field_P_over_pi"].ravel(),
                result["field_R_over_2pi_kappa"].ravel(),
                result["branch_argument"].ravel(),
            ):
                branch_surface_rows.append(
                    {
                        "Q": f"{q_value:.17g}",
                        "P_over_pi": f"{p_value:.17g}",
                        "R_over_2pi_kappa": f"{conserved:.17g}",
                        "branch_cut_argument": f"{branch_argument:.17g}",
                        "execution_profile": profile,
                        "generated_data_provenance": "independent_numerics",
                    }
                )
            for trajectory_id in range(result["trajectory_Q"].shape[0]):
                for time_value, q_value, p_value in zip(
                    result["trajectory_time"],
                    result["trajectory_Q"][trajectory_id],
                    result["trajectory_P_over_pi"][trajectory_id],
                ):
                    branch_trajectory_rows.append(
                        {
                            "trajectory_id": trajectory_id,
                            "time": f"{time_value:.17g}",
                            "Q": f"{q_value:.17g}",
                            "P_over_pi": f"{p_value:.17g}",
                            "execution_profile": profile,
                            "generated_data_provenance": "independent_numerics",
                        }
                    )
    _write_csv(
        data_dir / "supp_phase_trajectories.csv",
        list(trajectory_rows[0]),
        trajectory_rows,
    )
    _write_csv(
        data_dir / "supp_branch_surface.csv",
        list(branch_surface_rows[0]),
        branch_surface_rows,
    )
    _write_csv(
        data_dir / "supp_branch_trajectories.csv",
        list(branch_trajectory_rows[0]),
        branch_trajectory_rows,
    )


def _target_acceptance(
    config: Mapping[str, Any],
    jobs: Sequence[PaperScaleJob],
    results: Mapping[str, Mapping[str, np.ndarray]],
    data_dir: Path,
) -> dict[str, Any]:
    thresholds = config["parameters"]["solver"]
    parity_metadata = _metadata_from_result(results["parity__cpu"])
    metadata_by_job = {
        job.job_id: _metadata_from_result(results[job.job_id]) for job in jobs
    }

    def jobs_for(
        target_id: str, families: set[str] | None = None
    ) -> list[PaperScaleJob]:
        return [
            job
            for job in jobs
            if target_id in job.target_ids
            and job.family != "parity"
            and (families is None or job.family in families)
        ]

    def eigen_residual_ok(selected: Sequence[PaperScaleJob]) -> bool:
        return all(
            float(metadata_by_job[job.job_id].get("maximum_eigen_residual", 0.0))
            <= float(thresholds["maximum_eigen_residual"])
            and bool(metadata_by_job[job.job_id].get("arpack_converged", True))
            for job in selected
        )

    def norm_ok(selected: Sequence[PaperScaleJob]) -> bool:
        return all(
            float(metadata_by_job[job.job_id].get("maximum_norm_drift", 0.0))
            <= float(thresholds["maximum_norm_drift"])
            for job in selected
        )

    def trace_ok(selected: Sequence[PaperScaleJob]) -> bool:
        return all(
            float(metadata_by_job[job.job_id].get("maximum_trace_error", 0.0))
            <= float(thresholds["maximum_trace_error"])
            for job in selected
        )

    target_rows: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        selected = jobs_for(target_id)
        checks: dict[str, bool] = {
            "all_target_jobs_complete": bool(selected),
            "backend_parity_passed": parity_metadata["status"] == "passed",
            "expected_outputs_nonempty": all(
                (data_dir / name).is_file() and (data_dir / name).stat().st_size > 100
                for name in TARGET_OUTPUTS[target_id]
            ),
            "source_pixels_excluded": True,
            "author_code_excluded": True,
            "author_arrays_excluded": True,
        }
        if target_id in {"T001", "T008", "T009"}:
            checks["trace_or_norm_within_tolerance"] = trace_ok(selected) and norm_ok(
                selected
            )
        if target_id in {"T002", "T003", "T004", "T005"}:
            checks["spectrum_finite"] = all(
                bool(metadata_by_job[job.job_id]["finite"]) for job in selected
            )
            checks["stationary_eigenvalue_present"] = all(
                float(metadata_by_job[job.job_id]["stationary_eigenvalue_absolute"])
                <= float(thresholds["maximum_stationary_eigenvalue_absolute"])
                for job in selected
            )
            checks["conjugate_pairs"] = all(
                float(metadata_by_job[job.job_id]["conjugate_pair_distance"])
                <= float(thresholds["maximum_conjugate_pair_distance"])
                for job in selected
            )
            checks["nonpositive_real_part"] = all(
                float(metadata_by_job[job.job_id]["maximum_positive_real_part"])
                <= float(thresholds["maximum_positive_real_part"])
                for job in selected
            )
        if target_id in {"T006", "T007", "T010", "T013", "T014", "T015"}:
            checks["eigen_residual_and_convergence"] = eigen_residual_ok(selected)
        if target_id in {"T011", "T012"}:
            checks["steady_residual"] = all(
                float(metadata_by_job[job.job_id]["liouvillian_residual"])
                <= float(thresholds["maximum_steady_residual"])
                for job in selected
            )
            checks["steady_trace_and_hermiticity"] = all(
                float(metadata_by_job[job.job_id]["trace_error"])
                <= float(thresholds["maximum_trace_error"])
                and float(metadata_by_job[job.job_id]["hermiticity_error"])
                <= float(thresholds["maximum_hermiticity_error"])
                for job in selected
            )
        if target_id == "T012":
            header = (
                (data_dir / "supp_phase_diagram.csv")
                .read_text(encoding="utf-8")
                .splitlines()[0]
            )
            checks["stable_semantic_discrepancy_preserved"] = all(
                token in header
                for token in (
                    "centered_variance_sx_over_N2",
                    "paper_squared_mean_tilde_sx_over_N2",
                    "paper_second_moment_tilde_sx_over_N2",
                )
            )
        if target_id in {
            "T016",
            "T017",
            "T018",
            "T019",
            "T020",
            "T021",
            "T022",
            "T023",
            "T024",
        }:
            checks["semiclassical_norm"] = norm_ok(selected)
        if target_id == "T020":
            checks["conserved_field_finite"] = all(
                bool(metadata_by_job[job.job_id]["conserved_field_finite"])
                for job in selected
            )
            checks["branch_cut_formula_evaluated"] = all(
                bool(metadata_by_job[job.job_id]["branch_cut_is_formula_evaluated"])
                for job in selected
            )

        contract = config["targets"][target_id]
        target_rows.append(
            {
                "target_id": target_id,
                "paper_region": contract["paper_region"],
                "status": "passed" if all(checks.values()) else "failed",
                "execution_profile": config["profile"],
                "parameter_scope": contract["parameter_scope"],
                "paper_parameter_source": contract["paper_parameter_source"],
                "acceptance_criteria": contract["acceptance_criteria"],
                "checks": checks,
                "job_ids": [job.job_id for job in selected],
                "expected_outputs": [
                    f"data/{name}" for name in TARGET_OUTPUTS[target_id]
                ],
                "paper_assessment": "not_evaluated_by_execution_contract",
            }
        )

    status = (
        "passed" if all(row["status"] == "passed" for row in target_rows) else "failed"
    )
    return {
        "schema_version": 2,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "profile": config["profile"],
        "status": status,
        "targets": target_rows,
        "summary": {
            "targets_total": len(target_rows),
            "targets_passed": sum(row["status"] == "passed" for row in target_rows),
            "jobs_total": len(jobs),
            "paper_scale_final_run_executed": config["profile"] == "paper_scale",
            "strict_original_reference_comparison_executed": False,
        },
        "review_protocol": {
            "protocol_version": 2,
            "paper_error_candidate_emitted": False,
            "stable_discrepancies_preserved": [
                {
                    "target_id": "T012",
                    "issue": "Supplement S2 caption says variances while the displayed limiting behavior is compatible with squared normalized means.",
                    "classification": "inconclusive_until_paper_exact_run_convergence_and_two_independent_cross_checks",
                }
            ],
            "promotion_requirements": [
                "paper-exact parameters and frozen independent numerical data",
                "convergence evidence",
                "two distinct passing independent cross-checks",
                "explicit falsification attempt",
                "quantified discrepancy against a strict paper reference",
                "fresh-context protocol-v2 review",
            ],
        },
    }


def aggregate_campaign(
    config_path: Path,
    *,
    output_root_override: Path | None = None,
) -> dict[str, Any]:
    """Require all shards, aggregate frozen tables, and apply target gates."""

    config_path = config_path.resolve()
    config = load_paper_scale_config(config_path)
    workspace = config_path.parents[1]
    output_root = (
        output_root_override.resolve()
        if output_root_override is not None
        else _safe_output_root(workspace, str(config["output_root"]))
    )
    jobs = plan_jobs(config)
    results, markers = _load_complete_results(config, output_root)
    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    kappa = float(config["parameters"]["kappa"])

    _aggregate_dynamics(
        jobs,
        results,
        data_dir,
        kappa=kappa,
        paper_sizes=config["families"]["dynamics"]["paper_finite_N"],
        fourier_maximum=float(config["families"]["dynamics"]["fourier_maximum"]),
        profile=str(config["profile"]),
    )
    _aggregate_spectra(
        jobs, results, data_dir, kappa=kappa, profile=str(config["profile"])
    )
    _aggregate_steady_state(jobs, results, data_dir, profile=str(config["profile"]))
    _aggregate_phase_space(jobs, results, data_dir, profile=str(config["profile"]))

    acceptance = _target_acceptance(config, jobs, results, data_dir)
    _atomic_json(checks_dir / "paper_scale_acceptance.json", acceptance)
    parity = _metadata_from_result(results["parity__cpu"])
    _atomic_json(checks_dir / "backend_parity.json", parity)
    _atomic_json(
        checks_dir / "machine_contract.json",
        {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "run_id": config["run_id"],
            "profile": config["profile"],
            "declared": config["resource_contract"],
            "observed_aggregation_machine": _machine_snapshot(),
            "job_machine_snapshots": [marker["machine"] for marker in markers],
        },
    )
    _atomic_json(
        checks_dir / "run_summary.json",
        {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "run_id": config["run_id"],
            "profile": config["profile"],
            "status": acceptance["status"],
            "config_hash": config_fingerprint(config),
            "implementation_hash": implementation_fingerprint(),
            "jobs_total": len(jobs),
            "jobs_complete": len(markers),
            "elapsed_seconds_sum": float(
                sum(float(marker["elapsed_seconds"]) for marker in markers)
            ),
            "source_pixels_read": False,
            "author_code_used": False,
            "author_arrays_used": False,
            "final_run_boundary": config["resource_contract"]["unexecuted_boundary"],
        },
    )
    _atomic_json(output_root / "config_snapshot.json", config)

    manifest_files = sorted(data_dir.glob("*.csv")) + sorted(checks_dir.glob("*.json"))
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "profile": config["profile"],
        "status": acceptance["status"],
        "frozen": True,
        "generated_data_provenance": "independent_numerics",
        "source_pixels_read": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "config_hash": config_fingerprint(config),
        "implementation_hash": implementation_fingerprint(),
        "files": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": _sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in manifest_files
        ],
    }
    _atomic_json(output_root / "manifest.json", manifest)
    if acceptance["status"] != "passed":
        raise RuntimeError("paper-scale target acceptance failed")
    return {"acceptance": acceptance, "manifest": manifest}
