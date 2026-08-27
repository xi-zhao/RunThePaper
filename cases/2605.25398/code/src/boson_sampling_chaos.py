from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.stats import wasserstein_distance


PAPER_TIMES = np.array([1.0, 1.79, 29.29, 100.0, 1000.0])
DEFAULT_INPUT = (2, 3)


@dataclass(frozen=True)
class EnsembleSpec:
    label: str
    Lambda: float
    seed: int


CHAOTIC = EnsembleSpec(label="chaotic_GOE", Lambda=1000.0, seed=260525398)
INTEGRABLE = EnsembleSpec(label="integrable_Poisson", Lambda=0.01, seed=260525399)


def collision_free_pairs(modes: int) -> list[tuple[int, int]]:
    return list(combinations(range(modes), 2))


def lambda_from_Lambda(Lambda: float, dimension: int) -> float:
    return math.sqrt(2.0 * math.pi * Lambda / dimension)


def sample_goe(rng: np.random.Generator, dimension: int) -> np.ndarray:
    matrix = np.zeros((dimension, dimension), dtype=float)
    upper = rng.normal(0.0, math.sqrt(1.0 / dimension), size=(dimension, dimension))
    matrix += np.triu(upper, 1)
    matrix += matrix.T
    np.fill_diagonal(matrix, rng.normal(0.0, math.sqrt(2.0 / dimension), size=dimension))
    return matrix


def sample_hamiltonian(rng: np.random.Generator, dimension: int, Lambda: float) -> np.ndarray:
    h0 = np.diag(rng.normal(0.0, 1.0, size=dimension))
    v = sample_goe(rng, dimension)
    lam = lambda_from_Lambda(Lambda, dimension)
    return (h0 + lam * v) / math.sqrt(1.0 + lam * lam)


