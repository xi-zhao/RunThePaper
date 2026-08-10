"""Formula-derived continuum and tight-binding models from arXiv:1807.10676.

This module deliberately contains no file I/O and no reference-image access.  It
implements the Hamiltonians printed in the paper and supplement, together with
the numerical operations needed for band structures and Wilson loops.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Callable, Iterable

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import eigh
from scipy.sparse import block_diag, csr_matrix, lil_matrix
from scipy.sparse.linalg import eigsh


Array = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]

S0 = np.eye(2, dtype=complex)
SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def rotation(angle: float) -> Array:
    """Return a two-dimensional counter-clockwise rotation."""

    return np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=float,
    )


def polar_unitary(matrix: ComplexArray) -> ComplexArray:
    """Unitary factor of a small overlap matrix."""

    left, _, right = np.linalg.svd(matrix, full_matrices=False)
    return left @ right


@dataclass(frozen=True)
class Lattice:
    """Real and reciprocal lattices used by the paper's honeycomb models."""

    a1: tuple[float, float] = (1.0, 0.0)
    a2: tuple[float, float] = (-0.5, np.sqrt(3.0) / 2.0)

    @cached_property
    def real_vectors(self) -> Array:
        return np.array([self.a1, self.a2], dtype=float)

    @cached_property
    def reciprocal_vectors(self) -> Array:
        # Rows are a_i.  Columns of 2*pi*inv(A) are b_i, then transpose.
        return (2.0 * np.pi * np.linalg.inv(self.real_vectors)).T

    @cached_property
    def b1(self) -> Array:
        return self.reciprocal_vectors[0]

    @cached_property
    def b2(self) -> Array:
        return self.reciprocal_vectors[1]

    @cached_property
    def gamma(self) -> Array:
        return np.zeros(2, dtype=float)

    @cached_property
    def k(self) -> Array:
        return (self.b1 + self.b2) / 3.0

    @cached_property
    def m(self) -> Array:
        return self.b1 / 2.0

    @cached_property
    def delta(self) -> Array:
        # The third vector repairs the obvious repeated-delta_2 typo in the TeX.
        a1, a2 = self.real_vectors
        return np.array(
            [(a1 + 2.0 * a2) / 3.0, (-2.0 * a1 - a2) / 3.0, (a1 - a2) / 3.0]
        )

    @cached_property
    def second_neighbours(self) -> Array:
        a1, a2 = self.real_vectors
        return np.array([a1, a2, -a1 - a2])

    @cached_property
    def sublattices(self) -> Array:
        a1, a2 = self.real_vectors
        return np.array([(a1 + 2.0 * a2) / 3.0, (2.0 * a1 + a2) / 3.0])

    def embedding(self, reciprocal: Array, orbitals_per_site: int) -> ComplexArray:
        phases = np.exp(-1.0j * (self.sublattices @ reciprocal))
        return np.diag(np.tile(phases, orbitals_per_site)).astype(complex)


def band_path(
    points: Iterable[Array], points_per_segment: int
) -> tuple[Array, Array, list[int]]:
    """Piecewise-linear momentum path without duplicating internal vertices."""

    vertices = [np.asarray(point, dtype=float) for point in points]
    momenta: list[Array] = []
    distance: list[float] = []
    ticks = [0]
    travelled = 0.0
    for segment, (start, stop) in enumerate(zip(vertices[:-1], vertices[1:])):
        fractions = np.linspace(0.0, 1.0, points_per_segment, endpoint=True)
        if segment:
            fractions = fractions[1:]
        for fraction in fractions:
            momentum = start + fraction * (stop - start)
            if momenta:
                travelled += float(np.linalg.norm(momentum - momenta[-1]))
            momenta.append(momentum)
            distance.append(travelled)
        ticks.append(len(momenta) - 1)
    return np.asarray(momenta), np.asarray(distance), ticks


