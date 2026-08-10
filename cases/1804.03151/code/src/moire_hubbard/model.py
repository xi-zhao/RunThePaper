"""Formula-derived moire Hubbard model without author code or numerical data.

Energies are in meV and lengths are in nm unless a function explicitly says
otherwise.  The implementation follows main-text Eqs. (1)--(5) and
Supplement Eq. (6) of arXiv:1804.03151.  Plane waves use complete hexagonal
reciprocal shells so the truncation preserves threefold symmetry.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Iterable

import numpy as np
from numpy.typing import NDArray
from scipy.special import j0


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]

HBAR2_OVER_2ME_MEV_NM2 = 38.0998212
COULOMB_EV_NM = 1.439964548
FIRST_SHELL_Q = ((1, 0), (0, 1), (-1, -1))


@dataclass(frozen=True)
class MoireGeometry:
    """Direct and reciprocal geometry of one triangular moire lattice."""

    a_moire_nm: float

    @classmethod
    def from_twist(
        cls,
        theta_deg: float,
        *,
        a0_nm: float = 0.332,
        mismatch: float = 0.0,
    ) -> "MoireGeometry":
        theta = np.deg2rad(theta_deg)
        scale = float(np.hypot(theta, mismatch))
        if scale <= 0.0:
            raise ValueError("twist and mismatch cannot both vanish")
        return cls(a0_nm / scale)

    @property
    def reciprocal_magnitude(self) -> float:
        return 4.0 * pi / (sqrt(3.0) * self.a_moire_nm)

    @property
    def B1(self) -> FloatArray:
        return np.array([self.reciprocal_magnitude, 0.0])

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
    def reciprocal_cell_area_nm_minus2(self) -> float:
        b1, b2 = self.B1, self.B2
        return float(abs(b1[0] * b2[1] - b1[1] * b2[0]))

    @property
    def bz_vertices(self) -> FloatArray:
        candidates = np.array(
            [
                (2.0 * self.B1 + self.B2) / 3.0,
                (self.B1 + 2.0 * self.B2) / 3.0,
                (-self.B1 + self.B2) / 3.0,
            ]
        )
        vertices = np.concatenate([candidates, -candidates], axis=0)
        angles = np.arctan2(vertices[:, 1], vertices[:, 0])
        return vertices[np.argsort(angles)]

    def inside_first_bz(self, points: FloatArray, tolerance: float = 1e-12) -> NDArray[np.bool_]:
        """Return the Wigner--Seitz mask for Cartesian momentum points."""

        points = np.asarray(points, dtype=float)
        nearest = np.array(
            [self.B1, self.B2, self.B1 + self.B2, -self.B1, -self.B2, -self.B1 - self.B2]
        )
        projections = points @ nearest.T
        bounds = 0.5 * np.sum(nearest**2, axis=1)
        return np.all(projections <= bounds[None, :] + tolerance, axis=1)


def hex_indices(cutoff: int) -> list[tuple[int, int]]:
    """Complete reciprocal shells in the 120-degree basis."""

    if cutoff < 0:
        raise ValueError("cutoff must be non-negative")
    return [
        (n1, n2)
        for n1 in range(-cutoff, cutoff + 1)
        for n2 in range(-cutoff, cutoff + 1)
        if max(abs(n1), abs(n2), abs(n1 + n2)) <= cutoff
    ]


class PlaneWaveBasis:
    """Hexagonal plane-wave basis with precomputed Fourier links."""

    def __init__(self, geometry: MoireGeometry, cutoff: int) -> None:
        self.geometry = geometry
        self.indices = hex_indices(cutoff)
        self.index = {pair: position for position, pair in enumerate(self.indices)}
        self.vectors = np.asarray(
            [n1 * geometry.B1 + n2 * geometry.B2 for n1, n2 in self.indices], dtype=float
        )

    def shift_pairs(self, shift: tuple[int, int]) -> list[tuple[int, int]]:
        pairs: list[tuple[int, int]] = []
        for source, (n1, n2) in enumerate(self.indices):
            destination = self.index.get((n1 + shift[0], n2 + shift[1]))
            if destination is not None:
                pairs.append((destination, source))
        return pairs

    def __len__(self) -> int:
        return len(self.indices)


def _piecewise_path(
    vertices: list[FloatArray], points_per_segment: int
) -> tuple[FloatArray, FloatArray, FloatArray]:
    if points_per_segment < 2:
        raise ValueError("points_per_segment must be at least two")
    chunks: list[FloatArray] = []
    coordinates: list[float] = []
    ticks = [0.0]
    total = 0.0
    for index, (start, stop) in enumerate(zip(vertices[:-1], vertices[1:])):
        endpoint = index == len(vertices) - 2
        count = points_per_segment if endpoint else points_per_segment - 1
        fractions = np.linspace(0.0, 1.0, points_per_segment)[:count]
        chunks.append(start[None, :] + fractions[:, None] * (stop - start)[None, :])
        distance = float(np.linalg.norm(stop - start))
        coordinates.extend((total + fractions * distance).tolist())
        total += distance
        ticks.append(total)
    return np.concatenate(chunks), np.asarray(coordinates), np.asarray(ticks)


class SingleBandContinuum:
    """Scalar effective-mass Hamiltonian of main Eqs. (1)--(2)."""

    def __init__(
        self,
        a_moire_nm: float,
        *,
        cutoff: int = 4,
        effective_mass_me: float = 0.35,
        potential_mev: float = 6.6,
        potential_phase_deg: float = -94.0,
    ) -> None:
        self.geometry = MoireGeometry(a_moire_nm)
        self.basis = PlaneWaveBasis(self.geometry, cutoff)
        self.mass = effective_mass_me
        self.V = potential_mev
        self.psi = np.deg2rad(potential_phase_deg)
        self.kinetic_coefficient = HBAR2_OVER_2ME_MEV_NM2 / effective_mass_me
        self._links = {shift: self.basis.shift_pairs(shift) for shift in FIRST_SHELL_Q}

    @property
    def dimension(self) -> int:
        return len(self.basis)

    def hamiltonian(self, k: Iterable[float]) -> ComplexArray:
        k_array = np.asarray(k, dtype=float)
        momenta = k_array[None, :] + self.basis.vectors
        diagonal = -self.kinetic_coefficient * np.sum(momenta**2, axis=1)
        matrix = np.diag(diagonal.astype(complex))
        coefficient = self.V * np.exp(1j * self.psi)
        for links in self._links.values():
            for destination, source in links:
                matrix[destination, source] += coefficient
                matrix[source, destination] += coefficient.conjugate()
        return matrix

    def eigenvalues(self, k: Iterable[float]) -> FloatArray:
        return np.linalg.eigvalsh(self.hamiltonian(k))

    def top_bands(self, k: Iterable[float], count: int = 5) -> FloatArray:
        return self.eigenvalues(k)[-count:][::-1]

    def top_eigenpair(self, k: Iterable[float]) -> tuple[float, ComplexArray]:
        values, vectors = np.linalg.eigh(self.hamiltonian(k))
        return float(values[-1]), vectors[:, -1]

    def potential(self, positions_nm: FloatArray) -> FloatArray:
        positions = np.asarray(positions_nm, dtype=float)
        reciprocal = np.array(
            [
                self.geometry.B1,
                self.geometry.B2,
                -self.geometry.B1 - self.geometry.B2,
            ]
        )
        phases = positions @ reciprocal.T + self.psi
        return 2.0 * self.V * np.sum(np.cos(phases), axis=-1)

    def potential_maximum(self, grid_points: int = 121) -> FloatArray:
        a1, a2 = self.geometry.direct_vectors
        fractions = np.linspace(0.0, 1.0, grid_points, endpoint=False)
        u, v = np.meshgrid(fractions, fractions, indexing="ij")
        points = u[..., None] * a1 + v[..., None] * a2
        values = self.potential(points)
        return np.asarray(points.reshape(-1, 2)[int(np.argmax(values))])

    def band_path(self, points_per_segment: int = 61, count: int = 5) -> dict[str, object]:
        b1, b2 = self.geometry.B1, self.geometry.B2
        vertices = [
            np.zeros(2),
            (2.0 * b1 + b2) / 3.0,
            (b1 + 2.0 * b2) / 3.0,
            (-b1 + b2) / 3.0,
        ]
        k, coordinate, ticks = _piecewise_path(vertices, points_per_segment)
        bands = np.asarray([self.top_bands(point, count) for point in k])
        return {
            "k": k,
            "s": coordinate,
            "ticks": ticks,
            "labels": [r"$\gamma$", r"$\kappa'$", r"$\kappa''$", r"$\kappa$"],
            "bands": bands,
        }

    def sample_bands(self, grid_points: int = 31, count: int = 4) -> FloatArray:
        fractions = (np.arange(grid_points) + 0.5) / grid_points - 0.5
        samples = []
        for u in fractions:
            for v in fractions:
                samples.append(self.top_bands(u * self.geometry.B1 + v * self.geometry.B2, count))
        return np.asarray(samples)

    def density_of_states_vs_hole_filling(
        self,
        *,
        grid_points: int = 41,
        band_count: int = 4,
        broadening_mev: float = 0.16,
        filling_points: int = 401,
    ) -> dict[str, FloatArray]:
        energies = self.sample_bands(grid_points=grid_points, count=band_count).reshape(-1)
        ordered = np.sort(energies)[::-1]
        filling = np.linspace(0.0, float(band_count), filling_points)
        ranks = np.clip(np.rint(filling * grid_points**2).astype(int), 0, len(ordered) - 1)
        fermi_energy = ordered[ranks]
        delta = fermi_energy[:, None] - energies[None, :]
        kernel = np.exp(-0.5 * (delta / broadening_mev) ** 2) / (
            sqrt(2.0 * pi) * broadening_mev
        )
        dos_per_mev_nm2 = 2.0 * np.sum(kernel, axis=1) / (
            grid_points**2 * self.geometry.unit_cell_area_nm2
        )
        return {
            "filling": filling,
            "fermi_energy_mev": fermi_energy,
            "dos_ev_inv_nm2": 1000.0 * dos_per_mev_nm2,
            "full_hole_density_1e12_cm2": np.asarray(
                [200.0 / self.geometry.unit_cell_area_nm2]
            ),
        }

    def tight_binding_fit(self, grid_points: int = 15) -> dict[str, object]:
        a1, a2 = self.geometry.direct_vectors
        shell_vectors = [
            [a1, a2, a1 - a2],
            [a1 + a2, 2.0 * a1 - a2, a1 - 2.0 * a2],
            [2.0 * a1, 2.0 * a2, 2.0 * (a1 - a2)],
        ]
        fractions = (np.arange(grid_points) + 0.5) / grid_points - 0.5
        rows = []
        energies = []
        for u in fractions:
            for v in fractions:
                k = u * self.geometry.B1 + v * self.geometry.B2
                factors = [
                    2.0 * sum(np.cos(float(k @ vector)) for vector in shell)
                    for shell in shell_vectors
                ]
                rows.append([1.0, *factors])
                energies.append(self.top_bands(k, 1)[0])
        coefficients, _, _, _ = np.linalg.lstsq(np.asarray(rows), np.asarray(energies), rcond=None)
        residual = np.asarray(rows) @ coefficients - np.asarray(energies)
        return {
            "onsite_mev": float(coefficients[0]),
            "hopping_mev": np.asarray(coefficients[1:]),
            "rms_residual_mev": float(np.sqrt(np.mean(residual**2))),
            "shell_vectors_nm": [np.asarray(shell) for shell in shell_vectors],
        }

    @staticmethod
    def tight_binding_energy(k: FloatArray, fit: dict[str, object]) -> FloatArray:
        points = np.atleast_2d(np.asarray(k, dtype=float))
        energy = np.full(len(points), float(fit["onsite_mev"]))
        hoppings = np.asarray(fit["hopping_mev"], dtype=float)
        for hopping, shell in zip(hoppings, fit["shell_vectors_nm"]):
            vectors = np.asarray(shell)
            energy += 2.0 * hopping * np.sum(np.cos(points @ vectors.T), axis=1)
        return energy if np.asarray(k).ndim > 1 else energy[0]

    def wannier_amplitude(
        self,
        *,
        k_grid: int = 7,
        real_grid: int = 121,
        span_moire_periods: float = 1.45,
    ) -> dict[str, FloatArray]:
        """Construct the isolated-band Wannier orbital from Bloch eigenstates."""

        center = self.potential_maximum()
        span = span_moire_periods * self.geometry.a_moire_nm
        x = np.linspace(-span, span, real_grid)
        y = np.linspace(-span, span, real_grid)
        xx, yy = np.meshgrid(x, y, indexing="xy")
        relative = np.column_stack([xx.ravel(), yy.ravel()])
        absolute = relative + center[None, :]
        amplitude = np.zeros(len(relative), dtype=complex)
        fractions = (np.arange(k_grid) - k_grid // 2) / k_grid
        for u in fractions:
            for v in fractions:
                k = u * self.geometry.B1 + v * self.geometry.B2
                _, vector = self.top_eigenpair(k)
                momenta = k[None, :] + self.basis.vectors
                value_at_center = np.sum(vector * np.exp(1j * (momenta @ center)))
                vector = vector * np.exp(-1j * np.angle(value_at_center))
                amplitude += np.exp(1j * (absolute @ momenta.T)) @ vector
        amplitude = amplitude.reshape(real_grid, real_grid) / float(k_grid**2)
        probability = np.abs(amplitude) ** 2
        dx = x[1] - x[0]
        dy = y[1] - y[0]
        norm = float(np.sum(probability) * dx * dy)
        amplitude /= sqrt(norm)
        return {
            "x_over_am": x / self.geometry.a_moire_nm,
            "y_over_am": y / self.geometry.a_moire_nm,
            "amplitude_times_am": np.abs(amplitude) * self.geometry.a_moire_nm,
            "probability_nm_minus2": np.abs(amplitude) ** 2,
            "center_nm": center,
            "normalization": np.asarray([float(np.sum(np.abs(amplitude) ** 2) * dx * dy)]),
        }

    def fermi_contour_map(self, grid_points: int = 181, hole_filling: float = 0.75) -> dict[str, FloatArray]:
        vertices = self.geometry.bz_vertices
        limit_x = float(np.max(np.abs(vertices[:, 0])))
        limit_y = float(np.max(np.abs(vertices[:, 1])))
        x = np.linspace(-1.04 * limit_x, 1.04 * limit_x, grid_points)
        y = np.linspace(-1.04 * limit_y, 1.04 * limit_y, grid_points)
        xx, yy = np.meshgrid(x, y, indexing="xy")
        points = np.column_stack([xx.ravel(), yy.ravel()])
        mask = self.geometry.inside_first_bz(points)
        energy = np.full(len(points), np.nan)
        energy[mask] = np.asarray([self.top_bands(point, 1)[0] for point in points[mask]])
        finite = energy[mask]
        fermi = float(np.quantile(finite, 1.0 - hole_filling))
        return {
            "kx": x,
            "ky": y,
            "energy_mev": energy.reshape(grid_points, grid_points),
            "mask": mask.reshape(grid_points, grid_points),
            "fermi_energy_mev": np.asarray([fermi]),
            "bz_vertices": vertices,
        }


def harmonic_wannier_length_nm(
    a_moire_nm: float,
    *,
    effective_mass_me: float,
    potential_mev: float,
    potential_phase_deg: float,
) -> float:
    """Paper's harmonic estimate below main Eq. (1)."""

    beta = 16.0 * pi**2 * np.cos(np.deg2rad(potential_phase_deg + 120.0))
    if beta <= 0.0:
        raise ValueError("the printed harmonic curvature must be positive")
    hbar2_over_m = 2.0 * HBAR2_OVER_2ME_MEV_NM2 / effective_mass_me
    prefactor = (hbar2_over_m / (beta * potential_mev)) ** 0.25
    return float(prefactor * sqrt(a_moire_nm))


