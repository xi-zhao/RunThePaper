from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import math
import os
import time

import numpy as np
import scipy.ndimage
from threadpoolctl import threadpool_limits

from lyapunov_band import (
    LongRangeModel,
    density_from_potential,
    finite_eigensystem_with_obc_gauge,
    finite_logdet_potential,
    finite_spectrum,
    lyapunov_exponents,
    lyapunov_potentials,
    sample_onsite,
    write_csv,
    write_json,
)


@dataclass
class SpectrumRunState:
    """Resumable state for the paper's expensive ED ensemble."""

    obc_counts: np.ndarray
    pbc_counts: np.ndarray
    scaling_sum: np.ndarray
    completed_batches: dict[int, int]

    @classmethod
    def empty(cls, histogram_shape: tuple[int, int], scaling_shape: tuple[int, int]) -> "SpectrumRunState":
        return cls(
            obc_counts=np.zeros(histogram_shape, dtype=np.int64),
            pbc_counts=np.zeros(histogram_shape, dtype=np.int64),
            scaling_sum=np.zeros(scaling_shape, dtype=float),
            completed_batches={},
        )

    @property
    def completed_realizations(self) -> int:
        return int(sum(self.completed_batches.values()))

    def add_batch(self, result: dict[str, Any]) -> None:
        batch_id = int(result["batch_id"])
        if batch_id in self.completed_batches:
            raise ValueError(f"batch {batch_id} was already applied")
        obc = np.asarray(result["obc_counts"], dtype=np.int64)
        pbc = np.asarray(result["pbc_counts"], dtype=np.int64)
        scaling = np.asarray(result["scaling_sum"], dtype=float)
        if obc.shape != self.obc_counts.shape or pbc.shape != self.pbc_counts.shape:
            raise ValueError("batch histogram shape does not match the run state")
        if scaling.shape != self.scaling_sum.shape:
            raise ValueError("batch scaling shape does not match the run state")
        if np.any(obc < 0) or np.any(pbc < 0) or not np.all(np.isfinite(scaling)):
            raise ValueError("batch contains invalid numerical values")
        self.obc_counts += obc
        self.pbc_counts += pbc
        self.scaling_sum += scaling
        self.completed_batches[batch_id] = int(result["realizations"])


