"""Hamiltonian projection and self-energy assembly for ibDET."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

ComplexArray = NDArray[np.complex128]


def project_two_body(eri: ComplexArray, rotation: ComplexArray) -> ComplexArray:
    """Transform chemist-ordered (pq|rs) integrals into the embedding basis."""

    tensor = np.asarray(eri, dtype=np.complex128)
    transform = np.asarray(rotation, dtype=np.complex128)
    return np.einsum(
        "pi,qj,rk,sl,pqrs->ijkl",
        transform.conj(),
        transform,
        transform.conj(),
        transform,
        tensor,
        optimize=True,
    )


def hf_self_energy(density: ComplexArray, eri: ComplexArray) -> ComplexArray:
    """Evaluate the Hartree-Fock contraction printed in Eq. (2)."""

    gamma = np.asarray(density, dtype=np.complex128)
    tensor = np.asarray(eri, dtype=np.complex128)
    coulomb = np.einsum("kl,ijlk->ij", gamma, tensor, optimize=True)
    exchange = np.einsum("kl,iklj->ij", gamma, tensor, optimize=True)
    return coulomb - 0.5 * exchange


def remove_hf_self_energy(
    embedded_fock: ComplexArray,
    embedded_density: ComplexArray,
    embedded_eri: ComplexArray,
) -> ComplexArray:
    """Return the one-body matrix F-tilde from Eq. (2)."""

    return np.asarray(embedded_fock) - hf_self_energy(embedded_density, embedded_eri)


def project_hamiltonian(
    full_fock: ComplexArray,
    full_density: ComplexArray,
    full_eri: ComplexArray,
    rotation: ComplexArray,
) -> dict[str, ComplexArray]:
    """Project F, gamma and ERI, then remove the embedded HF contribution."""

    transform = np.asarray(rotation, dtype=np.complex128)
    fock = transform.conj().T @ np.asarray(full_fock) @ transform
    density = transform.conj().T @ np.asarray(full_density) @ transform
    eri = project_two_body(full_eri, transform)
    one_body = remove_hf_self_energy(fock, density, eri)
    return {
        "fock": np.asarray(fock, dtype=np.complex128),
        "density": np.asarray(density, dtype=np.complex128),
        "eri": np.asarray(eri, dtype=np.complex128),
        "one_body": np.asarray(one_body, dtype=np.complex128),
    }


def rotate_self_energy(
    rotation: ComplexArray, embedded_sigma: ComplexArray
) -> ComplexArray:
    """Apply Eq. (3) for either one frequency or a frequency stack."""

    transform = np.asarray(rotation, dtype=np.complex128)
    sigma = np.asarray(embedded_sigma, dtype=np.complex128)
    if sigma.ndim == 2:
        return transform @ sigma @ transform.conj().T
    if sigma.ndim == 3:
        return np.einsum(
            "pi,wij,qj->wpq",
            transform,
            sigma,
            transform.conj(),
            optimize=True,
        )
    raise ValueError("embedded_sigma must be a matrix or frequency stack")


def democratic_assembly(
    self_energies: Sequence[ComplexArray],
    weights: Sequence[ComplexArray],
) -> ComplexArray:
    """Average overlapping full-space blocks using explicit democratic weights."""

    if not self_energies or len(self_energies) != len(weights):
        raise ValueError("self_energies and weights must be nonempty and aligned")
    numerator = np.zeros_like(np.asarray(self_energies[0]), dtype=np.complex128)
    denominator = np.zeros_like(np.asarray(weights[0]), dtype=float)
    for sigma, weight in zip(self_energies, weights, strict=True):
        w = np.asarray(weight, dtype=float)
        if sigma.ndim == 3 and w.ndim == 2:
            numerator += np.asarray(sigma) * w[None, :, :]
        else:
            numerator += np.asarray(sigma) * w
        denominator += w
    if np.any(denominator <= 0):
        raise ValueError("democratic weights leave uncovered matrix elements")
    if numerator.ndim == 3:
        return numerator / denominator[None, :, :]
    return numerator / denominator


def combine_gw_ibdet(
    full_gw: ComplexArray,
    embedded_cc: ComplexArray,
    embedded_gw: ComplexArray,
) -> ComplexArray:
    """Apply the GW+ibDET subtraction identity in Eq. (4)."""

    arrays = [
        np.asarray(value, dtype=np.complex128)
        for value in (full_gw, embedded_cc, embedded_gw)
    ]
    if arrays[0].shape != arrays[1].shape or arrays[0].shape != arrays[2].shape:
        raise ValueError("all self-energy tensors must share basis and frequency shape")
    return arrays[0] + arrays[1] - arrays[2]


def local_only_correction(
    correction: ComplexArray,
    atom_labels: Sequence[int],
) -> ComplexArray:
    """Zero interatomic blocks while preserving every same-atom matrix block."""

    sigma = np.asarray(correction, dtype=np.complex128).copy()
    labels = np.asarray(atom_labels, dtype=int)
    if sigma.shape[-1] != labels.size or sigma.shape[-2] != labels.size:
        raise ValueError("atom_labels do not match correction basis")
    mask = labels[:, None] == labels[None, :]
    if sigma.ndim == 2:
        sigma *= mask
    elif sigma.ndim == 3:
        sigma *= mask[None, :, :]
    else:
        raise ValueError("correction must be a matrix or frequency stack")
    return sigma


def real_to_momentum(
    real_space: ComplexArray,
    lattice_vectors: NDArray[np.float64],
    k_points: NDArray[np.float64],
) -> ComplexArray:
    """Fourier transform Sigma(R,omega) to Sigma(k,omega)."""

    values = np.asarray(real_space, dtype=np.complex128)
    vectors = np.asarray(lattice_vectors, dtype=float)
    points = np.asarray(k_points, dtype=float)
    phase = np.exp(-1j * points @ vectors.T)
    return np.einsum("kr,rwij->kwij", phase, values, optimize=True)


def momentum_to_real(
    momentum_space: ComplexArray,
    lattice_vectors: NDArray[np.float64],
    k_points: NDArray[np.float64],
) -> ComplexArray:
    """Inverse transform on a complete mutually dual finite grid."""

    values = np.asarray(momentum_space, dtype=np.complex128)
    vectors = np.asarray(lattice_vectors, dtype=float)
    points = np.asarray(k_points, dtype=float)
    phase = np.exp(1j * points @ vectors.T)
    return np.einsum("kr,kwij->rwij", phase, values, optimize=True) / points.shape[0]