@dataclass
class ContinuumModel:
    """One-valley Moire band model, Supplement Eq. (M-model-1)."""

    cutoff: int
    basis_shape: str = "hex"

    def __post_init__(self) -> None:
        root3 = np.sqrt(3.0)
        self.q = np.array(
            [[0.0, -1.0], [root3 / 2.0, 0.5], [-root3 / 2.0, 0.5]],
            dtype=float,
        )
        self.b1 = self.q[0] - self.q[2]
        self.b2 = self.q[1] - self.q[2]
        self.k_absolute = (self.b1 + self.b2) / 3.0
        # The plane-wave origin is one black honeycomb vertex (a Moire K).
        # The centre of the adjacent hexagon is Gamma, and q1/2 is its edge M.
        self.gamma = self.k_absolute
        self.k_point = np.zeros(2, dtype=float)
        self.m_point = self.q[0] / 2.0
        self.k_end = self.q[0].copy()
        if self.basis_shape not in {"hex", "periodic_rectangle"}:
            raise ValueError(f"unsupported basis shape: {self.basis_shape}")
        coords = [
            (m, n)
            for m in range(-self.cutoff, self.cutoff + 1)
            for n in range(-self.cutoff, self.cutoff + 1)
            if self.basis_shape == "periodic_rectangle"
            or max(abs(m), abs(n), abs(m + n)) <= self.cutoff
        ]
        self.coords = tuple(sorted(coords))
        self.coord_index = {coord: index for index, coord in enumerate(self.coords)}
        self.g_vectors = np.array(
            [m * self.b1 + n * self.b2 for m, n in self.coords], dtype=float
        )
        self.q_vectors = np.stack([self.g_vectors, self.q[0] + self.g_vectors])
        self.t_matrices = (
            S0 + SX,
            S0 - 0.5 * SX + np.sqrt(3.0) * 0.5 * SY,
            S0 - 0.5 * SX - np.sqrt(3.0) * 0.5 * SY,
        )
        self._couplings = self._build_couplings()
        self._sparse_coupling_unit = self._build_sparse_coupling()

    @property
    def n_g(self) -> int:
        return len(self.coords)

    @property
    def dimension(self) -> int:
        return 4 * self.n_g

    @property
    def middle(self) -> int:
        return self.dimension // 2

    def _slice(self, layer: int, g_index: int) -> slice:
        start = 2 * (layer * self.n_g + g_index)
        return slice(start, start + 2)

    def _build_couplings(self) -> tuple[tuple[int, int, int], ...]:
        edges: list[tuple[int, int, int]] = []
        # Q_bottom - Q_top = q_j for these integer-coordinate offsets.
        offsets = ((0, 0), (-1, 1), (-1, 0))
        for top_index, (m, n) in enumerate(self.coords):
            for matrix_index, (dm, dn) in enumerate(offsets):
                candidate = (m + dm, n + dn)
                if self.basis_shape == "periodic_rectangle":
                    width = 2 * self.cutoff + 1
                    candidate = (
                        (candidate[0] + self.cutoff) % width - self.cutoff,
                        (candidate[1] + self.cutoff) % width - self.cutoff,
                    )
                bottom_index = self.coord_index.get(candidate)
                if bottom_index is not None:
                    edges.append((top_index, bottom_index, matrix_index))
        return tuple(edges)

    def _build_sparse_coupling(self) -> csr_matrix:
        matrix = lil_matrix((self.dimension, self.dimension), dtype=complex)
        for top_index, bottom_index, matrix_index in self._couplings:
            top = self._slice(0, top_index)
            bottom = self._slice(1, bottom_index)
            block = self.t_matrices[matrix_index]
            matrix[top, bottom] = block
            matrix[bottom, top] = block.conj().T
        return matrix.tocsr()

    def sparse_hamiltonian(self, momentum: Array, alpha: float) -> csr_matrix:
        """Sparse PH-symmetric Hamiltonian for large reciprocal cutoffs."""

        momentum = np.asarray(momentum, dtype=float)
        blocks = []
        for layer in range(2):
            for q_vector in self.q_vectors[layer]:
                delta = momentum - q_vector
                blocks.append(delta[0] * SX + delta[1] * SY)
        diagonal = block_diag(blocks, format="csr")
        return diagonal + float(alpha) * self._sparse_coupling_unit

    def hamiltonian(
        self,
        momentum: Array,
        alpha: float,
        *,
        ph_breaking: dict[str, float] | None = None,
    ) -> ComplexArray:
        momentum = np.asarray(momentum, dtype=float)
        matrix = np.zeros((self.dimension, self.dimension), dtype=complex)
        if ph_breaking is None:
            for layer in range(2):
                for g_index, q_vector in enumerate(self.q_vectors[layer]):
                    delta = momentum - q_vector
                    block = delta[0] * SX + delta[1] * SY
                    matrix[self._slice(layer, g_index), self._slice(layer, g_index)] = block
            coupling = float(alpha)
        else:
            t = float(ph_breaking["t_ev"])
            t_prime = float(ph_breaking["t_prime_ev"])
            theta = float(ph_breaking["theta_rad"])
            w = float(ph_breaking["w_ev"])
            kd_a = 8.0 * np.pi / (3.0 * np.sqrt(3.0)) * np.sin(theta / 2.0)
            for layer in range(2):
                for g_index, q_vector in enumerate(self.q_vectors[layer]):
                    delta = (momentum - q_vector) * kd_a
                    if layer == 1:
                        delta = rotation(-theta) @ delta
                    qx, qy = delta
                    block = (
                        1.5 * t * (qx * SX + qy * SY)
                        + 0.375
                        * t
                        * ((qx * qx - qy * qy) * SX - 2.0 * qx * qy * SY)
                        + 2.25 * t_prime * (qx * qx + qy * qy) * S0
                    )
                    matrix[self._slice(layer, g_index), self._slice(layer, g_index)] = block
            coupling = w
        for top_index, bottom_index, matrix_index in self._couplings:
            top = self._slice(0, top_index)
            bottom = self._slice(1, bottom_index)
            block = coupling * self.t_matrices[matrix_index]
            matrix[top, bottom] = block
            matrix[bottom, top] = block.conj().T
        return matrix

    def central_eigenvalues(
        self,
        momentum: Array,
        alpha: float,
        count_each_side: int = 4,
        *,
        ph_breaking: dict[str, float] | None = None,
    ) -> Array:
        if ph_breaking is None and self.cutoff >= 6:
            values = eigsh(
                self.sparse_hamiltonian(momentum, alpha),
                k=2 * count_each_side,
                sigma=1.0e-9,
                which="LM",
                return_eigenvectors=False,
                tol=2.0e-10,
            )
            return np.sort(np.asarray(values, dtype=float))
        lower = self.middle - count_each_side
        upper = self.middle + count_each_side - 1
        values = eigh(
            self.hamiltonian(momentum, alpha, ph_breaking=ph_breaking),
            eigvals_only=True,
            subset_by_index=[lower, upper],
            check_finite=False,
            driver="evr",
        )
        return np.asarray(values, dtype=float)

    def middle_states(self, momentum: Array, alpha: float) -> ComplexArray:
        if self.cutoff >= 6:
            values, vectors = eigsh(
                self.sparse_hamiltonian(momentum, alpha),
                # Request a safety window.  With only four Ritz pairs, the
                # nearly degenerate +2/-2 levels at the C/D phases can swap
                # into the returned subspace and create false Wilson spikes.
                k=8,
                sigma=1.0e-9,
                which="LM",
                return_eigenvectors=True,
                tol=5.0e-12,
            )
            order = np.argsort(values)
            vectors = vectors[:, order]
            return np.asarray(vectors[:, 3:5], dtype=complex)
        _, vectors = eigh(
            self.hamiltonian(momentum, alpha),
            subset_by_index=[self.middle - 1, self.middle],
            check_finite=False,
            driver="evr",
        )
        return np.asarray(vectors, dtype=complex)

    def band_structure(
        self, momenta: Array, alpha: float, count_each_side: int = 4
    ) -> Array:
        return np.asarray(
            [self.central_eigenvalues(k, alpha, count_each_side) for k in momenta]
        )

    def fermi_velocity(self, alpha: float, step: float = 1.0e-3) -> float:
        direction = np.array([1.0, 0.0])
        plus = self.central_eigenvalues(step * direction, alpha, 2)
        minus = self.central_eigenvalues(-step * direction, alpha, 2)
        # The PH-symmetric Dirac splitting is 2*v*|dk|.  Average opposite sides.
        split = 0.5 * ((plus[2] - plus[1]) + (minus[2] - minus[1]))
        return float(abs(split) / (2.0 * step))

    def isolation_gap(self, momentum: Array, alpha: float) -> float:
        values = self.central_eigenvalues(momentum, alpha, 3)
        lower_gap = values[2] - values[1]
        upper_gap = values[4] - values[3]
        return float(min(lower_gap, upper_gap))

    def central_gap(self, momentum: Array, alpha: float) -> float:
        values = self.central_eigenvalues(momentum, alpha, 2)
        return float(values[2] - values[1])

    def embedding_b2(self) -> ComplexArray:
        embedding = np.zeros((self.dimension, self.dimension), dtype=complex)
        for layer in range(2):
            for row_index, (m, n) in enumerate(self.coords):
                source_coord = (m, n - 1)
                if self.basis_shape == "periodic_rectangle":
                    width = 2 * self.cutoff + 1
                    source_coord = (
                        m,
                        (source_coord[1] + self.cutoff) % width - self.cutoff,
                    )
                source_index = self.coord_index.get(source_coord)
                if source_index is None:
                    continue
                row = self._slice(layer, row_index)
                source = self._slice(layer, source_index)
                embedding[row, source] = S0
        return embedding

    def wilson_spectrum(
        self, alpha: float, u_values: Array, loop_points: int
    ) -> Array:
        embedding = self.embedding_b2()
        spectra = []
        symmetry_cache: dict[float, Array] = {}
        for u in np.asarray(u_values, dtype=float):
            # C2x makes the spectrum symmetric under k1 -> 2*pi-k1.
            # Evaluating only the first half also avoids finite-cutoff edge
            # leakage close to the translated u=1 plane-wave boundary.
            u_evaluated = float(min(u % 1.0, 1.0 - (u % 1.0)))
            cache_key = round(u_evaluated, 12)
            if cache_key in symmetry_cache:
                spectra.append(symmetry_cache[cache_key].copy())
                continue
            states = []
            for v in np.linspace(0.0, 1.0, loop_points, endpoint=False):
                momentum = self.gamma + u_evaluated * self.b1 + v * self.b2
                states.append(self.middle_states(momentum, alpha))
            wilson = np.eye(2, dtype=complex)
            for left, right in zip(states[:-1], states[1:]):
                wilson = wilson @ polar_unitary(left.conj().T @ right)
            wilson = wilson @ polar_unitary(states[-1].conj().T @ embedding @ states[0])
            # C2zT constrains the two eigenphases to a +/- pair.  Remove the
            # tiny finite-cutoff determinant phase before diagonalization.
            determinant_phase = np.angle(np.linalg.det(wilson))
            wilson = np.exp(-0.5j * determinant_phase) * wilson
            eigenphases = np.sort(np.angle(np.linalg.eigvals(wilson)))
            symmetry_cache[cache_key] = eigenphases
            spectra.append(eigenphases)
        return np.asarray(spectra, dtype=float)


