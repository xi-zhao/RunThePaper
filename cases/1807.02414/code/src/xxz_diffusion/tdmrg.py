"""Independent purification-TEBD implementation for the XXZ tDMRG markers.

The paper starts from a mixed, infinite-temperature domain wall.  We represent
``sqrt(rho_0)`` as a product purification with one ancilla qubit per physical
spin and evolve only the physical legs.  Grouping a physical spin and its
ancilla into one four-state MPS site turns the calculation into ordinary
two-site TEBD.  No author tensor-network code or numerical arrays are used.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .backend import array_module, to_numpy


@dataclass
class EvolutionDiagnostics:
    """Accumulated truncation and normalization diagnostics."""

    two_site_updates: int = 0
    total_discarded_weight: float = 0.0
    maximum_discarded_weight: float = 0.0
    maximum_bond_reached: int = 1

    def record(self, discarded_weight: float, kept_bond: int) -> None:
        self.two_site_updates += 1
        self.total_discarded_weight += float(discarded_weight)
        self.maximum_discarded_weight = max(
            self.maximum_discarded_weight, float(discarded_weight)
        )
        self.maximum_bond_reached = max(self.maximum_bond_reached, int(kept_bond))

    def as_dict(self) -> dict[str, float | int]:
        return {
            "two_site_updates": self.two_site_updates,
            "total_discarded_weight": self.total_discarded_weight,
            "maximum_discarded_weight": self.maximum_discarded_weight,
            "maximum_bond_reached": self.maximum_bond_reached,
        }


def xxz_two_site_hamiltonian(delta: float) -> np.ndarray:
    """Printed paper Hamiltonian on one bond.

    The convention follows the paper literally:

    ``S+ S- + S- S+ + (Delta/2) Sz Sz``

    with spin-1/2 operators ``Sz=diag(1/2,-1/2)``.
    """

    raising = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
    lowering = raising.T.conj()
    sz = np.diag([0.5, -0.5]).astype(complex)
    return (
        np.kron(raising, lowering)
        + np.kron(lowering, raising)
        + 0.5 * float(delta) * np.kron(sz, sz)
    )


def physical_two_site_gate(delta: float, time_step: float) -> np.ndarray:
    """Exact two-spin gate obtained by diagonalizing the 4x4 bond Hamiltonian."""

    hamiltonian = xxz_two_site_hamiltonian(delta)
    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
    unitary = (eigenvectors * np.exp(-1j * float(time_step) * eigenvalues)) @ eigenvectors.T.conj()
    return unitary.reshape(2, 2, 2, 2)


def purified_two_site_gate(delta: float, time_step: float, backend: str = "numpy"):
    """Lift a physical two-spin gate to grouped physical+ancilla MPS sites."""

    xp = array_module(backend)
    physical = physical_two_site_gate(delta, time_step)
    lifted = np.zeros((4, 4, 4, 4), dtype=complex)
    for out_p_left in range(2):
        for out_p_right in range(2):
            for in_p_left in range(2):
                for in_p_right in range(2):
                    amplitude = physical[
                        out_p_left, out_p_right, in_p_left, in_p_right
                    ]
                    for ancilla_left in range(2):
                        for ancilla_right in range(2):
                            out_left = 2 * out_p_left + ancilla_left
                            out_right = 2 * out_p_right + ancilla_right
                            in_left = 2 * in_p_left + ancilla_left
                            in_right = 2 * in_p_right + ancilla_right
                            lifted[out_left, out_right, in_left, in_right] = amplitude
    return xp.asarray(lifted)


def initial_domain_wall_purification(
    chain_length: int,
    mu: float,
    *,
    backend: str = "numpy",
) -> list[Any]:
    """Build the product purification of the weak domain-wall density matrix."""

    if chain_length < 2 or chain_length % 2:
        raise ValueError("chain_length must be an even integer >= 2")
    xp = array_module(backend)
    sz_values = np.array([0.5, -0.5])
    tensors: list[Any] = []
    for site in range(chain_length):
        field = float(mu) if site < chain_length // 2 else -float(mu)
        probabilities = np.exp(field * sz_values)
        probabilities /= probabilities.sum()
        local = np.zeros(4, dtype=complex)
        local[0] = np.sqrt(probabilities[0])  # |up physical, up ancilla>
        local[3] = np.sqrt(probabilities[1])  # |down physical, down ancilla>
        tensors.append(xp.asarray(local.reshape(1, 4, 1)))
    return tensors


def apply_two_site_gate(
    tensors: list[Any],
    bond: int,
    gate: Any,
    *,
    max_bond: int,
    relative_cutoff: float,
) -> tuple[float, int]:
    """Apply and truncate one two-site gate, returning discarded weight and rank."""

    if bond < 0 or bond + 1 >= len(tensors):
        raise IndexError(f"bond {bond} is outside a chain of length {len(tensors)}")
    xp = array_module("cupy" if type(tensors[bond]).__module__.startswith("cupy") else "numpy")
    left = tensors[bond]
    right = tensors[bond + 1]
    theta = xp.einsum("aib,bjc->aijc", left, right, optimize=True)
    theta = xp.einsum("IJij,aijc->aIJc", gate, theta, optimize=True)
    left_bond, local_left, local_right, right_bond = theta.shape
    matrix = theta.reshape(left_bond * local_left, local_right * right_bond)
    u_matrix, singular_values, vh_matrix = xp.linalg.svd(matrix, full_matrices=False)
    host_singular_values = to_numpy(singular_values)
    if host_singular_values.size == 0:
        raise RuntimeError("two-site SVD returned no singular values")
    threshold = max(0.0, float(relative_cutoff)) * float(host_singular_values[0])
    above_cutoff = int(np.count_nonzero(host_singular_values > threshold))
    kept = max(1, min(int(max_bond), above_cutoff))
    squared = np.square(host_singular_values)
    denominator = float(squared.sum())
    discarded_weight = (
        float(squared[kept:].sum() / denominator) if denominator > 0.0 else 0.0
    )

    u_matrix = u_matrix[:, :kept]
    singular_values = singular_values[:kept]
    vh_matrix = vh_matrix[:kept, :]
    tensors[bond] = u_matrix.reshape(left_bond, local_left, kept)
    tensors[bond + 1] = (singular_values[:, None] * vh_matrix).reshape(
        kept, local_right, right_bond
    )
    return discarded_weight, kept


def mps_norm(tensors: list[Any]) -> float:
    """Contract the purification norm."""

    xp = array_module("cupy" if type(tensors[0]).__module__.startswith("cupy") else "numpy")
    environment = xp.ones((1, 1), dtype=complex)
    for tensor in tensors:
        environment = xp.einsum(
            "ab,aic,bid->cd", environment, tensor.conj(), tensor, optimize=True
        )
    return float(np.real(to_numpy(environment).item()))


def magnetization_profile(tensors: list[Any]) -> np.ndarray:
    """Evaluate physical ``Sz`` at every site using left/right environments."""

    xp = array_module("cupy" if type(tensors[0]).__module__.startswith("cupy") else "numpy")
    local_sz = xp.asarray(np.diag([0.5, 0.5, -0.5, -0.5]).astype(complex))
    left_environments = [xp.ones((1, 1), dtype=complex)]
    for tensor in tensors:
        left_environments.append(
            xp.einsum(
                "ab,aic,bid->cd",
                left_environments[-1],
                tensor.conj(),
                tensor,
                optimize=True,
            )
        )
    right_environments: list[Any] = [None] * (len(tensors) + 1)
    right_environments[-1] = xp.ones((1, 1), dtype=complex)
    for site in range(len(tensors) - 1, -1, -1):
        tensor = tensors[site]
        right_environments[site] = xp.einsum(
            "aic,bid,cd->ab",
            tensor.conj(),
            tensor,
            right_environments[site + 1],
            optimize=True,
        )
    norm = float(np.real(to_numpy(left_environments[-1]).item()))
    if norm <= 0.0:
        raise RuntimeError("purification has non-positive norm")
    values = []
    for site, tensor in enumerate(tensors):
        expectation = xp.einsum(
            "ab,aic,ij,bjd,cd->",
            left_environments[site],
            tensor.conj(),
            local_sz,
            tensor,
            right_environments[site + 1],
            optimize=True,
        )
        values.append(float(np.real(to_numpy(expectation).item())) / norm)
    return np.asarray(values)


def save_checkpoint(
    path: Path,
    tensors: list[Any],
    *,
    step: int,
    time: float,
    diagnostics: EvolutionDiagnostics,
    metadata: dict[str, Any],
    snapshots: dict[float, np.ndarray] | None = None,
    norms: dict[float, float] | None = None,
) -> None:
    """Write a resumable, self-describing MPS checkpoint."""

    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {f"tensor_{index:04d}": to_numpy(tensor) for index, tensor in enumerate(tensors)}
    snapshot_items = sorted((snapshots or {}).items())
    for index, (_, values) in enumerate(snapshot_items):
        arrays[f"snapshot_{index:04d}"] = np.asarray(values)
    payload = {
        "schema_version": 1,
        "step": int(step),
        "time": float(time),
        "tensor_count": len(tensors),
        "diagnostics": diagnostics.as_dict(),
        "metadata": metadata,
        "snapshot_times": [time for time, _ in snapshot_items],
        "snapshot_norms": {
            str(time): float((norms or {}).get(time, np.nan)) for time, _ in snapshot_items
        },
    }
    temporary = path.with_name(f".{path.name}.tmp.npz")
    np.savez_compressed(temporary, metadata_json=np.asarray(json.dumps(payload)), **arrays)
    temporary.replace(path)


def load_checkpoint(
    path: Path, *, backend: str = "numpy"
) -> tuple[list[Any], dict[str, Any], dict[float, np.ndarray], dict[float, float]]:
    """Load a checkpoint onto the selected execution backend."""

    xp = array_module(backend)
    with np.load(path, allow_pickle=False) as archive:
        payload = json.loads(str(archive["metadata_json"].item()))
        count = int(payload["tensor_count"])
        tensors = [xp.asarray(archive[f"tensor_{index:04d}"]) for index in range(count)]
        snapshot_times = [float(value) for value in payload.get("snapshot_times", [])]
        snapshots = {
            time: np.asarray(archive[f"snapshot_{index:04d}"])
            for index, time in enumerate(snapshot_times)
        }
        stored_norms = payload.get("snapshot_norms", {})
        norms = {time: float(stored_norms[str(time)]) for time in snapshot_times}
    return tensors, payload, snapshots, norms


def _tebd_layer(
    tensors: list[Any],
    bonds: Iterable[int],
    gate: Any,
    *,
    max_bond: int,
    relative_cutoff: float,
    diagnostics: EvolutionDiagnostics,
) -> None:
    for bond in bonds:
        discarded_weight, kept = apply_two_site_gate(
            tensors,
            int(bond),
            gate,
            max_bond=max_bond,
            relative_cutoff=relative_cutoff,
        )
        diagnostics.record(discarded_weight, kept)


def evolve_domain_wall(
    *,
    chain_length: int,
    delta: float,
    mu: float,
    time_step: float,
    times: list[float],
    max_bond: int,
    relative_cutoff: float,
    backend: str = "numpy",
    checkpoint_path: Path | None = None,
    checkpoint_every_steps: int = 0,
    resume: bool = False,
    checkpoint_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run second-order TEBD and retain only requested magnetization snapshots."""

    if time_step <= 0.0:
        raise ValueError("time_step must be positive")
    if max_bond < 1:
        raise ValueError("max_bond must be positive")
    sorted_times = sorted(float(value) for value in times)
    if not sorted_times or sorted_times[0] <= 0.0:
        raise ValueError("times must contain positive values")
    target_steps: dict[int, float] = {}
    for target_time in sorted_times:
        step_float = target_time / float(time_step)
        step = int(round(step_float))
        if abs(step_float - step) > 1.0e-9:
            raise ValueError(f"time {target_time} is not an integer multiple of dt={time_step}")
        target_steps[step] = target_time

    diagnostics = EvolutionDiagnostics()
    current_step = 0
    current_time = 0.0
    metadata = dict(checkpoint_metadata or {})
    snapshots: dict[float, np.ndarray] = {}
    norms: dict[float, float] = {}
    if resume and checkpoint_path is not None and checkpoint_path.exists():
        tensors, checkpoint, snapshots, norms = load_checkpoint(
            checkpoint_path, backend=backend
        )
        current_step = int(checkpoint["step"])
        current_time = float(checkpoint["time"])
        stored_metadata = checkpoint.get("metadata", {})
        mismatched_metadata = {
            key: {"expected": value, "stored": stored_metadata.get(key)}
            for key, value in metadata.items()
            if stored_metadata.get(key) != value
        }
        if mismatched_metadata:
            raise ValueError(
                "checkpoint metadata does not match the selected run contract: "
                f"{mismatched_metadata}"
            )
        stored = checkpoint.get("diagnostics", {})
        diagnostics = EvolutionDiagnostics(
            two_site_updates=int(stored.get("two_site_updates", 0)),
            total_discarded_weight=float(stored.get("total_discarded_weight", 0.0)),
            maximum_discarded_weight=float(stored.get("maximum_discarded_weight", 0.0)),
            maximum_bond_reached=int(stored.get("maximum_bond_reached", 1)),
        )
        if len(tensors) != chain_length:
            raise ValueError("checkpoint chain length does not match the selected variant")
    else:
        tensors = initial_domain_wall_purification(chain_length, mu, backend=backend)

    half_gate = purified_two_site_gate(delta, 0.5 * time_step, backend=backend)
    full_gate = purified_two_site_gate(delta, time_step, backend=backend)
    even_bonds = range(0, chain_length - 1, 2)
    odd_bonds = range(1, chain_length - 1, 2)
    last_step = max(target_steps)
    while current_step < last_step:
        _tebd_layer(
            tensors,
            even_bonds,
            half_gate,
            max_bond=max_bond,
            relative_cutoff=relative_cutoff,
            diagnostics=diagnostics,
        )
        _tebd_layer(
            tensors,
            odd_bonds,
            full_gate,
            max_bond=max_bond,
            relative_cutoff=relative_cutoff,
            diagnostics=diagnostics,
        )
        _tebd_layer(
            tensors,
            even_bonds,
            half_gate,
            max_bond=max_bond,
            relative_cutoff=relative_cutoff,
            diagnostics=diagnostics,
        )
        current_step += 1
        current_time = current_step * float(time_step)
        if current_step in target_steps:
            target_time = target_steps[current_step]
            snapshots[target_time] = magnetization_profile(tensors)
            norms[target_time] = mps_norm(tensors)
        if (
            checkpoint_path is not None
            and checkpoint_every_steps > 0
            and current_step % int(checkpoint_every_steps) == 0
        ):
            save_checkpoint(
                checkpoint_path,
                tensors,
                step=current_step,
                time=current_time,
                diagnostics=diagnostics,
                metadata=metadata,
                snapshots=snapshots,
                norms=norms,
            )

    if checkpoint_path is not None:
        save_checkpoint(
            checkpoint_path,
            tensors,
            step=current_step,
            time=current_time,
            diagnostics=diagnostics,
            metadata=metadata,
            snapshots=snapshots,
            norms=norms,
        )
    missing = sorted(set(sorted_times) - set(snapshots))
    if missing:
        raise RuntimeError(
            "requested snapshots precede the resume checkpoint or were not generated: "
            f"{missing}"
        )
    return {
        "times": np.asarray(sorted_times),
        "magnetization": np.stack([snapshots[time] for time in sorted_times]),
        "norms": np.asarray([norms[time] for time in sorted_times]),
        "diagnostics": diagnostics.as_dict(),
        "final_step": current_step,
        "final_time": current_time,
    }
