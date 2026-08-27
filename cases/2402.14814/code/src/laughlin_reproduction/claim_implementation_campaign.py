"""Clean-room analytic implementations for the five uncovered claims.

All validation points are frozen algebraic probes, not fitted paper data.  The
runner reads no paper, image, author code, or author numerical array and never
promotes implementation attestation into scientific coverage.
"""

from __future__ import annotations

import json
from math import comb, factorial, pi
from pathlib import Path
from typing import Any

import numpy as np
from scipy.special import eval_genlaguerre, gamma

from .model import angle_correlation, ho_energy


TARGET_IDS = ("T019", "T020", "T021", "T022", "T023")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def laughlin_polynomial(coordinates: np.ndarray, exponent: int) -> complex:
    """Return the arbitrary-N Jastrow polynomial from Main Eq. (1)."""

    points = np.asarray(coordinates, dtype=np.complex128)
    if points.ndim != 1 or points.size < 2 or exponent < 1:
        raise ValueError("coordinates must be a 1D N>=2 vector and exponent positive")
    result = 1.0 + 0.0j
    for first in range(points.size):
        for second in range(first + 1, points.size):
            result *= (points[first] - points[second]) ** exponent
    return complex(result)


def laughlin_wavefunction(coordinates: np.ndarray, exponent: int) -> complex:
    """Evaluate the unnormalized arbitrary-N Laughlin wavefunction."""

    points = np.asarray(coordinates, dtype=np.complex128)
    gaussian = np.exp(-0.5 * float(np.sum(np.abs(points) ** 2)))
    return laughlin_polynomial(points, exponent) * gaussian


def minimal_coupling_energy(
    position: np.ndarray,
    momentum: np.ndarray,
    *,
    mass: float,
    trap_frequency: float,
    rotation_frequency: float,
) -> tuple[float, float]:
    """Evaluate both exactly equivalent forms of Supplement Eq. S1."""

    r = np.asarray(position, dtype=float)
    p = np.asarray(momentum, dtype=float)
    if r.shape != (2,) or p.shape != (2,) or mass <= 0.0:
        raise ValueError("position/momentum must be 2D and mass positive")
    angular_momentum = r[0] * p[1] - r[1] * p[0]
    direct = (
        float(np.dot(p, p)) / (2.0 * mass)
        + 0.5 * mass * trap_frequency**2 * float(np.dot(r, r))
        - rotation_frequency * angular_momentum
    )
    omega_cross_r = rotation_frequency * np.array([-r[1], r[0]])
    kinetic_momentum = p - mass * omega_cross_r
    gauge = (
        float(np.dot(kinetic_momentum, kinetic_momentum)) / (2.0 * mass)
        + 0.5
        * mass
        * (trap_frequency**2 - rotation_frequency**2)
        * float(np.dot(r, r))
    )
    return direct, gauge


def harmonic_wavefunction(
    shell: int,
    angular_momentum: int,
    radius: np.ndarray,
    angle: np.ndarray,
) -> np.ndarray:
    """General normalized 2D harmonic-oscillator eigenfunction, Eq. S3."""

    if (
        shell < 0
        or abs(angular_momentum) > shell
        or (shell - abs(angular_momentum)) % 2
    ):
        raise ValueError("angular momentum is not allowed in the shell")
    radial = np.asarray(radius, dtype=float)
    phi = np.asarray(angle, dtype=float)
    degree = (shell - abs(angular_momentum)) // 2
    normalization = np.sqrt(
        factorial(degree) / (pi * factorial(degree + abs(angular_momentum)))
    )
    return (
        normalization
        * radial ** abs(angular_momentum)
        * np.exp(1j * angular_momentum * phi)
        * np.exp(-(radial**2) / 2.0)
        * eval_genlaguerre(degree, abs(angular_momentum), radial**2)
    )


def general_angle_correlation(exponent: int, phi: np.ndarray) -> np.ndarray:
    """Evaluate and normalize the Supplement S15-S16 double-gamma sum."""

    if exponent < 1:
        raise ValueError("exponent must be positive")
    angles = np.asarray(phi, dtype=float)
    unnormalized = np.zeros_like(angles)
    cosine = np.cos(angles)
    for power in range(exponent + 1):
        for second_power in range(exponent - power + 1):
            coefficient = (
                comb(exponent, power)
                * comb(exponent - power, second_power)
                * gamma(1.0 - power / 2.0 + exponent - second_power)
                * gamma(1.0 + power / 2.0 + second_power)
            )
            unnormalized += coefficient * (-2.0 * cosine) ** power
    unnormalized *= pi / 2.0
    normalization = float(np.trapezoid(unnormalized, angles))
    if not np.isfinite(normalization) or normalization <= 0.0:
        raise ValueError("angle-correlation normalization is not positive")
    return unnormalized / normalization


