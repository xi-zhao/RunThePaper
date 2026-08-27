from __future__ import annotations

from dataclasses import asdict
import copy
from pathlib import Path
import os
import sys
import time

import mpmath as mp
import numpy as np
import scipy.linalg

from lyapunov_band import LongRangeModel, lyapunov_exponents, sample_onsite, write_csv, write_json


def unidirectional_hamiltonian(
    onsite: np.ndarray,
    hopping: complex,
    *,
    direction: str = "right",
) -> np.ndarray:
    """Build the paper's one-way nearest-neighbour OBC Hamiltonian.

    With only one hopping direction the matrix is triangular, hence its
    eigenvalues are exactly its onsite diagonal. This is the numerical object
    behind the main-text claim ``rho_OBC = rho_w``.
    """

    onsite = np.asarray(onsite, dtype=float)
    if onsite.ndim != 1 or onsite.size < 2:
        raise ValueError("onsite must be a one-dimensional array with at least two sites")
    if direction not in {"right", "left"}:
        raise ValueError("direction must be right or left")
    matrix = np.diag(onsite.astype(complex))
    indices = np.arange(onsite.size - 1)
    if direction == "right":
        matrix[indices, indices + 1] = hopping
    else:
        matrix[indices + 1, indices] = hopping
    return matrix


def run_unidirectional_claim(config: dict, seed: int) -> tuple[list[dict], dict]:
    length = int(config["length"])
    realizations = int(config["realizations"])
    disorder_strength = float(config["W"])
    hopping = complex(float(config["hopping_real"]), float(config.get("hopping_imag", 0.0)))
    direction = str(config.get("direction", "right"))
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    maximum_error = 0.0
    for realization in range(realizations):
        onsite = sample_onsite(length, disorder_strength, rng)
        eigenvalues = scipy.linalg.eigvals(
            unidirectional_hamiltonian(onsite, hopping, direction=direction),
            check_finite=False,
            overwrite_a=True,
        )
        ordered_onsite = np.sort(onsite)
        ordered_eigenvalues = np.sort(eigenvalues.real)
        realization_error = float(np.max(np.abs(ordered_eigenvalues - ordered_onsite)))
        maximum_error = max(maximum_error, realization_error)
        for site, (onsite_value, eigenvalue) in enumerate(zip(ordered_onsite, ordered_eigenvalues)):
            rows.append(
                {
                    "realization": realization,
                    "site": site,
                    "onsite": float(onsite_value),
                    "eigenvalue_real": float(eigenvalue),
                    "absolute_error": float(abs(eigenvalue - onsite_value)),
                }
            )
    return rows, {
        "status": "passed" if maximum_error <= float(config["max_eigenvalue_error"]) else "failed",
        "model": {
            "length": length,
            "realizations": realizations,
            "W": disorder_strength,
            "hopping": [hopping.real, hopping.imag],
            "direction": direction,
        },
        "maximum_eigenvalue_onsite_error": maximum_error,
        "acceptance_threshold": float(config["max_eigenvalue_error"]),
        "analytic_basis": "An OBC one-way hopping matrix is triangular, so its eigenvalue multiset equals its onsite diagonal exactly.",
    }


def _mp_matrix_for_onsite(onsite: np.ndarray, model: LongRangeModel) -> mp.matrix:
    length = int(len(onsite))
    matrix = mp.matrix(length, length)
    for row in range(length):
        matrix[row, row] = mp.mpf(str(float(onsite[row])))
        for displacement in (-2, -1, 1, 2):
            column = row + displacement
            if 0 <= column < length:
                matrix[row, column] = mp.mpf(str(model.hopping(displacement)))
    return matrix


def _mp_ed_potentials(
    onsite_sequences: list[np.ndarray],
    energies: list[complex],
    model: LongRangeModel,
    bits: int,
) -> list[float]:
    accumulator = [mp.mpf("0") for _ in energies]
    with mp.workprec(bits):
        for onsite in onsite_sequences:
            values = mp.eig(_mp_matrix_for_onsite(onsite, model), left=False, right=False)
            length = mp.mpf(len(values))
            for energy_index, energy in enumerate(energies):
                probe = mp.mpc(str(energy.real), str(energy.imag))
                accumulator[energy_index] += sum(mp.log(abs(probe - value)) for value in values) / length
        count = mp.mpf(len(onsite_sequences))
        return [float(value / count) for value in accumulator]