def diagonalize_ensemble(spec: EnsembleSpec, dimension: int, count: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(spec.seed + 1000 * dimension + count)
    samples = []
    for _ in range(count):
        hamiltonian = sample_hamiltonian(rng, dimension, spec.Lambda)
        eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
        samples.append((eigenvalues, eigenvectors))
    return samples


def unitary_from_eigendecomposition(eigenvalues: np.ndarray, eigenvectors: np.ndarray, time: float) -> np.ndarray:
    phases = np.exp(-1j * eigenvalues * time)
    return (eigenvectors * phases) @ eigenvectors.T


def conditional_two_photon_distribution(
    unitary: np.ndarray,
    input_pair: tuple[int, int] = DEFAULT_INPUT,
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    modes = unitary.shape[0]
    pairs = collision_free_pairs(modes)
    i, j = input_pair
    probabilities = []
    for r, s in pairs:
        amplitude = unitary[r, i] * unitary[s, j] + unitary[r, j] * unitary[s, i]
        probabilities.append(abs(amplitude) ** 2)
    probabilities = np.array(probabilities, dtype=float)
    total = probabilities.sum()
    if total <= 0:
        raise ValueError("collision-free probability mass is zero")
    return probabilities / total, pairs


def conditional_two_photon_trajectories(
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    times: np.ndarray,
    input_pair: tuple[int, int] = DEFAULT_INPUT,
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Return every conditional collision-free probability versus time.

    The returned array has shape ``(number_of_pairs, number_of_times)``.  The
    normalization is applied independently for every Hamiltonian realization
    and time before any ensemble average, matching Eqs. (S4)-(S7).
    """

    time_values = np.asarray(times, dtype=float)
    if time_values.ndim != 1 or time_values.size == 0:
        raise ValueError("times must be a non-empty one-dimensional array")
    modes = eigenvectors.shape[0]
    pairs = collision_free_pairs(modes)
    i, j = input_pair
    if not (0 <= i < modes and 0 <= j < modes and i != j):
        raise ValueError("input_pair must contain two distinct in-range modes")

    phases = np.exp(-1j * np.outer(eigenvalues, time_values))
    column_i = (eigenvectors * eigenvectors[i, :]) @ phases
    column_j = (eigenvectors * eigenvectors[j, :]) @ phases
    first = np.fromiter((pair[0] for pair in pairs), dtype=int)
    second = np.fromiter((pair[1] for pair in pairs), dtype=int)
    amplitudes = (
        column_i[first] * column_j[second]
        + column_j[first] * column_i[second]
    )
    probabilities = np.abs(amplitudes) ** 2
    retained_mass = probabilities.sum(axis=0)
    if np.any(retained_mass <= 0.0):
        raise ValueError("collision-free probability mass is zero")
    return probabilities / retained_mass[np.newaxis, :], pairs


def averaged_conditional_probability_curves(
    samples: list[tuple[np.ndarray, np.ndarray]],
    times: np.ndarray,
    input_pair: tuple[int, int] = DEFAULT_INPUT,
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Average paper-normalized collision-free trajectories over an ensemble."""

    if not samples:
        raise ValueError("samples must be non-empty")
    accumulated: np.ndarray | None = None
    pairs: list[tuple[int, int]] = []
    for eigenvalues, eigenvectors in samples:
        trajectories, pairs = conditional_two_photon_trajectories(
            eigenvalues,
            eigenvectors,
            times,
            input_pair=input_pair,
        )
        if accumulated is None:
            accumulated = np.zeros_like(trajectories)
        accumulated += trajectories
    assert accumulated is not None
    return accumulated / len(samples), pairs


def shannon_entropy(probabilities: np.ndarray) -> float:
    values = probabilities[probabilities > 0]
    return float(-np.sum(values * np.log(values)))


def participation_ratio(probabilities: np.ndarray) -> float:
    return float(1.0 / np.sum(probabilities**2))


def porter_thomas_w1(probabilities: np.ndarray, dimension: int) -> float:
    sorted_probs = np.sort(np.asarray(probabilities, dtype=float))
    quantiles = (np.arange(len(sorted_probs), dtype=float) + 0.5) / len(sorted_probs)
    porter_thomas = -np.log1p(-quantiles) / dimension
    return float(wasserstein_distance(sorted_probs, porter_thomas))


def spectral_form_factor_4(eigenvalues: np.ndarray, time: float) -> float:
    trace = np.sum(np.exp(-1j * eigenvalues * time))
    dimension = len(eigenvalues)
    return float(abs(trace) ** 4 / dimension**4)


def overlap_count(pair: tuple[int, int], input_pair: tuple[int, int] = DEFAULT_INPUT) -> int:
    return len(set(pair).intersection(input_pair))


def ensemble_metrics(
    samples: list[tuple[np.ndarray, np.ndarray]],
    times: np.ndarray,
    input_pair: tuple[int, int] = DEFAULT_INPUT,
    target_pair: tuple[int, int] = (2, 5),
    *,
    retain_probabilities: bool = True,
    retain_distribution_rows: bool = True,
) -> dict:
    dimension = samples[0][0].shape[0]
    output_pairs = collision_free_pairs(dimension)
    target_index = output_pairs.index(target_pair)
    rows = []
    distribution_rows = []
    otoc_rows = []
    all_probabilities_by_time: dict[float, list[float]] = {}

    for time in times:
        all_probabilities = []
        entropy_values = []
        pr_values = []
        target_values = []
        sff_values = []
        sector_values: dict[int, list[float]] = {0: [], 1: [], 2: []}

        for sample_index, (eigenvalues, eigenvectors) in enumerate(samples):
            unitary = unitary_from_eigendecomposition(eigenvalues, eigenvectors, float(time))
            probabilities, _ = conditional_two_photon_distribution(unitary, input_pair=input_pair)
            all_probabilities.extend(probabilities.tolist())
            entropy_values.append(shannon_entropy(probabilities))
            pr_values.append(participation_ratio(probabilities))
            target_values.append(float(probabilities[target_index]))
            sff_values.append(spectral_form_factor_4(eigenvalues, float(time)))

            if (
                retain_distribution_rows
                and sample_index < 5
                and float(time) in set(PAPER_TIMES.tolist())
            ):
                for pair, probability in zip(output_pairs, probabilities):
                    distribution_rows.append(
                        {
                            "time": float(time),
                            "sample_index": sample_index,
                            "output_pair": pair_name(pair),
                            "probability": float(probability),
                            "overlap": overlap_count(pair, input_pair),
                        }
                    )

            for pair, probability in zip(output_pairs, probabilities):
                sector_values[overlap_count(pair, input_pair)].append(float(probability))

        if retain_probabilities:
            all_probabilities_by_time[float(time)] = all_probabilities
        rows.append(
            {
                "time": float(time),
                "pt_wasserstein": porter_thomas_w1(np.array(all_probabilities), len(output_pairs)),
                "entropy_mean": float(np.mean(entropy_values)),
                "entropy_sem": float(np.std(entropy_values, ddof=1) / math.sqrt(len(entropy_values)))
                if len(entropy_values) > 1
                else 0.0,
                "participation_ratio_mean": float(np.mean(pr_values)),
                "participation_ratio_sem": float(np.std(pr_values, ddof=1) / math.sqrt(len(pr_values)))
                if len(pr_values) > 1
                else 0.0,
                "target_otoc_mean": float(np.mean(target_values)),
                "target_otoc_sem": float(np.std(target_values, ddof=1) / math.sqrt(len(target_values)))
                if len(target_values) > 1
                else 0.0,
                "sff4_mean": float(np.mean(sff_values)),
            }
        )
        for sector, values in sector_values.items():
            otoc_rows.append(
                {
                    "time": float(time),
                    "overlap": sector,
                    "probability_mean": float(np.mean(values)),
                    "probability_sem": float(np.std(values, ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.0,
                }
            )

    return {
        "metrics": rows,
        "distribution_rows": distribution_rows,
        "otoc_sector_rows": otoc_rows,
        "probabilities_by_time": all_probabilities_by_time,
    }


def pair_name(pair: tuple[int, int]) -> str:
    return f"{pair[0] + 1}-{pair[1] + 1}"


def run_sparse_paper_scale() -> dict:
    records = {}
    for spec in [INTEGRABLE, CHAOTIC]:
        rows = []
        distribution_rows = []
        otoc_sector_rows = []
        for time in PAPER_TIMES:
            count = 75 if spec == CHAOTIC and abs(float(time) - 1.79) < 1e-9 else 16
            samples = diagonalize_ensemble(spec, dimension=8, count=count)
            result = ensemble_metrics(samples, np.array([time]))
            for row in result["metrics"]:
                row["sample_count"] = count
                rows.append(row)
            distribution_rows.extend(result["distribution_rows"])
            otoc_sector_rows.extend(result["otoc_sector_rows"])
        records[spec.label] = {
            "metrics": rows,
            "distribution_rows": distribution_rows,
            "otoc_sector_rows": otoc_sector_rows,
        }
    return records


def run_ideal_curves(count: int = 320) -> dict:
    early = np.linspace(0.05, 4.0, 76)
    late = np.geomspace(4.2, 1000.0, 84)
    times = np.unique(np.concatenate([early, late, PAPER_TIMES]))
    records = {}
    for spec in [INTEGRABLE, CHAOTIC]:
        samples = diagonalize_ensemble(spec, dimension=8, count=count)
        records[spec.label] = ensemble_metrics(samples, times)
    return records


def run_scaling_summary(count: int = 180) -> list[dict]:
    times = np.unique(np.concatenate([np.linspace(0.2, 4.0, 55), np.array([1.79])]))
    rows = []
    for modes in [4, 6, 8, 10, 12, 14]:
        input_pair = (0, 1) if modes < 4 else DEFAULT_INPUT
        target_pair = (0, 2) if modes < 6 else (2, 5)
        for spec in [INTEGRABLE, CHAOTIC]:
            samples = diagonalize_ensemble(spec, dimension=modes, count=count)
            result = ensemble_metrics(samples, times, input_pair=input_pair, target_pair=target_pair)
            metrics = result["metrics"]
            entropy_values = np.array([row["entropy_mean"] for row in metrics])
            pt_values = np.array([row["pt_wasserstein"] for row in metrics])
            pr_values = np.array([row["participation_ratio_mean"] for row in metrics])
            sff_values = np.array([row["sff4_mean"] for row in metrics])
            d = math.comb(modes, 2)
            haar_entropy = -1.0 + sum(1.0 / i for i in range(1, d + 1))
            rows.append(
                {
                    "modes": modes,
                    "D": d,
                    "ensemble": spec.label,
                    "time_min_sff": float(times[int(np.argmin(sff_values))]),
                    "time_min_pt": float(times[int(np.argmin(pt_values))]),
                    "time_max_entropy": float(times[int(np.argmax(entropy_values))]),
                    "time_max_pr": float(times[int(np.argmax(pr_values))]),
                    "min_pt_wasserstein": float(np.min(pt_values)),
                    "max_entropy": float(np.max(entropy_values)),
                    "haar_entropy": float(haar_entropy),
                    "entropy_gap_percent": float(100.0 * abs(haar_entropy - np.max(entropy_values)) / haar_entropy),
                }
            )
    return rows


def conditional_probability_demo(seed: int = 2605) -> list[dict]:
    rng = np.random.default_rng(seed)
    n0 = 36
    p_grid = np.linspace(0.0, 0.32, 260)
    rows = []
    for d in [4, 8, 16, 28, 34]:
        draws = rng.exponential(1.0, size=(120000, n0))
        conditional = draws[:, :d] / draws[:, :d].sum(axis=1, keepdims=True)
        values = conditional[:, 0]
        hist, edges = np.histogram(values, bins=p_grid, density=True)
        centers = 0.5 * (edges[:-1] + edges[1:])
        for p, density in zip(centers, hist):
            rows.append(
                {
                    "D": d,
                    "p": float(p),
                    "conditional_density": float(density),
                    "porter_thomas_density": float(d * math.exp(-d * p)),
                }
            )
    return rows


def averaged_otoc_series(
    samples: list[tuple[np.ndarray, np.ndarray]],
    times: np.ndarray,
    output_pair: tuple[int, int],
    input_pair: tuple[int, int] = DEFAULT_INPUT,
) -> np.ndarray:
    curves, pairs = averaged_conditional_probability_curves(
        samples,
        times,
        input_pair=input_pair,
    )
    return curves[pairs.index(output_pair)]


def run_otoc_appendix(count: int = 260) -> dict:
    time_short = np.geomspace(1e-3, 0.18, 80)
    time_full = np.unique(np.concatenate([np.linspace(0.05, 4.0, 86), np.geomspace(4.2, 1000.0, 92)]))
    time_long = np.linspace(300.0, 1000.0, 700)
    rows_short = []
    rows_full = []
    rows_long = []
    rows_fft_pr = []

    for spec in [INTEGRABLE, CHAOTIC]:
        samples = diagonalize_ensemble(spec, dimension=8, count=count)
        full_curves, full_pairs = averaged_conditional_probability_curves(samples, time_full)
        short_curves, short_pairs = averaged_conditional_probability_curves(samples, time_short)
        long_curves, long_pairs = averaged_conditional_probability_curves(samples, time_long)
        for pair_index, pair in enumerate(full_pairs):
            overlap = overlap_count(pair, DEFAULT_INPUT)
            full_series = full_curves[pair_index]
            for time, value in zip(time_full, full_series):
                rows_full.append(
                    {
                        "ensemble": spec.label,
                        "output_pair": pair_name(pair),
                        "overlap": overlap,
                        "time": float(time),
                        "otoc": float(value),
                    }
                )

            # Fig. S5 says all collision-free configurations, so the initial
            # configuration belongs to the full curves above.  Fig. S6
            # explicitly excludes it from the power-law and FFT analyses.
            if pair == DEFAULT_INPUT:
                continue
            short_series = short_curves[short_pairs.index(pair)]
            for time, value in zip(time_short, short_series):
                rows_short.append(
                    {
                        "ensemble": spec.label,
                        "output_pair": pair_name(pair),
                        "overlap": overlap,
                        "time": float(time),
                        "otoc": float(value),
                    }
                )

            long_series = long_curves[long_pairs.index(pair)]
            normalized = long_series / max(float(np.mean(long_series)), 1e-15) - 1.0
            spectrum = np.abs(np.fft.rfft(normalized)) ** 2
            freqs = np.fft.rfftfreq(len(normalized), d=float(time_long[1] - time_long[0]))
            positive = freqs > 0
            spectrum = spectrum[positive]
            freqs = freqs[positive]
            spectrum_sum = float(spectrum.sum())
            if spectrum_sum > 0:
                weights = spectrum / spectrum_sum
                fft_pr = float(1.0 / np.sum(weights**2))
            else:
                weights = spectrum
                fft_pr = 0.0
            rows_fft_pr.append(
                {
                    "ensemble": spec.label,
                    "output_pair": pair_name(pair),
                    "overlap": overlap,
                    "fft_participation_ratio": fft_pr,
                }
            )
            if pair == (3, 4):
                for frequency, weight in zip(freqs, weights):
                    rows_long.append(
                        {
                            "ensemble": spec.label,
                            "frequency": float(frequency),
                            "normalized_power": float(weight),
                        }
                    )
    return {"full": rows_full, "short": rows_short, "fft_spectrum": rows_long, "fft_pr": rows_fft_pr}


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_case(workspace: Path) -> dict:
    data_dir = workspace / "outputs" / "data"
    check_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)

    sparse = run_sparse_paper_scale()
    ideal = run_ideal_curves()
    scaling = run_scaling_summary()
    conditional = conditional_probability_demo()
    otoc = run_otoc_appendix()

    for ensemble, payload in sparse.items():
        write_csv(data_dir / f"sparse_{ensemble}_metrics.csv", payload["metrics"])
        write_csv(data_dir / f"sparse_{ensemble}_output_distributions.csv", payload["distribution_rows"])
        write_csv(data_dir / f"sparse_{ensemble}_otoc_sectors.csv", payload["otoc_sector_rows"])

    for ensemble, payload in ideal.items():
        write_csv(data_dir / f"ideal_{ensemble}_metrics.csv", payload["metrics"])
        write_csv(data_dir / f"ideal_{ensemble}_otoc_sectors.csv", payload["otoc_sector_rows"])

    write_csv(data_dir / "appendix_scaling_summary.csv", scaling)
    write_csv(data_dir / "appendix_conditional_probability_demo.csv", conditional)
    write_csv(data_dir / "appendix_ideal_otocs_full.csv", otoc["full"])
    write_csv(data_dir / "appendix_otoc_short_time.csv", otoc["short"])
    write_csv(data_dir / "appendix_otoc_fft_spectrum.csv", otoc["fft_spectrum"])
    write_csv(data_dir / "appendix_otoc_fft_pr.csv", otoc["fft_pr"])

    checks = build_checks(sparse, ideal, otoc)
    write_json(check_dir / "reproduction_feature_checks.json", checks)
    return checks


def build_checks(sparse: dict, ideal: dict, otoc: dict) -> dict:
    chaotic_rows = sparse[CHAOTIC.label]["metrics"]
    integrable_rows = sparse[INTEGRABLE.label]["metrics"]
    row_c = min(chaotic_rows, key=lambda row: abs(row["time"] - 1.79))
    row_i = min(integrable_rows, key=lambda row: abs(row["time"] - 1.79))

    chaotic_ideal = ideal[CHAOTIC.label]["metrics"]
    min_pt_row = min(chaotic_ideal, key=lambda row: row["pt_wasserstein"])
    max_entropy_row = max(chaotic_ideal, key=lambda row: row["entropy_mean"])
    min_sff_row = min(chaotic_ideal, key=lambda row: row["sff4_mean"])

    short_rows = otoc["short"]
    slopes = {}
    for overlap in [0, 1]:
        grouped = [row for row in short_rows if row["ensemble"] == CHAOTIC.label and row["overlap"] == overlap]
        by_time: dict[float, list[float]] = {}
        for row in grouped:
            by_time.setdefault(row["time"], []).append(row["otoc"])
        times = np.array(sorted(by_time.keys()))
        values = np.array([np.mean(by_time[float(time)]) for time in times])
        mask = (values > 0) & (times < 0.08)
        slope = np.polyfit(np.log(times[mask]), np.log(values[mask]), 1)[0]
        slopes[f"overlap_{overlap}"] = float(slope)

    fft_pr_rows = otoc["fft_pr"]
    fft_chaotic = np.mean([row["fft_participation_ratio"] for row in fft_pr_rows if row["ensemble"] == CHAOTIC.label])
    fft_integrable = np.mean([row["fft_participation_ratio"] for row in fft_pr_rows if row["ensemble"] == INTEGRABLE.label])

    checks = {
        "status": "passed",
        "paper_feature_checks": {
            "chaotic_pt_distance_dips_near_t_star": {
                "observed_min_time": min_pt_row["time"],
                "paper_t_star": 1.79,
                "passed": bool(abs(min_pt_row["time"] - 1.79) < 0.35),
            },
            "chaotic_entropy_peaks_near_t_star": {
                "observed_max_time": max_entropy_row["time"],
                "paper_t_star": 1.79,
                "passed": bool(abs(max_entropy_row["time"] - 1.79) < 0.45),
            },
            "chaotic_sff_minimum_near_t_star": {
                "observed_min_time": min_sff_row["time"],
                "paper_t_star": 1.79,
                "passed": bool(abs(min_sff_row["time"] - 1.79) < 0.55),
            },
            "chaotic_pr_exceeds_integrable_at_t_star": {
                "chaotic_pr": row_c["participation_ratio_mean"],
                "integrable_pr": row_i["participation_ratio_mean"],
                "passed": bool(row_c["participation_ratio_mean"] > 5.0 * row_i["participation_ratio_mean"]),
            },
            "chaotic_entropy_exceeds_integrable_at_t_star": {
                "chaotic_entropy": row_c["entropy_mean"],
                "integrable_entropy": row_i["entropy_mean"],
                "passed": bool(row_c["entropy_mean"] > row_i["entropy_mean"] + 1.5),
            },
            "short_time_otoc_power_laws": {
                "overlap_1_expected": 2.0,
                "overlap_1_observed": slopes["overlap_1"],
                "overlap_0_expected": 4.0,
                "overlap_0_observed": slopes["overlap_0"],
                "passed": bool(1.5 < slopes["overlap_1"] < 2.6 and 3.1 < slopes["overlap_0"] < 4.9),
            },
            "chaotic_fft_pr_exceeds_integrable": {
                "chaotic_mean_fft_pr": float(fft_chaotic),
                "integrable_mean_fft_pr": float(fft_integrable),
                "passed": bool(fft_chaotic > fft_integrable),
            },
        },
    }
    checks["status"] = "passed" if all(item["passed"] for item in checks["paper_feature_checks"].values()) else "partial"
    return checks