def _laughlin_validation(params: dict[str, Any]) -> dict[str, Any]:
    points = np.asarray(
        [complex(float(real), float(imag)) for real, imag in params["coordinates"]]
    )
    scale = float(params["polynomial_scale_probe"])
    rows: list[dict[str, Any]] = []
    passed = True
    for particles in params["particle_counts"]:
        selected = points[: int(particles)]
        for exponent in params["exponents"]:
            exponent = int(exponent)
            polynomial = laughlin_polynomial(selected, exponent)
            swapped = selected.copy()
            swapped[[0, 1]] = swapped[[1, 0]]
            exchange_ratio = laughlin_polynomial(swapped, exponent) / polynomial
            degree = exponent * int(particles) * (int(particles) - 1) // 2
            scaling_ratio = laughlin_polynomial(scale * selected, exponent) / polynomial
            amplitude = laughlin_wavefunction(selected, exponent)
            exchange_error = abs(exchange_ratio - (-1) ** exponent)
            scaling_error = abs(scaling_ratio - scale**degree)
            passed = passed and bool(
                exchange_error <= float(params["tolerance"])
                and scaling_error <= float(params["tolerance"])
                and np.isfinite(amplitude)
            )
            rows.append(
                {
                    "particles": int(particles),
                    "exponent": exponent,
                    "polynomial_degree": degree,
                    "exchange_error": float(exchange_error),
                    "homogeneity_error": float(scaling_error),
                    "wavefunction_abs": float(abs(amplitude)),
                }
            )
    return {
        "target_id": "T019",
        "mode": "analytic_formula_validation",
        "rows": rows,
        "passed": passed,
        "scientific_coverage_promoted": False,
    }


def _minimal_coupling_validation(params: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, float]] = []
    for probe in params["phase_space_probes"]:
        direct, gauge = minimal_coupling_energy(
            probe["position"],
            probe["momentum"],
            mass=float(params["mass"]),
            trap_frequency=float(params["trap_frequency"]),
            rotation_frequency=float(params["rotation_frequency"]),
        )
        rows.append(
            {
                "direct_energy": direct,
                "minimal_coupling_energy": gauge,
                "absolute_error": abs(direct - gauge),
            }
        )
    passed = all(row["absolute_error"] <= float(params["tolerance"]) for row in rows)
    return {
        "target_id": "T020",
        "mode": "analytic_operator_identity",
        "rows": rows,
        "qB_over_mass": 2.0 * float(params["rotation_frequency"]),
        "passed": passed,
        "scientific_coverage_promoted": False,
    }


def _harmonic_validation(params: dict[str, Any]) -> dict[str, Any]:
    radius = np.linspace(0.0, float(params["radius_max"]), int(params["radius_points"]))
    delta = float(params["phase_delta"])
    rows: list[dict[str, float | int]] = []
    passed = True
    for shell, angular_momentum in params["states"]:
        shell = int(shell)
        angular_momentum = int(angular_momentum)
        psi = harmonic_wavefunction(shell, angular_momentum, radius, np.zeros_like(radius))
        norm = float(2.0 * pi * np.trapezoid(np.abs(psi) ** 2 * radius, radius))
        probe_radius = np.asarray([float(params["phase_probe_radius"])])
        first = harmonic_wavefunction(shell, angular_momentum, probe_radius, np.asarray([0.0]))[0]
        second = harmonic_wavefunction(shell, angular_momentum, probe_radius, np.asarray([delta]))[0]
        phase_error = abs(second / first - np.exp(1j * angular_momentum * delta))
        energy = ho_energy(shell, angular_momentum, float(params["rotation_ratio"]))
        passed = passed and bool(
            abs(norm - 1.0) <= float(params["normalization_tolerance"])
            and phase_error <= float(params["phase_tolerance"])
            and np.isfinite(energy)
        )
        rows.append(
            {
                "shell": shell,
                "angular_momentum": angular_momentum,
                "normalization": norm,
                "phase_error": float(phase_error),
                "rotating_energy": energy,
            }
        )
    return {
        "target_id": "T021",
        "mode": "analytic_eigenfunction_validation",
        "rows": rows,
        "passed": passed,
        "scientific_coverage_promoted": False,
    }