def _mp_transfer_matrix(energy: complex, onsite: float, model: LongRangeModel) -> mp.matrix:
    matrix = mp.matrix(4, 4)
    matrix[0, 0] = -mp.mpf(str(model.t_1)) / mp.mpf(str(model.t_2))
    matrix[0, 1] = (
        mp.mpc(str(energy.real), str(energy.imag)) - mp.mpf(str(float(onsite)))
    ) / mp.mpf(str(model.t_2))
    matrix[0, 2] = -mp.mpf(str(model.t_minus_1)) / mp.mpf(str(model.t_2))
    matrix[0, 3] = -mp.mpf(str(model.t_minus_2)) / mp.mpf(str(model.t_2))
    matrix[1, 0] = 1
    matrix[2, 1] = 1
    matrix[3, 2] = 1
    return matrix


def _mp_modified_gram_schmidt(matrix: mp.matrix) -> tuple[mp.matrix, list[mp.mpf]]:
    rows, columns = matrix.rows, matrix.cols
    q = mp.matrix(rows, columns)
    diagonal: list[mp.mpf] = []
    for column in range(columns):
        vector = [matrix[row, column] for row in range(rows)]
        for prior in range(column):
            projection = sum(mp.conj(q[row, prior]) * vector[row] for row in range(rows))
            for row in range(rows):
                vector[row] -= projection * q[row, prior]
        norm = mp.sqrt(sum(abs(value) ** 2 for value in vector))
        if norm == 0:
            raise ArithmeticError("rank-deficient transfer basis during QR stabilization")
        diagonal.append(norm)
        for row in range(rows):
            q[row, column] = vector[row] / norm
    return q, diagonal


def _mp_qr_potential(onsite: np.ndarray, energy: complex, model: LongRangeModel, bits: int) -> float:
    with mp.workprec(bits):
        q = mp.eye(4)
        log_growth = [mp.mpf("0") for _ in range(4)]
        for onsite_value in onsite:
            q, diagonal = _mp_modified_gram_schmidt(
                _mp_transfer_matrix(energy, float(onsite_value), model) * q
            )
            for index, value in enumerate(diagonal):
                log_growth[index] += mp.log(abs(value))
        exponents = sorted(value / len(onsite) for value in log_growth)
        return float(exponents[2] + exponents[3] + mp.log(abs(model.t_2)))


