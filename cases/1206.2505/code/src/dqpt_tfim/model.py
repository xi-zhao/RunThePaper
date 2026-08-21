"""Formula-first numerics for Heyl--Polkovnikov--Kehrein (2013).

The integrable-sector functions follow the equations printed in the paper.
The local-order-parameter channel is an independent finite-spin-chain
cross-check: it never reads author data, code, or source-figure pixels.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, diags
from scipy.sparse.linalg import eigsh, expm_multiply


def dispersion(k: np.ndarray | float, g: float) -> np.ndarray:
    momentum = np.asarray(k, dtype=float)
    return np.sqrt((g - np.cos(momentum)) ** 2 + np.sin(momentum) ** 2)


def bogoliubov_angle(k: np.ndarray | float, g: float) -> np.ndarray:
    momentum = np.asarray(k, dtype=float)
    return 0.5 * np.arctan2(np.sin(momentum), g - np.cos(momentum))


def angle_difference(k: np.ndarray | float, g0: float, g1: float) -> np.ndarray:
    return bogoliubov_angle(k, g0) - bogoliubov_angle(k, g1)


def critical_momentum(g0: float, g1: float) -> float | None:
    denominator = g0 + g1
    if abs(denominator) < 1e-15:
        return None
    cosine = (1.0 + g0 * g1) / denominator
    if not -1.0 <= cosine <= 1.0:
        return None
    return float(np.arccos(cosine))


def critical_period(g0: float, g1: float) -> float | None:
    momentum = critical_momentum(g0, g1)
    if momentum is None:
        return None
    return float(np.pi / dispersion(momentum, g1))


def ramp_mode_occupations(
    momentum: np.ndarray,
    g0: float,
    g1: float,
    duration: float,
    steps: int,
    profile: str = "linear",
) -> dict[str, np.ndarray | float]:
    """Evolve independent Bogoliubov modes through a field ramp.

    Each momentum mode obeys the two-level Hamiltonian
    ``h_k=(g-cos(k))*sigma_z+sin(k)*sigma_x``.  Midpoint exponentials preserve
    the norm exactly up to floating-point roundoff.  The returned occupation is
    the overlap with the positive-energy eigenstate of the final Hamiltonian.

    The paper proves the crossing-mode mechanism for a general ramp but does
    not publish a particular ramp function or duration.  Supporting ``linear``
    and ``smoothstep`` therefore gives an executable, explicitly reconstructed
    family without pretending that either protocol is an author-supplied one.
    """

    k = np.asarray(momentum, dtype=float)
    if k.ndim != 1 or k.size < 3:
        raise ValueError("momentum must be a one-dimensional grid")
    if duration <= 0.0 or steps < 2:
        raise ValueError("duration must be positive and steps at least two")
    if profile not in {"linear", "smoothstep"}:
        raise ValueError(f"unsupported ramp profile: {profile}")

    def field(fraction: float) -> float:
        if profile == "smoothstep":
            fraction = fraction * fraction * (3.0 - 2.0 * fraction)
        return g0 + (g1 - g0) * fraction

    sine = np.sin(k)
    cosine = np.cos(k)
    initial_h = np.zeros((k.size, 2, 2), dtype=float)
    initial_h[:, 0, 0] = g0 - cosine
    initial_h[:, 1, 1] = -(g0 - cosine)
    initial_h[:, 0, 1] = sine
    initial_h[:, 1, 0] = sine
    _, initial_vectors = np.linalg.eigh(initial_h)
    state = initial_vectors[:, :, 0].astype(complex)

    step_size = duration / steps
    identity = np.eye(2, dtype=complex)[None, :, :]
    for step in range(steps):
        g_midpoint = field((step + 0.5) / steps)
        z = g_midpoint - cosine
        energy = np.sqrt(z * z + sine * sine)
        hamiltonian = np.zeros((k.size, 2, 2), dtype=complex)
        hamiltonian[:, 0, 0] = z
        hamiltonian[:, 1, 1] = -z
        hamiltonian[:, 0, 1] = sine
        hamiltonian[:, 1, 0] = sine
        propagator = (
            np.cos(energy * step_size)[:, None, None] * identity
            - 1.0j
            * np.sin(energy * step_size)[:, None, None]
            * hamiltonian
            / energy[:, None, None]
        )
        state = np.einsum("kij,kj->ki", propagator, state)

    final_h = np.zeros((k.size, 2, 2), dtype=float)
    final_h[:, 0, 0] = g1 - cosine
    final_h[:, 1, 1] = -(g1 - cosine)
    final_h[:, 0, 1] = sine
    final_h[:, 1, 0] = sine
    _, final_vectors = np.linalg.eigh(final_h)
    excited = final_vectors[:, :, 1]
    occupation = np.abs(np.einsum("ki,ki->k", excited.conj(), state)) ** 2
    return {
        "occupation": occupation,
        "state_norm": np.sum(np.abs(state) ** 2, axis=1),
        "maximum_norm_error": float(
            np.max(np.abs(np.sum(np.abs(state) ** 2, axis=1) - 1.0))
        ),
    }


def fisher_zero_lines(
    k: np.ndarray,
    g0: float,
    g1: float,
    branch_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return Re z_n(k), Im z_n(k) for every requested branch."""

    momentum = np.asarray(k, dtype=float)
    branches = np.asarray(branch_indices, dtype=int)
    phi = angle_difference(momentum, g0, g1)
    energy = dispersion(momentum, g1)
    tangent_squared = np.tan(phi) ** 2
    real = np.log(np.clip(tangent_squared, 1e-30, 1e30)) / (2.0 * energy)
    imaginary = np.pi * (2.0 * branches[:, None] + 1.0) / (2.0 * energy[None, :])
    return np.broadcast_to(real, imaginary.shape).copy(), imaginary


