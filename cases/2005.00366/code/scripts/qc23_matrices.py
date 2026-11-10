"""Equal-segment matrices for the source MS model, in time/T units."""
import os

for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[key] = "1"

import numpy as np
from scipy.linalg import toeplitz

from ion_chain_control import modes
from two_ion_gate import segment_integrals


def geometry(cfg, ions, addressed, trap):
    frequency, eta, z, error = modes(dict(ions=ions, transverse_com_hz=trap[:2],
        axial_com_hz=trap[2], ion_mass_amu=cfg["mass_amu"], wavelength_m=cfg["wavelength_m"]))
    return frequency, eta[addressed], z, error


def matrices(frequency, eta, laser, duration, segments, pairs):
    """D and C are the closure and normalized centroid. Q gives pairwise phase."""
    theta = (2*np.pi*duration)*(frequency-laser)
    z, first, triangle = map(np.array, zip(*(segment_integrals(t, segments) for t in theta)))
    d = z/2
    centroid = (z-first)/2
    # The triangular integral of equal segments depends on their separation.
    # For s>r, the Hermitian lower diagonal is i*e^{-i theta (s-r)/S}|z_s|^2/4.
    lower = 0.25j * abs(z[:, :1])**2 * np.exp(-1j * theta[:,None] * np.arange(segments)/segments)
    lower[:,0] = triangle/2
    columns = np.einsum("ap,ap,ps->as",eta[pairs[:,0]],eta[pairs[:,1]],lower)
    return d,centroid,np.array([toeplitz(c) for c in columns]),theta


def physical_error(phase_error, coupled_displacements, pairs, occupation):
    """Stable exact thermal spin trace under the source's common-axis model."""
    phase_error = (phase_error+np.pi/2) % np.pi-np.pi/2
    n = len(coupled_displacements)
    binary = (np.arange(2**n)[:, None] >> np.arange(n)) & 1
    signs = 1-2*binary
    phase = np.einsum("sp,p->s",signs[:,pairs[:,0]] * signs[:,pairs[:,1]],phase_error)
    decay = (occupation+0.5)*np.sum(abs(np.einsum("sj,jp->sp",signs,coupled_displacements))**2,axis=1)
    loss = np.mean(-np.expm1(-decay) + np.exp(-decay)*2*np.sin(phase/2)**2)
    imaginary = np.mean(np.exp(-decay)*np.sin(phase))
    return float(max(0,2*loss-loss**2-imaginary**2))


def reflected(u, robust):
    return np.r_[u,u[::-1].conj()] if robust else u
