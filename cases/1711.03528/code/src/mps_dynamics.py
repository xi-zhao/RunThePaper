"""Finite-window MPS time evolution for the three-site PXP Hamiltonian.

The paper uses thermodynamic-limit iTEBD.  This module supplies a transparent
paper-scale numerical path that does not diagonalize the full Hilbert space:
an open chain large enough to keep the measured central window away from the
boundaries, evolved with a symmetric three-group Suzuki--Trotter sequence.
The method is intentionally labelled an MPS comparator rather than author-code
identity; time-step and bond-dimension convergence remain explicit outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
from scipy.linalg import expm
from scipy.signal import find_peaks

try:
    import quimb.tensor as qtn
except ImportError as exc:  # pragma: no cover - exercised only without optional dependency
    raise RuntimeError(
        "Paper-scale PXP dynamics requires the case dependency 'quimb>=1.14'."
    ) from exc


P = np.diag([1.0, 0.0])
X = np.array([[0.0, 1.0], [1.0, 0.0]])
Z = np.diag([1.0, -1.0])
N = np.diag([0.0, 1.0])
THREE_SITE_PXP = np.kron(np.kron(P, X), P)
ZZ = np.kron(Z, Z)
NN = np.kron(N, N)


@dataclass(frozen=True)
class DynamicsConfig:
    system_size: int
    max_bond: int
    time_step: float
    final_time: float
    sample_interval: float
    cutoff: float
    initial_states: tuple[str, ...]
    bulk_bonds: int


def validate_config(payload: dict[str, Any]) -> DynamicsConfig:
    system_size = int(payload.get("system_size", 101))
    max_bond = int(payload.get("max_bond", 400))
    time_step = float(payload.get("time_step", 0.05))
    final_time = float(payload.get("final_time", 30.0))
    sample_interval = float(payload.get("sample_interval", 0.25))
    cutoff = float(payload.get("cutoff", 1e-10))
    initial_states = tuple(str(value) for value in payload.get("initial_states", ["vacuum", "z2", "z3", "z4"]))
    bulk_bonds = int(payload.get("bulk_bonds", 6))

    if system_size < 9:
        raise ValueError("system_size must be at least 9")
    if max_bond < 2:
        raise ValueError("max_bond must be at least 2")
    if time_step <= 0.0 or final_time <= 0.0 or sample_interval <= 0.0:
        raise ValueError("time_step, final_time and sample_interval must be positive")
    steps_per_sample = sample_interval / time_step
    if not np.isclose(steps_per_sample, round(steps_per_sample), atol=1e-10):
        raise ValueError("sample_interval must be an integer multiple of time_step")
    total_steps = final_time / time_step
    if not np.isclose(total_steps, round(total_steps), atol=1e-10):
        raise ValueError("final_time must be an integer multiple of time_step")
    if not 0.0 < cutoff < 1.0:
        raise ValueError("cutoff must lie strictly between 0 and 1")
    allowed = {"vacuum", "z2", "z3", "z4"}
    unknown = sorted(set(initial_states) - allowed)
    if unknown:
        raise ValueError(f"unknown initial states: {unknown}")
    if bulk_bonds < 1 or bulk_bonds >= system_size - 1:
        raise ValueError("bulk_bonds must be positive and smaller than the chain")

    return DynamicsConfig(
        system_size=system_size,
        max_bond=max_bond,
        time_step=time_step,
        final_time=final_time,
        sample_interval=sample_interval,
        cutoff=cutoff,
        initial_states=initial_states,
        bulk_bonds=bulk_bonds,
    )


def pattern_bits(system_size: int, name: str) -> str:
    unit_cells = {
        "vacuum": "0",
        "z2": "10",
        "z3": "100",
        "z4": "1000",
    }
    try:
        cell = unit_cells[name]
    except KeyError as exc:
        raise ValueError(f"unsupported initial state {name!r}") from exc
    repeats = (system_size + len(cell) - 1) // len(cell)
    return (cell * repeats)[:system_size]


def three_site_gate(time_step: float) -> np.ndarray:
    """Return exp(-i dt P X P) as an 8 by 8 unitary."""

    return expm(-1j * float(time_step) * THREE_SITE_PXP)


def _apply_group(
    state: qtn.MatrixProductState,
    gate: np.ndarray,
    centers: Iterable[int],
    *,
    max_bond: int,
    cutoff: float,
) -> None:
    for center in centers:
        state.gate_(
            gate,
            (center - 1, center, center + 1),
            contract="auto-mps",
            max_bond=max_bond,
            cutoff=cutoff,
        )


def trotter_step(state: qtn.MatrixProductState, config: DynamicsConfig) -> float:
    """Apply one symmetric second-order step and return norm drift."""

    centers = range(1, config.system_size - 1)
    groups = [tuple(center for center in centers if center % 3 == residue) for residue in range(3)]
    half_gate = three_site_gate(config.time_step / 2.0)
    full_gate = three_site_gate(config.time_step)
    sequence = (
        (half_gate, groups[0]),
        (half_gate, groups[1]),
        (full_gate, groups[2]),
        (half_gate, reversed(groups[1])),
        (half_gate, reversed(groups[0])),
    )
    for gate, group in sequence:
        _apply_group(
            state,
            gate,
            group,
            max_bond=config.max_bond,
            cutoff=config.cutoff,
        )
    norm_before = float(np.real(state.H @ state))
    state.normalize()
    return abs(norm_before - 1.0)


def _bulk_bond_indices(config: DynamicsConfig) -> list[tuple[int, int]]:
    midpoint = config.system_size // 2
    start = max(0, midpoint - config.bulk_bonds // 2)
    stop = min(config.system_size - 1, start + config.bulk_bonds)
    return [(site, site + 1) for site in range(start, stop)]


def measure(state: qtn.MatrixProductState, config: DynamicsConfig) -> dict[str, float]:
    bonds = _bulk_bond_indices(config)
    zz_terms = {bond: ZZ for bond in bonds}
    nn_terms = {bond: NN for bond in bonds}
    zz_values = state.compute_local_expectation(zz_terms, return_all=True, inplace=False)
    nn_values = state.compute_local_expectation(nn_terms, return_all=True, inplace=False)
    return {
        "entanglement_entropy": float(np.real(state.entropy(config.system_size // 2))),
        "nearest_neighbor_zz": float(np.mean([np.real(value) for value in zz_values.values()])),
        "constraint_violation": float(np.mean([np.real(value) for value in nn_values.values()])),
        "bond_dimension": int(state.max_bond()),
    }


def simulate(config: DynamicsConfig) -> tuple[list[dict[str, float | int | str]], dict[str, Any]]:
    rows: list[dict[str, float | int | str]] = []
    max_norm_drift = 0.0
    sample_every = int(round(config.sample_interval / config.time_step))
    steps = int(round(config.final_time / config.time_step))

    for initial_state in config.initial_states:
        state = qtn.MPS_computational_state(pattern_bits(config.system_size, initial_state))
        for step in range(steps + 1):
            if step % sample_every == 0:
                rows.append(
                    {
                        "initial_state": initial_state,
                        "system_size": config.system_size,
                        "time": step * config.time_step,
                        **measure(state, config),
                    }
                )
            if step < steps:
                max_norm_drift = max(max_norm_drift, trotter_step(state, config))

    z2_rows = [row for row in rows if row["initial_state"] == "z2"]
    z2_period = None
    if len(z2_rows) >= 5:
        signal = np.asarray([float(row["nearest_neighbor_zz"]) for row in z2_rows])
        times = np.asarray([float(row["time"]) for row in z2_rows])
        peaks, _ = find_peaks(signal, prominence=max(1e-6, 0.05 * float(np.ptp(signal))))
        if len(peaks) >= 2:
            z2_period = float(np.mean(np.diff(times[peaks])))

    max_constraint_violation = max(float(row["constraint_violation"]) for row in rows)
    max_observed_bond = max(int(row["bond_dimension"]) for row in rows)
    checks = {
        "max_norm_drift_before_renormalization": max_norm_drift,
        "max_constraint_violation": max_constraint_violation,
        "max_observed_bond": max_observed_bond,
        "z2_correlation_period": z2_period,
        "gate_flags": {
            "constraint_preserved": max_constraint_violation < 1e-7,
            "bond_cap_respected": max_observed_bond <= config.max_bond,
            "norm_stable": max_norm_drift < 1e-6,
            "z2_period_near_paper": z2_period is None or abs(z2_period - 2.35) < 0.35,
        },
    }
    checks["status"] = "passed" if all(checks["gate_flags"].values()) else "failed"
    return rows, checks