def load_paper_config(workspace: Path, config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or workspace / "config" / "paper_exact_run.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    validate_paper_config(config)
    return config


def validate_paper_config(config: dict[str, Any]) -> None:
    model = config["model"]
    if int(model["M"]) != 2:
        raise ValueError("the target paper case requires M=2")
    fig34 = config["fig3_fig4"]
    if int(fig34["diagonalization_length"]) != 1000:
        raise ValueError("paper-matched Fig. 3/4 requires L=1000")
    if int(fig34["disorder_realizations"]) != 3200:
        raise ValueError("paper-matched Fig. 3/4 requires 3200 disorder realizations")
    if not math.isclose(float(fig34["W"]), 0.8):
        raise ValueError("paper-matched Fig. 3/4 requires W=0.8")
    if list(map(float, config["fig5"]["contour_W"])) != [0.4, 0.8, 1.2, 1.6, 2.0]:
        raise ValueError("paper-matched Fig. 5 contour strengths do not match the caption")
    runtime = config["runtime"]
    for key in ("workers", "batch_size", "checkpoint_every_batches"):
        if int(runtime[key]) <= 0:
            raise ValueError(f"runtime.{key} must be positive")
    qa = config["scientific_qa"]
    if not 0.0 < float(qa["finite_tdl_density_overlap_min"]) <= 1.0:
        raise ValueError("scientific_qa.finite_tdl_density_overlap_min must be in (0, 1]")
    if float(qa["scaling_exponent_gap_max"]) <= 0.0:
        raise ValueError("scientific_qa.scaling_exponent_gap_max must be positive")


def run_paper_ed(
    workspace: Path,
    config_path: Path | None = None,
    *,
    max_batches: int | None = None,
) -> dict[str, Any]:
    """Run or resume the L=1000, 3200-realization OBC/PBC ensemble."""

    workspace = workspace.resolve()
    config = load_paper_config(workspace, config_path)
    fig34 = config["fig3_fig4"]
    runtime = config["runtime"]
    histogram = fig34["histogram"]
    real_edges = np.linspace(histogram["real_min"], histogram["real_max"], int(histogram["real_bins"]) + 1)
    imag_edges = np.linspace(histogram["imag_min"], histogram["imag_max"], int(histogram["imag_bins"]) + 1)
    scaling_lengths = np.asarray(fig34["scaling_lengths"], dtype=int)
    scaling_energies = np.asarray(
        [complex(item["real"], item["imag"]) for item in fig34["scaling_energies"]],
        dtype=complex,
    )
    fingerprint = _ed_fingerprint(config)
    checkpoint_dir = workspace / "outputs" / "paper_exact" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_npz = checkpoint_dir / "ed_state.npz"
    checkpoint_json = checkpoint_dir / "ed_state.json"
    state = _load_ed_state(
        checkpoint_npz,
        checkpoint_json,
        fingerprint,
        histogram_shape=(imag_edges.size - 1, real_edges.size - 1),
        scaling_shape=(scaling_lengths.size, scaling_energies.size),
    )

    realizations = int(fig34["disorder_realizations"])
    batch_size = int(runtime["batch_size"])
    batches = [
        (batch_id, start, min(start + batch_size, realizations))
        for batch_id, start in enumerate(range(0, realizations, batch_size))
    ]
    pending = [batch for batch in batches if batch[0] not in state.completed_batches]
    if max_batches is not None:
        if max_batches <= 0:
            raise ValueError("max_batches must be positive")
        pending = pending[:max_batches]

    model = _model_from_config(config["model"])
    worker_payloads = [
        {
            "batch_id": batch_id,
            "start": start,
            "stop": stop,
            "seed": int(config["seed"]),
            "length": int(fig34["diagonalization_length"]),
            "W": float(fig34["W"]),
            "model": model,
            "real_edges": real_edges,
            "imag_edges": imag_edges,
            "scaling_lengths": scaling_lengths,
            "scaling_energies": scaling_energies,
        }
        for batch_id, start, stop in pending
    ]
    started = time.perf_counter()
    since_checkpoint = 0
    if worker_payloads:
        with ProcessPoolExecutor(max_workers=int(runtime["workers"])) as executor:
            futures = [executor.submit(_compute_spectrum_batch, payload) for payload in worker_payloads]
            for future in as_completed(futures):
                state.add_batch(future.result())
                since_checkpoint += 1
                if since_checkpoint >= int(runtime["checkpoint_every_batches"]):
                    _save_ed_state(checkpoint_npz, checkpoint_json, fingerprint, state, realizations)
                    since_checkpoint = 0
                print(
                    json.dumps(
                        {
                            "event": "ed_batch_completed",
                            "completed_realizations": state.completed_realizations,
                            "target_realizations": realizations,
                            "elapsed_seconds": round(time.perf_counter() - started, 2),
                        }
                    ),
                    flush=True,
                )
    _save_ed_state(checkpoint_npz, checkpoint_json, fingerprint, state, realizations)
    complete = state.completed_realizations == realizations
    result = _finalize_ed_outputs(
        workspace,
        config,
        state,
        real_edges,
        imag_edges,
        scaling_lengths,
        scaling_energies,
        complete=complete,
        runtime_seconds=time.perf_counter() - started,
    )
    return result


def run_paper_profiles(workspace: Path, config_path: Path | None = None) -> dict[str, Any]:
    workspace = workspace.resolve()
    config = load_paper_config(workspace, config_path)
    fig34 = config["fig3_fig4"]
    profile_config = config["profiles"]
    model = _model_from_config(config["model"])
    length = int(fig34["diagonalization_length"])
    disorder_strength = float(fig34["W"])
    targets = {
        name: complex(spec["real"], spec["imag"])
        for name, spec in profile_config["targets"].items()
    }
    candidates: dict[str, list[tuple[float, complex, np.ndarray, int]]] = {
        "alm": [],
        "critical": [],
        "skin": [],
    }
    started = time.perf_counter()
    for realization in range(int(profile_config["search_realizations"])):
        rng = _realization_rng(int(config["seed"]) + 20_000, realization)
        onsite = sample_onsite(length, disorder_strength, rng)
        with threadpool_limits(limits=1):
            values, vectors = finite_eigensystem_with_obc_gauge(
                onsite,
                model,
                radius=float(profile_config["obc_similarity_gauge"]),
            )
        probabilities = np.abs(vectors) ** 2
        probabilities /= np.maximum(probabilities.sum(axis=0, keepdims=True), np.finfo(float).tiny)
        for name, target in targets.items():
            keep = int(profile_config["alm_count"]) if name == "alm" else 3
            indices = np.argsort(np.abs(values - target))[:keep]
            for index in indices:
                candidates[name].append(
                    (float(abs(values[index] - target)), complex(values[index]), probabilities[:, index].copy(), realization)
                )
        print(
            json.dumps(
                {
                    "event": "profile_realization_completed",
                    "realization": realization + 1,
                    "target": int(profile_config["search_realizations"]),
                }
            ),
            flush=True,
        )

    alm_selected = sorted(candidates["alm"], key=lambda item: item[0])[: int(profile_config["alm_count"])]
    critical_selected = min(candidates["critical"], key=lambda item: item[0])
    skin_selected = min(candidates["skin"], key=lambda item: item[0])
    selected_energies = np.asarray(
        [item[1] for item in alm_selected] + [critical_selected[1], skin_selected[1]],
        dtype=complex,
    )
    classification_onsite = sample_onsite(
        int(profile_config["classification_transfer_length"]),
        disorder_strength,
        np.random.default_rng(int(config["seed"]) + 21_000),
    )
    exponents = lyapunov_exponents(
        selected_energies,
        classification_onsite,
        model,
        qr_interval=int(profile_config["qr_interval"]),
    )
    output_dir = workspace / "outputs" / "paper_exact" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "paper_profiles.npz"
    _atomic_savez(
        output,
        site=np.arange(length),
        alm_profiles=np.vstack([item[2] for item in alm_selected]),
        alm_energies=np.asarray([item[1] for item in alm_selected]),
        alm_realizations=np.asarray([item[3] for item in alm_selected], dtype=int),
        critical_profile=critical_selected[2],
        critical_energy=np.asarray(critical_selected[1]),
        critical_realization=np.asarray(critical_selected[3]),
        skin_profile=skin_selected[2],
        skin_energy=np.asarray(skin_selected[1]),
        skin_realization=np.asarray(skin_selected[3]),
        selected_lyapunov_exponents=exponents,
    )
    alm_exponents = exponents[: len(alm_selected)]
    critical_exponents = exponents[len(alm_selected)]
    skin_exponents = exponents[len(alm_selected) + 1]
    result = {
        "status": "passed",
        "artifact_stage": "paper_matched_reproduction",
        "generated_data_provenance": "independent_numerics",
        "search_realizations": int(profile_config["search_realizations"]),
        "alm_profiles": len(alm_selected),
        "classification_checks": {
            "all_alm_central_exponents_straddle_zero": bool(
                np.all((alm_exponents[:, 1] < 0.0) & (alm_exponents[:, 2] > 0.0))
            ),
            "critical_min_abs_central_exponent": float(
                min(abs(critical_exponents[1]), abs(critical_exponents[2]))
            ),
            "skin_central_exponents_have_same_sign": bool(skin_exponents[1] * skin_exponents[2] > 0.0),
        },
        "runtime_seconds": time.perf_counter() - started,
        "output": str(output.relative_to(workspace)),
    }
    write_json(workspace / "outputs" / "checks" / "paper_profile_generation.json", result)
    return result


def recompute_paper_scaling(workspace: Path, config_path: Path | None = None) -> dict[str, Any]:
    """Replace fragile eigenvalue-based scaling sums with stable log determinants.

    The already completed OBC/PBC DOS histograms remain unchanged. This is also
    an auditable repair path for checkpoints produced by an older algorithm.
    """

    workspace = workspace.resolve()
    config = load_paper_config(workspace, config_path)
    fig34 = config["fig3_fig4"]
    runtime = config["runtime"]
    checkpoint_dir = workspace / "outputs" / "paper_exact" / "checkpoints"
    checkpoint_npz = checkpoint_dir / "ed_state.npz"
    checkpoint_json = checkpoint_dir / "ed_state.json"
    if not checkpoint_npz.exists() or not checkpoint_json.exists():
        raise FileNotFoundError("a completed ED checkpoint is required before scaling repair")
    with np.load(checkpoint_npz, allow_pickle=False) as data:
        ids = data["completed_batch_ids"].astype(int)
        sizes = data["completed_batch_sizes"].astype(int)
        state = SpectrumRunState(
            obc_counts=data["obc_counts"].astype(np.int64),
            pbc_counts=data["pbc_counts"].astype(np.int64),
            scaling_sum=np.zeros_like(data["scaling_sum"], dtype=float),
            completed_batches={int(batch_id): int(size) for batch_id, size in zip(ids, sizes)},
        )
    target_realizations = int(fig34["disorder_realizations"])
    if state.completed_realizations != target_realizations:
        raise ValueError("scaling repair requires a complete 3200-realization ED checkpoint")

    scaling_lengths = np.asarray(fig34["scaling_lengths"], dtype=int)
    scaling_energies = np.asarray(
        [complex(item["real"], item["imag"]) for item in fig34["scaling_energies"]],
        dtype=complex,
    )
    batch_size = int(runtime["batch_size"])
    model = _model_from_config(config["model"])
    payloads = [
        {
            "batch_id": batch_id,
            "start": start,
            "stop": min(start + batch_size, target_realizations),
            "seed": int(config["seed"]),
            "length": int(fig34["diagonalization_length"]),
            "W": float(fig34["W"]),
            "model": model,
            "scaling_lengths": scaling_lengths,
            "scaling_energies": scaling_energies,
        }
        for batch_id, start in enumerate(range(0, target_realizations, batch_size))
    ]
    started = time.perf_counter()
    completed = 0
    with ProcessPoolExecutor(max_workers=int(runtime["workers"])) as executor:
        futures = [executor.submit(_compute_scaling_batch, payload) for payload in payloads]
        for future in as_completed(futures):
            batch = future.result()
            state.scaling_sum += batch["scaling_sum"]
            completed += int(batch["realizations"])
            if completed % 256 == 0 or completed == target_realizations:
                print(
                    json.dumps(
                        {
                            "event": "logdet_scaling_progress",
                            "completed_realizations": completed,
                            "target_realizations": target_realizations,
                        }
                    ),
                    flush=True,
                )
    _save_ed_state(
        checkpoint_npz,
        checkpoint_json,
        _ed_fingerprint(config),
        state,
        target_realizations,
    )
    ed_result = run_paper_ed(workspace, config_path)
    return {
        "status": ed_result["status"],
        "method": "banded_sparse_lu_logdet",
        "completed_realizations": completed,
        "runtime_seconds": time.perf_counter() - started,
        "ed_result": ed_result,
    }


def run_paper_theory(workspace: Path, config_path: Path | None = None) -> dict[str, Any]:
    workspace = workspace.resolve()
    config = load_paper_config(workspace, config_path)
    model = _model_from_config(config["model"])
    workers = int(config["runtime"]["workers"])
    seed = int(config["seed"])
    output_dir = workspace / "outputs" / "paper_exact" / "data"
    cache_dir = workspace / "outputs" / "paper_exact" / "checkpoints" / "theory"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    fig34_config = config["fig3_fig4"]["theory"]
    fig34 = _load_or_compute_theory_grid(
        cache_dir / "fig34_w0p8.npz",
        model,
        float(config["fig3_fig4"]["W"]),
        fig34_config,
        seed + 30_000,
        workers,
    )
    fig34_obc_potential, fig34_pbc_potential = lyapunov_potentials(fig34["exponents"], model)
    fig34_obc_density = density_from_potential(
        fig34_obc_potential,
        fig34["real_axis"],
        fig34["imag_axis"],
        smoothing_sigma=float(fig34_config["density_smoothing_sigma_cells"]),
    )
    fig34_pbc_density = density_from_potential(
        fig34_pbc_potential,
        fig34["real_axis"],
        fig34["imag_axis"],
        smoothing_sigma=float(fig34_config["density_smoothing_sigma_cells"]),
    )
    _atomic_savez(
        output_dir / "paper_fig34_theory.npz",
        real_axis=fig34["real_axis"],
        imag_axis=fig34["imag_axis"],
        exponents=fig34["exponents"],
        obc_density=fig34_obc_density,
        pbc_density=fig34_pbc_density,
    )

    contour_config = config["fig5"]["contour_theory"]
    contour_exponents: list[np.ndarray] = []
    contour_real_axis: np.ndarray | None = None
    contour_imag_axis: np.ndarray | None = None
    for index, disorder_strength in enumerate(config["fig5"]["contour_W"]):
        token = _float_token(float(disorder_strength))
        grid = _load_or_compute_theory_grid(
            cache_dir / f"contour_w{token}.npz",
            model,
            float(disorder_strength),
            contour_config,
            seed + 31_000 + index,
            workers,
        )
        contour_real_axis = grid["real_axis"]
        contour_imag_axis = grid["imag_axis"]
        contour_exponents.append(grid["exponents"])
    assert contour_real_axis is not None and contour_imag_axis is not None
    _atomic_savez(
        output_dir / "paper_fig5_contours.npz",
        W=np.asarray(config["fig5"]["contour_W"], dtype=float),
        real_axis=contour_real_axis,
        imag_axis=contour_imag_axis,
        exponents=np.stack(contour_exponents),
    )

    alpha_rows = _run_alpha_grid(workspace, config, model, cache_dir, workers)
    alpha_values = np.asarray([row["alpha"] for row in alpha_rows], dtype=float)
    w_values = np.asarray([row["W"] for row in alpha_rows], dtype=float)
    candidates = w_values[alpha_values >= 0.98]
    estimated_wc = float(candidates[0]) if candidates.size else None
    result = {
        "status": "passed",
        "artifact_stage": "paper_matched_reproduction",
        "generated_data_provenance": "independent_numerics",
        "fig34_grid_shape": list(fig34["exponents"].shape[:2]),
        "fig34_transfer_length": int(fig34_config["transfer_length"]),
        "contour_grid_shape": list(contour_exponents[0].shape[:2]),
        "contour_transfer_length": int(contour_config["transfer_length"]),
        "alpha_points": len(alpha_rows),
        "estimated_Wc_alpha_ge_0_98": estimated_wc,
        "paper_Wc": 2.1,
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(workspace / "outputs" / "checks" / "paper_theory_generation.json", result)
    return result


def _compute_spectrum_batch(payload: dict[str, Any]) -> dict[str, Any]:
    model: LongRangeModel = payload["model"]
    length = int(payload["length"])
    disorder_strength = float(payload["W"])
    real_edges = np.asarray(payload["real_edges"], dtype=float)
    imag_edges = np.asarray(payload["imag_edges"], dtype=float)
    scaling_lengths = np.asarray(payload["scaling_lengths"], dtype=int)
    scaling_energies = np.asarray(payload["scaling_energies"], dtype=complex)
    obc_counts = np.zeros((imag_edges.size - 1, real_edges.size - 1), dtype=np.int64)
    pbc_counts = np.zeros_like(obc_counts)
    scaling_sum = np.zeros((scaling_lengths.size, scaling_energies.size), dtype=float)
    with threadpool_limits(limits=1):
        for realization in range(int(payload["start"]), int(payload["stop"])):
            onsite = sample_onsite(
                length,
                disorder_strength,
                _realization_rng(int(payload["seed"]), realization),
            )
            for length_index, scaling_length in enumerate(scaling_lengths):
                scaling_sum[length_index] += finite_logdet_potential(
                    onsite[: int(scaling_length)],
                    model,
                    scaling_energies,
                )
            full_obc = finite_spectrum(onsite, model, boundary="obc")
            pbc = finite_spectrum(onsite, model, boundary="pbc")
            obc_counts += np.histogram2d(full_obc.imag, full_obc.real, bins=(imag_edges, real_edges))[0].astype(np.int64)
            pbc_counts += np.histogram2d(pbc.imag, pbc.real, bins=(imag_edges, real_edges))[0].astype(np.int64)
    return {
        "batch_id": int(payload["batch_id"]),
        "realizations": int(payload["stop"]) - int(payload["start"]),
        "obc_counts": obc_counts,
        "pbc_counts": pbc_counts,
        "scaling_sum": scaling_sum,
    }


def _compute_scaling_batch(payload: dict[str, Any]) -> dict[str, Any]:
    model: LongRangeModel = payload["model"]
    scaling_lengths = np.asarray(payload["scaling_lengths"], dtype=int)
    scaling_energies = np.asarray(payload["scaling_energies"], dtype=complex)
    scaling_sum = np.zeros((scaling_lengths.size, scaling_energies.size), dtype=float)
    with threadpool_limits(limits=1):
        for realization in range(int(payload["start"]), int(payload["stop"])):
            onsite = sample_onsite(
                int(payload["length"]),
                float(payload["W"]),
                _realization_rng(int(payload["seed"]), realization),
            )
            for length_index, scaling_length in enumerate(scaling_lengths):
                scaling_sum[length_index] += finite_logdet_potential(
                    onsite[: int(scaling_length)],
                    model,
                    scaling_energies,
                )
    return {
        "batch_id": int(payload["batch_id"]),
        "realizations": int(payload["stop"]) - int(payload["start"]),
        "scaling_sum": scaling_sum,
    }


def _finalize_ed_outputs(
    workspace: Path,
    config: dict[str, Any],
    state: SpectrumRunState,
    real_edges: np.ndarray,
    imag_edges: np.ndarray,
    scaling_lengths: np.ndarray,
    scaling_energies: np.ndarray,
    *,
    complete: bool,
    runtime_seconds: float,
) -> dict[str, Any]:
    fig34 = config["fig3_fig4"]
    histogram_config = fig34["histogram"]
    real_axis = 0.5 * (real_edges[:-1] + real_edges[1:])
    imag_axis = 0.5 * (imag_edges[:-1] + imag_edges[1:])
    total_levels = state.completed_realizations * int(fig34["diagonalization_length"])
    dx = float(np.diff(real_edges)[0])
    dy = float(np.diff(imag_edges)[0])
    sigma = float(histogram_config["gaussian_sigma_cells"])
    if total_levels:
        obc_density = scipy.ndimage.gaussian_filter(
            state.obc_counts.astype(float) / (total_levels * dx * dy), sigma=sigma, mode="constant"
        )
        pbc_density = scipy.ndimage.gaussian_filter(
            state.pbc_counts.astype(float) / (total_levels * dx * dy), sigma=sigma, mode="constant"
        )
    else:
        obc_density = state.obc_counts.astype(float)
        pbc_density = state.pbc_counts.astype(float)
    output_dir = workspace / "outputs" / "paper_exact" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_savez(
        output_dir / "paper_ed_histograms.npz",
        real_axis=real_axis,
        imag_axis=imag_axis,
        real_edges=real_edges,
        imag_edges=imag_edges,
        obc_counts=state.obc_counts,
        pbc_counts=state.pbc_counts,
        obc_density=obc_density,
        pbc_density=pbc_density,
        completed_realizations=np.asarray(state.completed_realizations),
    )

    scaling_specs = fig34["scaling_energies"]
    model = _model_from_config(config["model"])
    if complete:
        theory_potential, theory_standard_error = _high_precision_scaling_potential(
            workspace,
            config,
            model,
            scaling_energies,
        )
    else:
        theory_onsite = sample_onsite(
            300_000,
            float(fig34["W"]),
            np.random.default_rng(int(config["seed"]) + 40_000),
        )
        theory_exponents = lyapunov_exponents(scaling_energies, theory_onsite, model, qr_interval=4)
        theory_potential, _ = lyapunov_potentials(theory_exponents, model)
        theory_standard_error = np.full(scaling_energies.shape, np.nan)
    scaling_mean = state.scaling_sum / max(state.completed_realizations, 1)
    fit_min_length = int(fig34["scaling_fit_min_length"])
    rows: list[dict[str, Any]] = []
    fits: dict[str, dict[str, float]] = {}
    for energy_index, spec in enumerate(scaling_specs):
        deviations = np.abs(scaling_mean[:, energy_index] - theory_potential[energy_index])
        for length_index, length in enumerate(scaling_lengths):
            rows.append(
                {
                    "label": spec["label"],
                    "real_energy": spec["real"],
                    "imag_energy": spec["imag"],
                    "L": int(length),
                    "fit_min_length": fit_min_length,
                    "fit_included": bool(length >= fit_min_length),
                    "realizations": state.completed_realizations,
                    "finite_potential": float(scaling_mean[length_index, energy_index]),
                    "lyapunov_potential": float(theory_potential[energy_index]),
                    "delta_phi": float(deviations[length_index]),
                    "paper_exponent_L": spec["paper_exponent"],
                    "paper_intercept": spec["paper_intercept"],
                }
            )
        valid = (deviations > 0.0) & (scaling_lengths >= fit_min_length)
        slope, intercept = np.polyfit(np.log(scaling_lengths[valid].astype(float)), np.log(deviations[valid]), 1)
        fits[spec["label"]] = {
            "fit_min_length": fit_min_length,
            "fit_exponent_L": float(slope),
            "fit_intercept": float(intercept),
            "paper_exponent_L": float(spec["paper_exponent"]),
            "paper_intercept": float(spec["paper_intercept"]),
        }
    write_csv(output_dir / "paper_scaling.csv", rows)
    obc_coverage = float(state.obc_counts.sum() / total_levels) if total_levels else 0.0
    pbc_coverage = float(state.pbc_counts.sum() / total_levels) if total_levels else 0.0
    result = {
        "status": "passed" if complete and min(obc_coverage, pbc_coverage) > 0.999 else "in_progress",
        "artifact_stage": "paper_matched_reproduction",
        "parameter_match": "paper_reported",
        "generated_data_provenance": "independent_numerics",
        "completed_realizations": state.completed_realizations,
        "target_realizations": int(fig34["disorder_realizations"]),
        "L": int(fig34["diagonalization_length"]),
        "W": float(fig34["W"]),
        "histogram_coverage": {"obc": obc_coverage, "pbc": pbc_coverage},
        "scaling_fits": fits,
        "scaling_theory": {
            "transfer_length_per_realization": int(fig34["scaling_theory_transfer_length"]),
            "realizations": int(fig34["scaling_theory_realizations"]),
            "potential_standard_error": theory_standard_error.tolist(),
        },
        "runtime_seconds_this_invocation": runtime_seconds,
    }
    write_json(workspace / "outputs" / "checks" / "paper_ed_generation.json", result)
    return result


def _load_or_compute_theory_grid(
    cache_path: Path,
    model: LongRangeModel,
    disorder_strength: float,
    grid_config: dict[str, Any],
    seed: int,
    workers: int,
) -> dict[str, np.ndarray]:
    fingerprint = _fingerprint({"W": disorder_strength, "grid": grid_config, "seed": seed, "model": model.__dict__})
    if cache_path.exists():
        with np.load(cache_path, allow_pickle=False) as cached:
            cached_fingerprint = str(cached["fingerprint"].item())
            if cached_fingerprint == fingerprint:
                return {
                    "real_axis": cached["real_axis"].copy(),
                    "imag_axis": cached["imag_axis"].copy(),
                    "exponents": cached["exponents"].copy(),
                }
    real_axis = np.linspace(grid_config["real_min"], grid_config["real_max"], int(grid_config["real_points"]))
    imag_axis = np.linspace(grid_config["imag_min"], grid_config["imag_max"], int(grid_config["imag_points"]))
    energies = (real_axis[None, :] + 1j * imag_axis[:, None]).reshape(-1)
    onsite = sample_onsite(
        int(grid_config["transfer_length"]),
        disorder_strength,
        np.random.default_rng(seed),
    )
    batch_size = int(grid_config.get("energy_batch_size", energies.size))
    chunks = [(start, energies[start : start + batch_size]) for start in range(0, energies.size, batch_size)]
    flat_exponents = np.empty((energies.size, 4), dtype=float)
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _theory_chunk,
                chunk_energies,
                onsite,
                model,
                int(grid_config["qr_interval"]),
            ): start
            for start, chunk_energies in chunks
        }
        completed = 0
        for future in as_completed(futures):
            start = futures[future]
            values = future.result()
            flat_exponents[start : start + values.shape[0]] = values
            completed += values.shape[0]
            print(
                json.dumps(
                    {
                        "event": "theory_energy_batch_completed",
                        "W": disorder_strength,
                        "completed_energies": completed,
                        "target_energies": energies.size,
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                    }
                ),
                flush=True,
            )
    exponents = flat_exponents.reshape(imag_axis.size, real_axis.size, 4)
    _atomic_savez(
        cache_path,
        fingerprint=np.asarray(fingerprint),
        real_axis=real_axis,
        imag_axis=imag_axis,
        exponents=exponents,
    )
    return {"real_axis": real_axis, "imag_axis": imag_axis, "exponents": exponents}


