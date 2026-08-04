"""Derivation-backed exact-sector tools for the spin-1 Kitaev-AKLT chain."""

from __future__ import annotations

from functools import lru_cache
from itertools import product
from typing import Iterable

import numpy as np


X_LABEL = 0
Y_LABEL = 1
Z_LABEL = 2
LOCAL_DIMENSION = 3


def spin_one_operators() -> dict[str, np.ndarray]:
    """Return the paper's spin-1 matrices in the ordered m_z=(+1,0,-1) basis."""

    root_two = np.sqrt(2.0)
    sx = np.array(
        [[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]],
        dtype=np.complex128,
    ) / root_two
    sy = np.array(
        [[0.0, -1.0j, 0.0], [1.0j, 0.0, -1.0j], [0.0, 1.0j, 0.0]],
        dtype=np.complex128,
    ) / root_two
    sz = np.diag([1.0, 0.0, -1.0]).astype(np.complex128)
    return {"x": sx, "y": sy, "z": sz}


def cartesian_basis_transform() -> np.ndarray:
    """Columns are |S_x=0>, |S_y=0>, |S_z=0> in the paper's m_z basis."""

    return np.array(
        [
            [1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0],
            [0.0, 0.0, 1.0],
            [-1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0],
        ],
        dtype=np.complex128,
    )


def cartesian_spin_operators() -> dict[str, np.ndarray]:
    """Return spin matrices in the local Cartesian zero-state basis."""

    transform = cartesian_basis_transform()
    return {
        axis: transform.conj().T @ operator @ transform
        for axis, operator in spin_one_operators().items()
    }


def pi_rotation(axis: str, *, cartesian: bool = True) -> np.ndarray:
    """Return exp(i*pi*S_axis) using the exact spin-1 polynomial identity."""

    operators = cartesian_spin_operators() if cartesian else spin_one_operators()
    spin = operators[axis]
    return np.eye(LOCAL_DIMENSION, dtype=np.complex128) - 2.0 * (spin @ spin)


def bond_operator(axis: str, theta: float) -> np.ndarray:
    """Two-site bilinear-biquadratic bond matrix in the Cartesian basis."""

    spin = cartesian_spin_operators()[axis]
    bilinear = np.kron(spin, spin)
    return np.cos(theta) * bilinear + np.sin(theta) * (bilinear @ bilinear)


def maximal_component_projector(axis: str) -> np.ndarray:
    """Project onto S_i^axis+S_j^axis=+/-2."""

    spin = cartesian_spin_operators()[axis]
    total = np.kron(spin, np.eye(3)) + np.kron(np.eye(3), spin)
    total_squared = total @ total
    return (total_squared @ total_squared - total_squared) / 12.0


def projector_from_bond_product(axis: str) -> np.ndarray:
    """Equivalent polynomial (A+A^2)/2 with A=S_i^axis S_j^axis."""

    spin = cartesian_spin_operators()[axis]
    product_operator = np.kron(spin, spin)
    return 0.5 * (product_operator + product_operator @ product_operator)


def _rotation_eigenvalues(axis: str) -> np.ndarray:
    if axis == "x":
        return np.array([1, -1, -1], dtype=np.int8)
    if axis == "y":
        return np.array([-1, 1, -1], dtype=np.int8)
    raise ValueError(f"unsupported bond rotation axis: {axis}")


def bond_character(bond_index: int) -> str:
    """Even bonds are X interactions; odd bonds are Y interactions."""

    return "x" if bond_index % 2 == 0 else "y"


def conserved_rotation_axis(bond_index: int) -> str:
    """The conserved pi rotation is perpendicular to the bond interaction."""

    return "y" if bond_index % 2 == 0 else "x"


def configuration_sector(configuration: Iterable[int]) -> tuple[int, ...]:
    """Return the full w string of one Cartesian product configuration."""

    labels = tuple(int(value) for value in configuration)
    number_sites = len(labels)
    if number_sites % 2:
        raise ValueError("the periodic alternating chain requires even N")
    sector: list[int] = []
    for bond in range(number_sites):
        axis = conserved_rotation_axis(bond)
        signs = _rotation_eigenvalues(axis)
        sector.append(int(signs[labels[bond]] * signs[labels[(bond + 1) % number_sites]]))
    return tuple(sector)


