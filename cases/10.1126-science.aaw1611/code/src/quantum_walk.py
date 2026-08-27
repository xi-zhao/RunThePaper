"""Exact Bose-Hubbard dynamics in a fixed-particle-number sector.

The domain object is an occupation basis with an invariant total particle
number.  Hamiltonian construction, evolution, and observables are kept here;
file formats and plotting live in the runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray


RealArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]
Basis = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class BackendResult:
    """Evolved states together with the backend provenance."""

    states: ComplexArray
    backend: str
    accelerator: str


@dataclass(frozen=True)
class LindbladResult:
    """Single-excitation density evolution including the vacuum state."""

    site_density: RealArray
    traces: RealArray
    density_matrices: ComplexArray


def mhz_to_rad_per_ns(values: Sequence[float] | RealArray) -> RealArray:
    """Convert f/(2*pi) in MHz to angular frequency in rad/ns."""

    return np.asarray(values, dtype=np.float64) * (2.0 * np.pi * 1.0e-3)


def occupation_basis(
    site_count: int,
    particle_count: int,
    max_occupation: int | None = None,
) -> Basis:
    """Enumerate occupation tuples satisfying the sector invariants."""

    if site_count <= 0 or particle_count < 0:
        raise ValueError("site_count must be positive and particle_count non-negative")
    cap = particle_count if max_occupation is None else max_occupation
    if cap < 0 or site_count * cap < particle_count:
        raise ValueError("occupation cap cannot hold the requested particles")

    states: list[tuple[int, ...]] = []

    def append_states(prefix: tuple[int, ...], sites_left: int, particles_left: int) -> None:
        if sites_left == 1:
            if particles_left <= cap:
                states.append(prefix + (particles_left,))
            return
        for occupation in range(min(cap, particles_left) + 1):
            append_states(prefix + (occupation,), sites_left - 1, particles_left - occupation)

    append_states((), site_count, particle_count)
    return tuple(states)


def basis_index(basis: Basis) -> dict[tuple[int, ...], int]:
    return {state: index for index, state in enumerate(basis)}


def fock_state(basis: Basis, occupied_sites: Iterable[int]) -> ComplexArray:
    """Return a normalized basis vector for zero-based occupied site indices."""

    occupations = [0] * len(basis[0])
    for site in occupied_sites:
        if site < 0 or site >= len(occupations):
            raise IndexError(f"site {site} outside the chain")
        occupations[site] += 1
    try:
        index = basis_index(basis)[tuple(occupations)]
    except KeyError as exc:
        raise ValueError("requested Fock state is outside the selected basis") from exc
    state = np.zeros(len(basis), dtype=np.complex128)
    state[index] = 1.0
    return state


def build_hamiltonian(
    basis: Basis,
    couplings: Sequence[float] | RealArray,
    interactions: Sequence[float] | RealArray | None = None,
    onsite: Sequence[float] | RealArray | None = None,
) -> RealArray:
    """Build the exact sector Hamiltonian from EQC001-EQC002."""

    site_count = len(basis[0])
    coupling_array = np.asarray(couplings, dtype=np.float64)
    if coupling_array.shape != (site_count - 1,):
        raise ValueError("couplings must contain one value per nearest-neighbor bond")
    interaction_array = (
        np.zeros(site_count, dtype=np.float64)
        if interactions is None
        else np.asarray(interactions, dtype=np.float64)
    )
    onsite_array = (
        np.zeros(site_count, dtype=np.float64)
        if onsite is None
        else np.asarray(onsite, dtype=np.float64)
    )
    if interaction_array.shape != (site_count,) or onsite_array.shape != (site_count,):
        raise ValueError("interactions and onsite must contain one value per site")

    state_to_index = basis_index(basis)
    hamiltonian = np.zeros((len(basis), len(basis)), dtype=np.float64)
    for column, state_tuple in enumerate(basis):
        state = np.asarray(state_tuple, dtype=np.int64)
        hamiltonian[column, column] = np.sum(
            0.5 * interaction_array * state * (state - 1) + onsite_array * state
        )
        for bond, coupling in enumerate(coupling_array):
            if state[bond] > 0:
                moved = state.copy()
                moved[bond] -= 1
                moved[bond + 1] += 1
                row = state_to_index.get(tuple(int(value) for value in moved))
                if row is not None:
                    amplitude = coupling * np.sqrt(state[bond] * (state[bond + 1] + 1))
                    hamiltonian[row, column] += amplitude
            if state[bond + 1] > 0:
                moved = state.copy()
                moved[bond + 1] -= 1
                moved[bond] += 1
                row = state_to_index.get(tuple(int(value) for value in moved))
                if row is not None:
                    amplitude = coupling * np.sqrt(state[bond + 1] * (state[bond] + 1))
                    hamiltonian[row, column] += amplitude
    return hamiltonian


def _cupy_module():
    try:
        import cupy as cp  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("CuPy backend requested but cupy is not installed") from exc
    if cp.cuda.runtime.getDeviceCount() < 1:
        raise RuntimeError("CuPy backend requested but no CUDA device is visible")
    return cp


def evolve_state(
    hamiltonian: RealArray,
    initial_state: ComplexArray,
    times_ns: Sequence[float] | RealArray,
    backend: str = "numpy",
) -> BackendResult:
    """Evaluate exp(-iHt)|psi0> by one Hermitian eigendecomposition."""

    selected = backend
    if backend == "auto":
        try:
            _cupy_module()
        except RuntimeError:
            selected = "numpy"
        else:
            selected = "cupy"
    times = np.asarray(times_ns, dtype=np.float64)
    if selected == "numpy":
        eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
        coefficients = eigenvectors.conj().T @ initial_state
        phases = np.exp(-1.0j * np.outer(times, eigenvalues))
        states = (phases * coefficients[None, :]) @ eigenvectors.T
        return BackendResult(np.asarray(states), "numpy", "CPU")
    if selected != "cupy":
        raise ValueError("backend must be numpy, cupy, or auto")

    cp = _cupy_module()
    h_gpu = cp.asarray(hamiltonian)
    psi_gpu = cp.asarray(initial_state)
    times_gpu = cp.asarray(times)
    eigenvalues, eigenvectors = cp.linalg.eigh(h_gpu)
    coefficients = eigenvectors.conj().T @ psi_gpu
    phases = cp.exp(-1.0j * times_gpu[:, None] * eigenvalues[None, :])
    states_gpu = (phases * coefficients[None, :]) @ eigenvectors.T
    cp.cuda.Stream.null.synchronize()
    accelerator = cp.cuda.runtime.getDeviceProperties(0)["name"]
    if isinstance(accelerator, bytes):
        accelerator = accelerator.decode("utf-8")
    return BackendResult(cp.asnumpy(states_gpu), "cupy", str(accelerator))


def state_norms(states: ComplexArray) -> RealArray:
    return np.sum(np.abs(states) ** 2, axis=1)


def site_density(states: ComplexArray, basis: Basis) -> RealArray:
    occupations = np.asarray(basis, dtype=np.float64)
    return np.abs(states) ** 2 @ occupations


def one_particle_entropy(density: RealArray) -> RealArray:
    clipped = np.clip(density, 0.0, 1.0)
    result = np.zeros_like(clipped)
    interior = (clipped > 0.0) & (clipped < 1.0)
    probabilities = clipped[interior]
    result[interior] = -probabilities * np.log(probabilities) - (1.0 - probabilities) * np.log1p(
        -probabilities
    )
    return result


def connected_z_correlation(density: RealArray) -> RealArray:
    """Connected sigma-z matrices for one-particle density rows."""

    result = -4.0 * density[:, :, None] * density[:, None, :]
    diagonal = 4.0 * density * (1.0 - density)
    indices = np.arange(density.shape[1])
    result[:, indices, indices] = diagonal
    return result


def one_particle_concurrence(states: ComplexArray) -> RealArray:
    amplitudes = np.abs(states)
    result = 2.0 * amplitudes[:, :, None] * amplitudes[:, None, :]
    indices = np.arange(states.shape[1])
    result[:, indices, indices] = 0.0
    return result


def two_particle_correlator(states: ComplexArray, basis: Basis) -> RealArray:
    occupations = np.asarray(basis, dtype=np.float64)
    basis_correlators = occupations[:, :, None] * occupations[:, None, :]
    indices = np.arange(occupations.shape[1])
    basis_correlators[:, indices, indices] = occupations * (occupations - 1.0)
    return np.tensordot(np.abs(states) ** 2, basis_correlators, axes=(1, 0))


def double_occupancy_probability(correlators: RealArray) -> RealArray:
    return np.diagonal(correlators, axis1=-2, axis2=-1) / 2.0


def normalized_correlation_distance(left: RealArray, right: RealArray) -> float:
    """Frobenius distance between normalized off-diagonal correlator patterns."""

    if left.shape != right.shape or left.ndim != 2:
        raise ValueError("correlators must be two matrices with identical shape")
    mask = ~np.eye(left.shape[0], dtype=bool)
    left_vector = left[mask]
    right_vector = right[mask]
    left_norm = np.linalg.norm(left_vector)
    right_norm = np.linalg.norm(right_vector)
    if left_norm == 0.0 or right_norm == 0.0:
        return float("inf")
    return float(np.linalg.norm(left_vector / left_norm - right_vector / right_norm))


def effective_couplings_from_detuning(
    couplings: Sequence[float] | RealArray,
    onsite_offsets: Sequence[float] | RealArray,
) -> RealArray:
    """Apply Supplement Sec. IV.C's detuning-renormalized hopping formula."""

    coupling_array = np.asarray(couplings, dtype=np.float64)
    onsite_array = np.asarray(onsite_offsets, dtype=np.float64)
    if coupling_array.ndim != 1 or onsite_array.shape != (coupling_array.size + 1,):
        raise ValueError("onsite offsets must contain one value per coupling endpoint")
    detuning = np.diff(onsite_array)
    return coupling_array**2 / np.sqrt(coupling_array**2 + detuning**2)


