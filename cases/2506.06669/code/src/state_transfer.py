"""Independent numerics for enhanced perfect/fractional state transfer.

The module contains no plotting and no source-figure access.  All Hamiltonians
are represented in the exact zero/single-excitation sector used by the paper.
Frequencies and couplings are angular frequencies in rad/ns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.sparse.linalg import expm_multiply
from scipy.special import erf


ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]
NoiseKind = Literal["even_frequency", "odd_frequency", "coupling"]
TransferKind = Literal["pst", "fst"]


def mhz_to_angular(value: ArrayLike) -> FloatArray:
    """Convert x/2pi in MHz to angular frequency in rad/ns."""

    return np.asarray(value, dtype=float) * (2.0 * np.pi * 1.0e-3)


def zigzag_parameters(n_sites: int, m: int, j_scale: float) -> tuple[FloatArray, FloatArray]:
    """Return paper Eqs. (8)-(9) for an odd-length chain."""

    if n_sites < 3 or n_sites % 2 == 0:
        raise ValueError("the published zig-zag construction used here requires odd n_sites >= 3")
    if m < 0 or int(m) != m:
        raise ValueError("m must be a non-negative integer")
    if j_scale <= 0:
        raise ValueError("j_scale must be positive")

    sites = np.arange(1, n_sites + 1, dtype=float)
    mu_odd = (sites.astype(int) % 2).astype(float)
    # Main Eq. (8) says mu_n=1 on odd n, but that parity conflicts with the
    # paper's spectrum, Fig. 1, the stated even-site suppression, and the
    # Supplement's Schur elimination.  The globally consistent onsite term is
    # high on even sites; Eq. (9)'s coupling coefficients remain unchanged.
    onsite = 2.0 * float(m) * j_scale * (1.0 - mu_odd)

    links = np.arange(1, n_sites, dtype=float)
    couplings = 0.5 * j_scale * np.sqrt(
        (links + 2.0 * float(m) * mu_odd[:-1])
        * (n_sites - links + 2.0 * float(m) * mu_odd[1:])
    )
    return onsite, couplings


def expected_zigzag_spectrum(n_sites: int, m: int, j_scale: float) -> FloatArray:
    """Spectrum implied by Eqs. (8)-(9), in ascending order.

    This is the spectrum printed in the paper.  It is recovered when the
    parity typo in Eq. (8) is corrected so that even sites carry 2mJ.
    """

    half = (n_sites - 1) // 2
    lower = np.arange(-half, 1, dtype=float)
    upper = np.arange(2 * m + 1, 2 * m + half + 1, dtype=float)
    return j_scale * np.concatenate([lower, upper])


def hamiltonian_from_parameters(onsite: ArrayLike, couplings: ArrayLike) -> FloatArray:
    """Build a real symmetric nearest-neighbour Hamiltonian."""

    onsite_array = np.asarray(onsite, dtype=float)
    coupling_array = np.asarray(couplings, dtype=float)
    if onsite_array.ndim != 1 or coupling_array.shape != (len(onsite_array) - 1,):
        raise ValueError("onsite must have length N and couplings length N-1")
    hamiltonian = np.diag(onsite_array)
    indices = np.arange(len(coupling_array))
    hamiltonian[indices, indices + 1] = coupling_array
    hamiltonian[indices + 1, indices] = coupling_array
    return hamiltonian


def zigzag_hamiltonian(n_sites: int, m: int, j_scale: float) -> FloatArray:
    onsite, couplings = zigzag_parameters(n_sites, m, j_scale)
    return hamiltonian_from_parameters(onsite, couplings)


def fst_parameters(
    n_sites: int,
    m: int,
    j_scale: float,
    theta: float = np.pi / 8.0,
) -> tuple[FloatArray, FloatArray]:
    """Apply the odd-N isospectral deformation in main Eq. (12)."""

    onsite, couplings = zigzag_parameters(n_sites, m, j_scale)
    couplings = couplings.copy()
    left = (n_sites - 1) // 2 - 1
    right = (n_sites + 1) // 2 - 1
    couplings[left] *= np.cos(theta) + np.sin(theta)
    couplings[right] *= np.cos(theta) - np.sin(theta)
    return onsite, couplings


def fst_hamiltonian(
    n_sites: int,
    m: int,
    j_scale: float,
    theta: float = np.pi / 8.0,
) -> FloatArray:
    onsite, couplings = fst_parameters(n_sites, m, j_scale, theta)
    return hamiltonian_from_parameters(onsite, couplings)


def fst_hamiltonian_2d(
    rows: int,
    columns: int,
    m: int,
    j_scale: float,
    theta: float = np.pi / 8.0,
) -> FloatArray:
    """Separable 2D construction described below main Fig. 4."""

    h_rows = fst_hamiltonian(rows, m, j_scale, theta)
    h_columns = fst_hamiltonian(columns, m, j_scale, theta)
    return np.kron(h_rows, np.eye(columns)) + np.kron(np.eye(rows), h_columns)


def embed_vacuum(single_excitation_hamiltonian: ArrayLike) -> ComplexArray:
    """Add a zero-energy vacuum to an excitation-preserving Hamiltonian."""

    single = np.asarray(single_excitation_hamiltonian, dtype=complex)
    if single.ndim != 2 or single.shape[0] != single.shape[1]:
        raise ValueError("single_excitation_hamiltonian must be square")
    full = np.zeros((single.shape[0] + 1, single.shape[1] + 1), dtype=complex)
    full[1:, 1:] = single
    return full


def three_site_populations(delta: ArrayLike, coupling: ArrayLike, time: ArrayLike) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Closed populations from Supplement Sec. 6 with NumPy broadcasting."""

    delta_array, coupling_array, time_array = np.broadcast_arrays(
        np.asarray(delta, dtype=float),
        np.asarray(coupling, dtype=float),
        np.asarray(time, dtype=float),
    )
    omega = np.sqrt(delta_array**2 + 8.0 * coupling_array**2)
    ratio = np.divide(delta_array, omega, out=np.zeros_like(omega), where=omega > 0.0)
    cos_omega = np.cos(0.5 * omega * time_array)
    sin_omega = np.sin(0.5 * omega * time_array)
    cos_delta = np.cos(0.5 * delta_array * time_array)
    sin_delta = np.sin(0.5 * delta_array * time_array)

    p1 = 0.25 * (cos_omega + cos_delta) ** 2 + 0.25 * (ratio * sin_omega + sin_delta) ** 2
    p2 = np.divide(
        4.0 * coupling_array**2,
        omega**2,
        out=np.zeros_like(omega),
        where=omega > 0.0,
    ) * sin_omega**2
    p3 = 0.25 * (cos_omega - cos_delta) ** 2 + 0.25 * (ratio * sin_omega - sin_delta) ** 2
    return p1, p2, p3