def _angle_validation(params: dict[str, Any]) -> dict[str, Any]:
    phi = np.linspace(0.0, 2.0 * pi, int(params["angle_points"]))
    rows: list[dict[str, Any]] = []
    passed = True
    for exponent in params["exponents"]:
        exponent = int(exponent)
        values = general_angle_correlation(exponent, phi)
        normalization = float(np.trapezoid(values, phi))
        peak_angle = float(phi[int(np.argmax(values))])
        special_case_error = None
        if exponent == 2:
            special_case_error = float(np.max(np.abs(values - angle_correlation(phi))))
        passed = passed and bool(
            abs(normalization - 1.0) <= float(params["normalization_tolerance"])
            and abs(peak_angle - pi) <= float(params["peak_tolerance"])
            and (
                special_case_error is None
                or special_case_error <= float(params["special_case_tolerance"])
            )
        )
        rows.append(
            {
                "exponent": exponent,
                "normalization": normalization,
                "peak_angle": peak_angle,
                "m2_special_case_error": special_case_error,
            }
        )
    return {
        "target_id": "T022",
        "mode": "analytic_formula_validation",
        "rows": rows,
        "passed": passed,
        "scientific_coverage_promoted": False,
    }


def _magnetic_scale_validation(params: dict[str, Any]) -> dict[str, Any]:
    hbar = float(params["hbar"])
    mass = float(params["mass"])
    omega = float(params["trap_frequency"])
    omega_b = 2.0 * omega
    l_ho = np.sqrt(hbar / (mass * omega))
    p_ho = np.sqrt(hbar * mass * omega)
    l_b = np.sqrt(hbar / (mass * omega_b))
    p_b = np.sqrt(hbar * mass * omega_b)
    rows = {
        "omega_b_over_omega": omega_b / omega,
        "l_b_over_l_ho": l_b / l_ho,
        "p_b_over_p_ho": p_b / p_ho,
        "l_b_p_b_over_hbar": l_b * p_b / hbar,
    }
    expected = {
        "omega_b_over_omega": 2.0,
        "l_b_over_l_ho": 1.0 / np.sqrt(2.0),
        "p_b_over_p_ho": np.sqrt(2.0),
        "l_b_p_b_over_hbar": 1.0,
    }
    passed = all(
        abs(rows[name] - value) <= float(params["tolerance"])
        for name, value in expected.items()
    )
    return {
        "target_id": "T023",
        "mode": "analytic_scale_identity",
        "observations": rows,
        "passed": passed,
        "scientific_coverage_promoted": False,
    }


def _run_target(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    runners = {
        "T019": _laughlin_validation,
        "T020": _minimal_coupling_validation,
        "T021": _harmonic_validation,
        "T022": _angle_validation,
        "T023": _magnetic_scale_validation,
    }
    return runners[target_id](params)


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    declared = tuple(config.get("attestation_parameters", {}).get("target_ids", ()))
    if declared != TARGET_IDS:
        raise ValueError("campaign target list does not match the fixed denominator")
    boundary = config.get("clean_room_boundary", {})
    for name in (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    ):
        if boundary.get(name) is not False:
            raise ValueError(f"clean-room boundary must set {name}=false")
    targets = config.get("targets", {})
    if tuple(targets) != TARGET_IDS:
        raise ValueError("target configuration order is not frozen")

    data_dir = output_root / "data" / "claim_implementation_closure"
    check_dir = output_root / "checks" / "claim_implementation_closure"
    checks: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        result = _run_target(target_id, targets[target_id])
        _write_json(data_dir / f"{target_id}.json", result)
        check = {
            "target_id": target_id,
            "status": "passed" if result["passed"] else "failed",
            "mode": result["mode"],
            "acceptance_criteria": targets[target_id]["acceptance_criteria"],
            "scientific_coverage_promoted": False,
        }
        _write_json(check_dir / f"{target_id}.json", check)
        checks.append(check)
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "status": "passed" if all(row["status"] == "passed" for row in checks) else "failed",
        "target_ids": list(TARGET_IDS),
        "target_checks": checks,
        "clean_room_boundary": boundary,
        "scientific_coverage_promoted": False,
    }
    _write_json(check_dir / "manifest.json", manifest)
    return manifest
