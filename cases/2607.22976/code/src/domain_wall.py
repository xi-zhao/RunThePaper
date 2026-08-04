"""Numerical core for the three-domain non-Hermitian ring in arXiv:2607.22976.

Every operation in this module starts from the Laurent coefficients printed in
the paper.  It does not load paper figures, digitized curves, or author data.
The same root ordering is used for winding, Ronkin, GBZ, DOS, and open-chain
calculations so that the five reproduction targets share one physical model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


LAURENT_COEFFICIENTS: tuple[dict[int, float], ...] = (
    {-1: 0.5, 0: 0.1, 1: 1.3},
    {-1: 0.7, 0: -0.3, 1: 0.9, 2: 0.3},
    {-2: 0.3, -1: 0.2, 0: -0.4, 1: 1.0, 2: 0.2},
)
DOMAIN_LENGTHS: tuple[int, int, int] = (58, 41, 87)
POLE_ORDERS: tuple[int, int, int] = (1, 1, 2)


@dataclass(frozen=True)
class GBZDiagnostics:
    """Residuals of the complete Case-I/Case-II conditions in SIII."""

    mu: tuple[np.ndarray, np.ndarray, np.ndarray]
    lambda0: float
    lambda1: float
    standing_residual: float
    traveling_residual: float
    standing_sector: int
    standing_domain: int
    traveling_branch: int

    @property
    def classification(self) -> str:
        return "standing" if self.standing_residual <= self.traveling_residual else "traveling"


def bulk_energy(domain: int, beta: np.ndarray | complex) -> np.ndarray | complex:
    """Evaluate the printed Laurent Hamiltonian h_domain(beta)."""
    value: np.ndarray | complex = np.zeros_like(beta, dtype=complex) if isinstance(beta, np.ndarray) else 0.0j
    for displacement, hopping in LAURENT_COEFFICIENTS[domain].items():
        value = value + hopping * np.power(beta, displacement)
    return value


def characteristic_roots(domain: int, energy: complex) -> np.ndarray:
    """Return roots of beta**s [h(beta)-E], ordered by modulus."""
    coefficients = LAURENT_COEFFICIENTS[domain]
    pole_order = POLE_ORDERS[domain]
    maximum_power = max(coefficients) + pole_order
    polynomial = np.zeros(maximum_power + 1, dtype=complex)
    for displacement, hopping in coefficients.items():
        power = displacement + pole_order
        polynomial[maximum_power - power] += hopping
    polynomial[maximum_power - pole_order] -= energy
    roots = np.roots(polynomial)
    return roots[np.argsort(np.abs(roots))]


def log_root_moduli(energy: complex) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return tuple(np.log(np.maximum(np.abs(characteristic_roots(domain, energy)), 1e-300)) for domain in range(3))  # type: ignore[return-value]


def winding(domain: int, energy: complex, radius: float = 1.0) -> int:
    """Point-gap winding from the argument principle, n_inside-s."""
    roots = characteristic_roots(domain, energy)
    return int(np.count_nonzero(np.abs(roots) < radius) - POLE_ORDERS[domain])


def pbc_spectra(k: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    beta = np.exp(1j * np.asarray(k, dtype=float))
    return tuple(np.asarray(bulk_energy(domain, beta), dtype=complex) for domain in range(3))  # type: ignore[return-value]


def site_domains(lengths: Sequence[int] = DOMAIN_LENGTHS) -> np.ndarray:
    return np.repeat(np.arange(len(lengths)), np.asarray(lengths, dtype=int))


def build_domain_wall_hamiltonian(
    lengths: Sequence[int] = DOMAIN_LENGTHS,
    *,
    periodic: bool = True,
    flux: float = 0.0,
) -> np.ndarray:
    """Build the disclosed local-row finite stencil.

    For row ``x`` in domain alpha, ``H[x, x+d] = t[alpha,d]``.  This
    convention exactly returns h_alpha(beta) on beta**x in a homogeneous
    region.  The paper does not map its Laurent exponent to an oriented site
    label, so positive flux is fixed by the explicit convention
    beta -> beta*exp(+i Phi/N).  Reversing all site labels reverses W but no
    spectrum or localization result.
    """
    lengths = tuple(int(length) for length in lengths)
    if len(lengths) != 3 or any(length <= 0 for length in lengths):
        raise ValueError("lengths must contain three positive integers")
    domains = site_domains(lengths)
    size = int(domains.size)
    matrix = np.zeros((size, size), dtype=complex)
    for row, domain in enumerate(domains):
        for displacement, hopping in LAURENT_COEFFICIENTS[int(domain)].items():
            raw_column = row + displacement
            if periodic:
                column = raw_column % size
            elif 0 <= raw_column < size:
                column = raw_column
            else:
                continue
            phase = np.exp(1j * flux * displacement / size) if periodic else 1.0
            matrix[row, column] += hopping * phase
    return matrix


def eigensystem(
    lengths: Sequence[int] = DOMAIN_LENGTHS,
    *,
    periodic: bool = True,
    flux: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    values, vectors = np.linalg.eig(build_domain_wall_hamiltonian(lengths, periodic=periodic, flux=flux))
    norms = np.linalg.norm(vectors, axis=0)
    vectors = vectors / np.where(norms > 0.0, norms, 1.0)
    return values, vectors


def gbz_diagnostics(energy: complex, lengths: Sequence[int] = DOMAIN_LENGTHS) -> GBZDiagnostics:
    """Evaluate Eqs. (S89)-(S105) without fitting to a source curve."""
    mu = log_root_moduli(energy)
    ratios = np.asarray(lengths, dtype=float) / float(sum(lengths))
    lambda0 = float(ratios[0] * mu[0][0] + ratios[1] * mu[1][0] + ratios[2] * mu[2][1])
    lambda1 = float(ratios[0] * mu[0][1] + ratios[1] * mu[1][1] + ratios[2] * mu[2][2])

    # A non-maximal sector is penalized by exactly the violated lambda inequality.
    standing_candidates: list[tuple[float, int, int]] = []
    standing_candidates.append((float(mu[2][1] - mu[2][0] + max(-lambda0, 0.0)), -1, 2))
    central_penalty = max(lambda0, 0.0) + max(-lambda1, 0.0)
    standing_candidates.extend(
        [
            (float(mu[0][1] - mu[0][0] + central_penalty), 0, 0),
            (float(mu[1][1] - mu[1][0] + central_penalty), 0, 1),
            (float(mu[2][2] - mu[2][1] + central_penalty), 0, 2),
        ]
    )
    upper_penalty = max(lambda1, 0.0)
    standing_candidates.extend(
        [
            (float(mu[1][2] - mu[1][1] + upper_penalty), 1, 1),
            (float(mu[2][3] - mu[2][2] + upper_penalty), 1, 2),
        ]
    )
    standing_residual, standing_sector, standing_domain = min(standing_candidates, key=lambda item: item[0])
    traveling_branch = 0 if abs(lambda0) <= abs(lambda1) else 1
    traveling_residual = min(abs(lambda0), abs(lambda1))
    return GBZDiagnostics(
        mu=mu,
        lambda0=lambda0,
        lambda1=lambda1,
        standing_residual=standing_residual,
        traveling_residual=float(traveling_residual),
        standing_sector=standing_sector,
        standing_domain=standing_domain,
        traveling_branch=traveling_branch,
    )


def classify_energies(energies: Iterable[complex], lengths: Sequence[int] = DOMAIN_LENGTHS) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    diagnostics = [gbz_diagnostics(complex(energy), lengths) for energy in energies]
    standing = np.asarray([item.standing_residual for item in diagnostics])
    traveling = np.asarray([item.traveling_residual for item in diagnostics])
    labels = np.where(standing <= traveling, "standing", "traveling")
    return labels, standing, traveling


def ronkin(domain: int, mu_value: np.ndarray | float, energy: complex) -> np.ndarray:
    """Jensen/root form of the single-domain Ronkin function."""
    mu_array = np.asarray(mu_value, dtype=float)
    root_mu = log_root_moduli(energy)[domain]
    leading_laurent = LAURENT_COEFFICIENTS[domain][-POLE_ORDERS[domain]]
    result = np.log(abs(leading_laurent)) - POLE_ORDERS[domain] * mu_array
    for breakpoint in root_mu:
        result = result + np.maximum(0.0, mu_array - breakpoint)
    return np.asarray(result, dtype=float)


def constrained_ronkin(mu1: np.ndarray | float, mu2: np.ndarray | float, energy: complex, lengths: Sequence[int] = DOMAIN_LENGTHS) -> np.ndarray:
    ratios = np.asarray(lengths, dtype=float) / float(sum(lengths))
    mu1_array = np.asarray(mu1, dtype=float)
    mu2_array = np.asarray(mu2, dtype=float)
    mu3_array = -(ratios[0] * mu1_array + ratios[1] * mu2_array) / ratios[2]
    return ratios[0] * ronkin(0, mu1_array, energy) + ratios[1] * ronkin(1, mu2_array, energy) + ratios[2] * ronkin(2, mu3_array, energy)


def constrained_ronkin_minimum(energy: complex, lengths: Sequence[int] = DOMAIN_LENGTHS) -> tuple[float, np.ndarray]:
    """Find the exact convex piecewise-linear minimum by vertex enumeration."""
    ratios = np.asarray(lengths, dtype=float) / float(sum(lengths))
    roots = log_root_moduli(energy)
    candidates: list[tuple[float, float, float]] = []
    for mu1 in roots[0]:
        for mu2 in roots[1]:
            mu3 = -(ratios[0] * mu1 + ratios[1] * mu2) / ratios[2]
            candidates.append((float(mu1), float(mu2), float(mu3)))
    for mu1 in roots[0]:
        for mu3 in roots[2]:
            mu2 = -(ratios[0] * mu1 + ratios[2] * mu3) / ratios[1]
            candidates.append((float(mu1), float(mu2), float(mu3)))
    for mu2 in roots[1]:
        for mu3 in roots[2]:
            mu1 = -(ratios[1] * mu2 + ratios[2] * mu3) / ratios[0]
            candidates.append((float(mu1), float(mu2), float(mu3)))
    values = np.asarray([constrained_ronkin(mu1, mu2, energy, lengths) for mu1, mu2, _ in candidates], dtype=float)
    index = int(np.argmin(values))
    return float(values[index]), np.asarray(candidates[index], dtype=float)


def scan_energy_grid(
    real_axis: np.ndarray,
    imag_axis: np.ndarray,
    lengths: Sequence[int] = DOMAIN_LENGTHS,
) -> dict[str, np.ndarray]:
    """Evaluate windings and GBZ residuals on a Cartesian energy grid."""
    real_axis = np.asarray(real_axis, dtype=float)
    imag_axis = np.asarray(imag_axis, dtype=float)
    shape = (imag_axis.size, real_axis.size)
    standing = np.empty(shape)
    traveling = np.empty(shape)
    lambda0 = np.empty(shape)
    lambda1 = np.empty(shape)
    delta2 = np.empty(shape, dtype=int)
    delta3 = np.empty(shape, dtype=int)
    for row, imag in enumerate(imag_axis):
        for column, real in enumerate(real_axis):
            energy = complex(real, imag)
            item = gbz_diagnostics(energy, lengths)
            standing[row, column] = item.standing_residual
            traveling[row, column] = item.traveling_residual
            lambda0[row, column] = item.lambda0
            lambda1[row, column] = item.lambda1
            domain_windings = [winding(domain, energy) for domain in range(3)]
            delta2[row, column] = domain_windings[2] - domain_windings[1]
            delta3[row, column] = domain_windings[0] - domain_windings[2]
    return {
        "real": real_axis,
        "imag": imag_axis,
        "standing_residual": standing,
        "traveling_residual": traveling,
        "lambda0": lambda0,
        "lambda1": lambda1,
        "delta2": delta2,
        "delta3": delta3,
    }


def representative_state_indices(values: np.ndarray, vectors: np.ndarray, lengths: Sequence[int] = DOMAIN_LENGTHS) -> dict[str, int]:
    """Select Fig. 2 representatives by topology/class and interface mass."""
    labels, standing_residual, traveling_residual = classify_energies(values, lengths)
    size = len(values)
    boundaries = (int(lengths[0] + lengths[1]), 0)
    sites = np.arange(size)
    probabilities = np.abs(vectors) ** 2
    selections: dict[str, int] = {}
    for interface_name, boundary in zip(("2|3", "3|1"), boundaries, strict=True):
        circular_distance = np.minimum((sites - boundary) % size, (boundary - sites) % size)
        mask = circular_distance <= 12
        interface_mass = probabilities[mask].sum(axis=0)
        for state_class, residual in (("standing", standing_residual), ("traveling", traveling_residual)):
            eligible = labels == state_class
            score = interface_mass / (0.015 + residual)
            score = np.where(eligible, score, -np.inf)
            selections[f"{interface_name}_{state_class}"] = int(np.argmax(score))
    return selections


def gbz_beta_points(energies: Sequence[complex], lengths: Sequence[int] = DOMAIN_LENGTHS) -> dict[str, np.ndarray]:
    """Return every domain-resolved characteristic branch on the DW spectrum.

    A single energy is generally multi-valued in beta.  Plotting all roots is
    essential for the far real branches in Fig. 3(g,h); selecting only the
    dominant root would silently discard part of the paper's GBZ object.
    """
    points: dict[str, list[complex]] = {f"domain_{domain + 1}": [] for domain in range(3)}
    labels: dict[str, list[str]] = {f"domain_{domain + 1}_class": [] for domain in range(3)}
    for energy in energies:
        item = gbz_diagnostics(complex(energy), lengths)
        roots = [characteristic_roots(domain, complex(energy)) for domain in range(3)]
        for domain in range(3):
            points[f"domain_{domain + 1}"].extend(roots[domain])
            labels[f"domain_{domain + 1}_class"].extend([item.classification] * roots[domain].size)
    output: dict[str, np.ndarray] = {}
    for key, value in points.items():
        output[key] = np.asarray(value, dtype=complex)
        output[f"{key}_class"] = np.asarray(labels[f"{key}_class"])
    return output


def constituent_obc_spectra(lengths: Sequence[int] = DOMAIN_LENGTHS) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    spectra: list[np.ndarray] = []
    for domain, length in enumerate(lengths):
        matrix = np.zeros((length, length), dtype=complex)
        for row in range(length):
            for displacement, hopping in LAURENT_COEFFICIENTS[domain].items():
                column = row + displacement
                if 0 <= column < length:
                    matrix[row, column] += hopping
        spectra.append(np.linalg.eigvals(matrix))
    return tuple(spectra)  # type: ignore[return-value]


def spectral_potential_from_eigenvalues(real_axis: np.ndarray, imag_axis: np.ndarray, values: np.ndarray, epsilon: float = 1e-7) -> np.ndarray:
    energies = np.asarray(real_axis)[None, :, None] + 1j * np.asarray(imag_axis)[:, None, None]
    distances = np.maximum(np.abs(energies - np.asarray(values)[None, None, :]), epsilon)
    return np.mean(np.log(distances), axis=2)


def spectral_potential_from_ronkin(real_axis: np.ndarray, imag_axis: np.ndarray, lengths: Sequence[int] = DOMAIN_LENGTHS) -> np.ndarray:
    potential = np.empty((len(imag_axis), len(real_axis)), dtype=float)
    for row, imag in enumerate(imag_axis):
        for column, real in enumerate(real_axis):
            potential[row, column] = constrained_ronkin_minimum(complex(real, imag), lengths)[0]
    return potential


def spectral_density(potential: np.ndarray, real_axis: np.ndarray, imag_axis: np.ndarray) -> np.ndarray:
    """Apply rho=(1/2pi) Delta_E Phi using a shared Cartesian stencil."""
    potential = np.asarray(potential, dtype=float)
    d_real = np.gradient(np.gradient(potential, np.asarray(real_axis), axis=1, edge_order=2), np.asarray(real_axis), axis=1, edge_order=2)
    d_imag = np.gradient(np.gradient(potential, np.asarray(imag_axis), axis=0, edge_order=2), np.asarray(imag_axis), axis=0, edge_order=2)
    return (d_real + d_imag) / (2.0 * np.pi)


def flux_spectra(fluxes: np.ndarray, lengths: Sequence[int] = DOMAIN_LENGTHS) -> np.ndarray:
    return np.asarray([np.linalg.eigvals(build_domain_wall_hamiltonian(lengths, periodic=True, flux=float(flux))) for flux in fluxes])


def flux_spectral_winding(base_energies: np.ndarray, spectra: np.ndarray, *, chunk_size: int = 128) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute determinant phase winding from precomputed flux spectra."""
    base = np.asarray(base_energies, dtype=complex).reshape(-1)
    winding_values = np.empty(base.size, dtype=float)
    residuals = np.empty(base.size, dtype=float)
    minimum_gaps = np.empty(base.size, dtype=float)
    for start in range(0, base.size, chunk_size):
        stop = min(start + chunk_size, base.size)
        batch = base[start:stop]
        differences = spectra[:, :, None] - batch[None, None, :]
        minimum_gaps[start:stop] = np.min(np.abs(differences), axis=(0, 1))
        summed_angles = np.sum(np.angle(differences), axis=1)
        wrapped_phase = np.angle(np.exp(1j * summed_angles))
        unwrapped = np.unwrap(wrapped_phase, axis=0)
        raw_winding = (unwrapped[-1] - unwrapped[0]) / (2.0 * np.pi)
        rounded = np.rint(raw_winding)
        winding_values[start:stop] = rounded
        residuals[start:stop] = np.abs(raw_winding - rounded)
    return winding_values.reshape(np.shape(base_energies)), residuals.reshape(np.shape(base_energies)), minimum_gaps.reshape(np.shape(base_energies))


def nearest_spectrum_distances(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    return np.min(np.abs(np.asarray(source)[:, None] - np.asarray(reference)[None, :]), axis=1)