def unitary_amplitudes(
    hamiltonian: ArrayLike,
    times: ArrayLike,
    initial_site: int = 0,
) -> ComplexArray:
    """Return amplitudes with shape `(len(times), dimension)`."""

    hamiltonian_array = np.asarray(hamiltonian, dtype=float)
    times_array = np.atleast_1d(np.asarray(times, dtype=float))
    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian_array)
    coefficients = eigenvectors.conj().T[:, initial_site]
    phases = np.exp(-1j * np.outer(times_array, eigenvalues))
    return (phases * coefficients[None, :]) @ eigenvectors.T


def population_scan(
    onsite: ArrayLike,
    couplings: ArrayLike,
    varied_site: int,
    offsets: ArrayLike,
    times: ArrayLike,
    observed_site: int = -1,
) -> FloatArray:
    """Scan one onsite perturbation and return a time-by-offset population map."""

    onsite_array = np.asarray(onsite, dtype=float)
    coupling_array = np.asarray(couplings, dtype=float)
    offsets_array = np.asarray(offsets, dtype=float)
    times_array = np.asarray(times, dtype=float)
    result = np.empty((len(times_array), len(offsets_array)), dtype=float)
    for column, offset in enumerate(offsets_array):
        shifted = onsite_array.copy()
        shifted[varied_site] += offset
        amplitudes = unitary_amplitudes(
            hamiltonian_from_parameters(shifted, coupling_array),
            times_array,
        )
        result[:, column] = np.abs(amplitudes[:, observed_site]) ** 2
    return result


