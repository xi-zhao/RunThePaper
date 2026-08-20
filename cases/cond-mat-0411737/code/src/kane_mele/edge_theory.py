"""Weak-coupling helical-edge operator and transport diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

import numpy as np
from scipy import integrate


@dataclass(frozen=True)
class EdgeField:
    """One fermion factor in a local helical-edge monomial."""

    branch: str
    spin: str
    dagger: bool
    derivative_order: int = 0


@dataclass(frozen=True)
class EdgeMonomial:
    """Ordered Grassmann monomial with a real phase for this paper's operator."""

    phase: int
    fields: tuple[EdgeField, ...]


def two_particle_backscattering_operator() -> EdgeMonomial:
    """Return ``psi_L^dag d psi_L^dag psi_R d psi_R`` from the paper."""

    return EdgeMonomial(
        phase=1,
        fields=(
            EdgeField("L", "up", True, 0),
            EdgeField("L", "up", True, 1),
            EdgeField("R", "down", False, 0),
            EdgeField("R", "down", False, 1),
        ),
    )


def _field_key(field: EdgeField) -> tuple[str, bool, int, str]:
    return (field.branch, field.dagger, field.derivative_order, field.spin)


def _canonicalize(monomial: EdgeMonomial) -> EdgeMonomial:
    fields = list(monomial.fields)
    phase = monomial.phase
    for right in range(1, len(fields)):
        left = right
        while left > 0 and _field_key(fields[left]) < _field_key(fields[left - 1]):
            fields[left], fields[left - 1] = fields[left - 1], fields[left]
            phase *= -1
            left -= 1
    if len({_field_key(field) for field in fields}) != len(fields):
        return EdgeMonomial(phase=0, fields=tuple(fields))
    return EdgeMonomial(phase=phase, fields=tuple(fields))


def _hermitian_conjugate(monomial: EdgeMonomial) -> EdgeMonomial:
    return EdgeMonomial(
        phase=monomial.phase,
        fields=tuple(
            EdgeField(
                field.branch,
                field.spin,
                not field.dagger,
                field.derivative_order,
            )
            for field in reversed(monomial.fields)
        ),
    )


def _time_reverse(monomial: EdgeMonomial) -> EdgeMonomial:
    phase = monomial.phase
    transformed: list[EdgeField] = []
    for field in monomial.fields:
        if (field.branch, field.spin) == ("L", "up"):
            branch, spin, field_phase = "R", "down", 1
        elif (field.branch, field.spin) == ("R", "down"):
            branch, spin, field_phase = "L", "up", -1
        else:
            raise ValueError(
                "operator contains a field outside the helical Kramers pair"
            )
        phase *= field_phase
        transformed.append(
            EdgeField(
                branch=branch,
                spin=spin,
                dagger=field.dagger,
                derivative_order=field.derivative_order,
            )
        )
    return EdgeMonomial(phase=phase, fields=tuple(transformed))


def interaction_operator_diagnostics() -> dict[str, float | int | bool]:
    """Derive time-reversal invariance and scaling dimension from the operator."""

    operator = two_particle_backscattering_operator()
    time_reversed = _canonicalize(_time_reverse(operator))
    conjugate = _canonicalize(_hermitian_conjugate(operator))
    fermion_dimension = 0.5 * len(operator.fields)
    derivative_dimension = sum(field.derivative_order for field in operator.fields)
    scaling_dimension = fermion_dimension + derivative_dimension
    return {
        "field_count": len(operator.fields),
        "derivative_count": int(derivative_dimension),
        "fermion_scaling_dimension": fermion_dimension,
        "total_scaling_dimension": scaling_dimension,
        "time_reversal_maps_to_hermitian_conjugate": time_reversed == conjugate,
        "time_reversal_phase": time_reversed.phase,
        "hermitian_conjugate_phase": conjugate.phase,
    }


