"""Independent dense-matrix audit for PRL-Bench record 085.

The module keeps three generators distinct:

* the phase-independent van Vleck Hamiltonian;
* the stroboscopic principal-log Floquet Hamiltonian at ``t0=0``;
* the expression printed in source Eq. (3) and copied into the frozen gold.

Conflating these objects is the central failure mode of the benchmark record.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm, schur


COMPLEX = np.complex128
I2 = np.eye(2, dtype=COMPLEX)
X = np.array([[0, 1], [1, 0]], dtype=COMPLEX)
Y = np.array([[0, -1j], [1j, 0]], dtype=COMPLEX)
Z = np.array([[1, 0], [0, -1]], dtype=COMPLEX)


def commutator(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return left @ right - right @ left


def pauli_string(length: int, sites: dict[int, np.ndarray]) -> np.ndarray:
    result = np.array([[1]], dtype=COMPLEX)
    for site in range(length):
        result = np.kron(result, sites.get(site, I2))
    return result


@dataclass(frozen=True)
class IsingOperators:
    length: int
    j: float
    h0: float
    identity: np.ndarray
    parity: np.ndarray
    szz: np.ndarray
    syy: np.ndarray
    sx_boundary: np.ndarray
    sx_bulk: np.ndarray
    szxz: np.ndarray
    a: np.ndarray
    b: np.ndarray

    @property
    def basis(self) -> tuple[np.ndarray, ...]:
        return (self.szz, self.syy, self.sx_boundary, self.sx_bulk, self.szxz)


def build_operators(length: int = 6, j: float = 1.0, h0: float = 2.0) -> IsingOperators:
    if length < 3:
        raise ValueError("length must be at least three")
    dimension = 2**length
    szz = sum(
        (pauli_string(length, {site: Z, site + 1: Z}) for site in range(length - 1)),
        np.zeros((dimension, dimension), dtype=COMPLEX),
    )
    syy = sum(
        (pauli_string(length, {site: Y, site + 1: Y}) for site in range(length - 1)),
        np.zeros((dimension, dimension), dtype=COMPLEX),
    )
    sx_boundary = pauli_string(length, {0: X}) + pauli_string(length, {length - 1: X})
    sx_bulk = sum(
        (pauli_string(length, {site: X}) for site in range(1, length - 1)),
        np.zeros((dimension, dimension), dtype=COMPLEX),
    )
    szxz = sum(
        (
            pauli_string(length, {site - 1: Z, site: X, site + 1: Z})
            for site in range(1, length - 1)
        ),
        np.zeros((dimension, dimension), dtype=COMPLEX),
    )
    sx_all = sx_boundary + sx_bulk
    parity = pauli_string(length, {site: X for site in range(length)})
    return IsingOperators(
        length=length,
        j=j,
        h0=h0,
        identity=np.eye(dimension, dtype=COMPLEX),
        parity=parity,
        szz=szz,
        syy=syy,
        sx_boundary=sx_boundary,
        sx_bulk=sx_bulk,
        szxz=szxz,
        a=-j * szz,
        b=-(h0 / 2.0) * sx_all,
    )


def hilbert_schmidt_coefficients(
    matrix: np.ndarray, basis: tuple[np.ndarray, ...]
) -> tuple[np.ndarray, float]:
    coefficients = np.array(
        [
            np.trace(operator.conj().T @ matrix).real
            / np.trace(operator.conj().T @ operator).real
            for operator in basis
        ]
    )
    residual = matrix - sum(
        (coefficient * operator for coefficient, operator in zip(coefficients, basis, strict=True)),
        np.zeros_like(matrix),
    )
    return coefficients, float(np.linalg.norm(residual, 2))


def nested_commutators(operators: IsingOperators) -> tuple[np.ndarray, np.ndarray]:
    ab = commutator(operators.a, operators.b)
    return commutator(operators.b, ab), commutator(operators.a, ab)


def van_vleck_hamiltonian(operators: IsingOperators, omega: float) -> np.ndarray:
    """Phase-independent van Vleck generator through order omega^-2.

    A periodic rotation which removes ``B cos(omega t)`` gives
    ``A + [B,[A,B]]/(4 omega^2)`` after averaging.  This is also the
    single-harmonic specialization of the standard van Vleck expansion.
    """

    cbb, _ = nested_commutators(operators)
    return operators.a + cbb / (4.0 * omega**2)


def stroboscopic_second_order_hamiltonian(
    operators: IsingOperators, omega: float
) -> np.ndarray:
    """Principal-log generator at drive phase t0=0 through order omega^-2."""

    cbb, caa = nested_commutators(operators)
    return operators.a + (cbb / 4.0 - caa) / omega**2


def frozen_gold_hamiltonian(operators: IsingOperators, omega: float) -> np.ndarray:
    """Source Eq. (3) / frozen Task-4 answer, represented without repair."""

    correction = (
        -(operators.j * operators.h0**2 / 2.0) * operators.szz
        + (operators.j * operators.h0**2 / 2.0) * operators.syy
        - (2.0 * operators.h0 * operators.j**2) * operators.sx_boundary
        - (4.0 * operators.h0 * operators.j**2) * operators.sx_bulk
        - (4.0 * operators.h0 * operators.j**2) * operators.szxz
    )
    return operators.a + correction / omega**2


def floquet_unitary_adaptive(
    operators: IsingOperators,
    omega: float,
    *,
    rtol: float = 2e-12,
    atol: float = 2e-14,
) -> tuple[np.ndarray, int]:
    """Reference time ordering from a high-order adaptive dense ODE solve."""

    dimension = operators.a.shape[0]
    period = 2.0 * np.pi / omega

    def rhs(time: float, flattened: np.ndarray) -> np.ndarray:
        unitary = flattened.reshape(dimension, dimension)
        hamiltonian = operators.a + operators.b * np.cos(omega * time)
        return (-1j * hamiltonian @ unitary).reshape(-1)

    solution = solve_ivp(
        rhs,
        (0.0, period),
        np.eye(dimension, dtype=COMPLEX).reshape(-1),
        method="DOP853",
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution.y[:, -1].reshape(dimension, dimension), int(solution.nfev)


def floquet_unitary_midpoint(
    operators: IsingOperators, omega: float, steps: int
) -> np.ndarray:
    """Explicit midpoint-product discretization of the time-ordered exponential."""

    if steps <= 0:
        raise ValueError("steps must be positive")
    dimension = operators.a.shape[0]
    period = 2.0 * np.pi / omega
    dt = period / steps
    unitary = np.eye(dimension, dtype=COMPLEX)
    for step in range(steps):
        time_midpoint = (step + 0.5) * dt
        hamiltonian = operators.a + operators.b * np.cos(omega * time_midpoint)
        unitary = expm(-1j * hamiltonian * dt) @ unitary
    return unitary


def principal_floquet_hamiltonian(unitary: np.ndarray, omega: float) -> np.ndarray:
    """Return i log(U)/T with eigenphases fixed to (-pi, pi]."""

    period = 2.0 * np.pi / omega
    triangular, vectors = schur(unitary, output="complex")
    phases = np.angle(np.diag(triangular))
    result = vectors @ np.diag(-phases / period) @ vectors.conj().T
    return (result + result.conj().T) / 2.0


def principal_floquet_from_adaptive(
    operators: IsingOperators, omega: float
) -> tuple[np.ndarray, int, float]:
    unitary, evaluations = floquet_unitary_adaptive(operators, omega)
    unitarity_error = float(
        np.linalg.norm(unitary.conj().T @ unitary - operators.identity, 2)
    )
    return principal_floquet_hamiltonian(unitary, omega), evaluations, unitarity_error


def source_frozen_mismatch(operators: IsingOperators, omega: float) -> dict[str, float]:
    exact, evaluations, unitarity_error = principal_floquet_from_adaptive(operators, omega)
    delta = exact - frozen_gold_hamiltonian(operators, omega)
    norm = float(np.linalg.norm(delta, 2))
    return {
        "omega": float(omega),
        "norm": norm,
        "omega2_norm": omega**2 * norm,
        "omega3_norm": omega**3 * norm,
        "ode_evaluations": evaluations,
        "unitarity_error": unitarity_error,
    }


def subsystem_parity(length: int, start: int, subsystem_length: int) -> np.ndarray:
    end = start + subsystem_length
    if not (0 <= start < end <= length):
        raise ValueError("subsystem must be a nonempty proper interval")
    return pauli_string(length, {site: X for site in range(start, end)})


def cut_count(length: int, start: int, subsystem_length: int) -> int:
    end = start + subsystem_length
    if not (0 <= start < end <= length) or subsystem_length == length:
        raise ValueError("subsystem must be a nonempty proper interval")
    return int(start > 0) + int(end < length)


def cut_commutator_norm(
    operators: IsingOperators, start: int, subsystem_length: int
) -> float:
    parity_a = subsystem_parity(operators.length, start, subsystem_length)
    return float(np.linalg.norm(commutator(operators.a, parity_a), 2))


def partial_trace_pure(
    state: np.ndarray, length: int, kept_sites: tuple[int, ...]
) -> np.ndarray:
    kept = tuple(sorted(kept_sites))
    traced = tuple(site for site in range(length) if site not in kept)
    tensor = state.reshape((2,) * length)
    permuted = np.transpose(tensor, kept + traced)
    matrix = permuted.reshape(2 ** len(kept), 2 ** len(traced))
    return matrix @ matrix.conj().T