def run_precision_pilot(config: dict, seed: int) -> tuple[list[dict], dict]:
    model = LongRangeModel()
    pilot = config["pilot"]
    paper = config["paper"]
    length = int(pilot["length"])
    realizations = int(pilot["realizations"])
    energies = [complex(float(item["real"]), float(item.get("imag", 0.0))) for item in paper["energies"]]
    precisions = [int(value) for value in paper["precision_bits"]]
    reference_bits = int(paper["reference_bits"])
    rng = np.random.default_rng(seed)
    onsite_sequences = [sample_onsite(length, float(paper["W"]), rng) for _ in range(realizations)]

    started = time.perf_counter()
    reference_started = time.perf_counter()
    reference = _mp_ed_potentials(onsite_sequences, energies, model, reference_bits)
    reference_seconds = time.perf_counter() - reference_started
    rows: list[dict] = []
    per_precision_seconds: dict[str, float] = {}
    for bits in precisions:
        precision_started = time.perf_counter()
        ed = _mp_ed_potentials(onsite_sequences, energies, model, bits)
        qr = [
            float(np.mean([_mp_qr_potential(onsite, energy, model, bits) for onsite in onsite_sequences]))
            for energy in energies
        ]
        per_precision_seconds[str(bits)] = time.perf_counter() - precision_started
        for energy_index, energy in enumerate(energies):
            rows.append(
                {
                    "precision_bits": bits,
                    "energy_real": energy.real,
                    "energy_imag": energy.imag,
                    "ed_potential": ed[energy_index],
                    "qr_potential": qr[energy_index],
                    "reference_256bit_ed_potential": reference[energy_index],
                    "ed_absolute_deviation": abs(ed[energy_index] - reference[energy_index]),
                    "qr_absolute_deviation": abs(qr[energy_index] - reference[energy_index]),
                }
            )
    elapsed = time.perf_counter() - started
    cubic_scale = (int(paper["length"]) / length) ** 3
    ensemble_scale = int(paper["realizations"]) / realizations
    projected_seconds = elapsed * cubic_scale * ensemble_scale
    projected_days = projected_seconds / 86400.0
    optimistic_a100_speedup = 50.0
    qr_better_at_64 = [
        row["qr_absolute_deviation"] < row["ed_absolute_deviation"]
        for row in rows
        if int(row["precision_bits"]) == 64
    ]
    summary = {
        "status": "pilot_completed",
        "paper_target": {
            "length": int(paper["length"]),
            "realizations": int(paper["realizations"]),
            "precision_bits": precisions,
            "reference_bits": reference_bits,
            "energies": [[energy.real, energy.imag] for energy in energies],
        },
        "pilot": {
            "length": length,
            "realizations": realizations,
            "elapsed_seconds": elapsed,
            "reference_seconds": reference_seconds,
            "per_precision_seconds": per_precision_seconds,
            "qr_more_accurate_than_ed_at_64bit_count": int(sum(qr_better_at_64)),
            "qr_more_accurate_than_ed_at_64bit_total": len(qr_better_at_64),
        },
        "resource_projection": {
            "model": "measured_pilot_times_dense_ED_O_L3_ensemble_ratio",
            "projected_paper_scale_seconds": projected_seconds,
            "projected_paper_scale_days": projected_days,
            "local_cpu_count": os.cpu_count(),
            "python_platform": sys.platform,
            "a100_precision_boundary": (
                "The reference contract uses 112-256-bit arbitrary-precision dense eigensolving and ensembles. "
                "A standard A100 FP32/FP64 path does not natively provide the required arithmetic precision."
            ),
            "optimistic_a100_speedup_factor": optimistic_a100_speedup,
            "optimistic_a100_projected_days": projected_days / optimistic_a100_speedup,
            "a100_conclusion": "available_a100_does_not_close_the_paper_scale_precision_and_time_boundary",
            "conclusion": "paper_scale_not_attempted_after_measured_pilot_projection",
        },
        "scientific_boundary": (
            "The pilot validates the independently written arbitrary-precision ED and QR paths. "
            "It does not promote the Fig. S3 precision-ordering claim because the published L=1000 x 1600 campaign was not executed."
        ),
    }
    return rows, summary


def run_gap_scaling(config: dict, seed: int) -> tuple[list[dict], dict]:
    model = LongRangeModel()
    lengths = [int(value) for value in config["lengths"]]
    reference_length = int(config["reference_length"])
    if reference_length in lengths:
        raise ValueError("reference_length must be separate from plotted lengths")
    energy = complex(float(config["energy"]["real"]), float(config["energy"]["imag"]))
    realizations = int(config["realizations"])
    rng = np.random.default_rng(seed)
    gap_samples = {length: [] for length in [*lengths, reference_length]}
    started = time.perf_counter()
    for _ in range(realizations):
        onsite = sample_onsite(reference_length, float(config["W"]), rng)
        for length in [*lengths, reference_length]:
            exponents = lyapunov_exponents(
                energy,
                onsite[:length],
                model,
                qr_interval=int(config["qr_interval"]),
            )
            gap_samples[length].append(float(exponents[2] - exponents[1]))
    mean_gaps = {length: float(np.mean(values)) for length, values in gap_samples.items()}
    reference_gap = mean_gaps[reference_length]
    deviations = np.asarray([abs(mean_gaps[length] - reference_gap) for length in lengths], dtype=float)
    log_deviations = np.log(np.maximum(deviations, np.finfo(float).tiny))
    length_array = np.asarray(lengths, dtype=float)
    exp_slope, exp_intercept = np.polyfit(length_array, log_deviations, 1)
    exp_prediction = exp_intercept + exp_slope * length_array
    power_slope, power_intercept = np.polyfit(np.log(length_array), log_deviations, 1)
    power_prediction = power_intercept + power_slope * np.log(length_array)
    exp_r2 = _r_squared(log_deviations, exp_prediction)
    power_r2 = _r_squared(log_deviations, power_prediction)
    rows = [
        {
            "length": length,
            "mean_lyapunov_gap": mean_gaps[length],
            "reference_length": reference_length,
            "reference_mean_lyapunov_gap": reference_gap,
            "absolute_gap_deviation": float(deviation),
            "log_absolute_gap_deviation": float(log_deviation),
            "realizations": realizations,
        }
        for length, deviation, log_deviation in zip(lengths, deviations, log_deviations)
    ]
    support_margin = float(config["exponential_r2_margin_over_power"])
    exponential_supported = bool(
        exp_slope < 0.0
        and exp_r2 >= float(config["minimum_exponential_r2"])
        and exp_r2 >= power_r2 + support_margin
    )
    return rows, {
        "status": "paper_feature_supported" if exponential_supported else "feature_not_resolved",
        "paper_reported_parameters": {
            "lengths": lengths,
            "reference_length": reference_length,
            "energy": [energy.real, energy.imag],
            "model": asdict(model),
            "W": float(config["W"]),
        },
        "declared_implementation_choice": {
            "realizations": realizations,
            "seed": seed,
            "qr_interval": int(config["qr_interval"]),
            "reason": "The supplement does not state the S4 disorder-ensemble count, realization identity, or QR interval.",
        },
        "fits": {
            "exponential": {"slope": float(exp_slope), "intercept": float(exp_intercept), "r_squared": exp_r2},
            "power_law": {"slope": float(power_slope), "intercept": float(power_intercept), "r_squared": power_r2},
            "required_exponential_r_squared": float(config["minimum_exponential_r2"]),
            "required_r_squared_margin_over_power": support_margin,
        },
        "runtime_seconds": time.perf_counter() - started,
        "scientific_boundary": (
            "The paper-reported size and energy grid are executed, but the unpublished ensemble/seed protocol prevents a paper-exact numerical identity claim."
        ),
    }