def _momentum_grid(points: int) -> np.ndarray:
    if points < 101:
        raise ValueError("momentum grid needs at least 101 points")
    return np.linspace(0.0, np.pi, points)


def loschmidt_rate(
    times: np.ndarray | float,
    g0: float,
    g1: float,
    k_points: int = 4001,
) -> np.ndarray:
    momentum = _momentum_grid(k_points)
    phi = angle_difference(momentum, g0, g1)
    energy = dispersion(momentum, g1)
    time = np.atleast_1d(np.asarray(times, dtype=float))
    factor = (
        np.sin(2.0 * phi)[:, None] ** 2 * np.sin(energy[:, None] * time[None, :]) ** 2
    )
    values = -np.trapezoid(
        np.log(np.clip(1.0 - factor, 1e-300, None)), momentum, axis=0
    ) / (2.0 * np.pi)
    return values if np.ndim(times) else values[0]


def _work_statistics(
    resistance: np.ndarray,
    time: float,
    g0: float,
    g1: float,
    k_points: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    momentum = _momentum_grid(k_points)
    phi = angle_difference(momentum, g0, g1)
    energy0 = dispersion(momentum, g0)
    energy1 = dispersion(momentum, g1)
    excitation = np.sin(2.0 * phi) ** 2 * np.sin(energy1 * time) ** 2
    resistance = np.atleast_1d(np.asarray(resistance, dtype=float))
    boltzmann = np.exp(
        np.clip(-2.0 * energy0[:, None] * resistance[None, :], -700.0, 700.0)
    )
    argument = 1.0 + excitation[:, None] * (boltzmann - 1.0)
    argument = np.clip(argument, 1e-300, None)
    cumulant = -np.trapezoid(np.log(argument), momentum, axis=0) / (2.0 * np.pi)
    derivative = np.trapezoid(
        2.0 * energy0[:, None] * excitation[:, None] * boltzmann / argument,
        momentum,
        axis=0,
    ) / (2.0 * np.pi)
    curvature = -np.trapezoid(
        4.0
        * energy0[:, None] ** 2
        * excitation[:, None]
        * (1.0 - excitation[:, None])
        * boltzmann
        / argument**2,
        momentum,
        axis=0,
    ) / (2.0 * np.pi)
    return cumulant, derivative, curvature


def _work_kernel(
    resistance: np.ndarray,
    time: float,
    g0: float,
    g1: float,
    k_points: int,
) -> tuple[np.ndarray, np.ndarray]:
    cumulant, derivative, _ = _work_statistics(resistance, time, g0, g1, k_points)
    return cumulant, derivative


def cumulant_rate(
    resistance: np.ndarray | float,
    time: float,
    g0: float,
    g1: float,
    k_points: int = 4001,
) -> np.ndarray:
    values, _ = _work_kernel(np.atleast_1d(resistance), time, g0, g1, k_points)
    return values if np.ndim(resistance) else values[0]


def mean_work_density(
    times: np.ndarray | float,
    g0: float,
    g1: float,
    k_points: int = 4001,
) -> np.ndarray:
    time = np.atleast_1d(np.asarray(times, dtype=float))
    values = np.array(
        [_work_kernel(np.array([0.0]), item, g0, g1, k_points)[1][0] for item in time]
    )
    return values if np.ndim(times) else values[0]


def work_rate_grid(
    times: np.ndarray,
    work_densities: np.ndarray,
    g0: float,
    g1: float,
    k_points: int = 2001,
    resistance_min: float = -20.0,
    resistance_max: float = 40.0,
    resistance_points: int = 401,
) -> tuple[np.ndarray, np.ndarray]:
    """Legendre-transform the exact cumulant with a bracketed saddle solve.

    The declared resistance grid supplies a deterministic bracket and initial
    guess.  Each requested work density is then refined against
    ``partial_R c(R,t)=w`` before evaluating ``c(R*,t)-wR*``.  Evaluating the
    cumulant at the solved saddle avoids the nonphysical zero plateaus produced
    by interpolating both axes of the Legendre transform.
    """

    time = np.asarray(times, dtype=float)
    work = np.asarray(work_densities, dtype=float)
    resistance = np.linspace(resistance_min, resistance_max, resistance_points)
    rates = np.full((time.size, work.size), np.nan, dtype=float)
    means = np.zeros(time.size, dtype=float)
    for index, value in enumerate(time):
        if abs(value) < 1e-14:
            rates[index, np.isclose(work, 0.0)] = 0.0
            continue
        _, derivative = _work_kernel(resistance, value, g0, g1, k_points)
        order = np.argsort(derivative)
        unique_work, unique_indices = np.unique(derivative[order], return_index=True)
        unique_resistance = resistance[order][unique_indices]
        means[index] = float(
            _work_kernel(np.array([0.0]), value, g0, g1, k_points)[1][0]
        )
        inside = (work >= unique_work[0]) & (work <= unique_work[-1])
        requested = work[inside]
        saddle = np.interp(requested, unique_work, unique_resistance)
        lower = np.full(requested.size, resistance_min, dtype=float)
        upper = np.full(requested.size, resistance_max, dtype=float)
        for _ in range(8):
            _, saddle_work, curvature = _work_statistics(
                saddle, value, g0, g1, k_points
            )
            lower = np.where(saddle_work > requested, saddle, lower)
            upper = np.where(saddle_work <= requested, saddle, upper)
            newton = saddle - np.divide(
                saddle_work - requested,
                curvature,
                out=np.zeros_like(saddle),
                where=np.abs(curvature) > 1e-14,
            )
            midpoint = 0.5 * (lower + upper)
            saddle = np.where(
                np.isfinite(newton) & (newton > lower) & (newton < upper),
                newton,
                midpoint,
            )
        c_saddle, _, _ = _work_statistics(saddle, value, g0, g1, k_points)
        solved_rates = c_saddle - requested * saddle
        if np.any(solved_rates < -1e-10):
            raise RuntimeError("Legendre saddle produced a negative rate")
        rates[index, inside] = np.where(np.abs(solved_rates) < 1e-13, 0.0, solved_rates)
        zero = np.isclose(work, 0.0, atol=1e-15)
        if np.any(zero):
            rates[index, zero] = float(loschmidt_rate(value, g0, g1, k_points=k_points))
    return rates, means


def spin_hamiltonian(sites: int, g: float, periodic: bool = True) -> csr_matrix:
    if sites < 2:
        raise ValueError("spin chain needs at least two sites")
    dimension = 1 << sites
    states = np.arange(dimension, dtype=np.int64)
    diagonal = np.zeros(dimension, dtype=float)
    bonds = sites if periodic else sites - 1
    for site in range(bonds):
        neighbor = (site + 1) % sites
        z_site = 1.0 - 2.0 * ((states >> site) & 1)
        z_neighbor = 1.0 - 2.0 * ((states >> neighbor) & 1)
        diagonal -= 0.5 * z_site * z_neighbor
    rows = np.tile(states, sites)
    columns = np.concatenate([states ^ (1 << site) for site in range(sites)])
    data = np.full(rows.size, 0.5 * g, dtype=float)
    transverse = coo_matrix(
        (data, (rows, columns)), shape=(dimension, dimension)
    ).tocsr()
    return (diags(diagonal, format="csr") + transverse).tocsr()


def _magnetization_z_diagonal(sites: int) -> np.ndarray:
    states = np.arange(1 << sites, dtype=np.int64)
    magnetization = np.zeros(states.size, dtype=float)
    for site in range(sites):
        magnetization += 1.0 - 2.0 * ((states >> site) & 1)
    return magnetization / sites


def _magnetization_y(state: np.ndarray, sites: int) -> float:
    basis = np.arange(state.size, dtype=np.int64)
    value = 0.0j
    for site in range(sites):
        bits = (basis >> site) & 1
        coefficient = np.where(bits == 0, -1.0j, 1.0j)
        value += np.vdot(state, coefficient * state[basis ^ (1 << site)])
    return float((value / sites).real)


@lru_cache(maxsize=24)
def _symmetry_broken_ground_pair(
    sites: int, g: float, periodic: bool
) -> tuple[np.ndarray, np.ndarray, float]:
    hamiltonian = spin_hamiltonian(sites, g, periodic)
    dimension = hamiltonian.shape[0]
    v0 = np.linspace(1.0, 2.0, dimension)
    v0 /= np.linalg.norm(v0)
    _, vectors = eigsh(hamiltonian, k=2, which="SA", v0=v0, tol=1e-11)
    magnetization = _magnetization_z_diagonal(sites)
    projected = vectors.conj().T @ (magnetization[:, None] * vectors)
    _, rotation = np.linalg.eigh(projected)
    minus = vectors @ rotation[:, 0]
    plus = vectors @ rotation[:, -1]
    plus /= np.linalg.norm(plus)
    minus /= np.linalg.norm(minus)
    m0 = float(np.vdot(plus, magnetization * plus).real)
    return plus.astype(complex), minus.astype(complex), m0


def _evolve_states(
    initial: np.ndarray,
    hamiltonian: csr_matrix,
    times: np.ndarray,
) -> np.ndarray:
    time = np.asarray(times, dtype=float)
    if time.size == 1:
        return initial[None, :]
    if not np.allclose(np.diff(time), time[1] - time[0], rtol=1e-11, atol=1e-13):
        raise ValueError("finite-chain time grid must be uniform")
    return expm_multiply(
        -1.0j * hamiltonian,
        initial,
        start=float(time[0]),
        stop=float(time[-1]),
        num=time.size,
        endpoint=True,
        traceA=0.0,
    )


def magnetization_dynamics(
    sites: int,
    g0: float,
    g1: float,
    times: np.ndarray,
    periodic: bool = True,
) -> dict[str, np.ndarray | float]:
    initial, _, m0 = _symmetry_broken_ground_pair(sites, float(g0), periodic)
    hamiltonian = spin_hamiltonian(sites, g1, periodic)
    states = _evolve_states(initial, hamiltonian, np.asarray(times, dtype=float))
    mz_diagonal = _magnetization_z_diagonal(sites)
    mz = np.einsum("ti,i,ti->t", states.conj(), mz_diagonal, states).real
    my = np.array([_magnetization_y(state, sites) for state in states])
    norms = np.linalg.norm(states, axis=1)
    return {
        "magnetization_z": mz,
        "magnetization_y": my,
        "state_norm": norms,
        "initial_magnetization": m0,
    }


def _pfaffian(matrix: np.ndarray) -> complex:
    """Pfaffian of an even-dimensional antisymmetric matrix with pivoting."""

    values = np.asarray(matrix, dtype=complex).copy()
    if values.ndim != 2 or values.shape[0] != values.shape[1]:
        raise ValueError("pfaffian input must be square")
    size = values.shape[0]
    if size % 2:
        raise ValueError("pfaffian input dimension must be even")
    result = 1.0 + 0.0j
    for pivot_index in range(0, size - 1, 2):
        pivot_column = (
            pivot_index
            + 1
            + int(np.argmax(np.abs(values[pivot_index, pivot_index + 1 :])))
        )
        if abs(values[pivot_index, pivot_column]) < 1e-14:
            return 0.0j
        if pivot_column != pivot_index + 1:
            values[[pivot_index + 1, pivot_column], :] = values[
                [pivot_column, pivot_index + 1], :
            ]
            values[:, [pivot_index + 1, pivot_column]] = values[
                :, [pivot_column, pivot_index + 1]
            ]
            result *= -1.0
        pivot = values[pivot_index, pivot_index + 1]
        result *= pivot
        if pivot_index + 2 < size:
            left = values[pivot_index, pivot_index + 2 :].copy()
            right = values[pivot_index + 1, pivot_index + 2 :].copy()
            values[pivot_index + 2 :, pivot_index + 2 :] += (
                np.outer(right, left) - np.outer(left, right)
            ) / pivot
    return result


def _majorana_symbol(momentum: np.ndarray, g: float) -> tuple[np.ndarray, np.ndarray]:
    """Return the real-space Majorana generator symbol and its energy."""

    k = np.asarray(momentum, dtype=float)
    off_diagonal = g - np.exp(-1.0j * k)
    generator = np.zeros((k.size, 2, 2), dtype=complex)
    generator[:, 0, 1] = off_diagonal
    generator[:, 1, 0] = -off_diagonal.conj()
    energy = np.abs(off_diagonal)
    return generator, energy


def longitudinal_correlation_dynamics(
    sites: int,
    separation: int,
    g0: float,
    g1: float,
    times: np.ndarray,
) -> dict[str, np.ndarray | float]:
    """Evaluate longitudinal order with the paper's Majorana-Pfaffian method.

    The parity-even ground state is represented on an antiperiodic momentum
    grid.  Its two-by-two Majorana covariance symbol is evolved exactly, then
    ``<sigma_z(0) sigma_z(r)>`` is obtained from a Pfaffian.  No author code,
    author arrays, or source pixels enter this calculation.

    Both quantities relevant to the figure-label ambiguity are frozen: the
    spin-1/2 correlator ``|<S_z S_z>|`` and the cluster-decomposition order
    parameter ``sqrt(|<S_z S_z>|)``.
    """

    if sites < 8 or sites % 2:
        raise ValueError("Majorana ring needs an even site count of at least 8")
    if separation < 1 or 2 * separation >= sites:
        raise ValueError("separation must be positive and smaller than sites/2")
    time = np.asarray(times, dtype=float)
    momenta = 2.0 * np.pi * (np.arange(sites) + 0.5) / sites
    generator0, energy0 = _majorana_symbol(momenta, g0)
    generator1, energy1 = _majorana_symbol(momenta, g1)
    gamma0 = -generator0 / energy0[:, None, None]

    indices = np.asarray(
        [index for cell in range(separation) for index in (2 * cell + 1, 2 * cell + 2)],
        dtype=int,
    )
    cells = indices // 2
    components = indices % 2
    differences = cells[:, None] - cells[None, :]
    fourier_phase = np.exp(1.0j * momenta[:, None, None] * differences[None, :, :])
    fourier_phase /= sites

    sigma_correlations = np.empty(time.size, dtype=float)
    maximum_antisymmetry_error = 0.0
    maximum_imaginary_error = 0.0
    identity = np.eye(2, dtype=complex)[None, :, :]
    for time_index, value in enumerate(time):
        propagator = (
            np.cos(energy1 * value)[:, None, None] * identity
            + np.sin(energy1 * value)[:, None, None]
            * generator1
            / energy1[:, None, None]
        )
        gamma_k = propagator @ gamma0 @ np.swapaxes(propagator.conj(), 1, 2)
        selected = gamma_k[:, components[:, None], components[None, :]]
        covariance = np.sum(fourier_phase * selected, axis=0)
        maximum_antisymmetry_error = max(
            maximum_antisymmetry_error,
            float(np.max(np.abs(covariance + covariance.T))),
        )
        correlation = ((-1) ** separation) * _pfaffian(covariance)
        maximum_imaginary_error = max(
            maximum_imaginary_error, float(abs(correlation.imag))
        )
        sigma_correlations[time_index] = correlation.real

    spin_correlations = 0.25 * sigma_correlations
    return {
        "sigma_z_correlation": sigma_correlations,
        "spin_z_correlation": spin_correlations,
        "absolute_spin_z_correlation": np.abs(spin_correlations),
        "cluster_magnetization": 0.5 * np.sqrt(np.abs(sigma_correlations)),
        "maximum_antisymmetry_error": maximum_antisymmetry_error,
        "maximum_imaginary_error": maximum_imaginary_error,
    }


def postselected_magnetization(
    sites: int,
    g0: float,
    g1: float,
    times: np.ndarray,
    periodic: bool = True,
) -> dict[str, np.ndarray | float]:
    plus, minus, m0 = _symmetry_broken_ground_pair(sites, float(g0), periodic)
    hamiltonian = spin_hamiltonian(sites, g1, periodic)
    states = _evolve_states(plus, hamiltonian, np.asarray(times, dtype=float))
    overlaps_plus = np.abs(states @ plus.conj()) ** 2
    overlaps_minus = np.abs(states @ minus.conj()) ** 2
    denominator = np.clip(overlaps_plus + overlaps_minus, 1e-300, None)
    postselected = m0 * (overlaps_plus - overlaps_minus) / denominator
    mz_diagonal = _magnetization_z_diagonal(sites)
    ordinary = np.einsum("ti,i,ti->t", states.conj(), mz_diagonal, states).real
    return {
        "ordinary_magnetization": ordinary,
        "postselected_magnetization": postselected,
        "ground_sector_probability": denominator,
        "initial_magnetization": m0,
    }


def extreme_quench_loschmidt_rates(
    times: np.ndarray | float,
    g1: float,
) -> dict[str, np.ndarray]:
    """Exact symmetry-sector rates for the supplement's ``g0=0, g1>>1`` limit.

    The amplitudes are ``|cos(g1 t/2)|**N`` and
    ``|sin(g1 t/2)|**N``.  With the paper's own convention
    ``L_ab=exp(-N f_ab)``, the physical rates are therefore minus the
    logarithms.  Both the physical and literal printed signs are returned so
    that an independent reviewer can adjudicate the source discrepancy.
    """

    time = np.atleast_1d(np.asarray(times, dtype=float))
    cosine = np.clip(np.abs(np.cos(g1 * time / 2.0)), 1e-300, None)
    sine = np.clip(np.abs(np.sin(g1 * time / 2.0)), 1e-300, None)
    physical_diagonal = -np.log(cosine)
    physical_off_diagonal = -np.log(sine)
    return {
        "physical_diagonal_rate": physical_diagonal,
        "physical_off_diagonal_rate": physical_off_diagonal,
        "printed_diagonal_rate": np.log(cosine),
        "printed_off_diagonal_rate": np.log(sine),
        "dominant_physical_rate": np.minimum(physical_diagonal, physical_off_diagonal),
    }


def postselection_normalization_check(
    probabilities: np.ndarray,
    energies: np.ndarray,
    observable: np.ndarray,
    beta: float,
) -> dict[str, float]:
    """Compare normalized postselection with the literal unnormalized sum."""

    weights = np.asarray(probabilities, dtype=float)
    energy = np.asarray(energies, dtype=float)
    values = np.asarray(observable, dtype=float)
    if weights.shape != energy.shape or weights.shape != values.shape:
        raise ValueError("probabilities, energies and observable must align")
    if np.any(weights < 0.0) or not np.isclose(np.sum(weights), 1.0):
        raise ValueError("probabilities must be normalized and nonnegative")
    tilted = weights * np.exp(-beta * energy)
    partition = float(np.sum(tilted))
    literal = float(np.sum(tilted * values))
    normalized = literal / partition
    return {
        "partition": partition,
        "literal_unnormalized_expectation": literal,
        "normalized_expectation": normalized,
    }


def complex_time_postselection_check(
    probabilities: np.ndarray,
    work_values: np.ndarray,
    beta: float,
    time: float,
) -> dict[str, complex | float]:
    """Evaluate the supplement's normalized complex-time identity.

    For normalized ``P_beta``, its characteristic function equals
    ``G(t+i beta) / G(i beta)`` under the source's ``exp(+i W t)``
    convention.  Returning the literal unnormalized right-hand side makes the
    potentially missing normalization visible without changing the source.
    """

    weights = np.asarray(probabilities, dtype=float)
    work = np.asarray(work_values, dtype=float)
    if weights.shape != work.shape:
        raise ValueError("probabilities and work values must align")
    if np.any(weights < 0.0) or not np.isclose(np.sum(weights), 1.0):
        raise ValueError("probabilities must be normalized and nonnegative")
    tilted = weights * np.exp(-beta * work)
    partition = float(np.sum(tilted))
    normalized_characteristic = complex(
        np.sum(tilted * np.exp(1.0j * work * time)) / partition
    )
    complex_time_amplitude = complex(
        np.sum(weights * np.exp(1.0j * work * (time + 1.0j * beta)))
    )
    return {
        "partition": partition,
        "normalized_characteristic": normalized_characteristic,
        "literal_complex_time_amplitude": complex_time_amplitude,
        "corrected_complex_time_amplitude": complex_time_amplitude / partition,
    }
