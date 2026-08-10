"""Continuum models derived from the paper, without author code or figure data.

The implementation follows main-text Eqs. (1)--(7) and the two four-band
Hamiltonians in the supplement.  Energies are in meV and lengths in nm.
Plane waves are indexed by the moire reciprocal vectors B1 and B2, which
enclose 120 degrees.  This gauge makes the lowest harmonic shell explicit
and keeps all truncation decisions auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Iterable

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]

HBAR2_OVER_2ME_MEV_NM2 = 38.0998212
HBAR_MEV_S = 6.582119569e-13


@dataclass(frozen=True)
class MoireGeometry:
    """Reciprocal/direct moire geometry at one twist angle."""

    theta_deg: float
    a0_nm: float = 0.3472

    @property
    def theta_rad(self) -> float:
        return np.deg2rad(self.theta_deg)

    @property
    def a_moire_nm(self) -> float:
        return self.a0_nm / self.theta_rad

    @property
    def reciprocal_magnitude(self) -> float:
        return 4.0 * pi / (sqrt(3.0) * self.a_moire_nm)

    @property
    def B1(self) -> FloatArray:
        b = self.reciprocal_magnitude
        return np.array([b, 0.0])

    @property
    def B2(self) -> FloatArray:
        b = self.reciprocal_magnitude
        return np.array([-0.5 * b, 0.5 * sqrt(3.0) * b])

    @property
    def direct_vectors(self) -> tuple[FloatArray, FloatArray]:
        reciprocal = np.column_stack([self.B1, self.B2])
        direct = 2.0 * pi * np.linalg.inv(reciprocal).T
        return direct[:, 0], direct[:, 1]

    @property
    def unit_cell_area_nm2(self) -> float:
        a1, a2 = self.direct_vectors
        return float(abs(a1[0] * a2[1] - a1[1] * a2[0]))

    @property
    def kappa_plus(self) -> FloatArray:
        # Bottom-layer +K corner in the gauge of main Eq. (4).
        return (self.B1 - self.B2) / 3.0

    @property
    def kappa_minus(self) -> FloatArray:
        # Top-layer +K corner; kappa_minus-kappa_plus is the twist-induced K shift.
        return (2.0 * self.B1 + self.B2) / 3.0

    @property
    def kappa_plus_prime(self) -> FloatArray:
        return self.kappa_plus - self.B1

    @property
    def mbz_area_nm_minus2(self) -> float:
        return float(abs(self.B1[0] * self.B2[1] - self.B1[1] * self.B2[0]))


def hex_indices(cutoff: int) -> list[tuple[int, int]]:
    """Return complete hexagonal reciprocal shells through ``cutoff``."""

    if cutoff < 0:
        raise ValueError("cutoff must be non-negative")
    return [
        (n1, n2)
        for n1 in range(-cutoff, cutoff + 1)
        for n2 in range(-cutoff, cutoff + 1)
        if max(abs(n1), abs(n2), abs(n1 + n2)) <= cutoff
    ]


class PlaneWaveBasis:
    """Hexagonal plane-wave basis and precomputed Fourier shifts."""

    def __init__(self, geometry: MoireGeometry, cutoff: int) -> None:
        self.geometry = geometry
        self.indices = hex_indices(cutoff)
        self.index = {pair: position for position, pair in enumerate(self.indices)}
        self.vectors = np.array(
            [n1 * geometry.B1 + n2 * geometry.B2 for n1, n2 in self.indices],
            dtype=float,
        )

    def shift_pairs(self, q: tuple[int, int]) -> list[tuple[int, int]]:
        """Pairs (destination, source) satisfying G_dest-G_source=q."""

        pairs: list[tuple[int, int]] = []
        for source, (n1, n2) in enumerate(self.indices):
            destination_pair = (n1 + q[0], n2 + q[1])
            destination = self.index.get(destination_pair)
            if destination is not None:
                pairs.append((destination, source))
        return pairs

    def shifted_vector(self, pair: tuple[int, int]) -> FloatArray:
        return pair[0] * self.geometry.B1 + pair[1] * self.geometry.B2

    def __len__(self) -> int:
        return len(self.indices)


POTENTIAL_Q = ((1, 0), (0, 1), (-1, -1))
TUNNEL_Q = ((0, 0), (-1, -1), (0, -1))


def _band_path(
    geometry: MoireGeometry, points_per_segment: int
) -> tuple[FloatArray, FloatArray, FloatArray, list[str]]:
    """Paper path kappa_+' -> gamma -> kappa_- -> kappa_+ -> kappa_+'."""

    if points_per_segment < 2:
        raise ValueError("points_per_segment must be at least two")
    vertices = [
        geometry.kappa_plus_prime,
        np.zeros(2),
        geometry.kappa_minus,
        geometry.kappa_plus,
        geometry.kappa_plus_prime,
    ]
    chunks: list[FloatArray] = []
    ticks = [0.0]
    total = 0.0
    path_coordinate: list[float] = []
    for segment, (start, stop) in enumerate(zip(vertices[:-1], vertices[1:])):
        endpoint = segment == len(vertices) - 2
        count = points_per_segment if endpoint else points_per_segment - 1
        fractions = np.linspace(0.0, 1.0, points_per_segment)[:count]
        points = start[None, :] + fractions[:, None] * (stop - start)[None, :]
        chunks.append(points)
        distance = float(np.linalg.norm(stop - start))
        path_coordinate.extend((total + fractions * distance).tolist())
        total += distance
        ticks.append(total)
    return (
        np.concatenate(chunks, axis=0),
        np.asarray(path_coordinate),
        np.asarray(ticks),
        [r"$\kappa_+'$", r"$\gamma$", r"$\kappa_-$", r"$\kappa_+$", r"$\kappa_+'$"],
    )


class TwoBandContinuum:
    """Main-text two-layer valence-band continuum Hamiltonian."""

    def __init__(
        self,
        theta_deg: float,
        cutoff: int = 3,
        *,
        a0_nm: float = 0.3472,
        effective_mass_me: float = 0.62,
        potential_mev: float = 8.0,
        potential_phase_deg: float = -89.6,
        tunneling_mev: float = -8.5,
    ) -> None:
        self.geometry = MoireGeometry(theta_deg, a0_nm)
        self.basis = PlaneWaveBasis(self.geometry, cutoff)
        self.mass = effective_mass_me
        self.V = potential_mev
        self.psi = np.deg2rad(potential_phase_deg)
        self.w = tunneling_mev
        self.kinetic_coefficient = HBAR2_OVER_2ME_MEV_NM2 / effective_mass_me
        self._potential_links = {q: self.basis.shift_pairs(q) for q in POTENTIAL_Q}
        self._tunnel_links = {q: self.basis.shift_pairs(q) for q in TUNNEL_Q}

    @property
    def dimension(self) -> int:
        return 2 * len(self.basis)

    def hamiltonian(self, k: Iterable[float], layer_bias_mev: float = 0.0) -> ComplexArray:
        k_array = np.asarray(k, dtype=float)
        n_pw = len(self.basis)
        matrix = np.zeros((2 * n_pw, 2 * n_pw), dtype=complex)
        kappas = (self.geometry.kappa_plus, self.geometry.kappa_minus)
        layer_signs = (1, -1)
        for layer, (kappa, layer_sign) in enumerate(zip(kappas, layer_signs)):
            offset = layer * n_pw
            momenta = k_array[None, :] + self.basis.vectors - kappa[None, :]
            energies = -self.kinetic_coefficient * np.sum(momenta**2, axis=1)
            energies += layer_sign * layer_bias_mev / 2.0
            matrix[offset : offset + n_pw, offset : offset + n_pw] = np.diag(energies)
            coefficient = self.V * np.exp(1j * layer_sign * self.psi)
            for links in self._potential_links.values():
                for destination, source in links:
                    matrix[offset + destination, offset + source] += coefficient
                    matrix[offset + source, offset + destination] += coefficient.conjugate()

        for links in self._tunnel_links.values():
            for destination, source in links:
                matrix[destination, n_pw + source] += self.w
                matrix[n_pw + source, destination] += self.w
        return matrix

    def eigenvalues(self, k: Iterable[float], layer_bias_mev: float = 0.0) -> FloatArray:
        return np.linalg.eigvalsh(self.hamiltonian(k, layer_bias_mev))

    def top_bands(
        self, k: Iterable[float], count: int = 8, layer_bias_mev: float = 0.0
    ) -> FloatArray:
        return self.eigenvalues(k, layer_bias_mev)[-count:][::-1]

    def band_path(
        self, points_per_segment: int = 41, count: int = 8, layer_bias_mev: float = 0.0
    ) -> dict[str, object]:
        points, coordinate, ticks, labels = _band_path(self.geometry, points_per_segment)
        bands = np.array([self.top_bands(k, count, layer_bias_mev) for k in points])
        return {
            "k": points,
            "s": coordinate,
            "ticks": ticks,
            "labels": labels,
            "bands": bands,
        }

    def velocity_diagonals(self, k: Iterable[float]) -> tuple[FloatArray, FloatArray]:
        k_array = np.asarray(k, dtype=float)
        blocks = []
        for kappa in (self.geometry.kappa_plus, self.geometry.kappa_minus):
            blocks.append(-2.0 * self.kinetic_coefficient * (k_array + self.basis.vectors - kappa))
        velocities = np.concatenate(blocks, axis=0)
        return velocities[:, 0], velocities[:, 1]

    def berry_curvature(self, k: Iterable[float], band_from_top: int = 0) -> float:
        """Kubo Berry curvature of one isolated band, in nm^2."""

        matrix = self.hamiltonian(k)
        energies, vectors = np.linalg.eigh(matrix)
        band = len(energies) - 1 - band_from_top
        vx, vy = self.velocity_diagonals(k)
        left_x = vectors[:, band].conjugate() @ (vx[:, None] * vectors)
        right_y = vectors.conjugate().T @ (vy * vectors[:, band])
        denominator = (energies[band] - energies) ** 2
        denominator[band] = np.inf
        return float(-2.0 * np.imag(np.sum(left_x * right_y / denominator)))

    def chern_number(self, band_from_top: int = 0, grid_points: int = 25) -> float:
        values = []
        for i in range(grid_points):
            for j in range(grid_points):
                u = (i + 0.5) / grid_points - 0.5
                v = (j + 0.5) / grid_points - 0.5
                values.append(self.berry_curvature(u * self.geometry.B1 + v * self.geometry.B2, band_from_top))
        return float(np.mean(values) * self.geometry.mbz_area_nm_minus2 / (2.0 * pi))

    def sampled_band_edges(
        self, *, grid_points: int = 9, count: int = 3, layer_bias_mev: float = 0.0
    ) -> tuple[FloatArray, FloatArray]:
        samples = []
        for i in range(grid_points):
            for j in range(grid_points):
                u = (i + 0.5) / grid_points - 0.5
                v = (j + 0.5) / grid_points - 0.5
                k = u * self.geometry.B1 + v * self.geometry.B2
                samples.append(self.top_bands(k, count, layer_bias_mev))
        array = np.asarray(samples)
        return np.min(array, axis=0), np.max(array, axis=0)

    def global_gaps(self, grid_points: int = 9, layer_bias_mev: float = 0.0) -> tuple[float, float]:
        minima, maxima = self.sampled_band_edges(
            grid_points=grid_points, count=3, layer_bias_mev=layer_bias_mev
        )
        return float(minima[0] - maxima[1]), float(minima[1] - maxima[2])


def pseudospin_field(
    positions_nm: FloatArray,
    geometry: MoireGeometry,
    *,
    potential_mev: float = 8.0,
    potential_phase_deg: float = -89.6,
    tunneling_mev: float = -8.5,
) -> FloatArray:
    """Main Eq. (5) evaluated from Eqs. (2)--(3)."""

    positions = np.asarray(positions_nm, dtype=float)
    phase = np.deg2rad(potential_phase_deg)
    reciprocal = (geometry.B1, geometry.B2, -geometry.B1 - geometry.B2)
    phases = np.stack([positions @ q for q in reciprocal], axis=-1)
    bottom = 2.0 * potential_mev * np.sum(np.cos(phases + phase), axis=-1)
    top = 2.0 * potential_mev * np.sum(np.cos(phases - phase), axis=-1)
    b2 = geometry.B1 + geometry.B2
    b3 = geometry.B2
    tunneling = tunneling_mev * (
        1.0 + np.exp(-1j * (positions @ b2)) + np.exp(-1j * (positions @ b3))
    )
    conjugate = tunneling.conjugate()
    return np.stack([conjugate.real, conjugate.imag, 0.5 * (bottom - top)], axis=-1)


def pseudospin_texture(
    geometry: MoireGeometry, u_points: int = 121, v_points: int = 121
) -> dict[str, FloatArray]:
    a1, a2 = geometry.direct_vectors
    u = np.linspace(0.0, 1.0, u_points)
    v = np.linspace(0.0, 1.0, v_points)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    positions = uu[..., None] * a1 + vv[..., None] * a2
    field = pseudospin_field(positions, geometry)
    return {
        "u": uu,
        "v": vv,
        "x_nm": positions[..., 0],
        "y_nm": positions[..., 1],
        "field": field,
    }


def pseudospin_winding(geometry: MoireGeometry, grid_points: int = 151) -> float:
    """Periodic discretization of main Eq. (6) on one moire cell."""

    a1, a2 = geometry.direct_vectors
    fraction = np.arange(grid_points) / grid_points
    uu, vv = np.meshgrid(fraction, fraction, indexing="ij")
    positions = uu[..., None] * a1 + vv[..., None] * a2
    field = pseudospin_field(positions, geometry)
    direction = field / np.linalg.norm(field, axis=-1, keepdims=True)
    derivative_u = 0.5 * (np.roll(direction, -1, axis=0) - np.roll(direction, 1, axis=0))
    derivative_v = 0.5 * (np.roll(direction, -1, axis=1) - np.roll(direction, 1, axis=1))
    density = np.einsum("ijk,ijk->ij", direction, np.cross(derivative_u, derivative_v))
    return float(np.sum(density) / (4.0 * pi))


def kane_mele_bands(
    k_points: FloatArray,
    geometry: MoireGeometry,
    *,
    t0_mev: float = 0.29,
    t1_mev: float = 0.06,
) -> FloatArray:
    """Spin-up sector of main Eq. (7), before an arbitrary energy shift."""

    a1, a2 = geometry.direct_vectors
    a3 = a2 - a1
    displacement = (a1 + a2) / 3.0
    nearest = (displacement, displacement - a1, displacement - a2)
    result = []
    for k in np.asarray(k_points):
        off_diagonal = t0_mev * sum(np.exp(1j * k @ delta) for delta in nearest)
        diagonal_bottom = 2.0 * t1_mev * sum(
            np.cos((k + geometry.kappa_plus) @ vector) for vector in (a1, a2, a3)
        )
        diagonal_top = 2.0 * t1_mev * sum(
            np.cos((k + geometry.kappa_minus) @ vector) for vector in (a1, a2, a3)
        )
        matrix = np.array(
            [[diagonal_bottom, off_diagonal], [off_diagonal.conjugate(), diagonal_top]],
            dtype=complex,
        )
        result.append(np.linalg.eigvalsh(matrix)[::-1])
    return np.asarray(result)


class DiracFourBandModel:
    """Supplemental conduction/valence, layer-resolved massive-Dirac model."""

    def __init__(self, theta_deg: float = 1.2, cutoff: int = 2) -> None:
        self.geometry = MoireGeometry(theta_deg)
        self.basis = PlaneWaveBasis(self.geometry, cutoff)
        self.gap_mev = 1100.0
        self.hv_mev_nm = HBAR_MEV_S * 0.4e15
        self.V = np.array([5.97, 8.0])  # conduction, valence
        self.psi = np.deg2rad(np.array([-87.9, -89.6]))
        self.wc = -2.0
        self.wv = -8.5
        self.wcv = 15.3 + 0.0j
        self.wvc = self.wcv.conjugate()
        self._potential_links = {q: self.basis.shift_pairs(q) for q in POTENTIAL_Q}
        self._tunnel_links = {q: self.basis.shift_pairs(q) for q in TUNNEL_Q}

    @property
    def dimension(self) -> int:
        return 4 * len(self.basis)

    def _state(self, layer: int, plane_wave: int, orbital: int) -> int:
        return (layer * len(self.basis) + plane_wave) * 2 + orbital

    def _tunnel_matrices(self) -> tuple[ComplexArray, ComplexArray, ComplexArray]:
        phase = np.exp(1j * 2.0 * pi / 3.0)
        return (
            np.array([[self.wc, self.wcv], [self.wvc, self.wv]], dtype=complex),
            np.array(
                [[self.wc, self.wcv / phase], [self.wvc * phase, self.wv]], dtype=complex
            ),
            np.array(
                [[self.wc, self.wcv * phase], [self.wvc / phase, self.wv]], dtype=complex
            ),
        )

    def hamiltonian(self, k: Iterable[float]) -> ComplexArray:
        k_array = np.asarray(k, dtype=float)
        n_pw = len(self.basis)
        matrix = np.zeros((4 * n_pw, 4 * n_pw), dtype=complex)
        for layer, (kappa, layer_sign) in enumerate(
            ((self.geometry.kappa_plus, 1), (self.geometry.kappa_minus, -1))
        ):
            for plane_wave, G in enumerate(self.basis.vectors):
                q = k_array + G - kappa
                phase = np.exp(-0.5j * layer_sign * self.geometry.theta_rad)
                cv = self.hv_mev_nm * (q[0] - 1j * q[1]) * phase
                block = np.array([[self.gap_mev, cv], [cv.conjugate(), 0.0]], dtype=complex)
                indices = [self._state(layer, plane_wave, orbital) for orbital in range(2)]
                matrix[np.ix_(indices, indices)] += block

            for links in self._potential_links.values():
                for orbital in range(2):
                    coefficient = self.V[orbital] * np.exp(1j * layer_sign * self.psi[orbital])
                    for destination, source in links:
                        row = self._state(layer, destination, orbital)
                        column = self._state(layer, source, orbital)
                        matrix[row, column] += coefficient
                        matrix[column, row] += coefficient.conjugate()

        for links, tunneling in zip(self._tunnel_links.values(), self._tunnel_matrices()):
            for destination, source in links:
                bottom = [self._state(0, destination, orbital) for orbital in range(2)]
                top = [self._state(1, source, orbital) for orbital in range(2)]
                matrix[np.ix_(bottom, top)] += tunneling
                matrix[np.ix_(top, bottom)] += tunneling.conjugate().T
        return matrix

    def selected_bands(self, k: Iterable[float], valence_count: int = 8) -> tuple[FloatArray, FloatArray]:
        energies = np.linalg.eigvalsh(self.hamiltonian(k))
        valence = energies[energies < 0.5 * self.gap_mev][-valence_count:][::-1]
        conduction = energies[energies > 0.5 * self.gap_mev][:2] - self.gap_mev
        return valence, conduction

    def band_path(self, points_per_segment: int = 31) -> dict[str, object]:
        points, coordinate, ticks, labels = _band_path(self.geometry, points_per_segment)
        valence = []
        conduction = []
        for k in points:
            val, cond = self.selected_bands(k)
            valence.append(val)
            conduction.append(cond)
        return {
            "k": points,
            "s": coordinate,
            "ticks": ticks,
            "labels": labels,
            "valence": np.asarray(valence),
            "conduction": np.asarray(conduction),
        }


class SpinMixedModel:
    """Supplemental layer x spin valence model including remote spin bands."""

    def __init__(self, theta_deg: float, cutoff: int = 2) -> None:
        self.geometry = MoireGeometry(theta_deg)
        self.basis = PlaneWaveBasis(self.geometry, cutoff)
        self.kinetic_coefficient = HBAR2_OVER_2ME_MEV_NM2 / 0.62
        self.spin_orbit_mev = 220.5
        self.V = np.array([8.0, 7.7])
        self.psi = np.deg2rad(np.array([-89.6, -88.35]))
        self.w_up = -8.5
        self.w_down = -6.0
        self.w_up_down = -1j * 5.6
        self.w_down_up = -self.w_up_down.conjugate()
        self._potential_links = {q: self.basis.shift_pairs(q) for q in POTENTIAL_Q}
        self._tunnel_links = {q: self.basis.shift_pairs(q) for q in TUNNEL_Q}

    @property
    def dimension(self) -> int:
        return 4 * len(self.basis)

    def _state(self, layer: int, plane_wave: int, spin: int) -> int:
        return (layer * len(self.basis) + plane_wave) * 2 + spin

    def _tunnel_matrices(self) -> tuple[ComplexArray, ComplexArray, ComplexArray]:
        phase = np.exp(1j * 2.0 * pi / 3.0)
        return (
            np.array(
                [[self.w_up, self.w_up_down], [self.w_down_up, self.w_down]], dtype=complex
            ),
            np.array(
                [
                    [self.w_up, self.w_up_down / phase],
                    [self.w_down_up * phase, self.w_down],
                ],
                dtype=complex,
            ),
            np.array(
                [
                    [self.w_up, self.w_up_down * phase],
                    [self.w_down_up / phase, self.w_down],
                ],
                dtype=complex,
            ),
        )

    def hamiltonian(self, k: Iterable[float]) -> ComplexArray:
        k_array = np.asarray(k, dtype=float)
        n_pw = len(self.basis)
        matrix = np.zeros((4 * n_pw, 4 * n_pw), dtype=complex)
        for layer, (kappa, layer_sign) in enumerate(
            ((self.geometry.kappa_plus, 1), (self.geometry.kappa_minus, -1))
        ):
            momenta = k_array[None, :] + self.basis.vectors - kappa
            kinetic = -self.kinetic_coefficient * np.sum(momenta**2, axis=1)
            for plane_wave, energy in enumerate(kinetic):
                matrix[self._state(layer, plane_wave, 0), self._state(layer, plane_wave, 0)] += energy
                matrix[self._state(layer, plane_wave, 1), self._state(layer, plane_wave, 1)] += (
                    energy - self.spin_orbit_mev
                )
            for links in self._potential_links.values():
                for spin in range(2):
                    coefficient = self.V[spin] * np.exp(1j * layer_sign * self.psi[spin])
                    for destination, source in links:
                        row = self._state(layer, destination, spin)
                        column = self._state(layer, source, spin)
                        matrix[row, column] += coefficient
                        matrix[column, row] += coefficient.conjugate()

        for links, tunneling in zip(self._tunnel_links.values(), self._tunnel_matrices()):
            for destination, source in links:
                bottom = [self._state(0, destination, spin) for spin in range(2)]
                top = [self._state(1, source, spin) for spin in range(2)]
                matrix[np.ix_(bottom, top)] += tunneling
                matrix[np.ix_(top, bottom)] += tunneling.conjugate().T
        return matrix

    def band_path(self, points_per_segment: int = 31, count: int = 8) -> dict[str, object]:
        points, coordinate, ticks, labels = _band_path(self.geometry, points_per_segment)
        bands = []
        for k in points:
            energies = np.linalg.eigvalsh(self.hamiltonian(k))
            bands.append(energies[-count:][::-1])
        return {
            "k": points,
            "s": coordinate,
            "ticks": ticks,
            "labels": labels,
            "bands": np.asarray(bands),
        }


def hermiticity_error(matrix: ComplexArray) -> float:
    return float(np.max(np.abs(matrix - matrix.conjugate().T)))


def hexagon_vertices(geometry: MoireGeometry) -> FloatArray:
    radius = np.linalg.norm(geometry.kappa_plus)
    # The reciprocal lattice vectors point at 0, 60, ... degrees, so the
    # Wigner-Seitz (MBZ) vertices lie halfway between them.
    angles = np.deg2rad(30.0 + np.arange(0.0, 360.0, 60.0))
    return np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])


def inside_convex_polygon(points: FloatArray, vertices: FloatArray) -> NDArray[np.bool_]:
    edges = np.roll(vertices, -1, axis=0) - vertices
    relative = points[:, None, :] - vertices[None, :, :]
    cross = edges[None, :, 0] * relative[:, :, 1] - edges[None, :, 1] * relative[:, :, 0]
    return np.all(cross >= -1e-12, axis=1) | np.all(cross <= 1e-12, axis=1)