class TB4OneValley:
    """Four-band one-valley model printed in the supplement."""

    def __init__(
        self,
        t: float = 1.0,
        t_prime: float = -1.0 / 3.0,
        lambda_: float = 2.0 / np.sqrt(27.0),
        delta: float = 0.15,
    ) -> None:
        self.t = float(t)
        self.t_prime = float(t_prime)
        self.lambda_ = float(lambda_)
        self.delta_energy = float(delta)
        self.lattice = Lattice()

    def hamiltonian(self, momentum: Array) -> ComplexArray:
        k = np.asarray(momentum, dtype=float)
        delta_phase = self.lattice.delta @ k
        d_phase = self.lattice.second_neighbours @ k
        real_hop = np.sum(
            self.t * np.cos(delta_phase) + self.t_prime * np.cos(-2.0 * delta_phase)
        )
        imag_hop = np.sum(
            self.t * np.sin(delta_phase) + self.t_prime * np.sin(-2.0 * delta_phase)
        )
        lambda_hop = np.sum(np.sin(d_phase))
        return (
            self.delta_energy * np.kron(SZ, S0)
            + real_hop * np.kron(S0, SX)
            - imag_hop * np.kron(S0, SY)
            - 2.0 * self.lambda_ * lambda_hop * np.kron(SY, SZ)
        )

    def eigensystem(self, momentum: Array) -> tuple[Array, ComplexArray]:
        values, vectors = np.linalg.eigh(self.hamiltonian(momentum))
        return np.asarray(values, dtype=float), np.asarray(vectors, dtype=complex)

    def embedding_b2(self) -> ComplexArray:
        return self.lattice.embedding(self.lattice.b2, orbitals_per_site=2)