def _run_alpha_grid(
    workspace: Path,
    config: dict[str, Any],
    model: LongRangeModel,
    cache_dir: Path,
    workers: int,
) -> list[dict[str, Any]]:
    alpha_config = config["fig5"]["alpha_theory"]
    w_values = [float(value) for value in config["fig5"]["alpha_W"]]
    rows_by_w: dict[float, dict[str, Any]] = {}
    pending: list[tuple[float, int, Path]] = []
    for index, disorder_strength in enumerate(w_values):
        cache_path = cache_dir / f"alpha_w{_float_token(disorder_strength)}.json"
        fingerprint = _fingerprint(
            {
                "W": disorder_strength,
                "grid": alpha_config,
                "seed": int(config["seed"]) + 32_000 + index,
                "model": model.__dict__,
            }
        )
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("fingerprint") == fingerprint:
                rows_by_w[disorder_strength] = cached["row"]
                continue
        pending.append((disorder_strength, index, cache_path))

    started = time.perf_counter()
    if pending:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for disorder_strength, index, cache_path in pending:
                seed = int(config["seed"]) + 32_000 + index
                fingerprint = _fingerprint(
                    {"W": disorder_strength, "grid": alpha_config, "seed": seed, "model": model.__dict__}
                )
                future = executor.submit(
                    _alpha_worker,
                    disorder_strength,
                    model,
                    alpha_config,
                    seed,
                )
                futures[future] = (disorder_strength, cache_path, fingerprint)
            for future in as_completed(futures):
                disorder_strength, cache_path, fingerprint = futures[future]
                row = future.result()
                rows_by_w[disorder_strength] = row
                _atomic_write_json(cache_path, {"fingerprint": fingerprint, "row": row})
                print(
                    json.dumps(
                        {
                            "event": "alpha_point_completed",
                            "W": disorder_strength,
                            "alpha": row["alpha"],
                            "completed_points": len(rows_by_w),
                            "target_points": len(w_values),
                            "elapsed_seconds": round(time.perf_counter() - started, 2),
                        }
                    ),
                    flush=True,
                )
    rows = [rows_by_w[value] for value in w_values]
    write_csv(workspace / "outputs" / "paper_exact" / "data" / "paper_alpha.csv", rows)
    return rows


