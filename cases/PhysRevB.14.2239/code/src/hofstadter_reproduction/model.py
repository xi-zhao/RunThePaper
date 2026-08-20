"""Harper-equation primitives derived directly from the printed paper."""

from __future__ import annotations

from functools import lru_cache
from math import gcd

import numpy as np


def harper_matrix(
    p: int,
    q: int,
    *,
    nu: float = 0.0,
    boundary_phase: float = 0.0,
) -> np.ndarray:
    """Return the q-periodic Harper matrix for alpha=p/q.

    The matrix implements

        g[m+1] + g[m-1] + 2 cos(2 pi p m/q - nu) g[m] = epsilon g[m]

    with a total Bloch phase ``boundary_phase`` across the q-site magnetic
    cell.  The construction handles q=1 and q=2 without dropping the two
    distinct nearest-neighbour bonds.
    """

    if q < 1 or not (0 <= p <= q) or gcd(p, q) != 1:
        raise ValueError("p/q must be a reduced fraction with q>=1")
    m = np.arange(q, dtype=float)
    matrix = np.diag(2.0 * np.cos(2.0 * np.pi * p * m / q - nu)).astype(complex)
    for site in range(q):
        neighbour = (site + 1) % q
        phase = np.exp(1j * boundary_phase) if site == q - 1 else 1.0
        matrix[site, neighbour] += phase
        matrix[neighbour, site] += np.conjugate(phase)
    return matrix


@lru_cache(maxsize=None)
def band_edges(p: int, q: int) -> tuple[tuple[float, float], ...]:
    """Return all q spectral bands using the two Chambers extrema.

    Hofstadter's trace-polynomial condition is equivalent to pairing the 2q
    roots obtained at opposite extrema of the two Bloch phases.  This avoids
    fitting or digitising the source plot and gives every band edge directly
    from the printed difference equation.
    """

    if p == 0 and q == 1:
        return ((-4.0, 4.0),)
    roots_a = np.linalg.eigvalsh(harper_matrix(p, q, nu=0.0, boundary_phase=0.0))
    roots_b = np.linalg.eigvalsh(
        harper_matrix(p, q, nu=np.pi / q, boundary_phase=np.pi)
    )
    roots = np.sort(np.concatenate([roots_a, roots_b])).real
    return tuple((float(roots[2 * i]), float(roots[2 * i + 1])) for i in range(q))


def transfer_trace(energy: float, p: int, q: int, *, nu: float | None = None) -> float:
    """Trace of the q-step transfer matrix used in the paper's band test."""

    phase = np.pi / (2.0 * q) if nu is None else float(nu)
    product = np.eye(2)
    for m in range(q):
        step = np.array(
            [
                [energy - 2.0 * np.cos(2.0 * np.pi * p * m / q - phase), -1.0],
                [1.0, 0.0],
            ]
        )
        product = step @ product
    return float(np.trace(product))


def largest_eigenpair(p: int, q: int) -> tuple[float, np.ndarray]:
    """Largest periodic eigenpair used by the paper's Fig. 6."""

    values, vectors = np.linalg.eigh(harper_matrix(p, q))
    vector = vectors[:, -1]
    phase = np.exp(-1j * np.angle(vector[np.argmax(np.abs(vector))]))
    vector = np.real_if_close(vector * phase).real
    if vector.sum() < 0:
        vector *= -1.0
    vector /= np.max(np.abs(vector))
    return float(values[-1]), vector


def reordered_wavefunction(p: int, q: int) -> dict[str, np.ndarray | float | int]:
    """Fold a rational wavefunction into the physical period P=1/alpha.

    The paper's order is m_j=j*p^{-1} (mod q).  With that ordering the
    coordinate within one magnetic period is x_j=j/p and x_j/P=j/q.
    """

    inverse = pow(p, -1, q)
    order = np.asarray([(j * inverse) % q for j in range(q)], dtype=int)
    energy, vector = largest_eigenpair(p, q)
    period = q / p
    x_over_period = np.arange(q, dtype=float) / q
    return {
        "p": p,
        "q": q,
        "period": period,
        "energy": energy,
        "order": order,
        "x": x_over_period * period,
        "x_over_period": x_over_period,
        "amplitude": vector[order],
    }
