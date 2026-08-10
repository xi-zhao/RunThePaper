r"""Checkpointable paper-scale campaign for arXiv:1812.05561.

The reduced reproduction is deliberately retained as a quick independent
feature check.  This module is the separate, code-ready path for every numeric
panel at the paper's stated scale.  It uses only equations and parameters in
the paper/source text; PDFs, source-figure pixels, author arrays and author
code are never numerical inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh, expm_multiply

from .mps_dmrg import (
    DMRGSettings,
    dmrg_ground_and_first_excited,
    open_pxp_mpo,
    schmidt_values,
)
from .scar_reproduction import (
    Bipartition,
    HamiltonianFamily,
    ansatz_couplings,
    fsa_basis,
    harmonic_gap_and_period,
    level_statistics,
    neel_state,
    sector_hamiltonian_sparse,
    sector_neel_vector,
    solve_h0,
    toy_hamiltonian_sparse,
)


TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 10))
FAILURE_ATTRIBUTION_ORDER = (
    "implementation_or_contract_error",
    "numerical_convergence_or_finite_size",
    "missing_or_ambiguous_paper_input",
    "potential_source_or_claim_discrepancy",
)


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(_json_bytes(payload)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary.replace(path)


def _deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_paper_scale_config(path: Path, *, smoke: bool = False) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2 or payload.get("profile") != "paper_scale":
        raise ValueError("paper-scale config must have schema_version=2 and profile=paper_scale")
    missing = sorted(set(TARGET_IDS) - set(payload.get("parameters", {})))
    if missing:
        raise ValueError(f"paper-scale config misses targets: {missing}")
    effective = dict(payload)
    if smoke:
        effective["parameters"] = _deep_merge(
            payload["parameters"], payload.get("smoke_parameters", {})
        )
        effective["run_id"] = f"{payload['run_id']}-smoke"
        effective["output_namespace"] = payload.get("smoke_output_namespace", "paper_scale_smoke")
    effective["smoke"] = bool(smoke)
    effective["config_path"] = path.as_posix()
    effective["config_digest"] = sha256_json(payload)
    validate_paper_parameters(payload["parameters"])
    return effective


def validate_paper_parameters(parameters: Mapping[str, Any]) -> None:
    """Fail before compute if a declared paper lane silently reduces the scale."""

    failures: list[str] = []
    if parameters["T001"]["dynamics_n_sites"] != 32:
        failures.append("T001 dynamics_n_sites must be 32")
    if parameters["T001"]["optimization_n_sites"] != 20 or parameters["T001"]["max_range"] != 10:
        failures.append("T001 optimization must use N=20,R=10")
    if max(parameters["T002"]["flow_sizes"]) != 32:
        failures.append("T002 flow must reach N=32")
    if parameters["T003"]["n_sites"] != 32:
        failures.append("T003 must cover the displayed k=0..32 range")
    if parameters["T004"]["n_sites"] != 60 or parameters["T004"]["ranges"] != list(range(1, 9)):
        failures.append("T004 must use open N=60,R=1..8")
    if parameters["T006"]["sizes"] != [22, 24, 26, 28, 30, 32]:
        failures.append("T006 sizes must be 22..32 by two")
    if parameters["T006"]["m_max"] != 1000:
        failures.append("T006 must reach revival 1000")
    if parameters["T006"]["short_fit"] != [5, 60] or parameters["T006"]["long_fit"] != [200, 1000]:
        failures.append("T006 fit windows must be 5..60 and 200..1000")
    if parameters["T007"]["n_sites"] != 30:
        failures.append("T007 must use N=30")
    if max(parameters["T008"]["sizes"]) != 32:
        failures.append("T008 must reach N=32")
    if parameters["T009"]["n_sites"] != 14:
        failures.append("T009 must use N=14")
    if not parameters["T009"].get("author_seed_missing", False):
        failures.append("T009 must disclose that the author realization is unavailable")
    if failures:
        raise ValueError("; ".join(failures))


@dataclass(frozen=True)
class WorkUnit:
    target_id: str
    key: str
    payload: Mapping[str, Any]

    @property
    def slug(self) -> str:
        safe = "".join(character if character.isalnum() or character in "-_" else "_" for character in self.key)
        return f"{self.target_id}_{safe}"


def plan_work_units(parameters: Mapping[str, Any]) -> list[WorkUnit]:
    units = [WorkUnit("T001", "dynamics_and_optimization", {})]
    for n_sites in parameters["T002"]["flow_sizes"]:
        for sector in parameters["T002"]["sectors"]:
            units.append(WorkUnit("T002", f"N{n_sites}_{sector['label']}", {"n_sites": n_sites, **sector}))
    units.append(WorkUnit("T003", f"N{parameters['T003']['n_sites']}", {}))
    for max_range in parameters["T004"]["ranges"]:
        units.append(WorkUnit("T004", f"R{max_range}", {"max_range": max_range}))
    for method in parameters["T005"]["methods"]:
        units.append(WorkUnit("T005", method, {"method": method}))
    for n_sites in parameters["T006"]["sizes"]:
        units.append(WorkUnit("T006", f"N{n_sites}", {"n_sites": n_sites}))
    for variant in parameters["T007"]["variants"]:
        units.append(WorkUnit("T007", variant, {"variant": variant}))
    for n_sites in parameters["T008"]["sizes"]:
        units.append(WorkUnit("T008", f"N{n_sites}", {"n_sites": n_sites}))
    for seed in parameters["T009"]["seeds"]:
        units.append(WorkUnit("T009", f"seed{seed}", {"seed": seed}))
    return units


class Campaign:
    def __init__(self, workspace: Path, config: Mapping[str, Any], resume: bool):
        self.workspace = workspace
        self.config = config
        self.parameters = config["parameters"]
        self.resume = resume
        namespace = str(config["output_namespace"])
        self.output_root = workspace / "outputs" / namespace
        self.unit_root = self.output_root / "units"
        self.checkpoint_root = (
            workspace
            / "outputs"
            / "checkpoints"
            / namespace
            / str(config["config_digest"])[:16]
        )
        self.data_root = self.output_root / "data"
        self.check_root = self.output_root / "checks"
        for directory in (self.unit_root, self.checkpoint_root, self.data_root, self.check_root):
            directory.mkdir(parents=True, exist_ok=True)

    def unit_path(self, unit: WorkUnit) -> Path:
        return self.unit_root / unit.target_id / f"{unit.slug}.npz"

    def checkpoint_directory(self, unit: WorkUnit) -> Path:
        return self.checkpoint_root / unit.target_id / unit.slug

    def unit_complete(self, unit: WorkUnit) -> bool:
        path = self.unit_path(unit)
        if not path.exists():
            return False
        try:
            with np.load(path, allow_pickle=False) as payload:
                return str(payload["config_digest"]) == self.config["config_digest"]
        except Exception:
            return False

    def save_unit(self, unit: WorkUnit, result: Mapping[str, Any]) -> None:
        arrays = {key: value for key, value in result.items()}
        arrays["config_digest"] = np.asarray(self.config["config_digest"])
        arrays["unit_json"] = np.asarray(json.dumps({"key": unit.key, **unit.payload}, sort_keys=True))
        write_npz(self.unit_path(unit), **arrays)

    def load_unit(self, unit: WorkUnit) -> dict[str, np.ndarray]:
        with np.load(self.unit_path(unit), allow_pickle=False) as payload:
            return {key: np.asarray(payload[key]) for key in payload.files}


def _peak_rss_gib() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.uname().sysname == "Darwin":
        return float(value / 1024**3)
    return float(value * 1024 / 1024**3)


def _hermiticity_error(matrix: Any) -> float:
    difference = matrix - matrix.conjugate().transpose()
    return float(np.max(np.abs(difference.data), initial=0.0))


def _initial_neel(family: HamiltonianFamily) -> tuple[np.ndarray, int]:
    index = family.indices[neel_state(family.n_sites)]
    vector = np.zeros(len(family.basis), dtype=np.complex128)
    vector[index] = 1.0
    return vector, index


def _fit_turning_point(gamma: np.ndarray, short_fit: Sequence[int], long_fit: Sequence[int]) -> float:
    short = np.arange(int(short_fit[0]), int(short_fit[1]) + 1)
    long = np.arange(int(long_fit[0]), int(long_fit[1]) + 1)
    selected = np.concatenate((short, long))
    if np.any(~np.isfinite(gamma[selected])) or np.any(gamma[selected] <= 0.0):
        return float("nan")
    slope_short, intercept_short = np.polyfit(np.log(short), np.log(gamma[short]), 1)
    slope_long, intercept_long = np.polyfit(np.log(long), np.log(gamma[long]), 1)
    denominator = slope_short - slope_long
    if abs(denominator) <= 1e-12:
        return float("nan")
    return float(math.exp((intercept_long - intercept_short) / denominator))


def _stream_dynamics(
    matrix: Any,
    family: HamiltonianFamily,
    times: np.ndarray,
    *,
    checkpoint_path: Path,
    resume: bool,
    chunk_points: int,
    entanglement_levels: int,
    compute_entropy: bool,
) -> dict[str, np.ndarray]:
    """Stream Krylov states and persist the current vector after each chunk."""

    initial, initial_index = _initial_neel(family)
    fidelity = np.full(len(times), np.nan)
    entropy = np.full(len(times), np.nan)
    spectrum = np.full((len(times), entanglement_levels), np.nan)
    next_index = 1
    state = initial
    if resume and checkpoint_path.exists():
        with np.load(checkpoint_path, allow_pickle=False) as payload:
            state = np.asarray(payload["state"])
            next_index = int(payload["next_index"])
            fidelity = np.asarray(payload["fidelity"])
            entropy = np.asarray(payload["entropy"])
            spectrum = np.asarray(payload["spectrum"])
    partition = Bipartition.from_basis(family.basis, family.n_sites) if compute_entropy else None
    if not (resume and checkpoint_path.exists()):
        if abs(float(times[0])) > 1e-15:
            state = expm_multiply(-1j * matrix * float(times[0]), initial, traceA=0.0)
        fidelity[0] = float(np.clip(abs(state[initial_index]) ** 2, 0.0, 1.0))
        if partition is not None:
            probabilities = partition.schmidt_probabilities(state)
            positive = probabilities[probabilities > 1e-15]
            entropy[0] = float(-np.sum(positive * np.log(positive)))
            spectrum[0, :] = 0.0
            spectrum[0, : min(entanglement_levels, len(probabilities))] = probabilities[
                :entanglement_levels
            ]
    while next_index < len(times):
        stop_index = min(len(times), next_index + chunk_points)
        count = stop_index - next_index
        start_time = times[next_index - 1]
        relative_stop = float(times[stop_index - 1] - start_time)
        states = expm_multiply(
            -1j * matrix,
            state,
            start=0.0,
            stop=relative_stop,
            num=count + 1,
            endpoint=True,
            traceA=0.0,
        )
        for offset, evolved in enumerate(states[1:]):
            index = next_index + offset
            fidelity[index] = float(np.clip(abs(evolved[initial_index]) ** 2, 0.0, 1.0))
            if partition is not None:
                probabilities = partition.schmidt_probabilities(evolved)
                positive = probabilities[probabilities > 1e-15]
                entropy[index] = float(-np.sum(positive * np.log(positive)))
                spectrum[index, :] = 0.0
                take = min(entanglement_levels, len(probabilities))
                spectrum[index, :take] = probabilities[:take]
        state = np.asarray(states[-1])
        next_index = stop_index
        write_npz(
            checkpoint_path,
            state=state,
            next_index=next_index,
            fidelity=fidelity,
            entropy=entropy,
            spectrum=spectrum,
        )
    return {"fidelity": fidelity, "entropy": entropy, "spectrum": spectrum}


def _checkpointed_coupling_optimization(
    family: HamiltonianFamily,
    h0: float,
    tau: float,
    config: Mapping[str, Any],
    checkpoint_path: Path,
    resume: bool,
) -> dict[str, Any]:
    distances = np.asarray(family.distances, dtype=np.int64)
    analytic = ansatz_couplings(h0, int(distances[-1]))
    initial = np.asarray([analytic[int(distance)] for distance in distances] + [tau])
    history: list[list[float]] = []
    if resume and checkpoint_path.exists():
        with np.load(checkpoint_path, allow_pickle=False) as payload:
            initial = np.asarray(payload["last_parameters"])
            history = np.asarray(payload["history"]).tolist()
            if bool(payload["completed"]):
                return {
                    "distances": distances,
                    "optimized": initial[:-1],
                    "ansatz": np.asarray([analytic[int(distance)] for distance in distances]),
                    "revival_time": float(initial[-1]),
                    "infidelity": float(payload["infidelity"]),
                    "nfev": int(payload["nfev"]),
                    "success": bool(payload["success"]),
                }
    initial_state, initial_index = _initial_neel(family)
    evaluations = 0

    def objective(values: np.ndarray) -> float:
        nonlocal evaluations
        evaluations += 1
        physical = values[:-1]
        revival_time = float(values[-1])
        if np.any(np.abs(physical) > 0.2) or not 3.5 <= revival_time <= 6.0:
            return 1.0 + float(np.sum(np.maximum(np.abs(physical) - 0.2, 0.0) ** 2))
        couplings = {int(distance): float(value) for distance, value in zip(distances, physical)}
        evolved = expm_multiply(
            -1j * family.matrix(couplings) * revival_time,
            initial_state,
            traceA=0.0,
        )
        return float(1.0 - abs(evolved[initial_index]) ** 2)

    def callback(values: np.ndarray) -> None:
        history.append(np.asarray(values).tolist())
        write_npz(
            checkpoint_path,
            last_parameters=np.asarray(values),
            history=np.asarray(history),
            completed=False,
            infidelity=np.nan,
            nfev=evaluations,
            success=False,
        )

    result = minimize(
        objective,
        initial,
        method="Nelder-Mead",
        callback=callback,
        options={
            "maxiter": int(config["optimization_maxiter"]),
            "adaptive": True,
            "xatol": float(config["optimization_xatol"]),
            "fatol": float(config["optimization_fatol"]),
        },
    )
    write_npz(
        checkpoint_path,
        last_parameters=np.asarray(result.x),
        history=np.asarray(history),
        completed=True,
        infidelity=float(result.fun),
        nfev=int(result.nfev),
        success=bool(result.success),
    )
    return {
        "distances": distances,
        "optimized": np.asarray(result.x[:-1]),
        "ansatz": np.asarray([analytic[int(distance)] for distance in distances]),
        "revival_time": float(result.x[-1]),
        "infidelity": float(result.fun),
        "nfev": int(result.nfev),
        "success": bool(result.success),
    }


def run_t001(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T001"]
    h0 = solve_h0()
    _, tau = harmonic_gap_and_period(h0)
    optimization_family = HamiltonianFamily.build(
        int(config["optimization_n_sites"]), periodic=True, max_range=int(config["max_range"])
    )
    checkpoint_dir = campaign.checkpoint_directory(unit)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    optimization = _checkpointed_coupling_optimization(
        optimization_family,
        h0,
        tau,
        config,
        checkpoint_dir / "optimization.npz",
        campaign.resume,
    )

    n_sites = int(config["dynamics_n_sites"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    couplings = ansatz_couplings(h0, n_sites // 2)
    matrices = {"pxp": family.matrix({}), "deformed": family.matrix(couplings)}
    times = np.linspace(0.0, float(config["time_max"]), int(config["time_points"]))
    payloads: dict[str, dict[str, np.ndarray]] = {}
    for name, matrix in matrices.items():
        payloads[name] = _stream_dynamics(
            matrix,
            family,
            times,
            checkpoint_path=checkpoint_dir / f"{name}_dynamics.npz",
            resume=campaign.resume,
            chunk_points=int(config["time_chunk_points"]),
            entanglement_levels=int(config["entanglement_levels"]),
            compute_entropy=True,
        )
    inset_times = np.linspace(
        float(config["inset_time_window"][0]),
        float(config["inset_time_window"][1]),
        int(config["inset_time_points"]),
    )
    inset = _stream_dynamics(
        matrices["deformed"],
        family,
        inset_times,
        checkpoint_path=checkpoint_dir / "inset.npz",
        resume=campaign.resume,
        chunk_points=int(config["time_chunk_points"]),
        entanglement_levels=1,
        compute_entropy=False,
    )
    return {
        "times": times,
        "fidelity_pxp": payloads["pxp"]["fidelity"],
        "fidelity_deformed": payloads["deformed"]["fidelity"],
        "entropy_pxp": payloads["pxp"]["entropy"],
        "entropy_deformed": payloads["deformed"]["entropy"],
        "entanglement_spectrum": payloads["deformed"]["spectrum"],
        "inset_times": inset_times,
        "inset_infidelity": 1.0 - inset["fidelity"],
        "distances": optimization["distances"],
        "optimized_couplings": optimization["optimized"],
        "ansatz_couplings": optimization["ansatz"],
        "optimized_revival_time": optimization["revival_time"],
        "optimized_infidelity": optimization["infidelity"],
        "optimization_nfev": optimization["nfev"],
        "optimization_success": optimization["success"],
        "n_sites": n_sites,
        "optimization_n_sites": optimization_family.n_sites,
        "basis_dimension": len(family.basis),
        "hermiticity_error": max(_hermiticity_error(matrix) for matrix in matrices.values()),
        "derived_h0": h0,
        "derived_tau": tau,
    }


def _dense_sector_eigensystem(
    family: HamiltonianFamily,
    couplings: Mapping[int, float],
    *,
    momentum: int,
    inversion: int,
    vectors: bool,
    allocated_memory_gib: float,
) -> tuple[np.ndarray, np.ndarray | None, Any, float, float]:
    projected, transform = sector_hamiltonian_sparse(
        family, couplings, momentum=momentum, inversion=inversion
    )
    hermiticity = _hermiticity_error(projected)
    dimension = projected.shape[0]
    # Matrix + eigenvectors + conservative LAPACK workspace allowance.
    multiplier = 4.5 if vectors else 2.5
    estimate_gib = multiplier * dimension * dimension * 8.0 / 1024**3
    if estimate_gib > allocated_memory_gib:
        raise MemoryError(
            f"sector dimension {dimension} estimates {estimate_gib:.1f} GiB, "
            f"above declared allocation {allocated_memory_gib:.1f} GiB"
        )
    dense = np.asarray(projected.toarray())
    if vectors:
        energies, eigenvectors = eigh(
            dense,
            overwrite_a=True,
            check_finite=False,
            driver="evd",
        )
        return energies, eigenvectors, transform, estimate_gib, hermiticity
    energies = eigh(
        dense,
        eigvals_only=True,
        overwrite_a=True,
        check_finite=False,
        driver="evd",
    )
    return energies, None, transform, estimate_gib, hermiticity


def run_t002(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T002"]
    n_sites = int(unit.payload["n_sites"])
    momentum = int(unit.payload["momentum"])
    inversion = int(unit.payload["inversion"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    couplings = ansatz_couplings(solve_h0(), n_sites // 2)
    need_vectors = n_sites == max(config["flow_sizes"]) and momentum == 0 and inversion == 1
    energies, eigenvectors, transform, estimate, hermiticity = _dense_sector_eigensystem(
        family,
        couplings,
        momentum=momentum,
        inversion=inversion,
        vectors=need_vectors,
        allocated_memory_gib=float(config["allocated_memory_gib"]),
    )
    unfolded, ratios, mean_r = level_statistics(energies)
    overlaps = np.asarray([], dtype=np.float64)
    if eigenvectors is not None:
        neel = sector_neel_vector(transform, family)
        overlaps = np.abs(neel @ eigenvectors) ** 2
    return {
        "n_sites": n_sites,
        "momentum": momentum,
        "inversion": inversion,
        "sector_dimension": len(energies),
        "energies": energies,
        "unfolded_spacings": unfolded,
        "adjacent_ratios": ratios,
        "mean_r": mean_r,
        "overlaps": overlaps,
        "memory_estimate_gib": estimate,
        "hermiticity_error": hermiticity,
    }


def _streaming_fsa(
    family: HamiltonianFamily,
    couplings: Mapping[int, float],
    checkpoint_path: Path,
    resume: bool,
) -> dict[str, np.ndarray | float]:
    """FSA diagnostics with one layer vector, not a ``dimension x (N+1)`` array."""

    plus = family.plus_matrix(couplings)
    minus = plus.transpose().tocsr()
    beta = np.zeros(family.n_sites + 1)
    hz_expectation = np.full(family.n_sites + 1, np.nan)
    hz_sigma = np.full(family.n_sites + 1, np.nan)
    vector = np.zeros(len(family.basis), dtype=np.float64)
    vector[family.indices[neel_state(family.n_sites)]] = 1.0
    next_k = 0
    if resume and checkpoint_path.exists():
        with np.load(checkpoint_path, allow_pickle=False) as payload:
            vector = np.asarray(payload["vector"])
            next_k = int(payload["next_k"])
            beta = np.asarray(payload["beta"])
            hz_expectation = np.asarray(payload["hz_expectation"])
            hz_sigma = np.asarray(payload["hz_sigma"])
    while next_k <= family.n_sites:
        hz_vector = plus @ (minus @ vector) - minus @ (plus @ vector)
        expectation = float(vector @ hz_vector)
        hz_expectation[next_k] = expectation
        hz_sigma[next_k] = float(np.linalg.norm(hz_vector - expectation * vector))
        if next_k < family.n_sites:
            candidate = plus @ vector
            beta[next_k + 1] = np.linalg.norm(candidate)
            if beta[next_k + 1] <= 1e-14:
                raise RuntimeError(f"FSA terminated before k=N at k={next_k}")
            vector = candidate / beta[next_k + 1]
        next_k += 1
        write_npz(
            checkpoint_path,
            vector=vector,
            next_k=next_k,
            beta=beta,
            hz_expectation=hz_expectation,
            hz_sigma=hz_sigma,
        )
    k_values = np.arange(family.n_sites, dtype=np.float64)
    su2_shape = np.sqrt((family.n_sites - k_values) * (k_values + 1.0))
    scale = float(np.dot(beta[1:], su2_shape) / np.dot(su2_shape, su2_shape))
    spacing = np.diff(hz_expectation)
    return {
        "k": np.arange(family.n_sites + 1),
        "beta": beta,
        "su2_beta": np.concatenate(([0.0], scale * su2_shape)),
        "su2_scale": scale,
        "hz_expectation": hz_expectation,
        "hz_sigma": hz_sigma,
        "hz_spacing": spacing,
        "spacing_mean": float(np.mean(spacing)),
        "spacing_relative_std": float(np.std(spacing) / abs(np.mean(spacing))),
        "beta_relative_rms": float(
            np.linalg.norm(beta[1:] - scale * su2_shape) / np.linalg.norm(scale * su2_shape)
        ),
    }


def run_t003(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    n_sites = int(campaign.parameters["T003"]["n_sites"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    result = _streaming_fsa(
        family,
        ansatz_couplings(solve_h0(), n_sites // 2),
        campaign.checkpoint_directory(unit) / "fsa.npz",
        campaign.resume,
    )
    return {**result, "n_sites": n_sites, "basis_dimension": len(family.basis)}


def run_t004(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T004"]
    n_sites = int(config["n_sites"])
    max_range = int(unit.payload["max_range"])
    couplings = {} if max_range == 1 else ansatz_couplings(solve_h0(), max_range)
    mpo = open_pxp_mpo(n_sites, couplings, compress_cutoff=float(config["mpo_compress_cutoff"]))
    settings = DMRGSettings(
        max_bond=int(config["max_bond"]),
        singular_value_cutoff=float(config["singular_value_cutoff"]),
        energy_tolerance=float(config["energy_tolerance"]),
        local_tolerance=float(config["local_tolerance"]),
        local_max_iterations=int(config["local_max_iterations"]),
        minimum_sweeps=int(config["minimum_sweeps"]),
        maximum_sweeps=int(config["maximum_sweeps"]),
        excited_state_penalty=float(config["excited_state_penalty"]),
        seed=int(config["seed"]) + max_range * 10,
    )
    ground, excited = dmrg_ground_and_first_excited(
        mpo,
        settings,
        checkpoint_directory=campaign.checkpoint_directory(unit) / "dmrg",
        resume=campaign.resume,
    )
    ground_singular = schmidt_values(ground.mps, n_sites // 2)
    excited_singular = schmidt_values(excited.mps, n_sites // 2)
    return {
        "n_sites": n_sites,
        "max_range": max_range,
        "ground_energy": ground.energy,
        "first_excited_energy": excited.energy,
        "gap": excited.energy - ground.energy,
        "ground_singular": ground_singular[: int(config["reported_singular_values"])],
        "first_singular": excited_singular[: int(config["reported_singular_values"])],
        "ground_tail_after_two": float(np.sum(ground_singular[2:] ** 2)),
        "first_tail_after_four": float(np.sum(excited_singular[4:] ** 2)),
        "ground_converged": ground.converged,
        "first_converged": excited.converged,
        "ground_energy_change": ground.energy_change,
        "first_energy_change": excited.energy_change,
        "maximum_local_residual": max(
            ground.maximum_local_residual, excited.maximum_local_residual
        ),
        "maximum_discarded_weight": max(
            ground.maximum_discarded_weight, excited.maximum_discarded_weight
        ),
        "ground_first_overlap": excited.overlap_with_penalized_state,
        "ground_sweeps": ground.sweeps,
        "first_sweeps": excited.sweeps,
        "maximum_mpo_bond": max(tensor.shape[1] for tensor in mpo),
    }


def _fsa_cost_bundle(family: HamiltonianFamily, values: np.ndarray) -> dict[str, float]:
    couplings = {distance: float(value) for distance, value in zip(family.distances, values)}
    hamiltonian = family.matrix(couplings)
    vectors, _, plus = fsa_basis(family, couplings)
    minus = plus.transpose().tocsr()
    backwards = minus @ vectors[:, 2]
    projection = float(vectors[:, 1] @ backwards)
    fsa_error = float(np.linalg.norm(backwards - projection * vectors[:, 1]) ** 2)
    projected = vectors.transpose() @ hamiltonian @ vectors
    residual = hamiltonian @ vectors - vectors @ projected
    subspace_variance = float(np.linalg.norm(residual) ** 2)
    ritz = np.linalg.eigvalsh(projected)
    coordinate = np.arange(len(ritz), dtype=np.float64)
    fit = np.polyfit(coordinate, ritz, 1)
    ritz_error = float(np.sqrt(np.mean((ritz - np.polyval(fit, coordinate)) ** 2)))
    return {"fsa": fsa_error, "trvar": subspace_variance, "rvals": ritz_error}


def run_t005(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T005"]
    method = str(unit.payload["method"])
    n_sites = int(config["n_sites"])
    max_range = int(config["max_range"])
    h0 = solve_h0()
    _, tau = harmonic_gap_and_period(h0)
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=max_range)
    distances = np.asarray(family.distances)
    analytic = ansatz_couplings(h0, max_range)
    initial = np.asarray([analytic[int(distance)] for distance in distances])
    initial_state, initial_index = _initial_neel(family)
    checkpoint_path = campaign.checkpoint_directory(unit) / "optimizer.npz"
    history: list[list[float]] = []
    period_initial = tau
    if campaign.resume and checkpoint_path.exists():
        with np.load(checkpoint_path, allow_pickle=False) as payload:
            previous = np.asarray(payload["last_parameters"])
            history = np.asarray(payload["history"]).tolist()
            if method == "fid":
                initial, period_initial = previous[:-1], float(previous[-1])
            else:
                initial = previous
            if bool(payload["completed"]):
                couplings = previous[:-1] if method == "fid" else previous
                return {
                    "method": method,
                    "n_sites": n_sites,
                    "max_range": max_range,
                    "distances": distances,
                    "couplings": couplings,
                    "period": float(previous[-1]) if method == "fid" else tau,
                    "objective": float(payload["objective"]),
                    "success": bool(payload["success"]),
                    "nfev": int(payload["nfev"]),
                    "ansatz": np.asarray([analytic[int(distance)] for distance in distances]),
                }

    def penalty(values: np.ndarray) -> float:
        excess = np.maximum(np.abs(values) - 0.2, 0.0)
        return float(1e3 * np.sum(excess * excess))

    def fidelity_objective(values: np.ndarray) -> float:
        physical = values[:-1]
        period = float(values[-1])
        if not 3.5 <= period <= 6.0:
            return 1.0 + abs(period - np.clip(period, 3.5, 6.0))
        couplings = {int(distance): float(value) for distance, value in zip(distances, physical)}
        evolved = expm_multiply(
            -1j * family.matrix(couplings) * period, initial_state, traceA=0.0
        )
        return float(1.0 - abs(evolved[initial_index]) ** 2 + penalty(physical))

    if method == "fid":
        objective: Callable[[np.ndarray], float] = fidelity_objective
        optimizer_initial = np.concatenate((initial, [period_initial]))
    elif method in ("fsa", "trvar", "rvals"):
        objective = lambda values: _fsa_cost_bundle(family, values)[method] + penalty(values)
        optimizer_initial = initial
    else:
        raise ValueError(f"unknown T005 optimization method: {method}")

    def callback(values: np.ndarray) -> None:
        history.append(np.asarray(values).tolist())
        write_npz(
            checkpoint_path,
            last_parameters=np.asarray(values),
            history=np.asarray(history),
            completed=False,
            objective=np.nan,
            success=False,
            nfev=-1,
        )

    result = minimize(
        objective,
        optimizer_initial,
        method="Nelder-Mead",
        callback=callback,
        options={
            "maxiter": int(config["optimization_maxiter"]),
            "adaptive": True,
            "xatol": float(config["optimization_xatol"]),
            "fatol": float(config["optimization_fatol"]),
        },
    )
    write_npz(
        checkpoint_path,
        last_parameters=np.asarray(result.x),
        history=np.asarray(history),
        completed=True,
        objective=float(result.fun),
        success=bool(result.success),
        nfev=int(result.nfev),
    )
    physical = result.x[:-1] if method == "fid" else result.x
    return {
        "method": method,
        "n_sites": n_sites,
        "max_range": max_range,
        "distances": distances,
        "couplings": np.asarray(physical),
        "period": float(result.x[-1]) if method == "fid" else tau,
        "objective": float(result.fun),
        "success": bool(result.success),
        "nfev": int(result.nfev),
        "ansatz": np.asarray([analytic[int(distance)] for distance in distances]),
    }


def _local_revival_peaks(
    family: HamiltonianFamily,
    matrix: Any,
    tau: float,
    config: Mapping[str, Any],
    checkpoint_path: Path,
    resume: bool,
) -> dict[str, np.ndarray]:
    initial, initial_index = _initial_neel(family)
    m_max = int(config["m_max"])
    peak_times = np.full(m_max + 1, np.nan)
    fidelities = np.full(m_max + 1, np.nan)
    peak_times[0] = 0.0
    fidelities[0] = 1.0
    state = initial
    next_m = 1
    accumulated_time = 0.0
    if resume and checkpoint_path.exists():
        with np.load(checkpoint_path, allow_pickle=False) as payload:
            state = np.asarray(payload["state"])
            next_m = int(payload["next_m"])
            accumulated_time = float(payload["accumulated_time"])
            peak_times = np.asarray(payload["peak_times"])
            fidelities = np.asarray(payload["fidelities"])
    samples = int(config["local_peak_samples"])
    if samples < 3 or samples % 2 == 0:
        raise ValueError("local_peak_samples must be an odd integer >=3")
    while next_m <= m_max:
        center = tau
        half_width = float(config["local_peak_half_width"])
        best_state: np.ndarray | None = None
        best_delta = center
        best_fidelity = -1.0
        for _ in range(int(config["local_peak_refinement_levels"])):
            relative_times = np.linspace(center - half_width, center + half_width, samples)
            candidates = expm_multiply(
                -1j * matrix,
                state,
                start=float(relative_times[0]),
                stop=float(relative_times[-1]),
                num=samples,
                endpoint=True,
                traceA=0.0,
            )
            candidate_fidelity = np.clip(
                np.abs(candidates[:, initial_index]) ** 2, 0.0, 1.0
            )
            best = int(np.argmax(candidate_fidelity))
            best_state = np.asarray(candidates[best])
            best_delta = float(relative_times[best])
            best_fidelity = float(candidate_fidelity[best])
            spacing = float(relative_times[1] - relative_times[0])
            center = best_delta
            half_width = spacing
        assert best_state is not None
        state = best_state
        accumulated_time += best_delta
        peak_times[next_m] = accumulated_time
        fidelities[next_m] = best_fidelity
        next_m += 1
        if (
            (next_m - 1) % int(config["checkpoint_every_revivals"]) == 0
            or next_m > m_max
        ):
            write_npz(
                checkpoint_path,
                state=state,
                next_m=next_m,
                accumulated_time=accumulated_time,
                peak_times=peak_times,
                fidelities=fidelities,
            )
    return {"peak_times": peak_times, "fidelities": fidelities}


def run_t006(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T006"]
    n_sites = int(unit.payload["n_sites"])
    h0 = solve_h0()
    _, tau = harmonic_gap_and_period(h0)
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    matrix = family.matrix(ansatz_couplings(h0, n_sites // 2))
    peaks = _local_revival_peaks(
        family,
        matrix,
        tau,
        config,
        campaign.checkpoint_directory(unit) / "revivals.npz",
        campaign.resume,
    )
    revival = np.arange(int(config["m_max"]) + 1, dtype=np.float64)
    g_tilde = np.power(np.maximum(peaks["fidelities"], 1e-300), 1.0 / n_sites)
    normalized_infidelity = 1.0 - g_tilde
    gamma = np.full_like(revival, np.nan)
    gamma[1:] = normalized_infidelity[1:] / revival[1:]
    return {
        "n_sites": n_sites,
        "basis_dimension": len(family.basis),
        "revival": revival,
        "peak_times": peaks["peak_times"],
        "fidelities": peaks["fidelities"],
        "normalized_infidelity": normalized_infidelity,
        "gamma": gamma,
        "turning_point": _fit_turning_point(gamma, config["short_fit"], config["long_fit"]),
        "analytic_tau": tau,
        "maximum_peak_grid_spacing": float(
            2.0
            * config["local_peak_half_width"]
            / (config["local_peak_samples"] - 1)
            * (2.0 / (config["local_peak_samples"] - 1))
            ** (config["local_peak_refinement_levels"] - 1)
        ),
    }


def _entropy_columns(
    transform: Any,
    eigenvectors: np.ndarray,
    family: HamiltonianFamily,
    *,
    chunk_size: int,
) -> np.ndarray:
    partition = Bipartition.from_basis(family.basis, family.n_sites)
    entropies = np.empty(eigenvectors.shape[1], dtype=np.float64)
    for start in range(0, eigenvectors.shape[1], chunk_size):
        stop = min(eigenvectors.shape[1], start + chunk_size)
        full = transform @ eigenvectors[:, start:stop]
        for offset in range(stop - start):
            entropies[start + offset] = partition.entropy(full[:, offset])
        del full
    return entropies


def run_t007(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T007"]
    n_sites = int(config["n_sites"])
    variant = str(unit.payload["variant"])
    if variant == "pxp":
        couplings: Mapping[int, float] = {}
    elif variant == "h2_0p02":
        couplings = {2: float(config["range4_h2"])}
    elif variant == "ansatz":
        couplings = ansatz_couplings(solve_h0(), n_sites // 2)
    else:
        raise ValueError(f"unknown T007 variant: {variant}")
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    energies, eigenvectors, transform, estimate, _ = _dense_sector_eigensystem(
        family,
        couplings,
        momentum=0,
        inversion=1,
        vectors=True,
        allocated_memory_gib=float(config["allocated_memory_gib"]),
    )
    assert eigenvectors is not None
    neel = sector_neel_vector(transform, family)
    overlaps = np.abs(neel @ eigenvectors) ** 2
    entropies = _entropy_columns(
        transform,
        eigenvectors,
        family,
        chunk_size=int(config["entropy_chunk_eigenvectors"]),
    )
    return {
        "variant": variant,
        "n_sites": n_sites,
        "sector_dimension": len(energies),
        "energies": energies,
        "overlaps": overlaps,
        "entropies": entropies,
        "memory_estimate_gib": estimate,
    }


def run_t008(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T008"]
    n_sites = int(unit.payload["n_sites"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    partition = Bipartition.from_basis(family.basis, n_sites)
    candidates: list[dict[str, Any]] = []
    sector_dimensions: list[int] = []
    coupling_values = ansatz_couplings(solve_h0(), n_sites // 2)
    for sector in config["sectors"]:
        matrix, transform = sector_hamiltonian_sparse(
            family,
            coupling_values,
            momentum=int(sector["momentum"]),
            inversion=int(sector["inversion"]),
        )
        sector_dimensions.append(matrix.shape[0])
        count = min(int(config["interior_eigenpairs"]), matrix.shape[0] - 2)
        if matrix.shape[0] <= int(config["dense_threshold"]):
            energies, eigenvectors = eigh(np.asarray(matrix.toarray()), check_finite=False)
            order = np.argsort(np.abs(energies - float(config["shift"])))[:count]
            energies, eigenvectors = energies[order], eigenvectors[:, order]
        else:
            energies, eigenvectors = eigsh(
                matrix,
                k=count,
                sigma=float(config["shift"]),
                which="LM",
                tol=float(config["eigensolver_tolerance"]),
                maxiter=int(config["eigensolver_max_iterations"]),
            )
        order = np.argsort(energies)
        energies, eigenvectors = energies[order], eigenvectors[:, order]
        neel = sector_neel_vector(transform, family)
        overlaps = np.abs(neel @ eigenvectors) ** 2
        pool_size = min(int(config["scar_candidate_pool"]), len(energies))
        for index in np.argsort(overlaps)[-pool_size:]:
            candidates.append(
                {
                    "energy": float(energies[index]),
                    "overlap": float(overlaps[index]),
                    "momentum": int(sector["momentum"]),
                    "inversion": int(sector["inversion"]),
                    "vector": np.asarray(eigenvectors[:, index]),
                    "matrix": matrix,
                    "transform": transform,
                }
            )
    selected_rows = sorted(candidates, key=lambda row: abs(row["energy"]))[:2]
    selected_rows.sort(key=lambda row: row["energy"])
    entropies: list[float] = []
    residuals: list[float] = []
    for row in selected_rows:
        full = row["transform"] @ row["vector"]
        entropies.append(partition.entropy(full))
        residuals.append(
            float(np.linalg.norm(row["matrix"] @ row["vector"] - row["energy"] * row["vector"]))
        )
    return {
        "n_sites": n_sites,
        "sector_dimensions": np.asarray(sector_dimensions),
        "candidate_energies": np.asarray([row["energy"] for row in candidates]),
        "candidate_overlaps": np.asarray([row["overlap"] for row in candidates]),
        "candidate_momenta": np.asarray([row["momentum"] for row in candidates]),
        "selected_energies": np.asarray([row["energy"] for row in selected_rows]),
        "selected_overlaps": np.asarray([row["overlap"] for row in selected_rows]),
        "selected_momenta": np.asarray([row["momentum"] for row in selected_rows]),
        "selected_inversions": np.asarray([row["inversion"] for row in selected_rows]),
        "selected_entropies": np.asarray(entropies),
        "selected_residuals": np.asarray(residuals),
    }


def _toy_eigensystem_checkpoint(
    matrix: Any,
    directory: Path,
    *,
    resume: bool,
) -> tuple[np.ndarray, np.ndarray]:
    marker = directory / "eigensystem.json"
    values_path = directory / "eigenvalues.npy"
    vectors_path = directory / "eigenvectors.npy"
    if resume and marker.exists() and values_path.exists() and vectors_path.exists():
        return np.load(values_path), np.load(vectors_path, mmap_mode="r")
    directory.mkdir(parents=True, exist_ok=True)
    dense = np.asarray(matrix.toarray())
    energies, eigenvectors = eigh(dense, overwrite_a=True, check_finite=False, driver="evd")
    np.save(values_path, energies, allow_pickle=False)
    np.save(vectors_path, eigenvectors, allow_pickle=False)
    write_json(
        marker,
        {
            "status": "complete",
            "dimension": len(energies),
            "eigenvalues_sha256": sha256_file(values_path),
            "eigenvectors_sha256": sha256_file(vectors_path),
        },
    )
    return energies, np.load(vectors_path, mmap_mode="r")


def run_t009(campaign: Campaign, unit: WorkUnit) -> dict[str, Any]:
    config = campaign.parameters["T009"]
    n_sites = int(config["n_sites"])
    seed = int(unit.payload["seed"])
    matrix, couplings = toy_hamiltonian_sparse(n_sites, seed, omega=float(config["omega"]))
    dimension = matrix.shape[0]
    estimate = 3.5 * dimension * dimension * 16.0 / 1024**3
    if estimate > float(config["allocated_memory_gib"]):
        raise MemoryError(
            f"toy eigensystem estimates {estimate:.1f} GiB above declared "
            f"{config['allocated_memory_gib']} GiB"
        )
    checkpoint_dir = campaign.checkpoint_directory(unit)
    energies, eigenvectors = _toy_eigensystem_checkpoint(
        matrix, checkpoint_dir, resume=campaign.resume
    )
    polarized_index = (1 << n_sites) - 1
    overlaps = np.abs(eigenvectors[polarized_index, :]) ** 2
    times = np.linspace(0.0, float(config["time_max"]), int(config["time_points"]))
    amplitude = np.exp(-2j * math.pi * np.outer(times, energies)) @ overlaps
    fidelity = np.abs(amplitude) ** 2
    entropy_checkpoint = checkpoint_dir / "entropy.npz"
    entropy = np.full(dimension, np.nan)
    next_index = 0
    if campaign.resume and entropy_checkpoint.exists():
        with np.load(entropy_checkpoint, allow_pickle=False) as payload:
            entropy = np.asarray(payload["entropy"])
            next_index = int(payload["next_index"])
    partition = Bipartition.from_basis(tuple(range(dimension)), n_sites)
    chunk = int(config["entropy_chunk_eigenvectors"])
    while next_index < dimension:
        stop = min(dimension, next_index + chunk)
        for index in range(next_index, stop):
            entropy[index] = partition.entropy(eigenvectors[:, index])
        next_index = stop
        write_npz(entropy_checkpoint, entropy=entropy, next_index=next_index)
    integer_indices = [int(np.argmin(np.abs(times - value))) for value in range(5)]
    return {
        "n_sites": n_sites,
        "dimension": dimension,
        "seed": seed,
        "omega": float(config["omega"]),
        "energies": energies,
        "overlaps": overlaps,
        "times": times,
        "fidelity": fidelity,
        "entropy": entropy,
        "couplings": couplings,
        "hermiticity_error": _hermiticity_error(matrix),
        "minimum_integer_time_fidelity": float(np.min(fidelity[integer_indices])),
        "supported_state_count": int(np.sum(overlaps > float(config["overlap_threshold"]))),
        "memory_estimate_gib": estimate,
        "author_seed_available": False,
    }


RUNNERS: dict[str, Callable[[Campaign, WorkUnit], dict[str, Any]]] = {
    "T001": run_t001,
    "T002": run_t002,
    "T003": run_t003,
    "T004": run_t004,
    "T005": run_t005,
    "T006": run_t006,
    "T007": run_t007,
    "T008": run_t008,
    "T009": run_t009,
}


def _clean_unit_payload(payload: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"config_digest", "unit_json"}
    }


def _aggregate_t002(campaign: Campaign, units: Sequence[WorkUnit]) -> dict[str, Any]:
    config = campaign.parameters["T002"]
    rows = [(unit, campaign.load_unit(unit)) for unit in units]
    labels = [str(item["label"]) for item in config["sectors"]]
    sizes = [int(value) for value in config["flow_sizes"]]
    r_values = np.full((len(labels), len(sizes)), np.nan)
    largest_unfolded: list[np.ndarray] = []
    largest_energies = np.asarray([])
    largest_overlaps = np.asarray([])
    dimensions = np.zeros((len(labels), len(sizes)), dtype=np.int64)
    for unit, payload in rows:
        meta = json.loads(str(payload["unit_json"]))
        label_index = labels.index(str(meta["label"]))
        size_index = sizes.index(int(meta["n_sites"]))
        r_values[label_index, size_index] = float(payload["mean_r"])
        dimensions[label_index, size_index] = int(payload["sector_dimension"])
        if int(meta["n_sites"]) == max(sizes):
            largest_unfolded.append(np.asarray(payload["unfolded_spacings"]))
            if int(meta["momentum"]) == 0 and int(meta["inversion"]) == 1:
                largest_energies = np.asarray(payload["energies"])
                largest_overlaps = np.asarray(payload["overlaps"])
    bins = np.linspace(0.0, float(config["histogram_max"]), int(config["histogram_bins"]) + 1)
    density, edges = np.histogram(np.concatenate(largest_unfolded), bins=bins, density=True)
    centers = 0.5 * (edges[:-1] + edges[1:])
    return {
        "flow_sizes": np.asarray(sizes),
        "sector_labels": np.asarray(labels),
        "mean_r": r_values,
        "sector_dimensions": dimensions,
        "energies": largest_energies,
        "overlaps": largest_overlaps,
        "spacing_centers": centers,
        "spacing_density": density,
        "goe_density": (math.pi / 2.0) * centers * np.exp(-math.pi * centers**2 / 4.0),
        "poisson_density": np.exp(-centers),
    }


def _aggregate_t004(campaign: Campaign, units: Sequence[WorkUnit]) -> dict[str, Any]:
    rows = sorted(
        (campaign.load_unit(unit) for unit in units), key=lambda row: int(row["max_range"])
    )
    return {
        "n_sites": int(rows[0]["n_sites"]),
        "ranges": np.asarray([int(row["max_range"]) for row in rows]),
        "ground_singular": np.asarray([row["ground_singular"] for row in rows]),
        "first_singular": np.asarray([row["first_singular"] for row in rows]),
        "gaps": np.asarray([float(row["gap"]) for row in rows]),
        "ground_tail_after_two": np.asarray(
            [float(row["ground_tail_after_two"]) for row in rows]
        ),
        "first_tail_after_four": np.asarray(
            [float(row["first_tail_after_four"]) for row in rows]
        ),
        "ground_converged": np.asarray([bool(row["ground_converged"]) for row in rows]),
        "first_converged": np.asarray([bool(row["first_converged"]) for row in rows]),
        "maximum_local_residual": np.asarray(
            [float(row["maximum_local_residual"]) for row in rows]
        ),
        "maximum_discarded_weight": np.asarray(
            [float(row["maximum_discarded_weight"]) for row in rows]
        ),
        "ground_first_overlap": np.asarray(
            [float(row["ground_first_overlap"]) for row in rows]
        ),
        "maximum_mpo_bond": np.asarray([int(row["maximum_mpo_bond"]) for row in rows]),
    }


def _aggregate_t005(campaign: Campaign, units: Sequence[WorkUnit]) -> dict[str, Any]:
    config = campaign.parameters["T005"]
    methods = [str(value) for value in config["methods"]]
    by_method = {
        str(campaign.load_unit(unit)["method"]): campaign.load_unit(unit) for unit in units
    }
    couplings = np.asarray([by_method[method]["couplings"] for method in methods])
    distances = np.asarray(by_method[methods[0]]["distances"])
    n_sites = int(config["n_sites"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=int(config["max_range"]))
    _, tau = harmonic_gap_and_period(solve_h0())
    initial, initial_index = _initial_neel(family)
    raw_costs = np.zeros((len(methods), len(methods)))
    for column, values in enumerate(couplings):
        bundle = _fsa_cost_bundle(family, values)
        coupling_map = {int(distance): float(value) for distance, value in zip(distances, values)}
        evolved = expm_multiply(-1j * family.matrix(coupling_map) * tau, initial, traceA=0.0)
        raw_costs[0, column] = 1.0 - abs(evolved[initial_index]) ** 2
        raw_costs[1, column] = bundle["fsa"]
        raw_costs[2, column] = bundle["trvar"]
        raw_costs[3, column] = bundle["rvals"]
    scale = np.maximum(np.max(raw_costs, axis=1, keepdims=True), 1e-300)
    return {
        "n_sites": n_sites,
        "max_range": int(config["max_range"]),
        "methods": np.asarray(methods),
        "distances": distances,
        "coupling_matrix": couplings,
        "ansatz": np.asarray(by_method[methods[0]]["ansatz"]),
        "periods": np.asarray([float(by_method[method]["period"]) for method in methods]),
        "optimizer_success": np.asarray(
            [bool(by_method[method]["success"]) for method in methods]
        ),
        "optimizer_nfev": np.asarray([int(by_method[method]["nfev"]) for method in methods]),
        "raw_costs": raw_costs,
        "normalized_costs": raw_costs / scale,
    }


def _aggregate_t006(campaign: Campaign, units: Sequence[WorkUnit]) -> dict[str, Any]:
    rows = sorted(
        (campaign.load_unit(unit) for unit in units), key=lambda row: int(row["n_sites"])
    )
    return {
        "sizes": np.asarray([int(row["n_sites"]) for row in rows]),
        "revival": rows[0]["revival"],
        "peak_times": np.asarray([row["peak_times"] for row in rows]),
        "fidelities": np.asarray([row["fidelities"] for row in rows]),
        "normalized_infidelity": np.asarray(
            [row["normalized_infidelity"] for row in rows]
        ),
        "gamma": np.asarray([row["gamma"] for row in rows]),
        "turning_points": np.asarray([float(row["turning_point"]) for row in rows]),
        "analytic_tau": float(rows[0]["analytic_tau"]),
        "maximum_peak_grid_spacing": max(
            float(row["maximum_peak_grid_spacing"]) for row in rows
        ),
    }


def _aggregate_t007(campaign: Campaign, units: Sequence[WorkUnit]) -> dict[str, Any]:
    by_variant = {
        str(campaign.load_unit(unit)["variant"]): campaign.load_unit(unit) for unit in units
    }
    result: dict[str, Any] = {"n_sites": int(next(iter(by_variant.values()))["n_sites"])}
    for variant in campaign.parameters["T007"]["variants"]:
        result[f"energies_{variant}"] = by_variant[variant]["energies"]
        result[f"overlaps_{variant}"] = by_variant[variant]["overlaps"]
        result[f"entropies_{variant}"] = by_variant[variant]["entropies"]
    return result


def _aggregate_t008(campaign: Campaign, units: Sequence[WorkUnit]) -> dict[str, Any]:
    rows = sorted(
        (campaign.load_unit(unit) for unit in units), key=lambda row: int(row["n_sites"])
    )
    return {
        "sizes": np.asarray([int(row["n_sites"]) for row in rows]),
        "selected_energies": np.asarray([row["selected_energies"] for row in rows]),
        "selected_overlaps": np.asarray([row["selected_overlaps"] for row in rows]),
        "selected_entropies": np.asarray([row["selected_entropies"] for row in rows]),
        "selected_residuals": np.asarray([row["selected_residuals"] for row in rows]),
        "selected_momenta": np.asarray([row["selected_momenta"] for row in rows]),
        "selected_inversions": np.asarray([row["selected_inversions"] for row in rows]),
    }


def _aggregate_t009(campaign: Campaign, units: Sequence[WorkUnit]) -> dict[str, Any]:
    rows = sorted((campaign.load_unit(unit) for unit in units), key=lambda row: int(row["seed"]))
    return {
        "n_sites": int(rows[0]["n_sites"]),
        "seeds": np.asarray([int(row["seed"]) for row in rows]),
        "energies": np.asarray([row["energies"] for row in rows]),
        "overlaps": np.asarray([row["overlaps"] for row in rows]),
        "times": rows[0]["times"],
        "fidelity": np.asarray([row["fidelity"] for row in rows]),
        "entropy": np.asarray([row["entropy"] for row in rows]),
        "couplings": np.asarray([row["couplings"] for row in rows]),
        "hermiticity_error": np.asarray([float(row["hermiticity_error"]) for row in rows]),
        "minimum_integer_time_fidelity": np.asarray(
            [float(row["minimum_integer_time_fidelity"]) for row in rows]
        ),
        "supported_state_count": np.asarray(
            [int(row["supported_state_count"]) for row in rows]
        ),
        "author_seed_available": False,
    }


AGGREGATE_NAMES = {
    "T001": "T001_main_figure_1.npz",
    "T002": "T002_main_figure_2.npz",
    "T003": "T003_main_figure_3.npz",
    "T004": "T004_supp_figure_s1.npz",
    "T005": "T005_supp_figure_s2.npz",
    "T006": "T006_supp_figure_s3.npz",
    "T007": "T007_supp_figure_s4.npz",
    "T008": "T008_supp_figure_s5.npz",
    "T009": "T009_supp_figure_s6.npz",
}


def aggregate_target(campaign: Campaign, target_id: str, units: Sequence[WorkUnit]) -> dict[str, Any]:
    if target_id in ("T001", "T003"):
        payload = _clean_unit_payload(campaign.load_unit(units[0]))
    elif target_id == "T002":
        payload = _aggregate_t002(campaign, units)
    elif target_id == "T004":
        payload = _aggregate_t004(campaign, units)
    elif target_id == "T005":
        payload = _aggregate_t005(campaign, units)
    elif target_id == "T006":
        payload = _aggregate_t006(campaign, units)
    elif target_id == "T007":
        payload = _aggregate_t007(campaign, units)
    elif target_id == "T008":
        payload = _aggregate_t008(campaign, units)
    elif target_id == "T009":
        payload = _aggregate_t009(campaign, units)
    else:
        raise ValueError(target_id)
    write_npz(campaign.data_root / AGGREGATE_NAMES[target_id], **payload)
    return payload


def _assertion(assertion_id: str, claim: str, passed: bool, observed: Any, criterion: str) -> dict[str, Any]:
    if isinstance(observed, np.ndarray):
        observed = observed.tolist()
    elif isinstance(observed, (np.floating, np.integer, np.bool_)):
        observed = observed.item()
    return {
        "assertion_id": assertion_id,
        "claim": claim,
        "status": "passed" if passed else "failed",
        "observed": observed,
        "criterion": criterion,
        "tier": "numeric",
        "essential": True,
    }


def _r_squared(x_values: np.ndarray, y_values: np.ndarray) -> float:
    fit = np.polyfit(x_values, y_values, 1)
    residual = y_values - np.polyval(fit, x_values)
    denominator = np.sum((y_values - np.mean(y_values)) ** 2)
    return float(1.0 - np.sum(residual**2) / max(denominator, 1e-30))


def target_assertions(
    target_id: str,
    payload: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    smoke: bool,
) -> list[dict[str, Any]]:
    if smoke:
        finite = all(
            np.all(np.isfinite(value))
            for key, value in payload.items()
            if isinstance(value, np.ndarray)
            and value.dtype.kind in "fc"
            and key not in {"gamma", "turning_points"}
        )
        assertions = [
            _assertion(
                f"{target_id}-SMOKE",
                "The target's small-scale execution produces finite structured outputs.",
                finite,
                finite,
                "all non-rate floating outputs are finite",
            )
        ]
        if target_id == "T004":
            converged = bool(np.all(payload["ground_converged"])) and bool(
                np.all(payload["first_converged"])
            )
            assertions.append(
                _assertion(
                    "T004-SMOKE-DMRG",
                    "Checkpointable DMRG converges for the exact-test scale.",
                    converged,
                    converged,
                    "ground and first excited states converge",
                )
            )
        if target_id == "T008":
            maximum = float(np.max(payload["selected_residuals"]))
            assertions.append(
                _assertion(
                    "T008-SMOKE-RES",
                    "Interior eigenpairs satisfy the sparse eigen-equation.",
                    maximum < 1e-7,
                    maximum,
                    "maximum residual < 1e-7",
                )
            )
        if target_id == "T009":
            expected = int(payload["n_sites"]) + 1
            observed = np.asarray(payload["supported_state_count"])
            assertions.append(
                _assertion(
                    "T009-SMOKE-SCAR",
                    "The independent toy realization has exactly N+1 supported scar states.",
                    bool(np.all(observed == expected)),
                    observed,
                    f"every seed has {expected} supported states",
                )
            )
        return assertions

    acceptance = config["acceptance"][target_id]
    if target_id == "T001":
        minimum_infidelity = float(np.nanmin(payload["inset_infidelity"]))
        correlation = float(
            np.corrcoef(payload["optimized_couplings"], payload["ansatz_couplings"])[0, 1]
        )
        return [
            _assertion("T001-SCALE", "Main Figure 1 dynamics use N=32 and optimization uses N=20.", int(payload["n_sites"]) == 32 and int(payload["optimization_n_sites"]) == 20, [int(payload["n_sites"]), int(payload["optimization_n_sites"])], "equals [32,20]"),
            _assertion("T001-H", "Both generated Hamiltonians are Hermitian.", float(payload["hermiticity_error"]) <= acceptance["maximum_hermiticity_error"], float(payload["hermiticity_error"]), f"<= {acceptance['maximum_hermiticity_error']}"),
            _assertion("T001-R", "The optimized ansatz gives the paper-scale near-perfect first revival.", minimum_infidelity <= acceptance["maximum_first_revival_infidelity"], minimum_infidelity, f"minimum local infidelity <= {acceptance['maximum_first_revival_infidelity']}"),
            _assertion("T001-C", "Numerically optimized couplings follow the analytic ansatz.", correlation >= acceptance["minimum_ansatz_correlation"], correlation, f">= {acceptance['minimum_ansatz_correlation']}"),
        ]
    if target_id == "T002":
        largest_index = int(np.argmax(payload["flow_sizes"]))
        largest_r = np.asarray(payload["mean_r"])[:, largest_index]
        closest_goe = bool(np.all(np.abs(largest_r - 0.5307) < np.abs(largest_r - 0.3863)))
        overlaps = np.asarray(payload["overlaps"])
        isolation = float(np.max(overlaps) / max(np.median(overlaps), 1e-300))
        return [
            _assertion("T002-SCALE", "The level-statistics flow and spectral-overlap panel reach N=32.", int(np.max(payload["flow_sizes"])) == 32, int(np.max(payload["flow_sizes"])), "largest N equals 32"),
            _assertion("T002-GOE", "Both resolved sectors are closer to GOE than Poisson at N=32.", closest_goe, largest_r, "|r-0.5307| < |r-0.3863| in both sectors"),
            _assertion("T002-SCAR", "A separated scar band dominates Neel spectral weight.", isolation >= acceptance["minimum_top_to_median_overlap"], isolation, f">= {acceptance['minimum_top_to_median_overlap']}"),
        ]
    if target_id == "T003":
        return [
            _assertion("T003-SCALE", "The FSA recursion covers k=0..32.", int(payload["n_sites"]) == 32 and len(payload["k"]) == 33, [int(payload["n_sites"]), len(payload["k"])], "N=32 and 33 FSA layers"),
            _assertion("T003-B", "FSA raising elements follow the spin-16 SU(2) law.", float(payload["beta_relative_rms"]) <= acceptance["maximum_beta_relative_rms"], float(payload["beta_relative_rms"]), f"<= {acceptance['maximum_beta_relative_rms']}"),
            _assertion("T003-Z", "H-z expectation spacings are nearly harmonic.", float(payload["spacing_relative_std"]) <= acceptance["maximum_spacing_relative_std"], float(payload["spacing_relative_std"]), f"<= {acceptance['maximum_spacing_relative_std']}"),
        ]
    if target_id == "T004":
        gaps = np.asarray(payload["gaps"])
        predicted_gap = 1.29294
        last_error = float(abs(gaps[-1] - predicted_gap) / predicted_gap)
        convergence = bool(np.all(payload["ground_converged"])) and bool(np.all(payload["first_converged"]))
        residual = float(np.max(payload["maximum_local_residual"]))
        overlap = float(np.max(payload["ground_first_overlap"]))
        return [
            _assertion("T004-SCALE", "Supplement Figure S1 uses open N=60 and R=1..8.", int(payload["n_sites"]) == 60 and payload["ranges"].tolist() == list(range(1, 9)), [int(payload["n_sites"]), payload["ranges"]], "N=60,R=1..8"),
            _assertion("T004-CONV", "Both DMRG states converge for every range.", convergence and residual <= acceptance["maximum_local_residual"], [convergence, residual], f"all converged and residual <= {acceptance['maximum_local_residual']}"),
            _assertion("T004-ORTH", "The projected first excited state is orthogonal to the ground state.", overlap <= acceptance["maximum_ground_first_overlap"], overlap, f"<= {acceptance['maximum_ground_first_overlap']}"),
            _assertion("T004-GAP", "The R=8 gap approaches the emergent-SU(2) value.", last_error <= acceptance["maximum_gap_relative_error"], last_error, f"<= {acceptance['maximum_gap_relative_error']}"),
        ]
    if target_id == "T005":
        ansatz = np.asarray(payload["ansatz"])
        correlations = np.asarray([np.corrcoef(row, ansatz)[0, 1] for row in payload["coupling_matrix"]])
        self_wins = int(sum(int(np.argmin(payload["raw_costs"][row])) == row for row in range(4)))
        return [
            _assertion("T005-SCALE", "All four printed optimization objectives run at the main-text N=20,R=10 scale inferred by section continuity.", int(payload["n_sites"]) == 20 and int(payload["max_range"]) == 10 and len(payload["methods"]) == 4, [int(payload["n_sites"]), int(payload["max_range"]), len(payload["methods"])], "N=20,R=10,four objectives"),
            _assertion("T005-CONV", "Every Nelder-Mead lane reaches its declared convergence tolerance.", bool(np.all(payload["optimizer_success"])), payload["optimizer_success"], "all optimizer_success are true"),
            _assertion("T005-C", "Each optimum retains the ansatz's decaying coupling pattern.", bool(np.all(correlations >= acceptance["minimum_ansatz_correlation"])), correlations, f"all >= {acceptance['minimum_ansatz_correlation']}"),
            _assertion("T005-X", "Most objective-specific solutions minimize their own cross-evaluated cost.", self_wins >= acceptance["minimum_self_cost_wins"], self_wins, f">= {acceptance['minimum_self_cost_wins']}"),
        ]
    if target_id == "T006":
        gamma = np.asarray(payload["gamma"])
        early = slice(5, 61)
        relative_spread = float(np.nanmedian(np.nanstd(gamma[:, early], axis=0) / np.maximum(np.nanmean(gamma[:, early], axis=0), 1e-300)))
        turning = np.asarray(payload["turning_points"])
        slope = float(np.polyfit(payload["sizes"], turning, 1)[0]) if np.all(np.isfinite(turning)) else float("nan")
        return [
            _assertion("T006-SCALE", "Late-time dynamics cover N=22..32 and m=1..1000.", payload["sizes"].tolist() == [22, 24, 26, 28, 30, 32] and len(payload["revival"]) == 1001, [payload["sizes"], len(payload["revival"])], "sizes 22..32 and 1001 samples including m=0"),
            _assertion("T006-PEAK", "Local revival maxima are resolved more finely than the declared time tolerance.", float(payload["maximum_peak_grid_spacing"]) <= acceptance["maximum_peak_time_spacing"], float(payload["maximum_peak_grid_spacing"]), f"<= {acceptance['maximum_peak_time_spacing']}"),
            _assertion("T006-C", "Early-time intensive rates collapse across system sizes.", relative_spread <= acceptance["maximum_early_gamma_relative_spread"], relative_spread, f"<= {acceptance['maximum_early_gamma_relative_spread']}"),
            _assertion("T006-MC", "Turning points are finite and increase with system size.", np.all(np.isfinite(turning)) and slope > acceptance["minimum_turning_point_slope"], [turning, slope], f"all finite and slope > {acceptance['minimum_turning_point_slope']}"),
        ]
    if target_id == "T007":
        ansatz_overlap = np.asarray(payload["overlaps_ansatz"])
        pxp_overlap = np.asarray(payload["overlaps_pxp"])
        scar_count = min(int(payload["n_sites"]) // 2 + 1, len(ansatz_overlap))
        scar_indices = np.argsort(ansatz_overlap)[-scar_count:]
        bulk_indices = np.argsort(ansatz_overlap)[:scar_count]
        scar_entropy = float(np.mean(np.asarray(payload["entropies_ansatz"])[scar_indices]))
        bulk_entropy = float(np.mean(np.asarray(payload["entropies_ansatz"])[bulk_indices]))
        gain = float((np.max(ansatz_overlap) / max(np.median(ansatz_overlap), 1e-300)) / (np.max(pxp_overlap) / max(np.median(pxp_overlap), 1e-300)))
        return [
            _assertion("T007-SCALE", "All three Supplement Figure S4 clouds use N=30,k=0,inversion-even full spectra.", int(payload["n_sites"]) == 30 and all(f"energies_{variant}" in payload for variant in ("pxp", "h2_0p02", "ansatz")), int(payload["n_sites"]), "N=30 and three variants"),
            _assertion("T007-I", "The ansatz separates scar overlap more strongly than bare PXP.", gain >= acceptance["minimum_overlap_isolation_gain"], gain, f">= {acceptance['minimum_overlap_isolation_gain']}"),
            _assertion("T007-E", "High-overlap ansatz scars are less entangled than the bulk.", scar_entropy < bulk_entropy - acceptance["minimum_entropy_separation"], [scar_entropy, bulk_entropy], f"bulk-scar > {acceptance['minimum_entropy_separation']}"),
        ]
    if target_id == "T008":
        sizes = np.asarray(payload["sizes"], dtype=float)
        entropies = np.asarray(payload["selected_entropies"])
        momenta = np.asarray(payload["selected_momenta"])
        log_r2_values: list[float] = []
        linear_r2_values: list[float] = []
        zero_momentum_counts: list[int] = []
        for column in range(2):
            mask = momenta[:, column] == 0
            zero_momentum_counts.append(int(np.sum(mask)))
            if np.sum(mask) < 3:
                log_r2_values.append(float("nan"))
                linear_r2_values.append(float("nan"))
            else:
                log_r2_values.append(_r_squared(np.log(sizes[mask]), entropies[mask, column]))
                linear_r2_values.append(_r_squared(sizes[mask], entropies[mask, column]))
        log_r2 = np.asarray(log_r2_values)
        linear_r2 = np.asarray(linear_r2_values)
        residual = float(np.max(payload["selected_residuals"]))
        return [
            _assertion("T008-SCALE", "The exact-scar entropy series reaches N=32.", int(np.max(sizes)) == 32, int(np.max(sizes)), "largest N equals 32"),
            _assertion("T008-RES", "Every selected interior eigenpair meets the residual tolerance.", residual <= acceptance["maximum_eigenpair_residual"], residual, f"<= {acceptance['maximum_eigenpair_residual']}"),
            _assertion("T008-LOG", "Caption-filtered zero-momentum logarithmic fits are competitive with or better than volume-law fits for both scar series.", bool(np.all(np.asarray(zero_momentum_counts) >= 3) and np.all(log_r2 + acceptance["log_fit_r2_tolerance"] >= linear_r2)), [zero_momentum_counts, log_r2, linear_r2], f"at least 3 zero-momentum points per series and log R2 + {acceptance['log_fit_r2_tolerance']} >= linear R2"),
        ]
    if target_id == "T009":
        expected = int(payload["n_sites"]) + 1
        return [
            _assertion("T009-SCALE", "Every disclosed independent realization uses N=14 and the paper's Gaussian ensemble.", int(payload["n_sites"]) == 14 and len(payload["seeds"]) >= acceptance["minimum_independent_seeds"], [int(payload["n_sites"]), len(payload["seeds"])], f"N=14 and at least {acceptance['minimum_independent_seeds']} seeds"),
            _assertion("T009-H", "Every toy Hamiltonian is Hermitian.", bool(np.all(payload["hermiticity_error"] <= acceptance["maximum_hermiticity_error"])), payload["hermiticity_error"], f"all <= {acceptance['maximum_hermiticity_error']}"),
            _assertion("T009-R", "Every realization has exact integer-period revival.", bool(np.all(payload["minimum_integer_time_fidelity"] >= 1.0 - acceptance["maximum_integer_time_infidelity"])), payload["minimum_integer_time_fidelity"], f"all >= 1-{acceptance['maximum_integer_time_infidelity']}"),
            _assertion("T009-N", "Every realization has exactly N+1 supported scar states.", bool(np.all(payload["supported_state_count"] == expected)), payload["supported_state_count"], f"all equal {expected}"),
        ]
    raise ValueError(target_id)


def _failure_attribution(target_id: str, assertions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [item for item in assertions if item["status"] == "failed"]
    if not failed:
        return {
            "status": "not_needed",
            "selected_category": None,
            "review_order": list(FAILURE_ATTRIBUTION_ORDER),
        }
    text = " ".join(str(item.get("assertion_id", "")) for item in failed)
    if any(token in text for token in ("CONV", "RES", "ORTH")):
        selected = "numerical_convergence_or_finite_size"
        next_action = "tighten solver convergence and repeat the same parameter point"
    elif target_id == "T009":
        selected = "missing_or_ambiguous_paper_input"
        next_action = "evaluate ensemble invariants across disclosed seeds; do not claim author-point equality"
    else:
        selected = "undetermined_pending_ordered_review"
        next_action = (
            "audit implementation/contract, then convergence/finite-size, then missing paper inputs; "
            "only after those are excluded may an independent reviewer consider a source/claim discrepancy"
        )
    return {
        "status": "required",
        "selected_category": selected,
        "review_order": list(FAILURE_ATTRIBUTION_ORDER),
        "failed_assertion_ids": [item["assertion_id"] for item in failed],
        "next_action": next_action,
        "paper_or_source_discrepancy_is_not_default": True,
        "paper_or_source_discrepancy_requires": [
            "an independently reproduced stable difference",
            "implementation and parameter-contract audit",
            "solver convergence and finite-size audit",
            "paper-input completeness audit",
            "fresh independent scientific review",
        ],
    }


def _write_campaign_evidence(
    campaign: Campaign,
    aggregates: Mapping[str, Mapping[str, Any]],
    timings: Mapping[str, float],
    missing_units: Sequence[WorkUnit],
) -> dict[str, Any]:
    targets: dict[str, Any] = {}
    all_assertions: list[dict[str, Any]] = []
    for target_id, payload in aggregates.items():
        assertions = target_assertions(
            target_id,
            payload,
            campaign.config,
            smoke=bool(campaign.config["smoke"]),
        )
        all_assertions.extend(assertions)
        targets[target_id] = {
            "assertions": assertions,
            "failure_attribution": _failure_attribution(target_id, assertions),
        }
    failed = sum(item["status"] == "failed" for item in all_assertions)
    if missing_units:
        status = "waiting_for_shards"
    elif failed:
        status = "failed_acceptance"
    else:
        status = "passed"
    checks = {
        "schema_version": 1,
        "paper_id": "1812.05561",
        "run_id": campaign.config["run_id"],
        "profile": "paper_scale_smoke" if campaign.config["smoke"] else "paper_scale",
        "status": status,
        "paper_scale_compute_executed": not bool(campaign.config["smoke"]),
        "targets": targets,
        "summary": {
            "passed": sum(item["status"] == "passed" for item in all_assertions),
            "failed": failed,
            "missing_work_units": len(missing_units),
            "status": status,
        },
        "failure_attribution_policy": {
            "ordered_categories": list(FAILURE_ATTRIBUTION_ORDER),
            "rule": "Never attribute a stable difference to the paper/source until the first three categories are explicitly excluded and fresh independent review agrees.",
        },
    }
    write_json(campaign.check_root / "target_checks.json", checks)
    write_json(
        campaign.check_root / "runtime_profile.json",
        {
            "schema_version": 1,
            "paper_id": "1812.05561",
            "run_id": campaign.config["run_id"],
            "status": status,
            "timings_seconds": dict(timings),
            "total_seconds": float(sum(timings.values())),
            "peak_rss_gib": _peak_rss_gib(),
            "missing_work_units": [unit.slug for unit in missing_units],
        },
    )
    data_files = sorted(campaign.data_root.glob("*.npz"))
    files = [
        {
            "path": path.relative_to(campaign.workspace).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "provenance": "independent_equation_driven_numerics",
        }
        for path in data_files
    ]
    write_json(
        campaign.check_root / "generated_data_manifest.json",
        {
            "schema_version": 1,
            "paper_id": "1812.05561",
            "run_id": campaign.config["run_id"],
            "status": "complete" if not missing_units else "partial",
            "generator": "scripts/run_reproduction.py --config config/paper_scale.json",
            "config_digest": campaign.config["config_digest"],
            "source_or_reference_arrays_used": False,
            "author_code_used": False,
            "author_numerical_arrays_used": False,
            "source_figure_pixels_used_as_numeric_input": False,
            "pdf_or_rendered_reference_available_to_numeric_runner": False,
            "toy_model_author_random_seed_available": False,
            "files": files,
        },
    )
    write_json(
        campaign.check_root / "campaign_state.json",
        {
            "schema_version": 1,
            "run_id": campaign.config["run_id"],
            "status": status,
            "completed_targets": sorted(aggregates),
            "missing_work_units": [
                {"target_id": unit.target_id, "key": unit.key, "slug": unit.slug}
                for unit in missing_units
            ],
            "resume_command": [
                "python",
                "scripts/run_reproduction.py",
                "--config",
                "config/paper_scale.json",
                "--targets",
                ",".join(sorted({unit.target_id for unit in missing_units}) or TARGET_IDS),
                "--resume",
            ],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return checks


def run_campaign(
    workspace: Path,
    config_path: Path,
    *,
    targets: Sequence[str],
    resume: bool,
    shard_index: int | None,
    shard_count: int | None,
    smoke: bool,
    validate_only: bool = False,
) -> int:
    config = load_paper_scale_config(config_path, smoke=smoke)
    unknown = sorted(set(targets) - set(TARGET_IDS))
    if unknown:
        raise ValueError(f"unknown targets: {unknown}")
    if (shard_index is None) != (shard_count is None):
        raise ValueError("--shard-index and --shard-count must be supplied together")
    if shard_count is not None and (shard_count <= 0 or not 0 <= int(shard_index) < shard_count):
        raise ValueError("invalid shard index/count")
    units = [unit for unit in plan_work_units(config["parameters"]) if unit.target_id in targets]
    if validate_only:
        print(
            json.dumps(
                {
                    "status": "valid",
                    "run_id": config["run_id"],
                    "targets": list(targets),
                    "work_units": len(units),
                    "config_digest": config["config_digest"],
                },
                sort_keys=True,
            )
        )
        return 0
    campaign = Campaign(workspace, config, resume)
    assigned = units
    if shard_count is not None:
        assigned = [unit for index, unit in enumerate(units) if index % shard_count == shard_index]
    timings: dict[str, float] = {}
    for unit in assigned:
        if resume and campaign.unit_complete(unit):
            print(f"{unit.slug}: resume skip (complete)", flush=True)
            continue
        started = time.perf_counter()
        result = RUNNERS[unit.target_id](campaign, unit)
        campaign.save_unit(unit, result)
        timings[unit.slug] = round(time.perf_counter() - started, 6)
        print(f"{unit.slug}: {timings[unit.slug]:.3f} s", flush=True)

    aggregates: dict[str, Mapping[str, Any]] = {}
    missing: list[WorkUnit] = []
    for target_id in targets:
        target_units = [unit for unit in units if unit.target_id == target_id]
        target_missing = [unit for unit in target_units if not campaign.unit_complete(unit)]
        if target_missing:
            missing.extend(target_missing)
            continue
        aggregates[target_id] = aggregate_target(campaign, target_id, target_units)
    checks = _write_campaign_evidence(campaign, aggregates, timings, missing)
    print(json.dumps(checks["summary"], sort_keys=True), flush=True)
    return 2 if not missing and checks["summary"]["failed"] else 0