def run_gap_protocol_sensitivity(config: dict, seed: int) -> tuple[list[dict], dict]:
    """Test whether omitted S4 numerical choices change the claim verdict.

    The supplement does not report its disorder ensemble or QR interval. A
    missing protocol may only be treated as causal if reasonable choices can
    change the scientific outcome, so this sweep records that sensitivity
    instead of using underspecification to absorb a negative run.
    """

    base = copy.deepcopy(config["base"])
    rows: list[dict] = []
    started = time.perf_counter()
    for realization_count in config["realization_counts"]:
        for seed_offset in config["seed_offsets"]:
            for qr_interval in config["qr_intervals"]:
                protocol = copy.deepcopy(base)
                protocol["realizations"] = int(realization_count)
                protocol["qr_interval"] = int(qr_interval)
                run_seed = int(seed) + int(seed_offset)
                _, result = run_gap_scaling(protocol, run_seed)
                exponential = result["fits"]["exponential"]
                power_law = result["fits"]["power_law"]
                rows.append(
                    {
                        "realizations": int(realization_count),
                        "seed": run_seed,
                        "qr_interval": int(qr_interval),
                        "status": result["status"],
                        "exponential_slope": exponential["slope"],
                        "exponential_r_squared": exponential["r_squared"],
                        "power_law_r_squared": power_law["r_squared"],
                        "exponential_r2_advantage": exponential["r_squared"]
                        - power_law["r_squared"],
                    }
                )
    supported = [row for row in rows if row["status"] == "paper_feature_supported"]
    support_count = len(supported)
    if support_count == 0:
        conclusion = "robust_non_match_in_declared_protocol_sweep"
    elif support_count == len(rows):
        conclusion = "robust_support_in_declared_protocol_sweep"
    else:
        conclusion = "protocol_sensitive_mixed_verdicts"
    return rows, {
        "status": "completed",
        "source_trace": {
            "published": [
                "E0=-0.9328+0.2210i",
                "L=50,100,...,400",
                "L=1000 reference",
                "claimed exponential decay on a semi-log plot",
            ],
            "omitted": [
                "disorder realization count and identity",
                "averaging order",
                "QR stabilization interval",
            ],
            "source": "Published Supplement Appendix S6 and Fig. S4 caption",
        },
        "protocols_total": len(rows),
        "paper_feature_supported_total": support_count,
        "paper_feature_supported_fraction": support_count / len(rows) if rows else 0.0,
        "exponential_r_squared_range": [
            min(row["exponential_r_squared"] for row in rows),
            max(row["exponential_r_squared"] for row in rows),
        ],
        "power_law_r_squared_range": [
            min(row["power_law_r_squared"] for row in rows),
            max(row["power_law_r_squared"] for row in rows),
        ],
        "conclusion": conclusion,
        "runtime_seconds": time.perf_counter() - started,
        "scientific_boundary": (
            "This finite protocol sweep tests the named publication omissions; only a fresh reviewer may promote a robust non-match to a paper-error candidate."
        ),
    }


