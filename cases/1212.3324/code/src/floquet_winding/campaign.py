"""End-to-end clean-room numerical campaign for all Rudner targets."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from .model import (
    quasienergy_eigensystem,
    square_floquet_bloch,
    square_floquet_strip,
    strip_edge_observables,
    weak_bloch_vector,
    weak_floquet_strip_hamiltonian,
    weak_strip_hamiltonian,
)
from .topology import (
    square_bulk_gaps,
    square_floquet_chern,
    square_winding_number,
    weak_floquet_chern,
    weak_static_chern,
)


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("paper_id") != "1212.3324":
        raise ValueError("configuration paper_id must be 1212.3324")
    parameters = payload.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("configuration must contain a parameters object")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _square_strip_spectrum(
    momenta: np.ndarray,
    *,
    width: int,
    hopping: float,
    sublattice: float,
    period: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    energies = np.empty((len(momenta), 2 * width), dtype=float)
    edge_weight = np.empty_like(energies)
    edge_polarization = np.empty_like(energies)
    maximum_unitarity_residual = 0.0
    identity = np.eye(2 * width, dtype=complex)
    for index, momentum in enumerate(momenta):
        floquet = square_floquet_strip(
            momentum, width, hopping, sublattice, period=period
        )
        maximum_unitarity_residual = max(
            maximum_unitarity_residual,
            float(np.linalg.norm(floquet.conjugate().T @ floquet - identity, ord=np.inf)),
        )
        energy, vectors = quasienergy_eigensystem(floquet, period=period)
        weight, polarization = strip_edge_observables(vectors)
        energies[index] = energy
        edge_weight[index] = weight
        edge_polarization[index] = polarization
    return energies, edge_weight, edge_polarization, maximum_unitarity_residual


def _scan_square_phase_cut(
    config: dict[str, Any], *, period: float, sublattice: float
) -> tuple[list[dict[str, float]], dict[str, float]]:
    scan = config["phase_scan"]
    hoppings = np.linspace(
        float(scan["hopping_pi_min"]) * np.pi / period,
        float(scan["hopping_pi_max"]) * np.pi / period,
        int(scan["hopping_points"]),
    )
    rows: list[dict[str, float]] = []
    for hopping in hoppings:
        gap_zero, gap_pi = square_bulk_gaps(
            hopping,
            sublattice,
            grid_points=int(scan["momentum_points"]),
            period=period,
        )
        rows.append(
            {
                "hopping_pi": float(hopping * period / np.pi),
                "gap_zero_pi": float(gap_zero * period / np.pi),
                "gap_pi_pi": float(gap_pi * period / np.pi),
            }
        )
    first_window = [
        row
        for row in rows
        if float(scan["first_transition_window"][0])
        <= row["hopping_pi"]
        <= float(scan["first_transition_window"][1])
    ]
    second_window = [
        row
        for row in rows
        if float(scan["second_transition_window"][0])
        <= row["hopping_pi"]
        <= float(scan["second_transition_window"][1])
    ]
    first = min(first_window, key=lambda row: row["gap_pi_pi"])
    second = min(second_window, key=lambda row: row["gap_zero_pi"])
    transitions = {
        "first_hopping_pi": first["hopping_pi"],
        "first_gap_pi_pi": first["gap_pi_pi"],
        "second_hopping_pi": second["hopping_pi"],
        "second_gap_zero_pi": second["gap_zero_pi"],
    }
    return rows, transitions


def _scan_square_phase_map(
    config: dict[str, Any],
    *,
    period: float,
    convention: str,
    coefficient_factor: float,
) -> list[dict[str, Any]]:
    """Independently evaluate both gap invariants on every phase-map point.

    ``delta_difference_pi`` is always the paper's declared onsite-energy
    difference.  ``coefficient_factor`` is one half for that definition and
    one for the literal displayed ``delta_AB * sigma_z`` equation.  Keeping
    both branches on the same grid makes the source-level factor-two conflict
    visible without fitting either branch to the published raster.
    """

    scan = config["phase_scan"]
    hoppings_pi = np.linspace(
        float(scan["hopping_pi_min"]),
        float(scan["hopping_pi_max"]),
        int(scan["map_hopping_points"]),
    )
    deltas_pi = np.linspace(
        float(scan["delta_difference_pi_min"]),
        float(scan["delta_difference_pi_max"]),
        int(scan["delta_points"]),
    )
    rows: list[dict[str, Any]] = []
    for delta_pi in deltas_pi:
        sublattice = coefficient_factor * float(delta_pi) * np.pi / period
        for hopping_pi in hoppings_pi:
            hopping = float(hopping_pi) * np.pi / period
            gap_zero, gap_pi = square_bulk_gaps(
                hopping,
                sublattice,
                grid_points=int(scan["map_momentum_points"]),
                period=period,
            )
            minimum_gap_pi = min(gap_zero, gap_pi) * period / np.pi
            if minimum_gap_pi <= float(scan["map_gap_closing_tolerance_pi"]):
                status = "gap_closing"
                winding_zero: float | None = None
                winding_pi: float | None = None
                coarse_winding_zero: float | None = None
                coarse_winding_pi: float | None = None
                chern: float | None = None
                integers: tuple[int | None, int | None, int | None] = (
                    None,
                    None,
                    None,
                )
                quantization_residual: float | None = None
                relation_residual: int | None = None
                momentum_points_used: int | None = None
                time_points_used: int | None = None
                refined = False
            else:
                try:
                    chern = square_floquet_chern(
                        hopping,
                        sublattice,
                        grid_points=int(scan["map_momentum_points"]),
                        period=period,
                    )
                    coarse_momentum_points = int(
                        scan["map_winding_momentum_points"]
                    )
                    coarse_time_points = int(scan["map_winding_time_points"])
                    coarse_winding_zero = square_winding_number(
                        hopping,
                        sublattice,
                        0.0,
                        momentum_points=coarse_momentum_points,
                        time_points=coarse_time_points,
                        period=period,
                    )
                    coarse_winding_pi = square_winding_number(
                        hopping,
                        sublattice,
                        np.pi / period,
                        momentum_points=coarse_momentum_points,
                        time_points=coarse_time_points,
                        period=period,
                    )
                except ValueError:
                    winding_zero = None
                    winding_pi = None
                    coarse_winding_zero = None
                    coarse_winding_pi = None
                    chern = None
                    integers = (None, None, None)
                    quantization_residual = None
                    relation_residual = None
                    momentum_points_used = None
                    time_points_used = None
                    refined = False
                    status = "unresolved_numerical"
                else:
                    winding_zero = coarse_winding_zero
                    winding_pi = coarse_winding_pi
                    momentum_points_used = coarse_momentum_points
                    time_points_used = coarse_time_points
                    integers = tuple(
                        int(np.rint(value))
                        for value in (winding_zero, winding_pi, chern)
                    )
                    quantization_residual = max(
                        abs(winding_zero - integers[0]),
                        abs(winding_pi - integers[1]),
                        abs(chern - integers[2]),
                    )
                    relation_residual = abs(
                        (integers[1] - integers[0]) - integers[2]
                    )
                    refined = False
                    if (
                        quantization_residual
                        > float(scan["map_refine_trigger_tolerance"])
                        or relation_residual != 0
                    ):
                        refined_momentum_points = int(
                            scan["map_refined_winding_momentum_points"]
                        )
                        refined_time_points = int(
                            scan["map_refined_winding_time_points"]
                        )
                        winding_zero = square_winding_number(
                            hopping,
                            sublattice,
                            0.0,
                            momentum_points=refined_momentum_points,
                            time_points=refined_time_points,
                            period=period,
                        )
                        winding_pi = square_winding_number(
                            hopping,
                            sublattice,
                            np.pi / period,
                            momentum_points=refined_momentum_points,
                            time_points=refined_time_points,
                            period=period,
                        )
                        momentum_points_used = refined_momentum_points
                        time_points_used = refined_time_points
                        refined = True
                        integers = tuple(
                            int(np.rint(value))
                            for value in (winding_zero, winding_pi, chern)
                        )
                        quantization_residual = max(
                            abs(winding_zero - integers[0]),
                            abs(winding_pi - integers[1]),
                            abs(chern - integers[2]),
                        )
                        relation_residual = abs(
                            (integers[1] - integers[0]) - integers[2]
                        )
                    if (
                        quantization_residual
                        <= float(scan["map_winding_quantization_tolerance"])
                        and relation_residual == 0
                    ):
                        status = "gapped_quantized"
                    elif minimum_gap_pi <= float(
                        scan["map_boundary_neighborhood_tolerance_pi"]
                    ):
                        status = "gap_closing_neighborhood"
                    else:
                        status = "unresolved_numerical"
            rows.append(
                {
                    "convention": convention,
                    "hopping_pi": float(hopping_pi),
                    "delta_difference_pi": float(delta_pi),
                    "sigma_z_coefficient_pi": coefficient_factor * float(delta_pi),
                    "gap_zero_pi": float(gap_zero * period / np.pi),
                    "gap_pi_pi": float(gap_pi * period / np.pi),
                    "coarse_winding_zero_raw": coarse_winding_zero,
                    "coarse_winding_pi_raw": coarse_winding_pi,
                    "winding_zero_raw": winding_zero,
                    "winding_pi_raw": winding_pi,
                    "chern_upper_raw": chern,
                    "winding_zero": integers[0],
                    "winding_pi": integers[1],
                    "chern_upper": integers[2],
                    "quantization_residual": quantization_residual,
                    "bulk_edge_relation_residual": relation_residual,
                    "winding_momentum_points_used": momentum_points_used,
                    "winding_time_points_used": time_points_used,
                    "adaptive_refinement_used": refined,
                    "status": status,
                }
            )
    return rows


def _write_phase_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _weak_bulk_arrays(config: dict[str, Any]) -> dict[str, np.ndarray]:
    points = int(config["bulk_grid_points"])
    coordinates = np.linspace(-np.pi, np.pi, points)
    energy = np.empty((points, points), dtype=float)
    sigma_z = np.empty_like(energy)
    for ix, kx in enumerate(coordinates):
        for iy, ky in enumerate(coordinates):
            vector = weak_bloch_vector(
                kx,
                ky,
                mu=float(config["mu"]),
                hopping=float(config["hopping"]),
                mass_curvature=float(config["mass_curvature"]),
                spin_orbit=float(config["spin_orbit"]),
            )
            norm = float(np.linalg.norm(vector))
            energy[ix, iy] = norm / float(config["drive_frequency"])
            sigma_z[ix, iy] = vector[2] / norm
    resonance_residual = np.abs(energy - 0.5)
    return {
        "momentum": coordinates,
        "positive_energy_over_omega": energy,
        "negative_energy_over_omega": -energy,
        "positive_sigma_z": sigma_z,
        "negative_sigma_z": -sigma_z,
        "resonance_residual": resonance_residual,
    }


def _weak_strip_arrays(config: dict[str, Any]) -> tuple[dict[str, np.ndarray], float]:
    momenta = np.linspace(-np.pi, np.pi, int(config["strip_momentum_points"]))
    width = int(config["strip_width"])
    truncation = int(config["floquet_truncation"])
    static_energies = np.empty((len(momenta), 2 * width), dtype=float)
    static_edge_weight = np.empty_like(static_energies)
    copies = 2 * truncation + 1
    floquet_dimension = copies * 2 * width
    floquet_energies = np.empty((len(momenta), floquet_dimension), dtype=float)
    floquet_edge_weight = np.empty_like(floquet_energies)
    maximum_hermitian_residual = 0.0
    for index, momentum in enumerate(momenta):
        static = weak_strip_hamiltonian(
            momentum,
            width,
            mu=float(config["mu"]),
            hopping=float(config["hopping"]),
            mass_curvature=float(config["mass_curvature"]),
            spin_orbit=float(config["spin_orbit"]),
        )
        values, vectors = np.linalg.eigh(static)
        static_energies[index] = values / float(config["drive_frequency"])
        static_edge_weight[index] = strip_edge_observables(vectors)[0]

        floquet = weak_floquet_strip_hamiltonian(
            momentum,
            width,
            truncation,
            mu=float(config["mu"]),
            hopping=float(config["hopping"]),
            mass_curvature=float(config["mass_curvature"]),
            spin_orbit=float(config["spin_orbit"]),
            drive_amplitude=float(config["drive_amplitude"]),
            drive_frequency=float(config["drive_frequency"]),
        )
        maximum_hermitian_residual = max(
            maximum_hermitian_residual,
            float(np.linalg.norm(floquet - floquet.conjugate().T, ord=np.inf)),
        )
        values, vectors = np.linalg.eigh(floquet)
        floquet_energies[index] = values / float(config["drive_frequency"])
        probability = np.abs(vectors.reshape(copies, 2 * width, floquet_dimension)) ** 2
        layers = min(2, width // 2)
        boundary = probability[:, : 2 * layers].sum(axis=(0, 1)) + probability[
            :, -2 * layers :
        ].sum(axis=(0, 1))
        floquet_edge_weight[index] = boundary
    return (
        {
            "momentum": momenta,
            "static_energies_over_omega": static_energies,
            "static_edge_weight": static_edge_weight,
            "floquet_energies_over_omega": floquet_energies,
            "floquet_edge_weight": floquet_edge_weight,
        },
        maximum_hermitian_residual,
    )


def _edge_points_in_square_gaps(
    energies: np.ndarray,
    weights: np.ndarray,
    gap_zero: float,
    gap_pi: float,
    *,
    period: float,
    threshold: float,
) -> tuple[int, int]:
    localized = weights >= threshold
    zero = localized & (np.abs(energies) < 0.85 * gap_zero)
    pi_distance = np.pi / period - np.abs(energies)
    pi_gap = localized & (pi_distance < 0.85 * gap_pi)
    return int(zero.sum()), int(pi_gap.sum())


def run_campaign(config: dict[str, Any], *, config_path: Path, output_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    parameters = config["parameters"]
    square = parameters["square_model"]
    weak = parameters["weak_drive_model"]
    period = float(square["period"])
    sublattice = float(square["sublattice_matrix_coefficient_pi"]) * np.pi / period
    literal_sublattice = float(square["literal_equation_coefficient_pi"]) * np.pi / period
    # Figs. 3(a-c) quote delta_AB=0.5 pi/T and the displayed Hamiltonian uses
    # +delta_AB sigma_z.  Generate those spectra from the literal equation.
    # The phase scan below retains both readings of the manuscript's
    # factor-two convention conflict.
    figure_sublattice = literal_sublattice
    data_root = output_root / "data"
    checks_root = output_root / "checks"
    data_root.mkdir(parents=True, exist_ok=True)
    checks_root.mkdir(parents=True, exist_ok=True)

    momenta = np.linspace(0.0, np.pi, int(square["strip_momentum_points"]))
    square_arrays: dict[str, np.ndarray] = {"momentum": momenta}
    representative_results: list[dict[str, Any]] = []
    maximum_square_unitarity = 0.0
    for label, hopping_pi in square["representative_hopping_pi"].items():
        hopping = float(hopping_pi) * np.pi / period
        energies, weights, polarization, residual = _square_strip_spectrum(
            momenta,
            width=int(square["strip_width"]),
            hopping=hopping,
            sublattice=figure_sublattice,
            period=period,
        )
        maximum_square_unitarity = max(maximum_square_unitarity, residual)
        square_arrays[f"energies_{label}"] = energies
        square_arrays[f"edge_weight_{label}"] = weights
        square_arrays[f"edge_polarization_{label}"] = polarization
        gap_zero, gap_pi = square_bulk_gaps(
            hopping,
            figure_sublattice,
            grid_points=int(square["topology_momentum_points"]),
            period=period,
        )
        chern = square_floquet_chern(
            hopping,
            figure_sublattice,
            grid_points=int(square["topology_momentum_points"]),
            period=period,
        )
        winding_zero = square_winding_number(
            hopping,
            figure_sublattice,
            0.0,
            momentum_points=int(square["winding_momentum_points"]),
            time_points=int(square["winding_time_points"]),
            period=period,
        )
        winding_pi = square_winding_number(
            hopping,
            figure_sublattice,
            np.pi / period,
            momentum_points=int(square["winding_momentum_points"]),
            time_points=int(square["winding_time_points"]),
            period=period,
        )
        edge_zero, edge_pi = _edge_points_in_square_gaps(
            energies,
            weights,
            gap_zero,
            gap_pi,
            period=period,
            threshold=float(square["edge_weight_threshold"]),
        )
        representative_results.append(
            {
                "label": label,
                "hopping_pi": float(hopping_pi),
                "gap_zero_pi": gap_zero * period / np.pi,
                "gap_pi_pi": gap_pi * period / np.pi,
                "chern_upper": chern,
                "winding_zero": winding_zero,
                "winding_pi": winding_pi,
                "edge_points_zero_gap": edge_zero,
                "edge_points_pi_gap": edge_pi,
            }
        )

    # Fig. 2(c) is the exactly solvable ideal point, not the nearby anomalous
    # representative of Fig. 3(c).  Keep its strip data as a distinct target
    # so a renderer can never substitute one for the other.
    ideal_energies, ideal_weights, ideal_polarization, ideal_unitarity = (
        _square_strip_spectrum(
            momenta,
            width=int(square["strip_width"]),
            hopping=2.5 * np.pi / period,
            sublattice=0.0,
            period=period,
        )
    )
    square_arrays["energies_ideal"] = ideal_energies
    square_arrays["edge_weight_ideal"] = ideal_weights
    square_arrays["edge_polarization_ideal"] = ideal_polarization
    maximum_square_unitarity = max(maximum_square_unitarity, ideal_unitarity)
    np.savez_compressed(data_root / "square_strip_spectra.npz", **square_arrays)

    _, transitions = _scan_square_phase_cut(
        square, period=period, sublattice=sublattice
    )
    _, literal_transitions = _scan_square_phase_cut(
        square, period=period, sublattice=literal_sublattice
    )
    phase_rows = _scan_square_phase_map(
        square,
        period=period,
        convention="onsite_difference",
        coefficient_factor=0.5,
    )
    phase_rows.extend(
        _scan_square_phase_map(
            square,
            period=period,
            convention="literal_equation",
            coefficient_factor=1.0,
        )
    )
    _write_phase_csv(data_root / "square_phase_diagram.csv", phase_rows)

    ideal_residual = 0.0
    for q1, q2 in ((0.0, 0.0), (0.7, -1.2), (2.1, 0.4), (-2.4, 2.7)):
        ideal_residual = max(
            ideal_residual,
            float(
                np.linalg.norm(
                    square_floquet_bloch(
                        q1, q2, 2.5 * np.pi / period, 0.0, period=period
                    )
                    - np.eye(2),
                    ord=np.inf,
                )
            ),
        )

    weak_bulk = _weak_bulk_arrays(weak)
    np.savez_compressed(data_root / "weak_drive_bulk.npz", **weak_bulk)
    weak_strip, weak_hermitian = _weak_strip_arrays(weak)
    np.savez_compressed(data_root / "weak_drive_strip.npz", **weak_strip)
    weak_static = weak_static_chern(
        mu=float(weak["mu"]),
        hopping=float(weak["hopping"]),
        mass_curvature=float(weak["mass_curvature"]),
        spin_orbit=float(weak["spin_orbit"]),
        grid_points=int(weak["topology_momentum_points"]),
    )
    weak_floquet = weak_floquet_chern(
        mu=float(weak["mu"]),
        hopping=float(weak["hopping"]),
        mass_curvature=float(weak["mass_curvature"]),
        spin_orbit=float(weak["spin_orbit"]),
        drive_amplitude=float(weak["drive_amplitude"]),
        drive_frequency=float(weak["drive_frequency"]),
        time_steps=int(weak["time_steps"]),
        grid_points=int(weak["topology_momentum_points"]),
    )
    weak_floquet_coarse = weak_floquet_chern(
        mu=float(weak["mu"]),
        hopping=float(weak["hopping"]),
        mass_curvature=float(weak["mass_curvature"]),
        spin_orbit=float(weak["spin_orbit"]),
        drive_amplitude=float(weak["drive_amplitude"]),
        drive_frequency=float(weak["drive_frequency"]),
        time_steps=max(16, int(weak["time_steps"]) // 2),
        grid_points=int(weak["topology_momentum_points"]),
    )

    topology = {
        "schema_version": 1,
        "paper_id": "1212.3324",
        "square_representatives": representative_results,
        "square_transitions": transitions,
        "square_literal_equation_transitions": literal_transitions,
        "square_phase_map": {
            "rows": len(phase_rows),
            "conventions": ["onsite_difference", "literal_equation"],
            "hopping_points_per_convention": int(
                square["phase_scan"]["map_hopping_points"]
            ),
            "delta_points_per_convention": int(
                square["phase_scan"]["delta_points"]
            ),
            "invariants_evaluated_per_grid_point": [
                "winding_zero",
                "winding_pi",
                "chern_upper",
            ],
            "status_counts": {
                status: sum(row["status"] == status for row in phase_rows)
                for status in (
                    "gapped_quantized",
                    "gap_closing",
                    "gap_closing_neighborhood",
                    "unresolved_numerical",
                )
            },
        },
        "sublattice_convention": {
            "printed_difference_pi": float(square["sublattice_difference_pi"]),
            "primary_sigma_z_coefficient_pi": float(
                square["sublattice_matrix_coefficient_pi"]
            ),
            "literal_equation_coefficient_pi": float(
                square["literal_equation_coefficient_pi"]
            ),
            "figure_3_spectra_convention": "literal_displayed_equation_coefficient",
            "phase_scan_primary_convention": "printed_onsite_energy_difference",
            "classification": "inconclusive_source_convention_discrepancy",
        },
        "weak_drive": {
            "static_upper_chern": weak_static,
            "floquet_upper_chern": weak_floquet,
            "floquet_upper_chern_coarse_time": weak_floquet_coarse,
        },
    }
    _write_json(data_root / "topological_invariants.json", topology)

    expected = {
        "trivial": (0, 0, 0),
        "chern": (0, 1, 1),
        "anomalous": (1, 1, 0),
    }
    checks: list[dict[str, Any]] = []

    def record(
        check_id: str,
        target_ids: list[str],
        description: str,
        value: float,
        threshold: float,
        comparator: str,
    ) -> None:
        passed = value <= threshold if comparator == "max" else value >= threshold
        checks.append(
            {
                "check_id": check_id,
                "target_ids": target_ids,
                "description": description,
                "value": float(value),
                "threshold": float(threshold),
                "comparator": comparator,
                "passed": bool(passed),
            }
        )

    record(
        "CHK_IDEAL_BULK_IDENTITY",
        ["T001", "T009"],
        "At JT/5=pi/2 and delta_AB=0 the bulk Floquet operator is identity.",
        ideal_residual,
        1e-11,
        "max",
    )
    record(
        "CHK_SQUARE_UNITARY",
        ["T001", "T002", "T003", "T004"],
        "Every strip Floquet operator is unitary.",
        maximum_square_unitarity,
        1e-10,
        "max",
    )
    record(
        "CHK_IDEAL_EDGE_BRANCH",
        ["T001"],
        "The ideal open strip contains boundary-localized quasienergy branches.",
        float(np.count_nonzero(ideal_weights >= 0.9)),
        float(2 * len(momenta)),
        "min",
    )
    for row in representative_results:
        exp_w0, exp_wpi, exp_chern = expected[row["label"]]
        record(
            f"CHK_{row['label'].upper()}_W0",
            ["T005", "T009"],
            "Full-evolution zero-gap winding agrees with the phase label.",
            abs(row["winding_zero"] - exp_w0),
            float(square["winding_tolerance"]),
            "max",
        )
        record(
            f"CHK_{row['label'].upper()}_WPI",
            ["T005", "T009"],
            "Full-evolution pi-gap winding agrees with the phase label.",
            abs(row["winding_pi"] - exp_wpi),
            float(square["winding_tolerance"]),
            "max",
        )
        record(
            f"CHK_{row['label'].upper()}_CHERN",
            ["T005", "T009"],
            "Gauge-aware Fukui Chern number agrees with the phase label.",
            abs(row["chern_upper"] - exp_chern),
            0.1,
            "max",
        )
    record(
        "CHK_PHASE_BOUNDARY_ORDER",
        ["T005"],
        "The pi-gap closes before the zero-gap as hopping increases.",
        transitions["second_hopping_pi"] - transitions["first_hopping_pi"],
        0.4,
        "min",
    )
    boundary_anchors = square["phase_scan"]["figure_boundary_anchors"]
    primary_anchor_error = abs(
        transitions["first_hopping_pi"] - float(boundary_anchors[0])
    ) + abs(transitions["second_hopping_pi"] - float(boundary_anchors[1]))
    literal_anchor_error = abs(
        literal_transitions["first_hopping_pi"] - float(boundary_anchors[0])
    ) + abs(
        literal_transitions["second_hopping_pi"] - float(boundary_anchors[1])
    )
    record(
        "CHK_SUBLATTICE_CONVENTION_DISCRIMINATION",
        ["T005", "T009"],
        "Treating delta_AB as an onsite-energy difference (sigma_z coefficient delta_AB/2) matches both printed phase-boundary anchors better than the literal equation coefficient.",
        literal_anchor_error - primary_anchor_error,
        0.05,
        "min",
    )
    expected_phase_rows = (
        2
        * int(square["phase_scan"]["map_hopping_points"])
        * int(square["phase_scan"]["delta_points"])
    )
    record(
        "CHK_PHASE_MAP_ALL_GRID_POINTS",
        ["T005", "T009"],
        "Both gaps and, wherever the gaps are open, both winding invariants and the upper-band Chern number are evaluated independently at every point of both two-dimensional convention grids; gap-closing points are explicitly marked undefined.",
        float(len(phase_rows)),
        float(expected_phase_rows),
        "min",
    )
    unresolved_phase_rows = sum(
        row["status"] == "unresolved_numerical" for row in phase_rows
    )
    record(
        "CHK_PHASE_MAP_NUMERICAL_RESOLUTION",
        ["T005", "T009"],
        "Every resolved gapped phase-map point quantizes consistently; exact closings and adaptively identified closing neighborhoods remain explicitly unlabeled.",
        float(unresolved_phase_rows),
        0.0,
        "max",
    )
    map_primary_cut = [
        row
        for row in phase_rows
        if row["convention"] == "onsite_difference"
        and abs(row["delta_difference_pi"] - 0.5) < 1e-12
    ]
    map_first = min(
        (
            row
            for row in map_primary_cut
            if float(square["phase_scan"]["first_transition_window"][0])
            <= row["hopping_pi"]
            <= float(square["phase_scan"]["first_transition_window"][1])
        ),
        key=lambda row: row["gap_pi_pi"],
    )
    map_second = min(
        (
            row
            for row in map_primary_cut
            if float(square["phase_scan"]["second_transition_window"][0])
            <= row["hopping_pi"]
            <= float(square["phase_scan"]["second_transition_window"][1])
        ),
        key=lambda row: row["gap_zero_pi"],
    )
    refinement_error = abs(
        map_first["hopping_pi"] - transitions["first_hopping_pi"]
    ) + abs(map_second["hopping_pi"] - transitions["second_hopping_pi"])
    record(
        "CHK_PHASE_MAP_GRID_REFINEMENT",
        ["T005"],
        "The two-dimensional map and the independently refined delta_AB=0.5 pi/T cut locate the same two phase boundaries within one coarse hopping step each.",
        float(refinement_error),
        float(square["phase_scan"]["map_refinement_tolerance_pi"]),
        "max",
    )
    record(
        "CHK_WEAK_STATIC_CHERN",
        ["T006", "T007", "T009"],
        "The unperturbed upper band has unit Chern magnitude.",
        abs(abs(weak_static) - 1.0),
        0.1,
        "max",
    )
    record(
        "CHK_WEAK_FLOQUET_CHERN",
        ["T008", "T009"],
        "The harmonically driven Floquet upper band is topologically trivial.",
        abs(weak_floquet),
        0.1,
        "max",
    )
    record(
        "CHK_WEAK_FLOQUET_TIME_CONVERGENCE",
        ["T008"],
        "Fine and coarse midpoint products give the same integer Floquet Chern number.",
        abs(round(weak_floquet) - round(weak_floquet_coarse)),
        0.0,
        "max",
    )
    record(
        "CHK_WEAK_RESONANCE_LOOP",
        ["T006"],
        "The printed single-photon resonance condition is sampled on the bulk grid.",
        float(np.count_nonzero(weak_bulk["resonance_residual"] < 0.015)),
        8.0,
        "min",
    )
    record(
        "CHK_WEAK_FLOQUET_HERMITIAN",
        ["T008"],
        "The truncated repeated-zone Hamiltonian is Hermitian.",
        weak_hermitian,
        1e-12,
        "max",
    )

    all_passed = all(check["passed"] for check in checks)
    science = {
        "schema_version": 1,
        "paper_id": "1212.3324",
        "status": "passed" if all_passed else "failed",
        "all_science_checks_passed": all_passed,
        "checks": checks,
    }
    _write_json(checks_root / "science_checks.json", science)
    summary = {
        "schema_version": 1,
        "paper_id": "1212.3324",
        "run_profile": config["run_profile"],
        "status": "passed" if all_passed else "failed",
        "duration_seconds": time.perf_counter() - started,
        "targets": 9,
        "science_checks_passed": sum(check["passed"] for check in checks),
        "science_checks_total": len(checks),
    }
    _write_json(checks_root / "run_summary.json", summary)

    generated = [
        data_root / "square_strip_spectra.npz",
        data_root / "square_phase_diagram.csv",
        data_root / "weak_drive_bulk.npz",
        data_root / "weak_drive_strip.npz",
        data_root / "topological_invariants.json",
        checks_root / "science_checks.json",
        checks_root / "run_summary.json",
    ]
    manifest = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": "1212.3324",
        "config_path": config_path.name,
        "config_sha256": _sha256(config_path),
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "files": [
            {
                "path": path.relative_to(output_root.parent).as_posix(),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in generated
        ],
    }
    _write_json(checks_root / "generated_data_manifest.json", manifest)
    return summary