def collapse_operators(
    n_sites: int,
    *,
    t1_ns: float,
    t2_ns: float | None = None,
    tphi_ns: float | None = None,
) -> list[ComplexArray]:
    """Independent relaxation and pure-dephasing operators per site."""

    if tphi_ns is None:
        if t2_ns is None:
            raise ValueError("provide t2_ns or tphi_ns")
        inverse_tphi = 1.0 / t2_ns - 1.0 / (2.0 * t1_ns)
        if inverse_tphi <= 0.0:
            raise ValueError("T2 and T1 imply a non-positive pure-dephasing rate")
        tphi_ns = 1.0 / inverse_tphi
    dimension = n_sites + 1
    operators: list[ComplexArray] = []
    for site in range(1, dimension):
        relaxation = np.zeros((dimension, dimension), dtype=complex)
        relaxation[0, site] = np.sqrt(1.0 / t1_ns)
        operators.append(relaxation)
        dephasing = np.zeros((dimension, dimension), dtype=complex)
        dephasing[site, site] = np.sqrt(2.0 / tphi_ns)
        operators.append(dephasing)
    return operators


def liouvillian(hamiltonian: ArrayLike, operators: list[ComplexArray]) -> ComplexArray:
    """Dense Liouvillian using column-major vectorization."""

    hamiltonian_array = np.asarray(hamiltonian, dtype=complex)
    dimension = hamiltonian_array.shape[0]
    identity = np.eye(dimension, dtype=complex)
    generator = -1j * (
        np.kron(identity, hamiltonian_array)
        - np.kron(hamiltonian_array.T, identity)
    )
    for operator in operators:
        gram = operator.conj().T @ operator
        generator += (
            np.kron(operator.conj(), operator)
            - 0.5 * np.kron(identity, gram)
            - 0.5 * np.kron(gram.T, identity)
        )
    return generator


def lindblad_trajectory(
    single_excitation_hamiltonian: ArrayLike,
    times: ArrayLike,
    *,
    initial_site: int = 0,
    t1_ns: float,
    t2_ns: float | None = None,
    tphi_ns: float | None = None,
) -> ComplexArray:
    """Constant-H Lindblad trajectory for an evenly spaced time grid."""

    times_array = np.asarray(times, dtype=float)
    if times_array.ndim != 1 or len(times_array) < 2:
        raise ValueError("times must be a one-dimensional grid with at least two points")
    differences = np.diff(times_array)
    if np.max(np.abs(differences - differences[0])) > 1e-10:
        raise ValueError("lindblad_trajectory requires an evenly spaced time grid")
    if times_array[0] < 0.0:
        raise ValueError("times must be non-negative")

    single = np.asarray(single_excitation_hamiltonian, dtype=float)
    n_sites = single.shape[0]
    full = embed_vacuum(single)
    operators = collapse_operators(
        n_sites,
        t1_ns=t1_ns,
        t2_ns=t2_ns,
        tphi_ns=tphi_ns,
    )
    generator = liouvillian(full, operators)
    initial = np.zeros_like(full)
    initial[initial_site + 1, initial_site + 1] = 1.0
    vectors = expm_multiply(
        generator,
        initial.reshape(-1, order="F"),
        start=float(times_array[0]),
        stop=float(times_array[-1]),
        num=len(times_array),
        endpoint=True,
    )
    return np.stack(
        [vector.reshape(full.shape, order="F") for vector in vectors],
        axis=0,
    )


def flattop_gaussian(time: ArrayLike, tau_ns: float, sigma_ns: float) -> FloatArray:
    """Unit-height Gaussian-smoothed rectangular pulse of nominal width tau."""

    time_array = np.asarray(time, dtype=float)
    scale = np.sqrt(2.0) * sigma_ns
    return 0.5 * (erf(time_array / scale) - erf((time_array - tau_ns) / scale))


@dataclass(frozen=True)
class PulsedResult:
    density_matrix: ComplexArray
    nfev: int
    trace_error: float
    hermiticity_error: float


