"""1D exactly-solvable spin model of Wang & Hazzard, Eq. (Hamil1Dspin).

For the Ex.3 R-matrix R^{ab}_{cd} = -delta_{ac} delta_{bd}, the paper gives an
explicit nearest-neighbour spin chain on (m+1)-level sites with basis
|0>, {|1,b>}_{b=1..m} and on-site ladder operators

    y^+_a |0> = |1,a> ,   y^-_a |1,b> = delta_{ab} |0> ,   x^\pm_a = y^\pm_a ,

    H = sum_{i,a} J_i (x^+_{i,a} y^-_{i+1,a} + x^-_{i,a} y^+_{i+1,a})
        - sum_{i,a} mu_i  y^+_{i,a} y^-_{i,a} ,     open BC (J_N = 0).

The paper's central claim is that a generalized Jordan-Wigner transformation maps
this local spin Hamiltonian onto *free paraparticles* H = sum_{ij} h_{ij} e_{ij}
with the tridiagonal single-particle matrix h_{i,i+1}=h_{i+1,i}=J_i, h_{ii}=-mu_i.
Because the JWT is an algebra isomorphism, the many-body SPECTRUM of the spin
chain must equal the free-paraparticle spectrum built from the single-particle
levels {eps_k}=eig(h) and the Ex.3 exclusion statistics d=(1,m,0,0,...):

    spectrum = { sum_{k in S} eps_k : S subseteq {1..N} },  multiplicity m^{|S|}.

This module builds H by brute force and returns its exact spectrum, plus the
free-paraparticle prediction, so the two can be compared with zero fitting.  This
independently verifies both the emergent-free-paraparticle claim and the
single-mode partition function z_R(x)=1+m x used in Fig. 2.
"""
from __future__ import annotations

from itertools import combinations
import numpy as np


def onsite_operators(m: int) -> tuple[list[np.ndarray], np.ndarray]:
    """Return [y^+_1..y^+_m] and the on-site number operator, on the (m+1)-dim site.

    Basis order: index 0 -> |0>, index a (1..m) -> |1,a>.
    """
    dim = m + 1
    yplus = []
    for a in range(1, m + 1):
        op = np.zeros((dim, dim))
        op[a, 0] = 1.0  # <1,a| y^+_a |0> = 1
        yplus.append(op)
    n_site = np.zeros((dim, dim))
    for a in range(1, m + 1):
        n_site += yplus[a - 1] @ yplus[a - 1].T  # y^+_a y^-_a
    return yplus, n_site


def _embed(op: np.ndarray, site: int, n_sites: int, site_dim: int) -> np.ndarray:
    mats = [np.eye(site_dim)] * n_sites
    mats[site] = op
    out = mats[0]
    for k in range(1, n_sites):
        out = np.kron(out, mats[k])
    return out


def build_hamiltonian(J: np.ndarray, mu: np.ndarray, m: int) -> np.ndarray:
    """Full spin-chain H (dimension (m+1)^N) for the Ex.3 model. OBC: J[N-1] ignored."""
    n_sites = len(mu)
    site_dim = m + 1
    yplus, n_site = onsite_operators(m)
    yminus = [yp.T for yp in yplus]

    Yp = [[_embed(yplus[a], i, n_sites, site_dim) for a in range(m)] for i in range(n_sites)]
    Ym = [[_embed(yminus[a], i, n_sites, site_dim) for a in range(m)] for i in range(n_sites)]
    Nsite = [_embed(n_site, i, n_sites, site_dim) for i in range(n_sites)]

    H = np.zeros((site_dim**n_sites, site_dim**n_sites))
    for i in range(n_sites - 1):  # hopping, x=y for Ex.3
        for a in range(m):
            H += J[i] * (Yp[i][a] @ Ym[i + 1][a] + Ym[i][a] @ Yp[i + 1][a])
    for i in range(n_sites):  # on-site chemical potential
        H += -mu[i] * Nsite[i]
    return H


def number_operator(m: int, n_sites: int) -> np.ndarray:
    site_dim = m + 1
    _, n_site = onsite_operators(m)
    return sum(_embed(n_site, i, n_sites, site_dim) for i in range(n_sites))


def single_particle_matrix(J: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """Tridiagonal hopping matrix h of the emergent free paraparticles."""
    n = len(mu)
    h = np.diag(-mu.astype(float))
    for i in range(n - 1):
        h[i, i + 1] = h[i + 1, i] = J[i]
    return h


def free_paraparticle_spectrum(eps: np.ndarray, m: int) -> np.ndarray:
    """Ex.3 free-paraparticle many-body levels: sum_{k in S} eps_k, multiplicity m^{|S|}."""
    n = len(eps)
    levels = []
    for occ in range(n + 1):
        for S in combinations(range(n), occ):
            energy = float(sum(eps[k] for k in S))
            levels.extend([energy] * (m**occ))
    return np.sort(np.array(levels))