class TB8TwoValley:
    """Time-reversal pair of TB4-1V with the printed intervalley term."""

    def __init__(
        self,
        zeta: float = 0.2,
        *,
        t: float = 1.0,
        t_prime: float = -1.0 / 3.0,
        lambda_: float = 2.0 / np.sqrt(27.0),
        delta: float = 0.15,
    ) -> None:
        self.single = TB4OneValley(
            t=t,
            t_prime=t_prime,
            lambda_=lambda_,
            delta=delta,
        )
        self.zeta = float(zeta)
        self.lattice = self.single.lattice

    def hamiltonian(self, momentum: Array) -> ComplexArray:
        k = np.asarray(momentum, dtype=float)
        positive = self.single.hamiltonian(k)
        negative = self.single.hamiltonian(-k).conj()
        block = np.zeros((8, 8), dtype=complex)
        block[:4, :4] = positive
        block[4:, 4:] = negative
        valley_term = self.zeta * np.kron(SY, np.kron(SZ, SZ))
        return block + valley_term

    def eigensystem(self, momentum: Array) -> tuple[Array, ComplexArray]:
        values, vectors = np.linalg.eigh(self.hamiltonian(momentum))
        return np.asarray(values, dtype=float), np.asarray(vectors, dtype=complex)

    def embedding_b2(self) -> ComplexArray:
        return np.kron(S0, self.single.embedding_b2())