def distribution_fidelity(left: RealArray, right: RealArray) -> RealArray:
    """Bhattacharyya fidelity used in Supplement Fig. S11."""

    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if left_array.shape != right_array.shape or left_array.ndim < 1:
        raise ValueError("distributions must have identical non-scalar shapes")
    if np.any(left_array < -1.0e-12) or np.any(right_array < -1.0e-12):
        raise ValueError("distributions cannot contain negative probabilities")
    return np.sum(
        np.sqrt(np.clip(left_array, 0.0, None) * np.clip(right_array, 0.0, None)),
        axis=-1,
    )


def evolve_single_excitation_lindblad(
    hamiltonian: RealArray,
    initial_site: int,
    times_ns: Sequence[float] | RealArray,
    t1_us: Sequence[float] | RealArray,
    t2_star_us: Sequence[float] | RealArray,
) -> LindbladResult:
    """Evolve a vacuum-plus-one-excitation Lindblad master equation.

    Amplitude damping is fixed by ``T1``.  Projector dephasing is chosen so the
    vacuum-to-site coherence decays with the printed ``T2*``.  This convention
    is declared as a reconstruction because the supplement does not publish
    the exact QuTiP collapse operators used for Fig. S11.
    """

    from scipy.sparse import csc_matrix
    from scipy.sparse.linalg import expm_multiply

    hamiltonian_array = np.asarray(hamiltonian, dtype=np.float64)
    if hamiltonian_array.ndim != 2 or hamiltonian_array.shape[0] != hamiltonian_array.shape[1]:
        raise ValueError("hamiltonian must be square")
    site_count = hamiltonian_array.shape[0]
    if initial_site < 0 or initial_site >= site_count:
        raise IndexError("initial site outside the chain")
    t1_ns = np.asarray(t1_us, dtype=np.float64) * 1000.0
    t2_star_ns = np.asarray(t2_star_us, dtype=np.float64) * 1000.0
    if t1_ns.shape != (site_count,) or t2_star_ns.shape != (site_count,):
        raise ValueError("T1 and T2-star must contain one value per site")
    if np.any(t1_ns <= 0.0) or np.any(t2_star_ns <= 0.0):
        raise ValueError("decoherence times must be positive")
    times = np.asarray(times_ns, dtype=np.float64)
    if times.ndim != 1 or times.size == 0 or np.any(np.diff(times) < 0.0):
        raise ValueError("times must be a non-empty sorted one-dimensional array")
    if times.size > 2 and not np.allclose(np.diff(times), np.diff(times)[0], atol=1.0e-12):
        raise ValueError("Lindblad evolution currently requires a uniform time grid")

    dimension = site_count + 1
    full_hamiltonian = np.zeros((dimension, dimension), dtype=np.complex128)
    full_hamiltonian[1:, 1:] = hamiltonian_array
    identity = np.eye(dimension, dtype=np.complex128)
    liouvillian = -1.0j * (
        np.kron(identity, full_hamiltonian)
        - np.kron(full_hamiltonian.T, identity)
    )

    collapse_operators: list[ComplexArray] = []
    for site in range(site_count):
        gamma_1 = 1.0 / t1_ns[site]
        relaxation = np.zeros((dimension, dimension), dtype=np.complex128)
        relaxation[0, site + 1] = np.sqrt(gamma_1)
        collapse_operators.append(relaxation)

        gamma_projector = max(0.0, 2.0 / t2_star_ns[site] - gamma_1)
        if gamma_projector > 0.0:
            dephasing = np.zeros((dimension, dimension), dtype=np.complex128)
            dephasing[site + 1, site + 1] = np.sqrt(gamma_projector)
            collapse_operators.append(dephasing)

    for collapse in collapse_operators:
        number = collapse.conj().T @ collapse
        liouvillian += np.kron(collapse.conj(), collapse)
        liouvillian -= 0.5 * np.kron(identity, number)
        liouvillian -= 0.5 * np.kron(number.T, identity)

    initial_density = np.zeros((dimension, dimension), dtype=np.complex128)
    initial_density[initial_site + 1, initial_site + 1] = 1.0
    initial_vector = initial_density.reshape(-1, order="F")
    if times.size == 1:
        if times[0] == 0.0:
            evolved_vectors = initial_vector[None, :]
        else:
            evolved_vectors = expm_multiply(csc_matrix(liouvillian * times[0]), initial_vector)[
                None, :
            ]
    else:
        evolved_vectors = expm_multiply(
            csc_matrix(liouvillian),
            initial_vector,
            start=float(times[0]),
            stop=float(times[-1]),
            num=times.size,
            endpoint=True,
        )
    density_matrices = np.asarray(
        [vector.reshape((dimension, dimension), order="F") for vector in evolved_vectors]
    )
    traces = np.real(np.trace(density_matrices, axis1=1, axis2=2))
    densities = np.real(np.diagonal(density_matrices[:, 1:, 1:], axis1=1, axis2=2))
    return LindbladResult(densities, traces, density_matrices)


def spectral_group_velocity(couplings_rad_per_ns: Sequence[float] | RealArray) -> float:
    """Paper Eq. S29 group velocity from the calibrated open-chain spectrum.

    For an ``L``-site chain the supplement samples momenta at
    ``k_n = n*pi/(L+1)``. The finite-difference derivative is therefore the
    largest adjacent eigenfrequency gap divided by ``pi/(L+1)``. Frequencies
    are supplied in rad/ns and the result is returned in sites/microsecond.
    """

    couplings = np.asarray(couplings_rad_per_ns, dtype=np.float64)
    if couplings.ndim != 1 or couplings.size == 0:
        raise ValueError("couplings must be a non-empty one-dimensional array")
    site_count = couplings.size + 1
    hamiltonian = np.zeros((site_count, site_count), dtype=np.float64)
    indices = np.arange(couplings.size)
    hamiltonian[indices, indices + 1] = couplings
    hamiltonian[indices + 1, indices] = couplings
    eigenfrequencies = np.linalg.eigvalsh(hamiltonian)
    delta_k = np.pi / (site_count + 1)
    return float(np.max(np.abs(np.diff(eigenfrequencies))) / delta_k * 1000.0)