def _r_squared(observed: np.ndarray, predicted: np.ndarray) -> float:
    residual = float(np.sum((observed - predicted) ** 2))
    total = float(np.sum((observed - np.mean(observed)) ** 2))
    return 1.0 if total == 0.0 and residual == 0.0 else 1.0 - residual / total if total > 0.0 else 0.0


def _plot_precision(path: Path, rows: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.3), sharey=True)
    energies = sorted({(row["energy_real"], row["energy_imag"]) for row in rows})
    for axis, energy in zip(axes, energies):
        subset = [row for row in rows if (row["energy_real"], row["energy_imag"]) == energy]
        axis.semilogy([row["precision_bits"] for row in subset], [row["ed_absolute_deviation"] for row in subset], "o-", label="ED")
        axis.semilogy([row["precision_bits"] for row in subset], [row["qr_absolute_deviation"] for row in subset], "s-", label="QR")
        axis.set_title(f"E={energy[0]:g}{energy[1]:+g}i")
        axis.set_xlabel("arithmetic precision (bits)")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("absolute potential deviation")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_gap(path: Path, rows: list[dict], summary: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.asarray([row["length"] for row in rows], dtype=float)
    y = np.asarray([row["log_absolute_gap_deviation"] for row in rows], dtype=float)
    fit = summary["fits"]["exponential"]
    fig, axis = plt.subplots(figsize=(5.3, 3.5))
    axis.plot(x, y, "o", label="independent QR ensemble")
    axis.plot(x, fit["intercept"] + fit["slope"] * x, "-", label=f"exponential fit, R2={fit['r_squared']:.3f}")
    axis.set_xlabel("L")
    axis.set_ylabel(r"$\log |\Delta_\gamma^L-\Delta_\gamma^{1000}|$")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_additional_numerics(workspace: Path, config: dict, *, render_figures: bool = True) -> dict:
    workspace = workspace.resolve()
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    figures_dir = workspace / "outputs" / "figures"
    started = time.perf_counter()

    unidirectional_rows, unidirectional = run_unidirectional_claim(
        config["unidirectional"], int(config["seed"]) + 10
    )
    precision_rows, precision = run_precision_pilot(config["s3_precision"], int(config["seed"]) + 20)
    gap_rows, gap = run_gap_scaling(config["s4_gap_scaling"], int(config["seed"]) + 30)
    sensitivity_rows, sensitivity = run_gap_protocol_sensitivity(
        config["s4_protocol_sensitivity"], int(config["seed"]) + 40
    )

    write_csv(data_dir / "unidirectional_density.csv", unidirectional_rows)
    write_csv(data_dir / "supplement_s3_precision_pilot.csv", precision_rows)
    write_csv(data_dir / "supplement_s4_gap_scaling.csv", gap_rows)
    write_csv(data_dir / "supplement_s4_protocol_sensitivity.csv", sensitivity_rows)
    if render_figures:
        _plot_precision(figures_dir / "figs3_precision_pilot.png", precision_rows)
        _plot_gap(figures_dir / "figs4_gap_scaling.png", gap_rows, gap)

    result = {
        "status": "completed_with_declared_boundaries",
        "artifact_stage": config["artifact_stage"],
        "parameter_match": config["parameter_match"],
        "render_figures": render_figures,
        "runtime_seconds": time.perf_counter() - started,
        "unidirectional": unidirectional,
        "s3_precision": precision,
        "s4_gap_scaling": gap,
        "s4_protocol_sensitivity": sensitivity,
        "scientific_input_attestation": {
            "paper_or_source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "paper_text_used_only_to_author_the_frozen_config": True,
        },
    }
    write_json(checks_dir / "supplement_additional_numerics.json", result)
    write_json(
        checks_dir / "supplement_compute_benchmark.json",
        {
            "status": "measured",
            "s3_precision": precision["resource_projection"],
            "s4_gap_scaling_runtime_seconds": gap["runtime_seconds"],
            "s4_protocol_sensitivity": sensitivity,
        },
    )
    return result
