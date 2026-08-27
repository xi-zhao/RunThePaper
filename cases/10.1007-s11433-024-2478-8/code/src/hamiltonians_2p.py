"""Two-photon ground-Rydberg sector Hamiltonians for the BAM gate.

Appendix eqs. (a5)-(a6): the two-photon transition replaces every single-photon
|1><->|r> coupling of eqs. (a3)/(a4) with a ladder |1><->|e><->|r| through an
intermediate state |e> at a large one-photon detuning Delta_0:

    H_local(atom) = (Omega_p/2)|1><e| + (Omega_S/2)|e><r| + h.c.
                    + Delta_0 |e><e| + delta |r><r|          (eqs. a5/a6)

The many-body interaction structure (Foerster resonance |r r'> <-> |q q'| with
strength B and pair penalty delta_q, adjacent (control-buffer, buffer-target)
pairs only, detunings delta_1 on the buffer Rydberg and delta_2 on the qubit
Rydberg) is *identical* to the single-photon eq. (a4) -- only the ground-Rydberg
coupling changes.  We therefore build the sectors directly in the per-atom
product basis with four local levels {|1>, |e>, |r>, |q>}:

    0 = |1>  register-active ground     2 = |r>  Rydberg (laser-reached)
    1 = |e>  intermediate                3 = |q>  Foerster-partner Rydberg

Atom order is (control qubit, buffer, target qubit); the buffer is index 1 and is
adjacent to both qubits.  |q> is populated only through the Foerster exchange, so
a lone |q> stays dark.  hbar = 1; frequencies in rad/us.
"""
from __future__ import annotations

import numpy as np

# local level indices
G, E, R, Q = 0, 1, 2, 3
D = 4


def _ket_bra(a, b):
    m = np.zeros((D, D), dtype=complex)
    m[a, b] = 1.0
    return m


def _embed(op, i, n):
    """Place a single-atom operator ``op`` on atom ``i`` of ``n`` atoms."""
    mats = [np.eye(D, dtype=complex)] * n
    mats[i] = op
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


def _embed2(op_i, i, op_j, j, n):
    """Place a two-atom operator ``op_i (x) op_j`` on atoms ``i`` and ``j``."""
    mats = [np.eye(D, dtype=complex)] * n
    mats[i] = op_i
    mats[j] = op_j
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


def _local_drive(omega_p, omega_s):
    return (omega_p / 2.0) * _ket_bra(G, E) + (omega_s / 2.0) * _ket_bra(E, R) \
        + (omega_p / 2.0) * _ket_bra(E, G) + (omega_s / 2.0) * _ket_bra(R, E)


def _local_energy(delta_0, delta):
    return delta_0 * _ket_bra(E, E) + delta * _ket_bra(R, R) + delta * _ket_bra(Q, Q)


def build_sector(n_atoms, roles, adjacency, params, pair_energy_shifts=None):
    """Assemble a two-photon sector Hamiltonian.

    roles[i] = "buffer" or "qubit" -> which (Omega_p, Omega_S, delta) it uses.
    adjacency = list of (i, j) Foerster-coupled atom pairs.
    pair_energy_shifts = optional mapping ``(i, j) -> delta_ij`` in rad/us.
                         Each entry adds the diagonal term
                         ``delta_ij |r_i r_j><r_i r_j|``.  This is distinct
                         from the off-diagonal Foerster exchange on adjacency
                         edges and represents Appendix Fig. a8's B/64 remote
                         end-qubit energy shift.
    params: dict with omega1p, omega1s, delta1 (buffer) and omega2p, omega2s,
            delta2 (qubit), plus delta_0, B, delta_q  (all scalars, rad/us).
    Returns an (D**n, D**n) complex matrix.
    """
    n = n_atoms
    dim = D ** n
    h = np.zeros((dim, dim), dtype=complex)
    for i, role in enumerate(roles):
        if role == "buffer":
            op = _local_drive(params["omega1p"], params["omega1s"])
            en = _local_energy(params["delta_0"], params["delta1"])
        else:
            op = _local_drive(params["omega2p"], params["omega2s"])
            en = _local_energy(params["delta_0"], params["delta2"])
        h += _embed(op, i, n) + _embed(en, i, n)

    B, dq = params["B"], params["delta_q"]
    rq = _ket_bra(R, Q)          # |r><q|
    qr = _ket_bra(Q, R)          # |q><r|
    qq = _ket_bra(Q, Q)          # |q><q|
    for (i, j) in adjacency:
        # B ( |r_i r_j><q_i q_j| + h.c. )
        h += B * (_embed2(rq, i, rq, j, n) + _embed2(qr, i, qr, j, n))
        # pair penalty delta_q on |q_i q_j>
        h += dq * _embed2(qq, i, qq, j, n)
    rr = _ket_bra(R, R)
    for (i, j), shift in (pair_energy_shifts or {}).items():
        h += shift * _embed2(rr, i, rr, j, n)
    return h


def init_index(n_atoms):
    """Index of the all-|1> state (every atom in register ground)."""
    return 0  # G=0 for every atom -> flat index 0


# sector wiring
SECTORS = {
    "00": {"n": 1, "roles": ["buffer"], "adjacency": []},
    "01": {"n": 2, "roles": ["buffer", "qubit"], "adjacency": [(0, 1)]},
    "11": {"n": 3, "roles": ["qubit", "buffer", "qubit"], "adjacency": [(0, 1), (1, 2)]},
    # three-qubit Toffoli phase-gate sector (all three qubits |1>): buffer relays
    # between the qubit chain; adjacency along (q, buffer, q, q) is model-specific.
}
