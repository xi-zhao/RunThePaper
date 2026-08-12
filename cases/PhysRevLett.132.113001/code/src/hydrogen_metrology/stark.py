"""Hydrogenic Stark maps derived from angular-momentum matrix elements.

The numerical path deliberately does not contain any digitized coordinates or
paper-output arrays.  It combines:

1. analytic same-n radial/angular matrix elements of z;
2. the leading reduced-mass Dirac fine-structure correction;
3. exact Clebsch-Gordan weights for a fixed m_l and spin projection;
4. the standard second-order inter-manifold hydrogen Stark correction; and
5. a declared high-n hyperfine scaling estimate.

The first four items determine the scientific shape and scale.  The fifth only
resolves the small branch splitting and remains explicitly approximate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.linalg import eigh

from .constants import CODATA2018, PhysicalConstants


@dataclass(frozen=True)
class StarkBranch:
    name: str
    spin_projection: float
    magnetic_label: int
    shift_hz: np.ndarray


def same_n_z_matrix(n: int, m_l: int = 1) -> np.ndarray:
    """Return <n,l,m|z/a0|n,l+1,m> in the fixed-n hydrogen manifold."""

    if n <= abs(m_l):
        raise ValueError("n must exceed |m_l|")
    angular_momenta = np.arange(abs(m_l), n, dtype=float)
    matrix = np.zeros((angular_momenta.size, angular_momenta.size), dtype=float)
    for index, l_value in enumerate(angular_momenta[:-1]):
        l_prime = l_value + 1.0
        numerator = (n * n - l_prime * l_prime) * (l_prime * l_prime - m_l * m_l)
        denominator = 4.0 * l_prime * l_prime - 1.0
        matrix_element = 1.5 * n * np.sqrt(numerator / denominator)
        matrix[index, index + 1] = matrix_element
        matrix[index + 1, index] = matrix_element
    return matrix


def expected_linear_stark_eigenvalues(n: int, m_l: int = 1) -> np.ndarray:
    """Exact parabolic-manifold z eigenvalues in units of a0."""

    k_values = np.arange(-(n - abs(m_l) - 1), n - abs(m_l), 2, dtype=float)
    return 1.5 * n * k_values


def inverse_j_expectation(
    l_value: np.ndarray, m_l: int, spin_projection: float
) -> np.ndarray:
    """Clebsch-Gordan expectation of 1/(j+1/2).

    A fixed |l,m_l>|s,m_s> state is expanded in j=l±1/2.  The returned
    expectation is then inserted into the leading Dirac fine-structure term.
    """

    l_value = np.asarray(l_value, dtype=float)
    if spin_projection not in (-0.5, 0.5):
        raise ValueError("spin_projection must be -0.5 or +0.5")
    denominator = 2.0 * l_value + 1.0
    if spin_projection < 0:
        weight_minus = (l_value + m_l) / denominator
        weight_plus = (l_value - m_l + 1.0) / denominator
    else:
        weight_minus = (l_value - m_l) / denominator
        weight_plus = (l_value + m_l + 1.0) / denominator
    return weight_minus / l_value + weight_plus / (l_value + 1.0)


def dirac_diagonal_hz(
    n: int,
    m_l: int,
    spin_projection: float,
    constants: PhysicalConstants = CODATA2018,
) -> np.ndarray:
    """Leading Dirac correction relative to the reduced-mass Bohr energy."""

    l_values = np.arange(abs(m_l), n, dtype=float)
    inverse_j = inverse_j_expectation(l_values, m_l, spin_projection)
    prefactor = (
        -constants.hydrogen_rydberg_frequency_hz * constants.fine_structure**2 / n**3
    )
    return prefactor * (inverse_j - 3.0 / (4.0 * n))


def intermanifold_quadratic_shift_hz(
    n: int,
    electric_field_v_per_cm: np.ndarray | float,
    *,
    k: int = 0,
    m_l: int = 1,
    constants: PhysicalConstants = CODATA2018,
) -> np.ndarray:
    """Second-order hydrogen Stark shift from neighboring n manifolds."""

    field_atomic = (
        np.asarray(electric_field_v_per_cm, dtype=float)
        / constants.atomic_field_v_per_cm
    )
    coefficient = -(n**4) * (17.0 * n**2 - 3.0 * k**2 - 9.0 * m_l**2 + 19.0) / 16.0
    return coefficient * field_atomic**2 * constants.hartree_over_h_hz


def _tracked_intramanifold_branch(
    n: int,
    fields_v_per_cm: np.ndarray,
    spin_projection: float,
    *,
    m_l: int = 1,
    constants: PhysicalConstants = CODATA2018,
) -> np.ndarray:
    """Track the k=0 eigenvector continuously from high to low field."""

    fields = np.asarray(fields_v_per_cm, dtype=float)
    if fields.ndim != 1 or fields.size < 2:
        raise ValueError("fields must be a one-dimensional grid")
    if np.any(fields < 0) or np.any(np.diff(fields) < 0):
        raise ValueError("fields must be nonnegative and ascending")

    z_matrix = same_n_z_matrix(n, m_l)
    z_eigenvalues, z_eigenvectors = eigh(z_matrix)
    k_zero_vector = z_eigenvectors[:, np.argmin(np.abs(z_eigenvalues))]
    diagonal_hz = dirac_diagonal_hz(n, m_l, spin_projection, constants)

    descending = fields[::-1]
    tracked_descending: list[float] = []
    previous_vector: np.ndarray | None = None
    for field in descending:
        scale_hz = field / constants.atomic_field_v_per_cm * constants.hartree_over_h_hz
        eigenvalues, eigenvectors = eigh(np.diag(diagonal_hz) + scale_hz * z_matrix)
        reference = k_zero_vector if previous_vector is None else previous_vector
        branch_index = int(np.argmax(np.abs(eigenvectors.T @ reference)))
        previous_vector = eigenvectors[:, branch_index]
        tracked_descending.append(float(eigenvalues[branch_index]))
    return np.asarray(tracked_descending[::-1])


def hyperfine_branch_offset_hz(n: int, family: str, magnetic_label: int) -> float:
    """Declared high-n hyperfine estimate used only to resolve close branches."""

    scale = CODATA2018.ground_hyperfine_hz * 6.0 / n**5
    if family == "lower":
        factors = {0: -0.75, 1: 0.0, 2: 0.25}
    elif family == "upper":
        factors = {0: -0.25, 1: 0.25}
    else:
        raise ValueError(f"unknown family: {family}")
    try:
        return float(scale * factors[magnetic_label])
    except KeyError as exc:
        raise ValueError("invalid magnetic label for branch family") from exc


def k_zero_stark_branches(
    n: int,
    fields_v_per_cm: Iterable[float],
    *,
    constants: PhysicalConstants = CODATA2018,
) -> list[StarkBranch]:
    """Return the five resolved k=0, |m_l|=1 branches used in the paper."""

    fields = np.asarray(tuple(fields_v_per_cm), dtype=float)
    quadratic = intermanifold_quadratic_shift_hz(n, fields, constants=constants)
    lower = (
        _tracked_intramanifold_branch(n, fields, -0.5, constants=constants) + quadratic
    )
    upper = (
        _tracked_intramanifold_branch(n, fields, 0.5, constants=constants) + quadratic
    )
    branches: list[StarkBranch] = []
    for magnetic_label in (0, 1, 2):
        branches.append(
            StarkBranch(
                name=f"lower_mf{magnetic_label}",
                spin_projection=-0.5,
                magnetic_label=magnetic_label,
                shift_hz=lower + hyperfine_branch_offset_hz(n, "lower", magnetic_label),
            )
        )
    for magnetic_label in (0, 1):
        branches.append(
            StarkBranch(
                name=f"upper_mf{magnetic_label}",
                spin_projection=0.5,
                magnetic_label=magnetic_label,
                shift_hz=upper + hyperfine_branch_offset_hz(n, "upper", magnetic_label),
            )
        )
    return branches


def field_free_level_rows(
    principal_quantum_numbers: Iterable[int],
    *,
    constants: PhysicalConstants = CODATA2018,
) -> list[dict[str, float | int | str]]:
    """Generate a complete leading-order n,l,j level table.

    This is an independent approximation to the gated supplemental table.
    QED and finite-size terms are intentionally not inferred from its values.
    """

    rows: list[dict[str, float | int | str]] = []
    for n in principal_quantum_numbers:
        for l_value in range(n):
            j_values = [0.5] if l_value == 0 else [l_value - 0.5, l_value + 0.5]
            for j_value in j_values:
                inverse_j = 1.0 / (j_value + 0.5)
                shift_hz = (
                    -constants.hydrogen_rydberg_frequency_hz
                    * constants.fine_structure**2
                    / n**3
                    * (inverse_j - 3.0 / (4.0 * n))
                )
                f_values = sorted(
                    {
                        abs(j_value - 0.5),
                        j_value + 0.5,
                    }
                )
                for f_value in f_values:
                    rows.append(
                        {
                            "n": n,
                            "l": l_value,
                            "j": j_value,
                            "f": f_value,
                            "dirac_shift_khz": shift_hz / 1e3,
                            "model_stage": "leading_dirac_only",
                        }
                    )
    return rows