class TB4TwoValley:
    """Truncated two-valley four-band model, Supplement Eq. (TB4-2V)."""

    def __init__(
        self,
        delta_minus: float = 0.1174,
        t_minus: float = 0.011,
        t_prime_minus: float = -0.011,
        lambda_1: float = 0.01842,
        lambda_2: float = 0.00509,
    ) -> None:
        self.lattice = Lattice()
        self.delta_minus = float(delta_minus)
        self.t_minus = float(t_minus)
        self.t_prime_minus = float(t_prime_minus)
        self.t_second_minus = (
            self.delta_minus - 3.0 * self.t_minus + 6.0 * self.t_prime_minus
        ) / 3.0
        self.lambda_1 = float(lambda_1)
        self.lambda_2 = float(lambda_2)

    def hamiltonian(self, momentum: Array) -> ComplexArray:
        k = np.asarray(momentum, dtype=float)
        d = self.lattice.second_neighbours
        delta = self.lattice.delta
        upsilon = (
            self.delta_minus
            + 2.0 * self.t_minus * np.sum(np.cos(d @ k))
            + 2.0 * self.t_prime_minus * np.sum(np.cos(3.0 * (delta @ k)))
            + 2.0 * self.t_second_minus * np.sum(np.cos(2.0 * (d @ k)))
        )
        d_next = np.roll(delta, -1, axis=0)
        big_d = 2.0 * d + d_next
        big_d_prime = 2.0 * d + delta
        c2x = np.array([[1.0, 0.0], [0.0, -1.0]])
        reflected = big_d @ c2x.T
        reflected_prime = big_d_prime @ c2x.T
        lambda_k = -self.lambda_1 * np.sum(
            np.exp(1.0j * (big_d @ k)) - np.exp(1.0j * (reflected @ k))
        ) + self.lambda_2 * np.sum(
            np.exp(1.0j * (big_d_prime @ k))
            - np.exp(1.0j * (reflected_prime @ k))
        )
        return (
            upsilon * np.kron(SZ, S0)
            + np.real(lambda_k) * np.kron(SX, SX)
            - np.imag(lambda_k) * np.kron(SX, SY)
        )

    def eigensystem(self, momentum: Array) -> tuple[Array, ComplexArray]:
        values, vectors = np.linalg.eigh(self.hamiltonian(momentum))
        return np.asarray(values, dtype=float), np.asarray(vectors, dtype=complex)

    def embedding_b2(self) -> ComplexArray:
        return self.lattice.embedding(self.lattice.b2, orbitals_per_site=2)


def wilson_spectrum(
    eigensystem: Callable[[Array], tuple[Array, ComplexArray]],
    embedding: ComplexArray,
    reciprocal_1: Array,
    reciprocal_2: Array,
    occupied: int,
    u_values: Array,
    loop_points: int,
) -> Array:
    """Wilson-loop eigenphases for a finite tight-binding Hamiltonian."""

    result = []
    for u in np.asarray(u_values, dtype=float):
        states = []
        for v in np.linspace(0.0, 1.0, loop_points, endpoint=False):
            _, vectors = eigensystem(u * reciprocal_1 + v * reciprocal_2)
            states.append(vectors[:, :occupied])
        wilson = np.eye(occupied, dtype=complex)
        for left, right in zip(states[:-1], states[1:]):
            wilson = wilson @ polar_unitary(left.conj().T @ right)
        wilson = wilson @ polar_unitary(states[-1].conj().T @ embedding @ states[0])
        result.append(np.sort(np.angle(np.linalg.eigvals(wilson))))
    return np.asarray(result, dtype=float)
