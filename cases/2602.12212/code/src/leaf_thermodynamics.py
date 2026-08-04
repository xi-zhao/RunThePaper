"""Core numerical model for arXiv:2602.12212v3.

The central object is the minimum-variance ensemble associated with a
full-rank density matrix ``rho`` and a Hamiltonian ``H``.  Figure-specific
scripts configure this object; they do not reimplement its rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np
from scipy import sparse


Array = Any
PauliOps = Sequence[tuple[int, str]]


@dataclass(frozen=True)
class MinimumVarianceEnsemble:
    """The state carried by one minimum-variance leaf decomposition."""

    backend: str
    state_hamiltonian: Array
    energies: Array
    eigenvectors: Array
    populations: Array
    representatives_rho_basis: Array
    representatives: Array


def array_module(backend: str = "numpy") -> Any:
    if backend == "numpy":
        return np
    if backend == "cupy":
        try:
            import cupy as cp
        except ImportError as exc:  # pragma: no cover - exercised on A100 only
            raise RuntimeError("backend='cupy' requires CuPy") from exc
        return cp
    raise ValueError(f"unsupported backend: {backend}")


def to_numpy(value: Array) -> np.ndarray:
    """Move a NumPy/CuPy value to host memory without importing CuPy eagerly."""

    if isinstance(value, np.ndarray):
        return value
    if np.isscalar(value):
        return np.asarray(value)
    if hasattr(value, "get"):
        return value.get()
    return np.asarray(value)


def synchronize(backend: str) -> None:
    if backend == "cupy":  # pragma: no cover - exercised on A100 only
        array_module(backend).cuda.Stream.null.synchronize()


def thermal_weights(energies: Array, beta: float, *, backend: str = "numpy") -> Array:
    """Stable normalized weights proportional to exp(-beta * energy)."""

    xp = array_module(backend)
    log_weights = -float(beta) * xp.asarray(energies)
    log_weights = log_weights - xp.max(log_weights)
    weights = xp.exp(log_weights)
    return weights / xp.sum(weights)


def effective_state_hamiltonian(
    h_in_rho_basis: Array,
    *,
    rho_eigenvalues: Array | None = None,
    thermal_energies: Array | None = None,
    beta: float | None = None,
    backend: str = "numpy",
) -> Array:
    """Solve {H_rho,rho}/2=sqrt(rho) H sqrt(rho) in the rho eigenbasis.

    For a Gibbs state, the coefficient is evaluated as a hyperbolic secant.
    This cancels the partition function and is more stable than operating on
    very small density-matrix eigenvalues.
    """

    xp = array_module(backend)
    h_matrix = xp.asarray(h_in_rho_basis)
    if thermal_energies is not None:
        if beta is None:
            raise ValueError("beta is required with thermal_energies")
        levels = xp.asarray(thermal_energies)
        delta = levels[:, None] - levels[None, :]
        factor = 1.0 / xp.cosh(0.5 * float(beta) * delta)
    elif rho_eigenvalues is not None:
        eigenvalues = xp.asarray(rho_eigenvalues)
        denominator = eigenvalues[:, None] + eigenvalues[None, :]
        numerator = 2.0 * xp.sqrt(eigenvalues[:, None] * eigenvalues[None, :])
        safe_denominator = xp.where(denominator > 0.0, denominator, 1.0)
        factor = xp.where(denominator > 0.0, numerator / safe_denominator, 0.0)
    else:
        raise ValueError("provide rho_eigenvalues or thermal_energies")
    result = factor * h_matrix
    return 0.5 * (result + result.conj().T)


def minimum_variance_ensemble(
    rho_eigenvalues: Array,
    h_in_rho_basis: Array,
    *,
    rho_basis: Array | None = None,
    thermal_energies: Array | None = None,
    beta: float | None = None,
    backend: str = "numpy",
) -> MinimumVarianceEnsemble:
    """Construct the Yu minimum-variance pure-state decomposition."""

    xp = array_module(backend)
    eigenvalues = xp.asarray(rho_eigenvalues)
    if bool(to_numpy(xp.any(eigenvalues <= 0.0))):
        raise ValueError("rho must have strictly positive eigenvalues")
    if not np.isclose(float(to_numpy(xp.sum(eigenvalues))), 1.0, atol=1e-10):
        raise ValueError("rho eigenvalues must sum to one")

    state_hamiltonian = effective_state_hamiltonian(
        h_in_rho_basis,
        rho_eigenvalues=eigenvalues,
        thermal_energies=thermal_energies,
        beta=beta,
        backend=backend,
    )
    energies, eigenvectors = xp.linalg.eigh(state_hamiltonian)
    populations = xp.sum(
        eigenvalues[:, None] * xp.abs(eigenvectors) ** 2,
        axis=0,
    ).real
    representatives_rho_basis = (
        xp.sqrt(eigenvalues)[:, None]
        * eigenvectors
        / xp.sqrt(populations)[None, :]
    )
    if rho_basis is None:
        representatives = representatives_rho_basis
    else:
        representatives = xp.asarray(rho_basis) @ representatives_rho_basis
    return MinimumVarianceEnsemble(
        backend=backend,
        state_hamiltonian=state_hamiltonian,
        energies=energies,
        eigenvectors=eigenvectors,
        populations=populations,
        representatives_rho_basis=representatives_rho_basis,
        representatives=representatives,
    )


def qfi_spectral(
    rho_eigenvalues: Array,
    h_in_rho_basis: Array,
    *,
    backend: str = "numpy",
) -> float:
    """Evaluate the standard spectral QFI with respect to H."""

    xp = array_module(backend)
    eigenvalues = xp.asarray(rho_eigenvalues)
    h_matrix = xp.asarray(h_in_rho_basis)
    difference = eigenvalues[:, None] - eigenvalues[None, :]
    denominator = eigenvalues[:, None] + eigenvalues[None, :]
    safe_denominator = xp.where(denominator > 0.0, denominator, 1.0)
    coefficient = xp.where(
        denominator > 0.0,
        difference**2 / safe_denominator,
        0.0,
    )
    value = 2.0 * xp.sum(coefficient * xp.abs(h_matrix) ** 2)
    return float(to_numpy(value.real))


def ensemble_invariants(
    rho_eigenvalues: Array,
    h_in_rho_basis: Array,
    ensemble: MinimumVarianceEnsemble,
) -> dict[str, float]:
    """Return executable identities required before figure generation."""

    xp = array_module(ensemble.backend)
    eigenvalues = xp.asarray(rho_eigenvalues)
    h_matrix = xp.asarray(h_in_rho_basis)
    representatives = ensemble.representatives_rho_basis
    populations = ensemble.populations

    gram = representatives.conj().T @ representatives
    norms = xp.real(xp.diag(gram))
    reconstruction = (
        representatives * populations[None, :]
    ) @ representatives.conj().T
    target_rho = xp.diag(eigenvalues)
    h_representatives = h_matrix @ representatives
    energy_means = xp.sum(
        representatives.conj() * h_representatives,
        axis=0,
    ).real
    h2_means = xp.sum(xp.abs(h_representatives) ** 2, axis=0).real
    variances = xp.maximum(h2_means - energy_means**2, 0.0)
    average_variance = xp.sum(populations * variances)
    qfi = qfi_spectral(eigenvalues, h_matrix, backend=ensemble.backend)
    energy_errors = xp.abs(energy_means - ensemble.energies)
    active_population_threshold = 1e-14
    active = populations >= active_population_threshold
    active_energy_errors = energy_errors[active]
    if int(to_numpy(xp.sum(active))) == 0:
        active_energy_errors = energy_errors
    weighted_energy_rms_error = xp.sqrt(
        xp.sum(populations * energy_errors**2)
    )

    return {
        "population_sum_error": abs(float(to_numpy(xp.sum(populations))) - 1.0),
        "minimum_population": float(to_numpy(xp.min(populations))),
        "maximum_norm_error": float(to_numpy(xp.max(xp.abs(norms - 1.0)))),
        "reconstruction_fro_error": float(
            to_numpy(xp.linalg.norm(reconstruction - target_rho))
        ),
        "representative_energy_max_error": float(
            to_numpy(xp.max(active_energy_errors))
        ),
        "representative_energy_max_error_all": float(
            to_numpy(xp.max(energy_errors))
        ),
        "representative_energy_active_population_threshold": (
            active_population_threshold
        ),
        "representative_energy_population_weighted_rms_error": float(
            to_numpy(weighted_energy_rms_error)
        ),
        "qfi_spectral": qfi,
        "four_times_average_variance": 4.0 * float(to_numpy(average_variance)),
        "qfi_variance_absolute_error": abs(
            qfi - 4.0 * float(to_numpy(average_variance))
        ),
    }


def pauli_action_indices(length: int, ops: PauliOps) -> tuple[np.ndarray, np.ndarray]:
    """Return destination indices and phases for a computational-basis Pauli string."""

    dimension = 1 << length
    source = np.arange(dimension, dtype=np.int64)
    destination = source.copy()
    phase = np.ones(dimension, dtype=np.complex128)
    sites_seen: set[int] = set()
    for site, operator in ops:
        if site in sites_seen:
            raise ValueError(f"duplicate Pauli operator on site {site}")
        if not 0 <= site < length:
            raise ValueError(f"site {site} outside chain length {length}")
        sites_seen.add(site)
        bit = (source >> site) & 1
        name = operator.lower()
        if name == "x":
            destination ^= 1 << site
        elif name == "y":
            destination ^= 1 << site
            phase *= 1j * (1 - 2 * bit)
        elif name == "z":
            phase *= 1 - 2 * bit
        elif name != "i":
            raise ValueError(f"unknown Pauli operator: {operator}")
    return destination, phase


def pauli_string_matrix(length: int, ops: PauliOps) -> sparse.csr_matrix:
    destination, phase = pauli_action_indices(length, ops)
    source = np.arange(1 << length, dtype=np.int64)
    return sparse.coo_matrix(
        (phase, (destination, source)),
        shape=(1 << length, 1 << length),
        dtype=np.complex128,
    ).tocsr()


def spin_chain_hamiltonian(
    length: int,
    field: Sequence[float],
    dzyaloshinskii_moriya: float,
    *,
    boundary: str = "open",
) -> sparse.csr_matrix:
    """Construct Eq. (9)/(S1) as a sparse Hermitian matrix."""

    if length < 2:
        raise ValueError("length must be at least 2")
    if len(field) != 3:
        raise ValueError("field must contain hx, hy, hz")
    if boundary not in {"open", "periodic"}:
        raise ValueError("boundary must be 'open' or 'periodic'")

    terms: list[sparse.csr_matrix] = []
    hx, hy, hz = (float(component) for component in field)
    for site in range(length):
        if hx:
            terms.append(hx * pauli_string_matrix(length, [(site, "x")]))
        if hy:
            terms.append(hy * pauli_string_matrix(length, [(site, "y")]))
        if hz:
            terms.append(hz * pauli_string_matrix(length, [(site, "z")]))

    pairs = [(site, site + 1) for site in range(length - 1)]
    if boundary == "periodic":
        pairs.append((length - 1, 0))
    dm = float(dzyaloshinskii_moriya)
    for left, right in pairs:
        terms.append(pauli_string_matrix(length, [(left, "x"), (right, "x")]))
        if dm:
            terms.append(
                dm * pauli_string_matrix(length, [(left, "z"), (right, "y")])
            )
            terms.append(
                -dm * pauli_string_matrix(length, [(left, "y"), (right, "z")])
            )

    result = sum(terms[1:], terms[0]).tocsr()
    result.sum_duplicates()
    return result


def pauli_expectations(
    states: Array,
    length: int,
    ops: PauliOps,
    *,
    backend: str = "numpy",
) -> Array:
    """Columnwise expectation values of a Pauli string."""

    xp = array_module(backend)
    state_matrix = xp.asarray(states)
    destination, phase = pauli_action_indices(length, ops)
    destination_xp = xp.asarray(destination)
    phase_xp = xp.asarray(phase)
    values = xp.sum(
        state_matrix[destination_xp, :].conj()
        * phase_xp[:, None]
        * state_matrix,
        axis=0,
    )
    return xp.real_if_close(values)


def apply_pauli_string(
    states: Array,
    length: int,
    ops: PauliOps,
    *,
    backend: str = "numpy",
) -> Array:
    """Apply a Pauli string to one state vector or a matrix of state columns."""

    xp = array_module(backend)
    state_matrix = xp.asarray(states)
    was_vector = state_matrix.ndim == 1
    if was_vector:
        state_matrix = state_matrix[:, None]
    if state_matrix.ndim != 2 or state_matrix.shape[0] != 1 << length:
        raise ValueError("states must have shape (2**length,) or (2**length, n)")
    destination, phase = pauli_action_indices(length, ops)
    destination_xp = xp.asarray(destination)
    phase_xp = xp.asarray(phase)
    result = xp.empty_like(state_matrix)
    result[destination_xp, :] = phase_xp[:, None] * state_matrix
    return result[:, 0] if was_vector else result


def central_local_observables(length: int) -> list[tuple[str, PauliOps]]:
    """The 3 one-site and 9 nearest-neighbour Pauli observables in Figs. S1-S4."""

    left = length // 2 - 1 if length % 2 == 0 else length // 2
    right = left + 1
    labels: list[tuple[str, PauliOps]] = [
        (f"sigma_{axis}", [(left, axis)]) for axis in ("x", "y", "z")
    ]
    labels.extend(
        (
            f"sigma_{first}_sigma_{second}",
            [(left, first), (right, second)],
        )
        for first in ("x", "y", "z")
        for second in ("x", "y", "z")
    )
    return labels


def centred_shell_mean(values: np.ndarray, shell_width: int) -> np.ndarray:
    """Centred rolling mean with truncated edge windows."""

    data = np.asarray(values, dtype=float)
    if not 1 <= shell_width <= data.size:
        raise ValueError("shell_width must lie between 1 and len(values)")
    left_radius = (shell_width - 1) // 2
    right_radius = shell_width // 2
    cumulative = np.concatenate(([0.0], np.cumsum(data)))
    result = np.empty_like(data)
    for index in range(data.size):
        start = max(0, index - left_radius)
        stop = min(data.size, index + right_radius + 1)
        result[index] = (cumulative[stop] - cumulative[start]) / (stop - start)
    return result


def blocked_shell_mean(values: np.ndarray, shell_width: int) -> np.ndarray:
    """Non-overlapping consecutive-shell mean, including the final short shell."""

    data = np.asarray(values, dtype=float)
    if not 1 <= shell_width <= data.size:
        raise ValueError("shell_width must lie between 1 and len(values)")
    result = np.empty_like(data)
    for start in range(0, data.size, shell_width):
        stop = min(data.size, start + shell_width)
        result[start:stop] = np.mean(data[start:stop])
    return result


def typicality_curve(
    observable_values: Array,
    *,
    thresholds: Iterable[float],
    shell_width: int | None = None,
    shell_mode: str = "centred",
) -> dict[str, np.ndarray | int | str]:
    """Compute residuals, N_Delta, and log_d(N_Delta)."""

    values = np.real(to_numpy(observable_values)).astype(float, copy=False)
    dimension = values.size
    width = shell_width or max(1, int(round(np.sqrt(dimension))))
    if shell_mode == "centred":
        smooth = centred_shell_mean(values, width)
    elif shell_mode == "blocked":
        smooth = blocked_shell_mean(values, width)
    else:
        raise ValueError("shell_mode must be 'centred' or 'blocked'")

    residuals = np.abs(values - smooth)
    delta = np.asarray(list(thresholds), dtype=float)
    counts = np.asarray(
        [np.count_nonzero(residuals > threshold) for threshold in delta],
        dtype=np.int64,
    )
    log_counts = np.full(delta.shape, np.nan, dtype=float)
    positive = counts > 0
    log_counts[positive] = np.log(counts[positive]) / np.log(dimension)
    return {
        "dimension": dimension,
        "shell_width": width,
        "shell_mode": shell_mode,
        "smooth_values": smooth,
        "residuals": residuals,
        "thresholds": delta,
        "counts": counts,
        "log_d_counts": log_counts,
    }


def diagonal_entropy(amplitudes_in_energy_basis: Array, *, backend: str = "numpy") -> Array:
    """Columnwise Shannon entropy of energy-basis probabilities."""

    xp = array_module(backend)
    amplitudes = xp.asarray(amplitudes_in_energy_basis)
    probabilities = xp.abs(amplitudes) ** 2
    normalizers = xp.sum(probabilities, axis=0)
    probabilities = probabilities / normalizers[None, :]
    safe = xp.where(probabilities > 0.0, probabilities, 1.0)
    return -xp.sum(xp.where(probabilities > 0.0, probabilities * xp.log(safe), 0.0), axis=0)


def spin1_leaf_vertices(transverse_component: float) -> np.ndarray:
    """Exact (n1,n3,n8) vertices for a spin-1 leaf in the paper's subspace."""

    x = float(transverse_component)
    if not 0.0 <= x < 1.0:
        raise ValueError("transverse_component must lie in [0,1)")
    z = np.sqrt(1.0 - x * x)
    return np.asarray(
        [
            [x, z, 1.0 / np.sqrt(3.0)],
            [x, -z, 1.0 / np.sqrt(3.0)],
            [0.0, 0.0, -2.0 / np.sqrt(3.0)],
        ]
    )


def spin1_barycenter_entropy(transverse_component: float) -> float:
    """Von Neumann entropy of the equal-population barycenter of a leaf."""

    x = float(transverse_component)
    eigenvalues = np.asarray([(1.0 + x) / 3.0, (1.0 - x) / 3.0, 1.0 / 3.0])
    return float(-np.sum(eigenvalues * np.log(eigenvalues)))


def spin1_leaf_canonical_curve(
    transverse_component: float,
    betas: Iterable[float],
) -> np.ndarray:
    """Coordinates of the paper's leaf-canonical curve for one spin-1 leaf."""

    vertices = spin1_leaf_vertices(transverse_component)
    z = np.sqrt(1.0 - float(transverse_component) ** 2)
    representative_energies = np.asarray([1.5 + 0.5 * z, 1.5 - 0.5 * z, -3.0])
    rows: list[np.ndarray] = []
    for beta in betas:
        weights = thermal_weights(representative_energies, float(beta))
        rows.append(np.asarray(weights) @ vertices)
    return np.asarray(rows)