def _all_configurations(number_sites: int) -> np.ndarray:
    number_states = LOCAL_DIMENSION**number_sites
    codes = np.arange(number_states, dtype=np.int64)
    configurations = np.empty((number_states, number_sites), dtype=np.int8)
    for site in range(number_sites):
        divisor = LOCAL_DIMENSION ** (number_sites - site - 1)
        configurations[:, site] = (codes // divisor) % LOCAL_DIMENSION
    return configurations


@lru_cache(maxsize=None)
def _sector_basis_cached(number_sites: int, sector: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    if number_sites % 2:
        raise ValueError("the periodic alternating chain requires even N")
    if len(sector) != number_sites or any(value not in (-1, 1) for value in sector):
        raise ValueError("sector must contain exactly N entries in {-1,+1}")

    configurations = _all_configurations(number_sites)
    mask = np.ones(configurations.shape[0], dtype=bool)
    for bond, requested_value in enumerate(sector):
        signs = _rotation_eigenvalues(conserved_rotation_axis(bond))
        actual = signs[configurations[:, bond]] * signs[
            configurations[:, (bond + 1) % number_sites]
        ]
        mask &= actual == requested_value
    return tuple(tuple(int(value) for value in row) for row in configurations[mask])


def sector_basis(number_sites: int, sector: Iterable[int]) -> np.ndarray:
    """Return Cartesian product configurations in the requested exact sector."""

    normalized_sector = tuple(int(value) for value in sector)
    return np.asarray(_sector_basis_cached(number_sites, normalized_sector), dtype=np.int8)


def all_sectors(number_sites: int) -> tuple[tuple[int, ...], ...]:
    return tuple(product((-1, 1), repeat=number_sites))


def _assemble_hamiltonian(configurations: np.ndarray, theta: float) -> np.ndarray:
    number_states, number_sites = configurations.shape
    state_to_index = {
        tuple(int(value) for value in configuration): index
        for index, configuration in enumerate(configurations)
    }
    matrix = np.zeros((number_states, number_states), dtype=np.complex128)
    local_operators = {
        "x": bond_operator("x", theta),
        "y": bond_operator("y", theta),
    }

    for column, configuration_array in enumerate(configurations):
        configuration = [int(value) for value in configuration_array]
        for bond in range(number_sites):
            next_site = (bond + 1) % number_sites
            local_input = 3 * configuration[bond] + configuration[next_site]
            local_operator = local_operators[bond_character(bond)]
            for local_output, amplitude in enumerate(local_operator[:, local_input]):
                if abs(amplitude) < 1e-14:
                    continue
                output_configuration = configuration.copy()
                output_configuration[bond] = local_output // 3
                output_configuration[next_site] = local_output % 3
                row = state_to_index.get(tuple(output_configuration))
                if row is None:
                    raise RuntimeError(
                        "Hamiltonian left the requested conserved sector; "
                        "check the W convention."
                    )
                matrix[row, column] += amplitude

    matrix = 0.5 * (matrix + matrix.conj().T)
    return np.real_if_close(matrix, tol=1000)


def sector_hamiltonian(
    number_sites: int,
    theta: float,
    sector: Iterable[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Return the exact Hamiltonian block and its ordered Cartesian basis."""

    normalized_sector = tuple(int(value) for value in sector)
    configurations = sector_basis(number_sites, normalized_sector)
    if configurations.size == 0:
        raise ValueError(f"empty conserved sector: {normalized_sector}")
    return _assemble_hamiltonian(configurations, theta), configurations


def full_hamiltonian(number_sites: int, theta: float) -> tuple[np.ndarray, np.ndarray]:
    """Return the full Cartesian-basis Hamiltonian for small-system validation."""

    if number_sites % 2:
        raise ValueError("the periodic alternating chain requires even N")
    configurations = _all_configurations(number_sites)
    return _assemble_hamiltonian(configurations, theta), configurations


def cluster_mps_matrices() -> dict[int, dict[int, np.ndarray]]:
    """Return A_w^chi with chi encoded as +1 (up) or -1 (down)."""

    root_two = np.sqrt(2.0)
    up_plus = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / root_two
    down_plus = np.array([[1.0, 1.0], [-1.0, 1.0]], dtype=np.complex128) / root_two
    return {
        1: {1: up_plus, -1: down_plus},
        -1: {1: down_plus, -1: up_plus},
    }


def physical_mps_tensors() -> dict[str, dict[int, tuple[np.ndarray, ...]]]:
    """Return C_(bond,w)^a tensors for Cartesian physical labels a=x,y,z."""

    root_two = np.sqrt(2.0)
    bond_matrices = {
        "x": {
            1: np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=np.complex128) / root_two,
            -1: np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128) / root_two,
        },
        "y": {
            1: np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=np.complex128) / root_two,
            -1: 1.0j * np.eye(2, dtype=np.complex128) / root_two,
        },
    }
    projections = (
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128),
        np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128) / root_two,
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128),
    )
    cluster = cluster_mps_matrices()
    transform = cartesian_basis_transform()
    tensors: dict[str, dict[int, tuple[np.ndarray, ...]]] = {"x": {}, "y": {}}

    for bond_axis in ("x", "y"):
        for w_value in (-1, 1):
            z_basis_tensors: list[np.ndarray] = []
            for projection in projections:
                tensor = np.zeros((4, 4), dtype=np.complex128)
                for chi in (1, -1):
                    tensor += np.kron(
                        projection @ bond_matrices[bond_axis][chi],
                        cluster[w_value][chi],
                    )
                z_basis_tensors.append(tensor)

            cartesian_tensors: list[np.ndarray] = []
            for cartesian_label in range(3):
                tensor = sum(
                    np.conjugate(transform[z_label, cartesian_label])
                    * z_basis_tensors[z_label]
                    for z_label in range(3)
                )
                cartesian_tensors.append(tensor)
            tensors[bond_axis][w_value] = tuple(cartesian_tensors)
    return tensors


def mps_amplitude(configuration: Iterable[int], sector: Iterable[int]) -> complex:
    labels = tuple(int(value) for value in configuration)
    normalized_sector = tuple(int(value) for value in sector)
    if len(labels) != len(normalized_sector):
        raise ValueError("configuration and sector lengths differ")
    tensors = physical_mps_tensors()
    product_matrix = np.eye(4, dtype=np.complex128)
    for site, physical_label in enumerate(labels):
        product_matrix = (
            product_matrix
            @ tensors[bond_character(site)][normalized_sector[site]][physical_label]
        )
    return complex(np.trace(product_matrix))


def mps_state_in_sector(
    number_sites: int,
    sector: Iterable[int],
    configurations: np.ndarray | None = None,
) -> np.ndarray:
    """Evaluate and normalize the physical MPS in an exact sector basis."""

    normalized_sector = tuple(int(value) for value in sector)
    basis = (
        sector_basis(number_sites, normalized_sector)
        if configurations is None
        else np.asarray(configurations, dtype=np.int8)
    )
    amplitudes = np.array(
        [mps_amplitude(configuration, normalized_sector) for configuration in basis],
        dtype=np.complex128,
    )
    norm = float(np.linalg.norm(amplitudes))
    if norm < 1e-14:
        raise RuntimeError(
            "physical MPS has zero norm in its requested sector; "
            "check the tensor/index convention."
        )
    return amplitudes / norm


def lowest_eigenspace(
    hamiltonian: np.ndarray,
    degeneracy_tolerance: float = 1e-10,
) -> tuple[float, np.ndarray, float]:
    """Return the lowest energy, an orthonormal lowest eigenspace, and residual."""

    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
    minimum = float(eigenvalues[0])
    multiplicity = int(np.count_nonzero(eigenvalues - minimum <= degeneracy_tolerance))
    subspace = eigenvectors[:, :multiplicity]
    residuals = [
        float(np.linalg.norm(hamiltonian @ subspace[:, index] - minimum * subspace[:, index]))
        for index in range(multiplicity)
    ]
    return minimum, subspace, max(residuals, default=0.0)


def state_overlap(state: np.ndarray, eigenspace: np.ndarray) -> float:
    """Norm of the projection of a normalized state onto an eigenspace."""

    normalized = np.asarray(state, dtype=np.complex128)
    normalized = normalized / np.linalg.norm(normalized)
    coefficients = eigenspace.conj().T @ normalized
    value = float(np.sqrt(np.sum(np.abs(coefficients) ** 2)))
    return min(1.0, max(0.0, value))


def overlap_in_sector(
    number_sites: int,
    theta: float,
    sector: Iterable[int],
) -> dict[str, float | int]:
    """Diagonalize one exact sector and overlap its minimum with the matching MPS."""

    normalized_sector = tuple(int(value) for value in sector)
    hamiltonian, configurations = sector_hamiltonian(number_sites, theta, normalized_sector)
    energy, eigenspace, residual = lowest_eigenspace(hamiltonian)
    mps = mps_state_in_sector(number_sites, normalized_sector, configurations)
    overlap_amplitude = state_overlap(mps, eigenspace)
    return {
        "energy": energy,
        "overlap_amplitude": overlap_amplitude,
        "fidelity": overlap_amplitude**2,
        "sector_dimension": int(len(configurations)),
        "lowest_multiplicity": int(eigenspace.shape[1]),
        "residual_norm": residual,
        "mps_energy": float(np.real(np.vdot(mps, hamiltonian @ mps))),
    }


def exact_point_zero_mode_count(
    number_sites: int,
    tolerance: float = 1e-10,
) -> dict[str, object]:
    """Count exact-point zero modes sector by sector for a small even chain."""

    theta = np.pi / 4.0
    total_zero_modes = 0
    sector_nullities: dict[str, int] = {}
    minimum_mps_energy = np.inf
    maximum_mps_energy = -np.inf
    for sector in all_sectors(number_sites):
        hamiltonian, configurations = sector_hamiltonian(number_sites, theta, sector)
        eigenvalues = np.linalg.eigvalsh(hamiltonian)
        nullity = int(np.count_nonzero(np.abs(eigenvalues) < tolerance))
        total_zero_modes += nullity
        key = "".join("+" if value == 1 else "-" for value in sector)
        sector_nullities[key] = nullity
        mps = mps_state_in_sector(number_sites, sector, configurations)
        mps_energy = float(np.real(np.vdot(mps, hamiltonian @ mps)))
        minimum_mps_energy = min(minimum_mps_energy, mps_energy)
        maximum_mps_energy = max(maximum_mps_energy, mps_energy)
    return {
        "number_sites": number_sites,
        "total_zero_modes": total_zero_modes,
        "expected_zero_modes": 2**number_sites + 1,
        "sector_nullities": sector_nullities,
        "minimum_mps_energy": minimum_mps_energy,
        "maximum_mps_energy": maximum_mps_energy,
    }


def product_configuration(number_sites: int, kind: str) -> tuple[int, ...]:
    """Return one of the paper's exact Cartesian product configurations."""

    if number_sites % 2:
        raise ValueError("the periodic alternating chain requires even N")
    if kind == "alternating_xy":
        return tuple(X_LABEL if site % 2 == 0 else Y_LABEL for site in range(number_sites))
    if kind == "alternating_yx":
        return tuple(Y_LABEL if site % 2 == 0 else X_LABEL for site in range(number_sites))
    if kind == "uniform_z":
        return (Z_LABEL,) * number_sites
    raise ValueError(f"unknown product-state kind: {kind}")


def product_state_diagnostics(number_sites: int, theta: float, kind: str) -> dict[str, float]:
    """Compute energy and eigenstate residual of a paper product state."""

    configuration = product_configuration(number_sites, kind)
    hamiltonian, configurations = full_hamiltonian(number_sites, theta)
    state_index = {
        tuple(int(value) for value in row): index
        for index, row in enumerate(configurations)
    }[configuration]
    vector = np.zeros(len(configurations), dtype=np.complex128)
    vector[state_index] = 1.0
    applied = hamiltonian @ vector
    energy = float(np.real(np.vdot(vector, applied)))
    residual = float(np.linalg.norm(applied - energy * vector))
    return {"energy": energy, "residual_norm": residual}
