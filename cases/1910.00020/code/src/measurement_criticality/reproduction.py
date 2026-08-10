"""Numerical reproduction of every quantitative panel in arXiv:1910.00020.

The module reads only the declared JSON configuration.  It never reads the
paper, source figures, author code, or author numerical arrays.  Paper-size
Monte Carlo metadata were not published, so the run is explicitly reduced
scale while preserving the printed circuit, observables, and physical rates.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import numpy as np

from .stabilizer import (
    MixedStabilizerState,
    StabilizerState,
    insert_bell_pair,
    two_qubit_symplectic_group,
)


TARGET_FILES = {
    "T001": "T001_main_fig1b_transition.npz",
    "T002": "T002_main_fig2a_lightcone.npz",
    "T003": "T003_main_fig2b_cutoff_decoder.npz",
    "T004": "T004_main_fig3a_surface_order.npz",
    "T005": "T005_main_fig3b_cylinder.npz",
    "T006": "T006_main_fig3c_strip.npz",
    "T007": "T007_supp_figS1_lightcones.npz",
    "T008": "T008_supp_figS2_purification.npz",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _save(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def _pairs(length: int, layer: int, periodic: bool) -> list[tuple[int, int]]:
    if layer % 2 == 0:
        return [(site, site + 1) for site in range(0, length - 1, 2)]
    pairs = [(site, site + 1) for site in range(1, length - 1, 2)]
    if periodic and length % 2 == 0:
        pairs.append((length - 1, 0))
    return pairs


def _distance(site: int, origin: int, length: int, periodic: bool) -> int:
    direct = abs(site - origin)
    return min(direct, length - direct) if periodic else direct


def _signed_distance(site: int, origin: int, length: int) -> int:
    return int((site - origin + length // 2) % length - length // 2)


def _random_layer(
    state: StabilizerState,
    length: int,
    layer: int,
    measurement_rate: float,
    periodic: bool,
    rng: np.random.Generator,
    measurement_allowed: Callable[[int], bool] | None = None,
    measurement_observer: Callable[[int], None] | None = None,
) -> None:
    cliffords = two_qubit_symplectic_group()
    for first, second in _pairs(length, layer, periodic):
        matrix = cliffords[int(rng.integers(len(cliffords)))]
        state.apply_two_qubit(first, second, matrix)
    attempts = rng.random(length) < measurement_rate
    for site in np.flatnonzero(attempts):
        site = int(site)
        if measurement_allowed is not None and not measurement_allowed(site):
            continue
        if measurement_observer is not None:
            measurement_observer(site)
        else:
            state.measure_z(site)


def _evolve(
    state: StabilizerState,
    length: int,
    layers: int,
    measurement_rate: float,
    periodic: bool,
    rng: np.random.Generator,
    layer_offset: int = 0,
    measurement_allowed: Callable[[int], bool] | None = None,
) -> None:
    for step in range(layers):
        _random_layer(
            state,
            length,
            layer_offset + step,
            measurement_rate,
            periodic,
            rng,
            measurement_allowed,
        )


def _one_reference_survival(
    length: int,
    measurement_rate: float,
    trajectories: int,
    rng: np.random.Generator,
    pre_layers: int,
    post_layers: int,
    pre_rate: float,
    periodic: bool = True,
) -> tuple[float, float]:
    values = np.zeros(trajectories, dtype=float)
    for trajectory in range(trajectories):
        state = StabilizerState.product_zero(length + 1)
        reference = length
        if pre_layers:
            _evolve(state, length, pre_layers, pre_rate, periodic, rng)
        insert_bell_pair(state, reference, length // 2)
        for layer in range(post_layers):
            _random_layer(state, length, pre_layers + layer, measurement_rate, periodic, rng)
            if state.entropy([reference]) == 0:
                break
        values[trajectory] = state.entropy([reference])
    mean = float(values.mean())
    error = float(values.std(ddof=1) / np.sqrt(trajectories)) if trajectories > 1 else 0.0
    return mean, error


def _run_transition(config: dict[str, Any], output: Path, rng: np.random.Generator) -> dict[str, Any]:
    target = config["targets"]["transition"]
    sizes = np.asarray(target["sizes"], dtype=int)
    rates = np.asarray(target["measurement_rates"], dtype=float)
    trajectories = int(target["trajectories"])
    entropy = np.zeros((len(sizes), len(rates)))
    stderr = np.zeros_like(entropy)
    for size_index, length in enumerate(sizes):
        for rate_index, rate in enumerate(rates):
            entropy[size_index, rate_index], stderr[size_index, rate_index] = _one_reference_survival(
                int(length),
                float(rate),
                trajectories,
                rng,
                pre_layers=int(target["encoding_layers_per_L"] * length),
                post_layers=int(target["measured_layers_per_L"] * length),
                pre_rate=0.0,
            )
    variance = np.var(entropy[-min(3, len(sizes)) :], axis=0)
    estimated_pc = float(rates[int(np.argmin(variance))])
    paper_pc = float(config["paper_parameters"]["critical_rate_main"])
    nu = float(config["paper_parameters"]["nu"])
    collapse_x = np.asarray([(rates - paper_pc) * length ** (1.0 / nu) for length in sizes])
    _save(
        output / TARGET_FILES["T001"],
        sizes=sizes,
        measurement_rates=rates,
        entropy=entropy,
        stderr=stderr,
        collapse_x=collapse_x,
        paper_pc=paper_pc,
        paper_nu=nu,
        estimated_pc=estimated_pc,
        trajectories=trajectories,
    )
    return {
        "estimated_crossing_rate": estimated_pc,
        "low_rate_mean": float(entropy[:, 0].mean()),
        "high_rate_mean": float(entropy[:, -1].mean()),
        "all_probabilities_bounded": bool(np.all((entropy >= 0.0) & (entropy <= 1.0))),
    }


def _decoding_heatmap(
    length: int,
    pre_layers: int,
    pre_rate: float,
    post_rate: float,
    duration: int,
    trajectories: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.arange(-length // 2, length // 2, dtype=int)
    counts = np.zeros((duration, len(displacement)), dtype=float)
    origin = length // 2
    for _ in range(trajectories):
        state = StabilizerState.product_zero(length + 1)
        reference = length
        if pre_layers:
            _evolve(state, length, pre_layers, pre_rate, True, rng)
        insert_bell_pair(state, reference, origin)
        alive = True
        for time in range(duration):
            if not alive:
                break

            def observe(site: int) -> None:
                nonlocal alive
                before = state.entropy([reference])
                state.measure_z(site)
                after = state.entropy([reference])
                drop = before - after
                if drop:
                    column = _signed_distance(site, origin, length) + length // 2
                    counts[time, column] += drop
                    alive = False

            _random_layer(
                state,
                length,
                pre_layers + time,
                post_rate,
                True,
                rng,
                measurement_observer=observe,
            )
    return displacement, counts / trajectories


def _run_main_lightcone(config: dict[str, Any], output: Path, rng: np.random.Generator) -> dict[str, Any]:
    target = config["targets"]["main_lightcone"]
    displacement, delta = _decoding_heatmap(
        int(target["L"]),
        0,
        0.0,
        float(config["paper_parameters"]["volume_rate"]),
        int(target["duration"]),
        int(target["trajectories"]),
        rng,
    )
    time = np.arange(1, delta.shape[0] + 1)
    causal = np.abs(displacement)[None, :] <= time[:, None]
    total = float(delta.sum())
    inside = float(delta[causal].sum())
    _save(
        output / TARGET_FILES["T002"],
        displacement=displacement,
        time=np.arange(delta.shape[0]),
        mean_delta_entropy=delta,
        log10_mean_delta_entropy=np.log10(np.maximum(delta, 1.0e-6)),
        trajectories=int(target["trajectories"]),
    )
    return {
        "purification_probability": total,
        "causal_weight_fraction": inside / total if total else 0.0,
        "peak_displacement": int(displacement[np.unravel_index(np.argmax(delta), delta.shape)[1]]),
    }


def _cutoff_curve(
    length: int,
    rate: float,
    cutoff: int | None,
    duration: int,
    trajectories: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Reference entropy conditioned on a spatially truncated record.

    Measurements are physically performed at every sampled site.  Outcomes
    inside ``cutoff`` are retained and condition the stabilizer state; outcomes
    outside it are marginalized with the exact dephasing channel.  This is not
    equivalent to omitting those measurements from the circuit.
    """

    means, errors = _cutoff_curves(
        length, rate, [cutoff], duration, trajectories, rng
    )
    return means[0], errors[0]