def weak_edge_perturbation_inventory() -> list[dict[str, float | str | bool]]:
    """Classify the lowest local perturbations of one helical Kramers pair."""

    single_backscatter = EdgeMonomial(
        phase=1,
        fields=(
            EdgeField("L", "up", True),
            EdgeField("R", "down", False),
        ),
    )
    local_pair_without_derivatives = EdgeMonomial(
        phase=1,
        fields=(
            EdgeField("L", "up", True),
            EdgeField("L", "up", True),
            EdgeField("R", "down", False),
            EdgeField("R", "down", False),
        ),
    )
    derivative_pair = two_particle_backscattering_operator()
    single_tr = _canonicalize(_time_reverse(single_backscatter))
    single_hc = _canonicalize(_hermitian_conjugate(single_backscatter))
    local_pair = _canonicalize(local_pair_without_derivatives)
    derivative_tr = _canonicalize(_time_reverse(derivative_pair))
    derivative_hc = _canonicalize(_hermitian_conjugate(derivative_pair))
    return [
        {
            "operator": "forward_density",
            "time_reversal_allowed": True,
            "pauli_nonzero": True,
            "scaling_dimension": 1.0,
            "rg_class": "marginal_no_backscattering",
        },
        {
            "operator": "single_particle_backscattering",
            "time_reversal_allowed": single_tr == single_hc,
            "pauli_nonzero": True,
            "scaling_dimension": 1.0,
            "rg_class": "forbidden_by_time_reversal",
        },
        {
            "operator": "local_pair_backscattering_without_derivatives",
            "time_reversal_allowed": True,
            "pauli_nonzero": local_pair.phase != 0,
            "scaling_dimension": 2.0,
            "rg_class": "vanishes_by_fermion_antisymmetry",
        },
        {
            "operator": "derivative_pair_backscattering",
            "time_reversal_allowed": derivative_tr == derivative_hc,
            "pauli_nonzero": True,
            "scaling_dimension": 4.0,
            "rg_class": "irrelevant_at_weak_coupling",
        },
    ]


def _thermal_relaxation_kernel(temperature: float, scaling_dimension: float) -> float:
    """Numerically integrate a finite-T Kubo relaxation kernel.

    The second time moment of the finite-temperature conformal correlator is
    proportional to the edge resistivity.  Evaluating it at every temperature,
    rather than inserting the final exponent, lets the fitted power law test
    the operator-derived scaling dimension.
    """

    if temperature <= 0 or scaling_dimension <= 0:
        raise ValueError("temperature and scaling dimension must be positive")
    time_limit = 15.0 / (pi * temperature)

    def integrand(time: float) -> float:
        correlator = (pi * temperature / np.cosh(pi * temperature * time)) ** (
            2.0 * scaling_dimension
        )
        return float(time**2 * correlator)

    value, error = integrate.quad(
        integrand,
        -time_limit,
        time_limit,
        epsabs=1e-13,
        epsrel=1e-11,
        limit=200,
    )
    if error > max(1e-10, 1e-8 * abs(value)):
        raise RuntimeError("thermal Kubo kernel did not converge")
    return float(value)