def pulsed_lindblad_final(
    single_excitation_hamiltonian: ArrayLike,
    tau_ns: float,
    *,
    sigma_ns: float,
    buffer_ns: float,
    initial_site: int = 0,
    t1_ns: float,
    t2_ns: float | None = None,
    tphi_ns: float | None = None,
    rtol: float = 1.0e-7,
    atol: float = 1.0e-9,
) -> PulsedResult:
    """Integrate QS009 with a shared effective Hamiltonian envelope."""

    single = np.asarray(single_excitation_hamiltonian, dtype=float)
    n_sites = single.shape[0]
    full = embed_vacuum(single)
    operators = collapse_operators(
        n_sites,
        t1_ns=t1_ns,
        t2_ns=t2_ns,
        tphi_ns=tphi_ns,
    )
    gram_operators = [(operator, operator.conj().T, operator.conj().T @ operator) for operator in operators]

    initial = np.zeros_like(full)
    initial[initial_site + 1, initial_site + 1] = 1.0

    def right_hand_side(time: float, vector: ComplexArray) -> ComplexArray:
        density = vector.reshape(full.shape)
        current_hamiltonian = float(flattop_gaussian(time, tau_ns, sigma_ns)) * full
        derivative = -1j * (current_hamiltonian @ density - density @ current_hamiltonian)
        for operator, adjoint, gram in gram_operators:
            derivative += operator @ density @ adjoint - 0.5 * (gram @ density + density @ gram)
        return derivative.reshape(-1)

    solution = solve_ivp(
        right_hand_side,
        (-buffer_ns, tau_ns + buffer_ns),
        initial.reshape(-1),
        method="DOP853",
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        raise RuntimeError(f"pulsed Lindblad integration failed: {solution.message}")
    density = solution.y[:, -1].reshape(full.shape)
    return PulsedResult(
        density_matrix=density,
        nfev=int(solution.nfev),
        trace_error=float(abs(np.trace(density) - 1.0)),
        hermiticity_error=float(np.max(np.abs(density - density.conj().T))),
    )


def reduced_endpoint_density(full_density: ArrayLike, n_sites: int) -> ComplexArray:
    """Trace a vacuum/single-excitation chain onto endpoint qubits.

    The returned basis is |00>, |01>, |10>, |11>, where the first logical
    qubit is site 1 and the second is site N.
    """

    density = np.asarray(full_density, dtype=complex)
    if density.shape != (n_sites + 1, n_sites + 1):
        raise ValueError("full_density shape does not match n_sites")
    reduced = np.zeros((4, 4), dtype=complex)
    middle_population = float(np.real(np.trace(density[2:n_sites, 2:n_sites]))) if n_sites > 2 else 0.0
    reduced[0, 0] = density[0, 0] + middle_population
    reduced[1, 1] = density[n_sites, n_sites]
    reduced[2, 2] = density[1, 1]
    reduced[1, 2] = density[n_sites, 1]
    reduced[2, 1] = density[1, n_sites]
    reduced[0, 1] = density[0, n_sites]
    reduced[1, 0] = density[n_sites, 0]
    reduced[0, 2] = density[0, 1]
    reduced[2, 0] = density[1, 0]
    return reduced


def reduced_selected_density(
    full_density: ArrayLike,
    n_sites: int,
    selected_sites: list[int],
) -> ComplexArray:
    """Trace a vacuum/single-excitation state onto selected one-based sites."""

    density = np.asarray(full_density, dtype=complex)
    if density.shape != (n_sites + 1, n_sites + 1):
        raise ValueError("full_density shape does not match n_sites")
    if not selected_sites or len(set(selected_sites)) != len(selected_sites):
        raise ValueError("selected_sites must be a non-empty unique list")
    if min(selected_sites) < 1 or max(selected_sites) > n_sites:
        raise ValueError("selected site lies outside the lattice")

    selected = set(selected_sites)
    dimension = 2 ** len(selected_sites)
    reduced = np.zeros((dimension, dimension), dtype=complex)
    unselected_population = sum(
        float(np.real(density[site, site]))
        for site in range(1, n_sites + 1)
        if site not in selected
    )
    reduced[0, 0] = density[0, 0] + unselected_population
    basis_indices = {
        site: 1 << (len(selected_sites) - position - 1)
        for position, site in enumerate(selected_sites)
    }
    for left_site, left_basis in basis_indices.items():
        reduced[0, left_basis] = density[0, left_site]
        reduced[left_basis, 0] = density[left_site, 0]
        for right_site, right_basis in basis_indices.items():
            reduced[left_basis, right_basis] = density[left_site, right_site]
    return reduced


def endpoint_target(n_sites: int, relative_phase: complex = 1.0) -> ComplexArray:
    target = np.zeros(n_sites + 1, dtype=complex)
    target[1] = 1.0 / np.sqrt(2.0)
    target[n_sites] = relative_phase / np.sqrt(2.0)
    return target


def four_corner_target(rows: int, columns: int) -> ComplexArray:
    target = np.zeros(rows * columns + 1, dtype=complex)
    corners = [0, columns - 1, (rows - 1) * columns, rows * columns - 1]
    target[np.asarray(corners) + 1] = 0.5
    return target


def state_fidelity(density: ArrayLike, target: ArrayLike) -> float:
    density_array = np.asarray(density, dtype=complex)
    target_array = np.asarray(target, dtype=complex)
    return float(np.real(np.vdot(target_array, density_array @ target_array)))


def transfer_process_fidelity(endpoint_amplitude: complex, ideal_phase: complex) -> float:
    """Entanglement/process fidelity of the induced transfer channel."""

    if abs(ideal_phase) == 0.0:
        raise ValueError("ideal_phase must be non-zero")
    relative = np.conj(ideal_phase / abs(ideal_phase)) * endpoint_amplitude
    return float(abs(1.0 + relative) ** 2 / 4.0)


def even_site_population(amplitudes: ArrayLike) -> FloatArray:
    """Population on paper-even sites Q2,Q4,... for amplitude rows."""

    amplitude_array = np.asarray(amplitudes, dtype=complex)
    return np.sum(np.abs(amplitude_array[..., 1::2]) ** 2, axis=-1)


def _perturbed_hamiltonian(
    onsite: FloatArray,
    couplings: FloatArray,
    noise_kind: NoiseKind,
    sigma: float,
    rng: np.random.Generator,
) -> FloatArray:
    noisy_onsite = onsite.copy()
    noisy_couplings = couplings.copy()
    if noise_kind == "even_frequency":
        noisy_onsite[1::2] += rng.normal(0.0, sigma, size=len(noisy_onsite[1::2]))
    elif noise_kind == "odd_frequency":
        noisy_onsite[0::2] += rng.normal(0.0, sigma, size=len(noisy_onsite[0::2]))
    elif noise_kind == "coupling":
        noisy_couplings += rng.normal(0.0, sigma, size=len(noisy_couplings))
    else:
        raise ValueError(f"unsupported noise kind: {noise_kind}")
    return hamiltonian_from_parameters(noisy_onsite, noisy_couplings)


def sample_parameter_noise(
    *,
    n_sites: int,
    m: int,
    j_scale: float,
    transfer_kind: TransferKind,
    noise_kind: NoiseKind,
    sigma: float,
    samples: int,
    rng: np.random.Generator,
    theta: float = np.pi / 8.0,
) -> FloatArray:
    """Return independent fidelity samples for Supplement Figs. S7-S8."""

    if samples <= 0:
        raise ValueError("samples must be positive")
    if transfer_kind == "pst":
        onsite, couplings = zigzag_parameters(n_sites, m, j_scale)
    elif transfer_kind == "fst":
        onsite, couplings = fst_parameters(n_sites, m, j_scale, theta)
    else:
        raise ValueError(f"unsupported transfer kind: {transfer_kind}")

    tau_ns = np.pi / j_scale
    baseline = unitary_amplitudes(
        hamiltonian_from_parameters(onsite, couplings),
        [tau_ns],
    )[0]
    ideal_transfer_phase = baseline[-1]
    fst_target = baseline / np.linalg.norm(baseline)
    fidelities = np.empty(samples, dtype=float)
    for sample in range(samples):
        hamiltonian = _perturbed_hamiltonian(onsite, couplings, noise_kind, sigma, rng)
        final_state = unitary_amplitudes(hamiltonian, [tau_ns])[0]
        if transfer_kind == "pst":
            fidelities[sample] = transfer_process_fidelity(final_state[-1], ideal_transfer_phase)
        else:
            fidelities[sample] = float(abs(np.vdot(fst_target, final_state)) ** 2)
    return fidelities


def direct_final_density(
    single_excitation_hamiltonian: ArrayLike,
    time_ns: float,
    *,
    initial_site: int = 0,
) -> ComplexArray:
    """Exact unitary density in the vacuum/single-excitation basis."""

    single = np.asarray(single_excitation_hamiltonian, dtype=float)
    full = embed_vacuum(single)
    unitary = expm(-1j * full * time_ns)
    initial = np.zeros(full.shape[0], dtype=complex)
    initial[initial_site + 1] = 1.0
    final = unitary @ initial
    return np.outer(final, final.conj())