def screened_interactions_harmonic(
    a_moire_nm: float,
    *,
    effective_mass_me: float = 0.35,
    potential_mev: float = 6.6,
    potential_phase_deg: float = -94.0,
    screening_separation_nm: float = 3.0,
    integration_points: int = 6001,
) -> FloatArray:
    """Return epsilon*U_0,1,2 in eV using the paper's screened interaction.

    The Wannier density is the Gaussian implied by the explicitly derived
    harmonic length.  This controlled approximation is used for parameter
    sweeps; the displayed Wannier target is constructed from Bloch states.
    """

    length = harmonic_wannier_length_nm(
        a_moire_nm,
        effective_mass_me=effective_mass_me,
        potential_mev=potential_mev,
        potential_phase_deg=potential_phase_deg,
    )
    q_max = 12.0 / length
    q = np.linspace(0.0, q_max, integration_points)
    form_factor_squared = np.exp(-0.5 * (length * q) ** 2)
    screened = 1.0 - np.exp(-q * screening_separation_nm)
    distances = np.array([0.0, a_moire_nm, sqrt(3.0) * a_moire_nm])
    values = []
    for distance in distances:
        integrand = screened * form_factor_squared * j0(q * distance)
        values.append(COULOMB_EV_NM * float(np.trapezoid(integrand, q)))
    return np.asarray(values)