def _cutoff_curves(
    length: int,
    rate: float,
    cutoffs: list[int | None],
    duration: int,
    trajectories: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Coupled partial-record curves on identical random circuit samples.

    Common random numbers are scientifically important here: every cutoff sees
    the same gates and physical measurement locations, differing only in which
    outcomes enter its record.  The data-processing order can then be checked
    trajectory by trajectory instead of being obscured by independent Monte
    Carlo noise.
    """

    origin = length // 2
    samples = np.zeros((trajectories, len(cutoffs), duration + 1), dtype=float)
    cliffords = two_qubit_symplectic_group()
    for trajectory in range(trajectories):
        states = [MixedStabilizerState.product_zero(length + 1) for _ in cutoffs]
        reference = length
        for state in states:
            insert_bell_pair(state, reference, origin)
        samples[trajectory, :, 0] = 1.0
        for time in range(duration):
            gates = []
            for first, second in _pairs(length, time, True):
                matrix = cliffords[int(rng.integers(len(cliffords)))]
                gates.append((first, second, matrix))
            attempts = [int(site) for site in np.flatnonzero(rng.random(length) < rate)]
            for cutoff_index, (cutoff, state) in enumerate(zip(cutoffs, states)):
                for first, second, matrix in gates:
                    state.apply_two_qubit(first, second, matrix)
                for site in attempts:
                    recorded = cutoff is None or _distance(site, origin, length, True) <= cutoff
                    state.measure_z(site, record_outcome=recorded)
                samples[trajectory, cutoff_index, time + 1] = state.entropy([reference])
    means = samples.mean(axis=0)
    errors = samples.std(axis=0, ddof=1) / np.sqrt(trajectories)
    return means, errors


def _run_cutoff(config: dict[str, Any], output: Path, rng: np.random.Generator) -> dict[str, Any]:
    target = config["targets"]["cutoff_decoder"]
    rates = np.asarray(config["paper_parameters"]["off_critical_rates"], dtype=float)
    cutoff_labels = list(target["cutoffs"])
    cutoffs = [None if item == "full" else int(item) for item in cutoff_labels]
    entropy = np.zeros((len(rates), len(cutoffs), int(target["duration"]) + 1))
    stderr = np.zeros_like(entropy)
    for rate_index, rate in enumerate(rates):
        entropy[rate_index], stderr[rate_index] = _cutoff_curves(
            int(target["L"]),
            float(rate),
            cutoffs,
            int(target["duration"]),
            int(target["trajectories"]),
            rng,
        )
    numeric_cutoffs = np.asarray([-1 if value is None else value for value in cutoffs], dtype=int)
    _save(
        output / TARGET_FILES["T003"],
        measurement_rates=rates,
        cutoffs=numeric_cutoffs,
        time=np.arange(entropy.shape[-1]),
        entropy=entropy,
        stderr=stderr,
        trajectories=int(target["trajectories"]),
        conditioning_model=np.asarray(
            "exact mixed-stabilizer conditioning; unrecorded outcomes are dephased"
        ),
    )
    return {
        "low_rate_final_full": float(entropy[0, -1, -1]),
        "high_rate_final_full": float(entropy[1, -1, -1]),
        "curves_bounded": bool(np.all((entropy >= 0.0) & (entropy <= 1.0))),
        "exact_incomplete_record_channel": True,
        "record_data_processing_passed": bool(
            np.all(entropy[:, :-1] >= entropy[:, 1:] - 1.0e-12)
        ),
    }


def _run_surface_order(config: dict[str, Any], output: Path, rng: np.random.Generator) -> dict[str, Any]:
    target = config["targets"]["surface_order"]
    sizes = np.asarray(target["sizes"], dtype=int)
    rates = np.asarray(target["measurement_rates"], dtype=float)
    trajectories = int(target["trajectories"])
    entropy = np.zeros((len(sizes), len(rates)))
    stderr = np.zeros_like(entropy)
    for size_index, length in enumerate(sizes):
        for rate_index, rate in enumerate(rates):
            entropy[size_index, rate_index], stderr[size_index, rate_index] = _one_reference_survival(
                int(length),
                float(rate),
                trajectories,
                rng,
                pre_layers=0,
                post_layers=2 * int(length),
                pre_rate=0.0,
            )
    pc = float(config["paper_parameters"]["critical_rate_correlations"])
    largest = entropy[-1]
    fit_mask = (rates < pc - 0.008) & (largest > 0.0)
    beta_fit = float(np.polyfit(np.log(pc - rates[fit_mask]), np.log(largest[fit_mask]), 1)[0])
    _save(
        output / TARGET_FILES["T004"],
        sizes=sizes,
        measurement_rates=rates,
        entropy=entropy,
        stderr=stderr,
        paper_pc=pc,
        paper_beta_surface=float(config["paper_parameters"]["beta_surface"]),
        fitted_beta_surface=beta_fit,
        trajectories=trajectories,
    )
    return {
        "fitted_beta_surface": beta_fit,
        "mean_monotone_fraction": float(np.mean(np.diff(entropy, axis=1) <= 0.08)),
        "all_probabilities_bounded": bool(np.all((entropy >= 0.0) & (entropy <= 1.0))),
    }


def _two_reference_curve(
    length: int,
    pre_layers: int,
    post_layers: int,
    rate: float,
    periodic: bool,
    sites: tuple[int, int],
    trajectories: int,
    rng: np.random.Generator,
) -> np.ndarray:
    accumulator = np.zeros(post_layers + 1, dtype=float)
    for _ in range(trajectories):
        state = StabilizerState.product_zero(length + 2)
        references = (length, length + 1)
        if pre_layers:
            _evolve(state, length, pre_layers, rate, periodic, rng)
        insert_bell_pair(state, references[0], sites[0])
        insert_bell_pair(state, references[1], sites[1])
        accumulator[0] += state.mutual_information([references[0]], [references[1]])
        for time in range(post_layers):
            _random_layer(state, length, pre_layers + time, rate, periodic, rng)
            accumulator[time + 1] += state.mutual_information([references[0]], [references[1]])
    return accumulator / trajectories


def _scaled_mutual_branch(
    sizes: np.ndarray,
    rate: float,
    pre_layers_per_L: int,
    post_layers_per_L: int,
    periodic: bool,
    site_selector: Callable[[int], tuple[int, int]],
    trajectories: int,
    exponent: float,
    grid: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    raw = np.zeros((len(sizes), len(grid)))
    for index, length in enumerate(sizes):
        curve = _two_reference_curve(
            int(length),
            pre_layers_per_L * int(length),
            post_layers_per_L * int(length),
            rate,
            periodic,
            site_selector(int(length)),
            trajectories,
            rng,
        )
        local_time = np.arange(len(curve)) / float(length)
        raw[index] = np.interp(grid, local_time, curve)
    scaled = raw * sizes[:, None] ** exponent
    return raw, scaled


def _run_correlations(config: dict[str, Any], output: Path, rng: np.random.Generator) -> dict[str, Any]:
    target = config["targets"]["correlations"]
    sizes = np.asarray(target["sizes"], dtype=int)
    time_over_L = np.linspace(0.0, float(target["post_layers_per_L"]), int(target["scaled_time_points"]))
    rate = float(config["paper_parameters"]["critical_rate_correlations"])
    trajectories = int(target["trajectories"])
    eta = float(config["paper_parameters"]["eta_bulk"])
    eta_parallel_1 = float(config["paper_parameters"]["eta_parallel_1"])
    eta_parallel_2 = float(config["paper_parameters"]["eta_parallel_2"])
    eta_parallel_3 = float(config["paper_parameters"]["eta_parallel_3"])
    surface_raw, surface_scaled = _scaled_mutual_branch(
        sizes, rate, 0, int(target["post_layers_per_L"]), True,
        lambda length: (0, length // 2), trajectories, eta_parallel_1, time_over_L, rng,
    )
    bulk_raw, bulk_scaled = _scaled_mutual_branch(
        sizes, rate, 4, int(target["post_layers_per_L"]), True,
        lambda length: (0, length // 2), trajectories, eta, time_over_L, rng,
    )
    end_raw, end_scaled = _scaled_mutual_branch(
        sizes, rate, 4, int(target["post_layers_per_L"]), False,
        lambda length: (0, length - 1), trajectories, eta_parallel_2, time_over_L, rng,
    )
    mixed_exponent = 0.5 * (eta + eta_parallel_3)
    mixed_raw, mixed_scaled = _scaled_mutual_branch(
        sizes, rate, 4, int(target["post_layers_per_L"]), False,
        lambda length: (0, length // 2), trajectories, mixed_exponent, time_over_L, rng,
    )
    _save(
        output / TARGET_FILES["T005"],
        sizes=sizes,
        time_over_L=time_over_L,
        surface_raw=surface_raw,
        surface_scaled=surface_scaled,
        bulk_raw=bulk_raw,
        bulk_scaled=bulk_scaled,
        eta_surface=eta_parallel_1,
        eta_bulk=eta,
        trajectories=trajectories,
    )
    _save(
        output / TARGET_FILES["T006"],
        sizes=sizes,
        time_over_L=time_over_L,
        end_to_end_raw=end_raw,
        end_to_end_scaled=end_scaled,
        boundary_to_bulk_raw=mixed_raw,
        boundary_to_bulk_scaled=mixed_scaled,
        eta_end_to_end=eta_parallel_2,
        eta_boundary_to_bulk=mixed_exponent,
        trajectories=trajectories,
    )
    return {
        "cylinder_peak_surface": float(surface_raw.max()),
        "cylinder_peak_bulk": float(bulk_raw.max()),
        "strip_peak_end_to_end": float(end_raw.max()),
        "strip_peak_mixed": float(mixed_raw.max()),
        "mutual_information_nonnegative": bool(
            np.all(surface_raw >= -1.0e-12)
            and np.all(bulk_raw >= -1.0e-12)
            and np.all(end_raw >= -1.0e-12)
            and np.all(mixed_raw >= -1.0e-12)
        ),
    }


def _run_supp_lightcones(config: dict[str, Any], output: Path, rng: np.random.Generator) -> dict[str, Any]:
    target = config["targets"]["supp_lightcones"]
    rate = float(config["paper_parameters"]["volume_rate"])
    common = {
        "length": int(target["L"]),
        "pre_layers": int(target["pre_layers_per_L"] * target["L"]),
        "post_rate": rate,
        "duration": int(target["duration"]),
        "trajectories": int(target["trajectories"]),
    }
    displacement, volume = _decoding_heatmap(pre_rate=rate, rng=rng, **common)
    _, pseudorandom = _decoding_heatmap(pre_rate=0.0, rng=rng, **common)
    _save(
        output / TARGET_FILES["T007"],
        displacement=displacement,
        time=np.arange(volume.shape[0]),
        volume_state_delta=volume,
        pseudorandom_state_delta=pseudorandom,
        log10_volume_state_delta=np.log10(np.maximum(volume, 1.0e-6)),
        log10_pseudorandom_state_delta=np.log10(np.maximum(pseudorandom, 1.0e-6)),
        trajectories=int(target["trajectories"]),
    )
    return {
        "volume_state_purification_probability": float(volume.sum()),
        "pseudorandom_state_purification_probability": float(pseudorandom.sum()),
        "both_have_nonzero_lightcones": bool(volume.sum() > 0 and pseudorandom.sum() > 0),
    }


def _reference_entropy_curve(
    length: int,
    references_count: int,
    rate: float,
    layers: int,
    trajectories: int,
    rng: np.random.Generator,
) -> np.ndarray:
    accumulator = np.zeros(layers + 1, dtype=float)
    center = length // 2 - references_count // 2
    sites = tuple(range(center, center + references_count))
    references = tuple(range(length, length + references_count))
    for _ in range(trajectories):
        state = StabilizerState.product_zero(length + references_count)
        for reference, site in zip(references, sites):
            insert_bell_pair(state, reference, site)
        accumulator[0] += state.entropy(references)
        for time in range(layers):
            _random_layer(state, length, time, rate, True, rng)
            accumulator[time + 1] += state.entropy(references)
    return accumulator / trajectories


def _fit_decay_exponent(sizes: np.ndarray, curves: np.ndarray) -> float:
    x_values: list[float] = []
    y_values: list[float] = []
    for index, length in enumerate(sizes):
        upper = max(4, int(length // 2))
        time = np.arange(2, upper + 1)
        values = curves[index, time]
        mask = values > 0.0
        x_values.extend(np.log(time[mask]).tolist())
        y_values.extend(np.log(values[mask]).tolist())
    slope = float(np.polyfit(np.asarray(x_values), np.asarray(y_values), 1)[0])
    return -2.0 * slope


def _run_supp_purification(config: dict[str, Any], output: Path, rng: np.random.Generator) -> dict[str, Any]:
    target = config["targets"]["supp_purification"]
    sizes = np.asarray(target["sizes"], dtype=int)
    max_layers = int(target["post_layers_per_L"] * sizes.max())
    one = np.full((len(sizes), max_layers + 1), np.nan)
    four = np.full_like(one, np.nan)
    rate = float(config["paper_parameters"]["critical_rate_correlations"])
    trajectories = int(target["trajectories"])
    for index, length in enumerate(sizes):
        layers = int(target["post_layers_per_L"] * length)
        one[index, : layers + 1] = _reference_entropy_curve(
            int(length), 1, rate, layers, trajectories, rng
        )
        four[index, : layers + 1] = _reference_entropy_curve(
            int(length), 4, rate, layers, trajectories, rng
        )
    eta_one = _fit_decay_exponent(sizes, one)
    eta_four = _fit_decay_exponent(sizes, four)
    _save(
        output / TARGET_FILES["T008"],
        sizes=sizes,
        time=np.arange(max_layers + 1),
        one_reference_entropy=one,
        four_reference_entropy=four,
        fitted_eta_one=eta_one,
        fitted_eta_four=eta_four,
        paper_eta_one=float(config["paper_parameters"]["supp_eta_one"]),
        paper_eta_four=float(config["paper_parameters"]["supp_eta_four"]),
        trajectories=trajectories,
    )
    return {
        "fitted_eta_one": eta_one,
        "fitted_eta_four": eta_four,
        "one_reference_decays": bool(np.nanmean(one[:, -1]) < np.nanmean(one[:, 0])),
        "four_reference_decays": bool(np.nanmean(four[:, -1]) < np.nanmean(four[:, 0])),
    }


def _formula_checks(seed: int) -> dict[str, Any]:
    group = two_qubit_symplectic_group()
    bell = StabilizerState.product_zero(2)
    insert_bell_pair(bell, 1, 0)
    bell_entropy = bell.entropy([1])
    bell.measure_z(0)
    measured_entropy = bell.entropy([1])
    rng = np.random.default_rng(seed)
    state = StabilizerState.product_zero(8)
    for layer in range(12):
        _random_layer(state, 8, layer, 0.2, True, rng)
    return {
        "symplectic_group_order": len(group),
        "symplectic_group_order_passed": len(group) == 720,
        "bell_reference_entropy_bits": bell_entropy,
        "bell_entropy_passed": bell_entropy == 1,
        "post_measurement_reference_entropy_bits": measured_entropy,
        "measurement_purification_passed": measured_entropy == 0,
        "random_circuit_tableau_valid": state.is_valid(),
    }


def run_reproduction(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    started = perf_counter()
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    seed = int(config["seed"])
    seed_sequence = np.random.SeedSequence(seed)
    child_rngs = [np.random.default_rng(child) for child in seed_sequence.spawn(8)]

    formula = _formula_checks(seed)
    formula["status"] = "passed" if all(
        formula[key]
        for key in (
            "symplectic_group_order_passed",
            "bell_entropy_passed",
            "measurement_purification_passed",
            "random_circuit_tableau_valid",
        )
    ) else "failed"
    (checks_dir / "scientific_formula_checks.json").write_text(
        json.dumps(formula, indent=2) + "\n", encoding="utf-8"
    )

    results = {
        "T001": _run_transition(config, data_dir, child_rngs[0]),
        "T002": _run_main_lightcone(config, data_dir, child_rngs[1]),
        "T003": _run_cutoff(config, data_dir, child_rngs[2]),
        "T004": _run_surface_order(config, data_dir, child_rngs[3]),
    }
    correlation = _run_correlations(config, data_dir, child_rngs[4])
    results["T005"] = correlation
    results["T006"] = correlation
    results["T007"] = _run_supp_lightcones(config, data_dir, child_rngs[5])
    results["T008"] = _run_supp_purification(config, data_dir, child_rngs[6])

    target_pass = {
        "T001": results["T001"]["all_probabilities_bounded"]
        and results["T001"]["low_rate_mean"] > results["T001"]["high_rate_mean"]
        and 0.10 <= results["T001"]["estimated_crossing_rate"] <= 0.20,
        "T002": results["T002"]["purification_probability"] > 0.05
        and results["T002"]["causal_weight_fraction"] > 0.90,
        "T003": results["T003"]["curves_bounded"]
        and results["T003"]["low_rate_final_full"] > results["T003"]["high_rate_final_full"]
        and results["T003"]["record_data_processing_passed"],
        "T004": results["T004"]["all_probabilities_bounded"]
        and np.isfinite(results["T004"]["fitted_beta_surface"])
        and 0.0 < results["T004"]["fitted_beta_surface"] < 1.5,
        "T005": results["T005"]["mutual_information_nonnegative"]
        and results["T005"]["cylinder_peak_surface"] > 0.0
        and results["T005"]["cylinder_peak_bulk"] > 0.0,
        "T006": results["T006"]["mutual_information_nonnegative"]
        and results["T006"]["strip_peak_end_to_end"] > 0.0
        and results["T006"]["strip_peak_mixed"] > 0.0,
        "T007": results["T007"]["both_have_nonzero_lightcones"],
        "T008": results["T008"]["one_reference_decays"]
        and results["T008"]["four_reference_decays"]
        and 0.0 < results["T008"]["fitted_eta_one"] < 2.0
        and 0.0 < results["T008"]["fitted_eta_four"] < 2.0,
    }
    target_checks = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if all(target_pass.values()) else "failed",
        "targets": [
            {
                "target_id": target_id,
                "status": "passed" if passed else "failed",
                "checks": results[target_id],
            }
            for target_id, passed in target_pass.items()
        ],
    }
    (checks_dir / "target_checks.json").write_text(
        json.dumps(target_checks, indent=2) + "\n", encoding="utf-8"
    )

    convergence = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if all(target_pass.values()) else "failed",
        "mode": "reduced_scale_monte_carlo",
        "notes": [
            "All random gates are sampled uniformly from the 720 phase-free two-qubit Clifford actions.",
            "Published trajectory counts and random seeds are absent; every replacement is declared in config/reduced_scale.json.",
            "T003 uses the exact mixed-stabilizer conditional channel: measurements outside the retained record are physically applied and their outcomes are marginalized by dephasing.",
            "T003 cutoffs at fixed measurement rate share identical random gates and measurement locations, enabling a paired data-processing check.",
        ],
        "target_results": results,
    }
    (checks_dir / "convergence.json").write_text(
        json.dumps(convergence, indent=2) + "\n", encoding="utf-8"
    )

    manifest = {
        "schema_version": 1,
        "status": "passed" if all(target_pass.values()) else "failed",
        "paper_id": config["paper_id"],
        "generated_data_provenance": "independent_numerics",
        "numerical_data_frozen": True,
        "files": [
            {
                "target_id": target_id,
                "path": f"outputs/data/{filename}",
                "sha256": _sha256(data_dir / filename),
            }
            for target_id, filename in TARGET_FILES.items()
        ],
    }
    (checks_dir / "generated_data_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    elapsed = perf_counter() - started
    return {
        "paper_id": config["paper_id"],
        "elapsed_seconds": elapsed,
        "formula_checks_passed": formula["status"] == "passed",
        "target_checks_passed": all(target_pass.values()),
        "target_results": results,
    }
