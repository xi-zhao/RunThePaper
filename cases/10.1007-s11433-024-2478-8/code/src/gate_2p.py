"""Integrate the two-photon BAM sectors and evaluate the CZ gate metrics.

Reuses the CZ metric definitions from ``gate`` (conditional phase and Pedersen
average gate error) but drives the two-photon sector Hamiltonians of
``hamiltonians_2p``.  hbar = 1; time in us, frequencies in rad/us.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

import hamiltonians_2p as h2
from waveforms import TWO_PI, TAU_US


@dataclass
class SectorResult:
    population: np.ndarray
    phase: np.ndarray
    amp_final: complex


def _params(proto, t):
    def w(f):
        return float(np.asarray(f(t)))
    return {
        "omega1p": w(proto.omega1p), "omega1s": proto.omega1s,
        "omega2p": w(proto.omega2p), "omega2s": proto.omega2s,
        "delta1": w(proto.delta1), "delta2": w(proto.delta2),
        "delta_0": TWO_PI * proto.delta0_mhz,
        "B": TWO_PI * proto.B_mhz, "delta_q": TWO_PI * proto.delta_q_mhz,
    }


def _evolve(
    proto,
    roles,
    adjacency,
    n_out,
    tau,
    *,
    pair_energy_shifts=None,
):
    n = len(roles)
    dim = h2.D ** n
    i0 = h2.init_index(n)

    def rhs(t, y):
        H = h2.build_sector(
            n,
            roles,
            adjacency,
            _params(proto, t),
            pair_energy_shifts=pair_energy_shifts,
        )
        psi = y[:dim] + 1j * y[dim:]
        d = -1j * (H @ psi)
        return np.concatenate([d.real, d.imag])

    y0 = np.zeros(2 * dim)
    y0[i0] = 1.0
    t_eval = np.linspace(0.0, tau, n_out)
    # Delta_0 ~ 2*pi*5 GHz drives fast intermediate-state oscillations -> tight steps.
    sol = solve_ivp(rhs, (0.0, tau), y0, t_eval=t_eval, method="DOP853",
                    rtol=1e-10, atol=1e-12, max_step=tau / 4000.0)
    amp = sol.y[i0] + 1j * sol.y[dim + i0]
    # population of the initial all-|1> state and its phase
    pop = np.abs(amp) ** 2
    phase = np.unwrap(np.angle(amp))
    return SectorResult(pop, phase, complex(amp[-1]))


def _evolve_sector(proto, sector, n_out, tau):
    spec = h2.SECTORS[sector]
    return _evolve(
        proto,
        spec["roles"],
        spec["adjacency"],
        n_out,
        tau,
    )


def run_protocol(proto, n_out: int = 401, tau: float = TAU_US):
    return {
        "00": _evolve_sector(proto, "00", n_out, tau),
        "01": _evolve_sector(proto, "01", n_out, tau),
        "11": _evolve_sector(proto, "11", n_out, tau),
    }


def run_protocol_with_end_coupling(
    proto,
    *,
    end_coupling_ratio: float,
    n_out: int = 401,
    tau: float = TAU_US,
):
    """Run a CZ protocol with the published residual end-qubit interaction.

    Only the all-active ``11`` sector contains both end qubits.  The other
    sectors are identical to :func:`run_protocol`.
    """

    shift = TWO_PI * proto.B_mhz * end_coupling_ratio
    return {
        "00": _evolve_sector(proto, "00", n_out, tau),
        "01": _evolve_sector(proto, "01", n_out, tau),
        "11": _evolve(
            proto,
            ["qubit", "buffer", "qubit"],
            [(0, 1), (1, 2)],
            n_out,
            tau,
            pair_energy_shifts={(0, 2): shift},
        ),
    }


def run_three_qubit_active_patterns(
    proto,
    *,
    n_out: int = 401,
    tau: float = TAU_US,
):
    """Generate every computational branch of the three-atom Fig. 6 gate.

    Inactive ``|0>`` atoms are dark and may be removed from the active
    Hamiltonian.  Active atoms retain their physical roles and nearest-neighbor
    edges in the ``qubit-buffer-qubit`` chain.  This yields all eight diagonal
    amplitudes without introducing a four-atom model.
    """

    physical_roles = ("qubit", "buffer", "qubit")
    physical_edges = ((0, 1), (1, 2))
    time = np.linspace(0.0, tau, n_out)
    results = {
        "000": SectorResult(
            population=np.ones(n_out),
            phase=np.zeros(n_out),
            amp_final=1.0 + 0.0j,
        )
    }
    for value in range(1, 8):
        bits = f"{value:03b}"
        active = [index for index, bit in enumerate(bits) if bit == "1"]
        compact_index = {physical: compact for compact, physical in enumerate(active)}
        roles = [physical_roles[index] for index in active]
        adjacency = [
            (compact_index[left], compact_index[right])
            for left, right in physical_edges
            if left in compact_index and right in compact_index
        ]
        results[bits] = _evolve(proto, roles, adjacency, n_out, tau)
    return time, results
