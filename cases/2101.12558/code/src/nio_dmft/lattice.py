"""Layered p-d lattice construction and multi-site Dyson operations.

The compact model in this module is an independent method-validation object.
It tests the same projection, layer indexing, surface coordination, and Dyson
algebra used by the paper-scale path; it is never presented as NiO data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LayeredPDModel:
    """Spin-degenerate layered p-d Hamiltonian sampled on a 1D k path."""

    orientation: str
    relaxed: bool
    kpoints: np.ndarray
    hamiltonian_k: np.ndarray
    layer_orbitals: tuple[tuple[int, int], ...]
    correlated_indices: tuple[int, ...]

    @property
    def n_layers(self) -> int:
        return len(self.layer_orbitals)

    @property
    def n_orbitals(self) -> int:
        return self.hamiltonian_k.shape[-1]

    def validate(self, *, tolerance: float = 1e-12) -> None:
        if self.orientation not in {"001", "110"}:
            raise ValueError(f"unsupported orientation: {self.orientation}")
        if self.hamiltonian_k.ndim != 3:
            raise ValueError("hamiltonian_k must have shape (nk, norb, norb)")
        nk, rows, cols = self.hamiltonian_k.shape
        if nk != self.kpoints.size or rows != cols:
            raise ValueError("inconsistent k-grid or Hamiltonian dimensions")
        if rows != 2 * self.n_layers:
            raise ValueError("each layer must contain one d and one p orbital")
        error = float(
            np.max(
                np.abs(
                    self.hamiltonian_k - np.swapaxes(self.hamiltonian_k.conj(), -1, -2)
                )
            )
        )
        if error > tolerance:
            raise ValueError(f"Hamiltonian is not Hermitian: {error:.3e}")


def build_layered_pd_model(
    *,
    orientation: str,
    n_layers: int,
    relaxed: bool,
    nk: int,
    epsilon_d: float,
    epsilon_p: float,
    inplane_d_hopping: float,
    inplane_p_hopping: float,
    interlayer_d_hopping: float,
    interlayer_p_hopping: float,
    pd_hybridization: float,
    surface_coordination: float,
    surface_crystal_field: float,
    relaxation_scale: float,
) -> LayeredPDModel:
    """Build a symmetric finite slab with one correlated d and one p orbital.

    Surface modifications are applied to both ends. The ``110`` lane receives
    a stronger coordination reduction, reflecting the orientation logic to be
    tested rather than fitting any paper curve.
    """

    if orientation not in {"001", "110"}:
        raise ValueError("orientation must be '001' or '110'")
    if n_layers < 3 or nk < 3:
        raise ValueError("at least three layers and three k-points are required")
    if not 0.0 < surface_coordination <= 1.0:
        raise ValueError("surface_coordination must lie in (0, 1]")

    kpoints = np.linspace(-np.pi, np.pi, nk, endpoint=False)
    n_orbitals = 2 * n_layers
    hamiltonian = np.zeros((nk, n_orbitals, n_orbitals), dtype=np.complex128)
    layer_orbitals = tuple((2 * layer, 2 * layer + 1) for layer in range(n_layers))
    correlated = tuple(pair[0] for pair in layer_orbitals)
    orientation_factor = 0.78 if orientation == "110" else 1.0
    surface_factor = surface_coordination * orientation_factor
    relaxed_shift = relaxation_scale if relaxed else 0.0

    for k_index, k_value in enumerate(kpoints):
        for layer, (d_index, p_index) in enumerate(layer_orbitals):
            at_surface = layer in {0, n_layers - 1}
            coordination = surface_factor if at_surface else 1.0
            crystal_shift = surface_crystal_field + relaxed_shift if at_surface else 0.0
            hamiltonian[k_index, d_index, d_index] = (
                epsilon_d
                + crystal_shift
                + 2.0 * inplane_d_hopping * coordination * np.cos(k_value)
            )
            hamiltonian[k_index, p_index, p_index] = (
                epsilon_p
                - 0.35 * crystal_shift
                + 2.0 * inplane_p_hopping * coordination * np.cos(k_value)
            )
            hybridization = pd_hybridization * np.sqrt(coordination)
            hamiltonian[k_index, d_index, p_index] = hybridization
            hamiltonian[k_index, p_index, d_index] = hybridization

        for layer in range(n_layers - 1):
            d_left, p_left = layer_orbitals[layer]
            d_right, p_right = layer_orbitals[layer + 1]
            boundary_bond = layer in {0, n_layers - 2}
            bond_scale = (1.0 + relaxed_shift) if relaxed and boundary_bond else 1.0
            hamiltonian[k_index, d_left, d_right] = interlayer_d_hopping * bond_scale
            hamiltonian[k_index, d_right, d_left] = interlayer_d_hopping * bond_scale
            hamiltonian[k_index, p_left, p_right] = interlayer_p_hopping * bond_scale
            hamiltonian[k_index, p_right, p_left] = interlayer_p_hopping * bond_scale

    model = LayeredPDModel(
        orientation=orientation,
        relaxed=relaxed,
        kpoints=kpoints,
        hamiltonian_k=hamiltonian,
        layer_orbitals=layer_orbitals,
        correlated_indices=correlated,
    )
    model.validate()
    return model


def matsubara_frequencies(beta: float, n_iw: int) -> np.ndarray:
    """Positive fermionic Matsubara frequencies."""

    if beta <= 0.0 or n_iw < 1:
        raise ValueError("beta and n_iw must be positive")
    return (2 * np.arange(n_iw) + 1) * np.pi / beta


def embed_layer_self_energy(
    model: LayeredPDModel,
    layer_sigma: np.ndarray,
) -> np.ndarray:
    """Embed one scalar d self-energy per layer into the orbital matrix."""

    array = np.asarray(layer_sigma, dtype=np.complex128)
    if array.ndim != 2 or array.shape[1] != model.n_layers:
        raise ValueError("layer_sigma must have shape (n_frequency, n_layers)")
    result = np.zeros(
        (array.shape[0], model.n_orbitals, model.n_orbitals),
        dtype=np.complex128,
    )
    for layer, orbital in enumerate(model.correlated_indices):
        result[:, orbital, orbital] = array[:, layer]
    return result


def lattice_green_function(
    model: LayeredPDModel,
    z: np.ndarray,
    layer_sigma: np.ndarray,
    *,
    chemical_potential: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return k-resolved and k-averaged interacting Green functions."""

    frequencies = np.asarray(z, dtype=np.complex128)
    embedded_sigma = embed_layer_self_energy(model, layer_sigma)
    if frequencies.ndim != 1 or frequencies.size != embedded_sigma.shape[0]:
        raise ValueError("frequency and self-energy dimensions differ")
    identity = np.eye(model.n_orbitals, dtype=np.complex128)
    green_k = np.empty(
        (frequencies.size, model.kpoints.size, model.n_orbitals, model.n_orbitals),
        dtype=np.complex128,
    )
    for omega_index, omega in enumerate(frequencies):
        for k_index, hamiltonian in enumerate(model.hamiltonian_k):
            inverse = (
                (omega + chemical_potential) * identity
                - hamiltonian
                - embedded_sigma[omega_index]
            )
            green_k[omega_index, k_index] = np.linalg.inv(inverse)
    return green_k, np.mean(green_k, axis=1)


def layer_diagonal(
    model: LayeredPDModel,
    local_green: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract d and p diagonal components for every layer."""

    if local_green.ndim != 3 or local_green.shape[1:] != (
        model.n_orbitals,
        model.n_orbitals,
    ):
        raise ValueError("local_green has an incompatible shape")
    d_values = np.column_stack(
        [local_green[:, d_index, d_index] for d_index, _ in model.layer_orbitals]
    )
    p_values = np.column_stack(
        [local_green[:, p_index, p_index] for _, p_index in model.layer_orbitals]
    )
    return d_values, p_values