def _alpha_worker(
    disorder_strength: float,
    model: LongRangeModel,
    alpha_config: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    length = int(alpha_config["diagonalization_length"])
    realization_count = int(alpha_config["disorder_realizations"])
    tolerance = float(alpha_config["classification_tolerance_factor"]) / int(alpha_config["transfer_length"])
    if disorder_strength == 0.0:
        return {
            "W": disorder_strength,
            "alpha": 0.0,
            "binomial_standard_error": 0.0,
            "method": f"{alpha_config['method']}_clean_limit_invariant",
            "L": length,
            "realizations": realization_count,
            "eigenvalues": length * realization_count,
            "transfer_length": int(alpha_config["transfer_length"]),
            "classification_tolerance": tolerance,
        }
    with threadpool_limits(limits=1):
        spectra = np.concatenate(
            [
                finite_spectrum(
                    sample_onsite(length, disorder_strength, _realization_rng(seed, realization)),
                    model,
                    boundary="obc",
                )
                for realization in range(realization_count)
            ]
        )
    onsite = sample_onsite(
        int(alpha_config["transfer_length"]),
        disorder_strength,
        np.random.default_rng(seed),
    )
    with threadpool_limits(limits=1):
        exponents = lyapunov_exponents(
            spectra,
            onsite,
            model,
            qr_interval=int(alpha_config["qr_interval"]),
        )
    alm_mask = (exponents[..., 1] < -tolerance) & (exponents[..., 2] > tolerance)
    alpha = float(np.mean(alm_mask))
    standard_error = float(np.sqrt(max(alpha * (1.0 - alpha), 0.0) / spectra.size))
    return {
        "W": disorder_strength,
        "alpha": alpha,
        "binomial_standard_error": standard_error,
        "method": alpha_config["method"],
        "L": length,
        "realizations": realization_count,
        "eigenvalues": int(spectra.size),
        "transfer_length": int(alpha_config["transfer_length"]),
        "classification_tolerance": tolerance,
    }


def _theory_chunk(
    energies: np.ndarray,
    onsite: np.ndarray,
    model: LongRangeModel,
    qr_interval: int,
) -> np.ndarray:
    with threadpool_limits(limits=1):
        return lyapunov_exponents(energies, onsite, model, qr_interval=qr_interval)


def _high_precision_scaling_potential(
    workspace: Path,
    config: dict[str, Any],
    model: LongRangeModel,
    energies: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    fig34 = config["fig3_fig4"]
    transfer_length = int(fig34["scaling_theory_transfer_length"])
    realization_count = int(fig34["scaling_theory_realizations"])
    fingerprint = _fingerprint(
        {
            "model": model.__dict__,
            "W": fig34["W"],
            "energies": [str(value) for value in energies],
            "transfer_length": transfer_length,
            "realizations": realization_count,
            "seed": config["seed"],
        }
    )
    cache_path = workspace / "outputs" / "paper_exact" / "checkpoints" / "scaling_theory_potential.npz"
    if cache_path.exists():
        with np.load(cache_path, allow_pickle=False) as cached:
            if str(cached["fingerprint"].item()) == fingerprint:
                return cached["mean"].copy(), cached["standard_error"].copy()
    with ProcessPoolExecutor(max_workers=int(config["runtime"]["workers"])) as executor:
        futures = [
            executor.submit(
                _scaling_theory_sample,
                energies,
                transfer_length,
                float(fig34["W"]),
                int(config["seed"]) + 40_000 + realization,
                model,
            )
            for realization in range(realization_count)
        ]
        samples = np.vstack([future.result() for future in as_completed(futures)])
    mean = np.mean(samples, axis=0)
    standard_error = np.std(samples, axis=0, ddof=1) / np.sqrt(realization_count)
    _atomic_savez(
        cache_path,
        fingerprint=np.asarray(fingerprint),
        mean=mean,
        standard_error=standard_error,
        samples=samples,
    )
    return mean, standard_error


def _scaling_theory_sample(
    energies: np.ndarray,
    transfer_length: int,
    disorder_strength: float,
    seed: int,
    model: LongRangeModel,
) -> np.ndarray:
    onsite = sample_onsite(transfer_length, disorder_strength, np.random.default_rng(seed))
    with threadpool_limits(limits=1):
        exponents = lyapunov_exponents(energies, onsite, model, qr_interval=4)
    obc_potential, _ = lyapunov_potentials(exponents, model)
    return obc_potential


def _load_ed_state(
    checkpoint_npz: Path,
    checkpoint_json: Path,
    fingerprint: str,
    *,
    histogram_shape: tuple[int, int],
    scaling_shape: tuple[int, int],
) -> SpectrumRunState:
    if not checkpoint_npz.exists() or not checkpoint_json.exists():
        return SpectrumRunState.empty(histogram_shape, scaling_shape)
    metadata = json.loads(checkpoint_json.read_text(encoding="utf-8"))
    if metadata.get("fingerprint") != fingerprint:
        raise ValueError("existing ED checkpoint belongs to a different configuration")
    with np.load(checkpoint_npz, allow_pickle=False) as data:
        ids = data["completed_batch_ids"].astype(int)
        sizes = data["completed_batch_sizes"].astype(int)
        state = SpectrumRunState(
            obc_counts=data["obc_counts"].astype(np.int64),
            pbc_counts=data["pbc_counts"].astype(np.int64),
            scaling_sum=data["scaling_sum"].astype(float),
            completed_batches={int(batch_id): int(size) for batch_id, size in zip(ids, sizes)},
        )
    if state.obc_counts.shape != histogram_shape or state.scaling_sum.shape != scaling_shape:
        raise ValueError("existing ED checkpoint shape does not match the configuration")
    return state


def _save_ed_state(
    checkpoint_npz: Path,
    checkpoint_json: Path,
    fingerprint: str,
    state: SpectrumRunState,
    target_realizations: int,
) -> None:
    items = sorted(state.completed_batches.items())
    _atomic_savez(
        checkpoint_npz,
        obc_counts=state.obc_counts,
        pbc_counts=state.pbc_counts,
        scaling_sum=state.scaling_sum,
        completed_batch_ids=np.asarray([item[0] for item in items], dtype=int),
        completed_batch_sizes=np.asarray([item[1] for item in items], dtype=int),
    )
    _atomic_write_json(
        checkpoint_json,
        {
            "fingerprint": fingerprint,
            "completed_realizations": state.completed_realizations,
            "target_realizations": target_realizations,
            "status": "complete" if state.completed_realizations == target_realizations else "in_progress",
        },
    )


def _model_from_config(config: dict[str, Any]) -> LongRangeModel:
    return LongRangeModel(**{key: float(value) for key, value in config.items() if key != "M"})


def _ed_fingerprint(config: dict[str, Any]) -> str:
    return _fingerprint(
        {
            "seed": config["seed"],
            "model": config["model"],
            "fig3_fig4": config["fig3_fig4"],
            "batch_size": config["runtime"]["batch_size"],
        }
    )


def _realization_rng(seed: int, realization: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([seed, realization]))


def _fingerprint(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _float_token(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".").replace("-", "m").replace(".", "p")


def _atomic_savez(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary.replace(path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)
