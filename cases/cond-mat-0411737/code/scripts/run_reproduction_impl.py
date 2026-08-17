#!/usr/bin/env python3
"""Generate Kane-Mele numerical evidence from the printed Hamiltonian."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections.abc import Iterable
from math import pi
from pathlib import Path
from typing import Any

import numpy as np  # noqa: E402

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kane_mele.model import (  # noqa: E402
    analytic_bulk_gap,
    band_eigensystem,
    bare_gap_kelvin,
    build_ribbon_geometry,
    continuum_energies,
    edge_weights,
    renormalized_gap_kelvin,
    ribbon_hamiltonian,
    rashba_kelvin,
    spin_chern_reference,
    transport_coefficients,
)


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"unsupported JSON type: {type(value)!r}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assertion(
    assertion_id: str,
    passed: bool,
    *,
    value: float | int | str | list[float],
    threshold: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "id": assertion_id,
        "status": "passed" if passed else "failed",
        "value": value,
        "threshold": threshold,
        "reason": reason,
    }


def _spectrum_rows(
    width: int,
    k_values: np.ndarray,
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
    energy_window: tuple[float, float],
    distance_tolerance: float,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    geometry = build_ribbon_geometry(width, distance_tolerance=distance_tolerance)
    rows: list[dict[str, Any]] = []
    max_hermiticity = 0.0
    for spin in (-1, 1):
        for momentum in k_values:
            matrix = ribbon_hamiltonian(
                geometry,
                momentum,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                spin=spin,
            )
            max_hermiticity = max(
                max_hermiticity, float(np.max(np.abs(matrix - matrix.conj().T)))
            )
            energies, vectors = np.linalg.eigh(matrix)
            total_edge, bottom_edge, top_edge = edge_weights(
                geometry, vectors, chain_depth=edge_depth
            )
            for band_index, energy in enumerate(energies):
                rows.append(
                    {
                        "k_over_pi": float(momentum / pi),
                        "k_times_a": float(momentum),
                        "spin_z": spin,
                        "band_index": band_index,
                        "energy_over_t": float(energy / hopping_t),
                        "edge_weight": float(total_edge[band_index]),
                        "bottom_edge_weight": float(bottom_edge[band_index]),
                        "top_edge_weight": float(top_edge[band_index]),
                        "visible_in_paper_window": bool(
                            energy_window[0] <= energy / hopping_t <= energy_window[1]
                        ),
                    }
                )
    return rows, {"max_hermiticity_residual": max_hermiticity}


def _width_metrics(
    width: int,
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
    distance_tolerance: float,
) -> dict[str, Any]:
    geometry = build_ribbon_geometry(width, distance_tolerance=distance_tolerance)
    valley_gaps = []
    for momentum in (2.0 * pi / 3.0, 4.0 * pi / 3.0):
        energies, _vectors = band_eigensystem(
            geometry,
            momentum,
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            spin=1,
        )
        valley_gaps.append(2.0 * float(np.min(np.abs(energies))) / hopping_t)
    crossing_energies, crossing_vectors = band_eigensystem(
        geometry,
        pi,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        spin=1,
    )
    crossing_edge, _, _ = edge_weights(
        geometry, crossing_vectors, chain_depth=edge_depth
    )
    central = np.argsort(np.abs(crossing_energies))[:2]
    return {
        "width_chains": width,
        "matrix_size_per_spin": len(geometry.sites),
        "valley_gap_over_t": float(np.mean(valley_gaps)),
        "valley_gap_spread": float(np.ptp(valley_gaps)),
        "kramers_crossing_max_abs_energy_over_t": float(
            np.max(np.abs(crossing_energies[central])) / hopping_t
        ),
        "kramers_crossing_min_edge_weight": float(np.min(crossing_edge[central])),
        "edge_coordination": [
            geometry.nearest_coordination[0],
            geometry.nearest_coordination[-1],
        ],
        "bulk_coordination_unique": sorted(set(geometry.nearest_coordination[1:-1])),
    }


def _build_science_checks(
    config: dict[str, Any],
    rows: list[dict[str, Any]],
    width_rows: list[dict[str, Any]],
    runtime_metrics: dict[str, float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    parameters = config["parameters"]
    numerics = config["numerics"]
    hopping_t = float(parameters["hopping_t"])
    spin_orbit_t2 = float(parameters["spin_orbit_t2"])
    final_width = int(parameters["ribbon_width_chains"])
    geometry = build_ribbon_geometry(
        final_width, distance_tolerance=float(numerics["distance_tolerance"])
    )

    time_reversal_error = 0.0
    particle_hole_error = 0.0
    for momentum in np.linspace(0.0, 2.0 * pi, 13):
        up = np.linalg.eigvalsh(
            ribbon_hamiltonian(
                geometry,
                momentum,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                spin=1,
            )
        )
        down_reversed = np.linalg.eigvalsh(
            ribbon_hamiltonian(
                geometry,
                2.0 * pi - momentum,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                spin=-1,
            )
        )
        time_reversal_error = max(
            time_reversal_error, float(np.max(np.abs(up - down_reversed)))
        )
        particle_hole_error = max(
            particle_hole_error, float(np.max(np.abs(up + up[::-1])))
        )

    analytic_gap = analytic_bulk_gap(spin_orbit_t2) / hopping_t
    largest = width_rows[-1]
    second_largest = width_rows[-2]
    gap_relative_error = abs(largest["valley_gap_over_t"] - analytic_gap) / analytic_gap
    width_relative_delta = (
        abs(largest["valley_gap_over_t"] - second_largest["valley_gap_over_t"])
        / largest["valley_gap_over_t"]
    )

    continuum_gap_errors = []
    for rashba_ratio in (0.0, 0.25, 0.75, 0.95):
        delta = 0.2
        rashba = rashba_ratio * delta
        energies = continuum_energies(0.0, 0.0, delta_so=delta, lambda_r=rashba)
        numerical_gap = float(energies[4] - energies[3])
        continuum_gap_errors.append(abs(numerical_gap - 2.0 * (delta - rashba)))

    transport = transport_coefficients()
    bare_gap = bare_gap_kelvin(float(parameters["graphene_lattice_constant_angstrom"]))
    rashba_gap = rashba_kelvin(
        fermi_velocity_m_per_s=float(parameters["fermi_velocity_m_per_s"]),
        electric_field_volts=float(parameters["electric_field_volts"]),
        electric_field_distance_nm=float(parameters["electric_field_distance_nm"]),
    )
    renormalized_gap = renormalized_gap_kelvin(
        bare_full_gap_kelvin=float(parameters["bare_full_gap_kelvin"]),
        coulomb_g0=float(parameters["coulomb_g0"]),
        cutoff_ev=float(parameters["cutoff_ev"]),
    )
    assertions = [
        _assertion(
            "SCI_GEOMETRY",
            largest["edge_coordination"] == [2, 2]
            and largest["bulk_coordination_unique"] == [3],
            value=largest["edge_coordination"] + largest["bulk_coordination_unique"],
            threshold="edges=2 and bulk=3",
            reason="The retained cut is a zigzag edge, not a bearded edge.",
        ),
        _assertion(
            "SCI_HERMITICITY",
            runtime_metrics["max_hermiticity_residual"]
            <= float(numerics["hermiticity_tolerance"]),
            value=runtime_metrics["max_hermiticity_residual"],
            threshold=f"<= {numerics['hermiticity_tolerance']}",
            reason="The oriented imaginary second-neighbour hopping must be Hermitian.",
        ),
        _assertion(
            "SCI_TIME_REVERSAL",
            time_reversal_error <= 1e-11,
            value=time_reversal_error,
            threshold="<= 1e-11",
            reason="Opposite spins at opposite momenta form time-reversal pairs.",
        ),
        _assertion(
            "SCI_PARTICLE_HOLE",
            particle_hole_error <= 1e-11,
            value=particle_hole_error,
            threshold="<= 1e-11",
            reason="The intrinsic model remains spectrally symmetric about zero energy.",
        ),
        _assertion(
            "SCI_KRAMERS_CROSSING",
            largest["kramers_crossing_max_abs_energy_over_t"]
            <= float(numerics["kramers_energy_tolerance"]),
            value=largest["kramers_crossing_max_abs_energy_over_t"],
            threshold=f"<= {numerics['kramers_energy_tolerance']}",
            reason="The gap-traversing states cross at k_x=pi/a.",
        ),
        _assertion(
            "SCI_EDGE_LOCALIZATION",
            largest["kramers_crossing_min_edge_weight"] >= 0.99,
            value=largest["kramers_crossing_min_edge_weight"],
            threshold=">= 0.99",
            reason="Both central crossing states reside on the strip boundaries.",
        ),
        _assertion(
            "SCI_BULK_GAP",
            gap_relative_error <= float(numerics["gap_relative_tolerance"]),
            value=gap_relative_error,
            threshold=f"<= {numerics['gap_relative_tolerance']}",
            reason="The largest finite ribbon approaches 6 sqrt(3) t2.",
        ),
        _assertion(
            "SCI_WIDTH_CONVERGENCE",
            width_relative_delta <= float(numerics["width_feature_tolerance"]),
            value=width_relative_delta,
            threshold=f"<= {numerics['width_feature_tolerance']}",
            reason="The two largest reconstructed widths agree on the valley gap.",
        ),
        _assertion(
            "SCI_CONTINUUM_RASHBA_GAP",
            max(continuum_gap_errors) <= 1e-12,
            value=max(continuum_gap_errors),
            threshold="<= 1e-12",
            reason="Direct continuum diagonalization gives 2(Delta_so-lambda_R).",
        ),
        _assertion(
            "SCI_SPIN_CHERN_PAIR",
            spin_chern_reference(1, spin_orbit_t2)
            == -spin_chern_reference(-1, spin_orbit_t2)
            != 0,
            value=[
                spin_chern_reference(1, spin_orbit_t2),
                spin_chern_reference(-1, spin_orbit_t2),
            ],
            threshold="opposite nonzero integers",
            reason="The two conserved-spin Haldane blocks carry opposite topology.",
        ),
        _assertion(
            "SCI_TRANSPORT_QUANTA",
            transport["charge_conductance_in_e2_over_h"] == 2.0
            and abs(transport["adjacent_spin_conductance_in_e"] - 1.0 / (4.0 * pi))
            <= 1e-15,
            value=transport["charge_conductance_in_e2_over_h"],
            threshold="G=2 and Gs=1/(4 pi) in printed units",
            reason="One Kramers pair reproduces the Fig. 2 quantitative labels.",
        ),
        _assertion(
            "SCI_BARE_GAP_ESTIMATE",
            abs(bare_gap - 2.4) / 2.4 <= 0.1,
            value=bare_gap,
            threshold="within 10% of 2.4 K",
            reason="The first-star estimate is reproduced with a=2.46 angstrom.",
        ),
        _assertion(
            "SCI_RASHBA_ESTIMATE",
            abs(1e3 * rashba_gap - 0.5) <= 0.2,
            value=1e3 * rashba_gap,
            threshold="0.5 +/- 0.2 mK",
            reason="The unprinted v_F convention explains the printed rounding.",
        ),
        _assertion(
            "SCI_RG_GAP",
            abs(renormalized_gap - 15.0) <= 0.3,
            value=renormalized_gap,
            threshold="15 +/- 0.3 K",
            reason="The half-gap self-consistency convention reproduces the printed 15 K full gap.",
        ),
    ]
    status = (
        "passed" if all(item["status"] == "passed" for item in assertions) else "failed"
    )
    analytic = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "analytic_bulk_gap_over_t": analytic_gap,
        "largest_width_valley_gap_over_t": largest["valley_gap_over_t"],
        "largest_width_gap_relative_error": gap_relative_error,
        "two_largest_width_relative_delta": width_relative_delta,
        "bare_full_gap_kelvin_from_constants": bare_gap,
        "rashba_kelvin_from_printed_field": rashba_gap,
        "renormalized_full_gap_kelvin": renormalized_gap,
        "transport_coefficients": transport,
        "spin_chern_reference": {
            "up": spin_chern_reference(1, spin_orbit_t2),
            "down": spin_chern_reference(-1, spin_orbit_t2),
        },
    }
    science = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "target_ids": ["T001"],
        "assertions": assertions,
        "summary": {
            "assertions_total": len(assertions),
            "assertions_passed": sum(item["status"] == "passed" for item in assertions),
            "assertions_failed": sum(item["status"] == "failed" for item in assertions),
            "generated_rows": len(rows),
        },
        "paper_assessment": {
            "status": "inconclusive_pending_fresh_review",
            "paper_error_candidate_emitted": False,
            "stable_cross_reference_discrepancies": [
                {
                    "source": "raw/paper.pdf p. 2, strip-geometry prose",
                    "printed": "solving (7)",
                    "internally_required": "Eq. (6), the lattice Hamiltonian",
                },
                {
                    "source": "raw/paper.pdf p. 3, Fig. 1 caption",
                    "printed": "modeled by (7)",
                    "internally_required": "Eq. (6), the lattice Hamiltonian",
                },
                {
                    "source": "raw/paper.pdf p. 4, paragraph after Eq. (7)",
                    "printed": "expectation value of (8)",
                    "internally_required": "Eq. (7), the microscopic SO interaction",
                },
            ],
            "impact": "Equation-number cross references only; the implemented formulas and numerical results are unambiguous from context.",
            "remaining_gate": "fresh-context protocol-v2 review",
        },
    }
    return science, analytic


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    arguments = parser.parse_args()
    started = time.perf_counter()
    config_path = Path(arguments.config).resolve()
    output_root = Path(arguments.output_root).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "cond-mat-0411737":
        raise ValueError("config paper_id mismatch")

    parameters = config["parameters"]
    numerics = config["numerics"]
    k_values = np.linspace(
        float(parameters["k_over_pi_min"]) * pi,
        float(parameters["k_over_pi_max"]) * pi,
        int(parameters["k_points"]),
    )
    energy_window = tuple(float(value) for value in parameters["energy_window_over_t"])
    rows, runtime_metrics = _spectrum_rows(
        int(parameters["ribbon_width_chains"]),
        k_values,
        hopping_t=float(parameters["hopping_t"]),
        spin_orbit_t2=float(parameters["spin_orbit_t2"]),
        edge_depth=int(parameters["edge_chain_depth"]),
        energy_window=energy_window,
        distance_tolerance=float(numerics["distance_tolerance"]),
    )
    width_rows = [
        _width_metrics(
            int(width),
            hopping_t=float(parameters["hopping_t"]),
            spin_orbit_t2=float(parameters["spin_orbit_t2"]),
            edge_depth=int(parameters["edge_chain_depth"]),
            distance_tolerance=float(numerics["distance_tolerance"]),
        )
        for width in sorted(parameters["width_convergence_chains"])
    ]
    science, analytic = _build_science_checks(config, rows, width_rows, runtime_metrics)

    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    _write_csv(
        data_dir / "main_fig1_bands.csv",
        [
            "k_over_pi",
            "k_times_a",
            "spin_z",
            "band_index",
            "energy_over_t",
            "edge_weight",
            "bottom_edge_weight",
            "top_edge_weight",
            "visible_in_paper_window",
        ],
        rows,
    )
    _write_csv(
        data_dir / "width_convergence.csv",
        [
            "width_chains",
            "matrix_size_per_spin",
            "valley_gap_over_t",
            "valley_gap_spread",
            "kramers_crossing_max_abs_energy_over_t",
            "kramers_crossing_min_edge_weight",
            "edge_coordination",
            "bulk_coordination_unique",
        ],
        width_rows,
    )
    _write_json(data_dir / "analytic_checks.json", analytic)
    _write_json(checks_dir / "science_checks.json", science)

    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["execution_profile"],
        "status": science["status"],
        "elapsed_seconds": time.perf_counter() - started,
        "generated_band_rows": len(rows),
        "widths_checked": [row["width_chains"] for row in width_rows],
        "paper_error_candidate_emitted": False,
        "paper_assessment": science["paper_assessment"],
    }
    _write_json(checks_dir / "run_summary.json", summary)

    generated_paths = [
        data_dir / "main_fig1_bands.csv",
        data_dir / "width_convergence.csv",
        data_dir / "analytic_checks.json",
        checks_dir / "science_checks.json",
        checks_dir / "run_summary.json",
    ]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": science["status"],
        "profile": config["execution_profile"],
        "config_sha256": _sha256(config_path),
        "generated_artifacts": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in generated_paths
        ],
        "scientific_data_frozen": True,
        "rendering_separated_from_numerics": True,
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
    }
    _write_json(checks_dir / "generated_data_manifest.json", manifest)
    print(json.dumps(summary, sort_keys=True, default=_json_default))
    return 0 if science["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