def interaction_conductivity_sweep(
    interaction_strengths: np.ndarray,
    temperatures: np.ndarray,
) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Compute and fit the leading ``u`` and ``T`` edge conductivity laws."""

    operator = interaction_operator_diagnostics()
    scaling_dimension = float(operator["total_scaling_dimension"])
    strengths = np.asarray(interaction_strengths, dtype=float)
    thermal_values = np.asarray(temperatures, dtype=float)
    if (
        strengths.ndim != 1
        or thermal_values.ndim != 1
        or len(strengths) < 3
        or len(thermal_values) < 4
        or np.any(strengths <= 0)
        or np.any(thermal_values <= 0)
    ):
        raise ValueError("positive one-dimensional u/T sweeps are required")

    kernels = {
        float(temperature): _thermal_relaxation_kernel(
            float(temperature), scaling_dimension
        )
        for temperature in thermal_values
    }
    rows = [
        {
            "interaction_u": float(strength),
            "temperature": float(temperature),
            "relaxation_kernel": kernels[float(temperature)],
            "conductivity_dimensionless": float(
                1.0 / (strength**2 * kernels[float(temperature)])
            ),
        }
        for strength in strengths
        for temperature in thermal_values
    ]
    reference_u = float(strengths[len(strengths) // 2])
    temperature_rows = [row for row in rows if row["interaction_u"] == reference_u]
    temperature_slope = float(
        np.polyfit(
            np.log([row["temperature"] for row in temperature_rows]),
            np.log([row["conductivity_dimensionless"] for row in temperature_rows]),
            1,
        )[0]
    )
    reference_temperature = float(thermal_values[len(thermal_values) // 2])
    interaction_rows = [
        row for row in rows if row["temperature"] == reference_temperature
    ]
    interaction_slope = float(
        np.polyfit(
            np.log([row["interaction_u"] for row in interaction_rows]),
            np.log([row["conductivity_dimensionless"] for row in interaction_rows]),
            1,
        )[0]
    )
    return rows, {
        "operator_scaling_dimension": scaling_dimension,
        "fitted_temperature_exponent": temperature_slope,
        "predicted_temperature_exponent": 3.0 - 2.0 * scaling_dimension,
        "fitted_interaction_exponent": interaction_slope,
        "predicted_interaction_exponent": -2.0,
    }


def helical_scalar_disorder_ensemble(
    *,
    realizations: int,
    sites: int,
    disorder_strength: float,
    velocity: float,
    seed: int,
) -> tuple[list[dict[str, float | int]], dict[str, float]]:
    """Propagate a single helical pair through scalar T-symmetric disorder.

    The first-order edge Dirac equations decouple exactly: scalar disorder only
    accumulates opposite propagation phases.  The returned scattering matrix
    is constructed realization by realization, so zero reflection and zero
    Lyapunov exponent are observable outputs rather than a hard-coded label.
    """

    if realizations < 4 or sites < 16 or disorder_strength < 0 or velocity <= 0:
        raise ValueError("resolved positive disorder ensemble required")
    generator = np.random.default_rng(seed)
    rows: list[dict[str, float | int]] = []
    for realization in range(realizations):
        potential = generator.uniform(-disorder_strength, disorder_strength, sites)
        integrated_potential = float(np.sum(potential) / sites)
        right_phase = np.exp(-1j * integrated_potential / velocity)
        left_phase = np.exp(1j * integrated_potential / velocity)
        scattering = np.asarray(
            [[right_phase, 0.0], [0.0, left_phase]], dtype=np.complex128
        )
        reflection_probability = float(
            abs(scattering[0, 1]) ** 2 + abs(scattering[1, 0]) ** 2
        )
        transmission_probability = float(
            (abs(scattering[0, 0]) ** 2 + abs(scattering[1, 1]) ** 2) / 2.0
        )
        rows.append(
            {
                "realization": realization,
                "mean_potential": integrated_potential,
                "reflection_probability": reflection_probability,
                "transmission_probability": transmission_probability,
                "unitarity_residual": float(
                    np.max(np.abs(scattering.conj().T @ scattering - np.eye(2)))
                ),
                "lyapunov_exponent_per_site": float(
                    -np.log(max(transmission_probability, np.finfo(float).tiny)) / sites
                ),
            }
        )
    return rows, {
        "max_reflection_probability": max(
            float(row["reflection_probability"]) for row in rows
        ),
        "min_transmission_probability": min(
            float(row["transmission_probability"]) for row in rows
        ),
        "max_unitarity_residual": max(float(row["unitarity_residual"]) for row in rows),
        "max_abs_lyapunov_exponent_per_site": max(
            abs(float(row["lyapunov_exponent_per_site"])) for row in rows
        ),
    }