def screened_interactions(
    model: SingleBandContinuum,
    *,
    screening_separation_nm: float = 3.0,
    k_grid: int = 7,
    real_grid: int = 101,
    span_moire_periods: float = 1.8,
) -> FloatArray:
    """Project the screened Coulomb kernel onto a Bloch-derived Wannier density.

    The convolution is evaluated in reciprocal space on a Cartesian box that
    contains the localized orbital and its exponentially small tails.  The
    returned values are epsilon*U_0,1,2 in eV for on-site, nearest-neighbor,
    and second-neighbor separations.
    """

    wannier = model.wannier_amplitude(
        k_grid=k_grid,
        real_grid=real_grid,
        span_moire_periods=span_moire_periods,
    )
    density = np.asarray(wannier["probability_nm_minus2"], dtype=float)
    x = np.asarray(wannier["x_over_am"], dtype=float) * model.geometry.a_moire_nm
    y = np.asarray(wannier["y_over_am"], dtype=float) * model.geometry.a_moire_nm
    dx = float(x[1] - x[0])
    dy = float(y[1] - y[0])
    density_transform = np.fft.fft2(density) * dx * dy
    qx = 2.0 * pi * np.fft.fftfreq(len(x), d=dx)
    qy = 2.0 * pi * np.fft.fftfreq(len(y), d=dy)
    qxx, qyy = np.meshgrid(qx, qy, indexing="xy")
    magnitude = np.hypot(qxx, qyy)
    kernel = np.empty_like(magnitude)
    nonzero = magnitude > 1e-14
    kernel[nonzero] = (
        2.0
        * pi
        * COULOMB_EV_NM
        * (1.0 - np.exp(-screening_separation_nm * magnitude[nonzero]))
        / magnitude[nonzero]
    )
    kernel[~nonzero] = 2.0 * pi * COULOMB_EV_NM * screening_separation_nm
    a1, a2 = model.geometry.direct_vectors
    separations = [np.zeros(2), a1, a1 + a2]
    periodic_area = len(x) * dx * len(y) * dy
    structure = kernel * np.abs(density_transform) ** 2
    interactions = []
    for separation in separations:
        phase = np.exp(1j * (qxx * separation[0] + qyy * separation[1]))
        interactions.append(float(np.real(np.sum(structure * phase) / periodic_area)))
    return np.asarray(interactions)


def exchange_couplings(hopping_mev: FloatArray, onsite_u_mev: float) -> FloatArray:
    """Main-text fourth/second-order t/U expressions for J_1,2,3."""

    t1, t2, t3 = np.asarray(hopping_mev, dtype=float)
    if onsite_u_mev <= 0.0:
        raise ValueError("onsite interaction must be positive")
    fourth = 4.0 * t1**4 / onsite_u_mev**3
    return np.array(
        [
            4.0 * t1**2 / onsite_u_mev * (1.0 - 7.0 * (t1 / onsite_u_mev) ** 2),
            4.0 * t2**2 / onsite_u_mev + fourth,
            4.0 * t3**2 / onsite_u_mev + fourth,
        ]
    )
