"""Reconstruct the six-qubit BeH2 ideal calculation under explicit orbital choices."""

import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize
from pyscf import fci, gto, lib, scf


DISTANCES = np.array(sorted({*np.round(np.arange(0.5, 5, 0.2), 2), 1.326, 5.0}))
SEED = 220906864
NQUBITS = 6
NORB = 4
DIM = 2**NQUBITS
TARGET_OCCUPATION = 0b00110011


def integrals(distance):
    """Use the five longitudinal AOs of the cited Kandala BeH2 model."""
    mol = gto.M(atom=[("Be", (0, 0, 0)), ("H", (-distance, 0, 0)), ("H", (distance, 0, 0))],
                unit="Angstrom", basis="sto-3g", symmetry="D2h", verbose=0)
    labels = mol.ao_labels(fmt=False)
    keep = [i for i, label in enumerate(labels) if not (label[2] == "2p" and label[3] in ("y", "z"))]
    transverse = sorted(set(range(mol.nao_nr())) - set(keep))
    assert len(keep) == 5 and len(transverse) == 2, labels
    h = scf.hf.get_hcore(mol)[np.ix_(keep, keep)]
    overlap = mol.intor("int1e_ovlp")[np.ix_(keep, keep)]
    eri = mol.intor("int2e")[np.ix_(keep, keep, keep, keep)]
    mf = scf.RHF(mol)
    mf.conv_tol = 1e-12
    mf.kernel()
    assert mf.converged, distance
    sigma = np.flatnonzero(np.max(abs(mf.mo_coeff[transverse]), axis=0) < 1e-8)
    assert len(sigma) == 5 and np.array_equal(mf.mo_occ[sigma], [2, 2, 2, 0, 0]), distance
    rhf = mf.mo_coeff[np.ix_(keep, sigma)]
    _, dressed = eigh(h, overlap)
    return h, overlap, eri, float(mol.energy_nuc()), rhf, dressed, float(mf.e_tot)


def freeze_core(h, overlap, eri, enuc, coeff):
    assert np.max(abs(coeff.T @ overlap @ coeff - np.eye(5))) < 1e-9
    hm = coeff.T @ h @ coeff
    gm = np.einsum("pi,qj,rk,sl,pqrs->ijkl", coeff, coeff, coeff, coeff, eri, optimize=True)
    constant = enuc + 2 * hm[0, 0] + gm[0, 0, 0, 0]
    active = hm[1:, 1:] + 2 * gm[1:, 1:, 0, 0] - gm[1:, 0, 0, 1:]
    return active, gm[1:, 1:, 1:, 1:], float(constant)


def decode_parity(label):
    """Restore even alpha and total parity bits, then undo prefix parity."""
    p = (label & 7) | ((label >> 3) << 4)
    return p ^ ((p << 1) & 255)


OCCUPATIONS = [decode_parity(i) for i in range(DIM)]
SECTOR = np.array([(o & 15).bit_count() == (o >> 4).bit_count() == 2 for o in OCCUPATIONS])


def apply_fermions(state, operations):
    sign = 1
    for mode, create in operations:
        bit = 1 << mode
        if bool(state & bit) == create:
            return None
        if (state & (bit - 1)).bit_count() % 2:
            sign = -sign
        state ^= bit
    return state, sign


def parity_hamiltonian(h, eri, constant):
    position = {state: i for i, state in enumerate(OCCUPATIONS)}
    terms = []
    for spin in (0, NORB):
        for p, q in product(range(NORB), repeat=2):
            terms.append((h[p, q], ((q + spin, False), (p + spin, True))))
        for other in (0, NORB):
            for p, q, r, s in product(range(NORB), repeat=4):
                terms.append((0.5 * eri[p, q, r, s],
                    ((q + spin, False), (s + other, False), (r + other, True), (p + spin, True))))
    matrix = np.eye(DIM) * constant
    for column, state in enumerate(OCCUPATIONS):
        for coefficient, operations in terms:
            if abs(coefficient) > 1e-14:
                applied = apply_fermions(state, operations)
                if applied is not None:
                    output, sign = applied
                    matrix[position[output], column] += coefficient * sign
    assert np.max(abs(matrix - matrix.T)) < 1e-11
    return matrix


def rotations_indices():
    index = np.arange(DIM)
    zero = [index[(index & (1 << q)) == 0] for q in range(NQUBITS)]
    return [(a, a | (1 << q)) for q, a in enumerate(zero)]


ROTATIONS = rotations_indices()
CNOT_CHAIN = np.arange(DIM)
for qubit in range(NQUBITS - 1):
    CNOT_CHAIN ^= ((CNOT_CHAIN >> qubit) & 1) << (qubit + 1)
CHAIN_INVERSE = np.argsort(CNOT_CHAIN)


def rotate(state, q, c, s):
    a, b = ROTATIONS[q]
    old_a, old_b = state[a], state[b]
    state[a] = c * old_a - s * old_b
    state[b] = s * old_a + c * old_b


def state_and_tape(angles):
    state = np.zeros(DIM)
    state[0] = 1
    tape = []
    for i, angle in enumerate(angles):
        q = i % NQUBITS
        if q == 0 and i:
            state = state[CHAIN_INVERSE]
        c, s = np.cos(angle / 2), np.sin(angle / 2)
        rotate(state, q, c, s)
        tape.append((q, c, s, state.copy()))
    return state, tape


def objective(angles, matrix):
    state, tape = state_and_tape(angles)
    costate = np.einsum("ij,j->i", matrix, state)
    energy = float(state @ costate)
    gradient = np.empty(len(angles))
    for i in reversed(range(len(tape))):
        q, c, s, after = tape[i]
        a, b = ROTATIONS[q]
        gradient[i] = costate[b] @ after[a] - costate[a] @ after[b]
        rotate(costate, q, c, -s)
        if q == 0 and i:
            costate = costate[CNOT_CHAIN]
    return energy, gradient


def optimize(matrix, constant, seed, previous):
    rng = np.random.default_rng(seed)
    hartree_fock = np.zeros(3 * NQUBITS)
    hf_index = OCCUPATIONS.index(TARGET_OCCUPATION)
    hartree_fock[-NQUBITS:] = [np.pi * ((hf_index >> i) & 1) for i in range(NQUBITS)]
    starts = [hartree_fock, *[hartree_fock + rng.normal(0, .25, len(hartree_fock)) for _ in range(4)],
              *[rng.uniform(-np.pi, np.pi, len(hartree_fock)) for _ in range(6)]]
    if previous is not None:
        starts.append(previous)
    shifted = matrix - np.eye(DIM) * constant
    results = [minimize(objective, initial, args=(shifted,), jac=True, method="L-BFGS-B",
                        options=dict(maxiter=550, ftol=3e-13, gtol=1e-8)) for initial in starts]
    best = min(results, key=lambda trial: trial.fun)
    state, _ = state_and_tape(best.x)
    return best.x, state, [dict(energy=float(r.fun + constant), iterations=r.nit,
                                success=bool(r.success)) for r in results]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("start", type=int)
    p.add_argument("stop", type=int)
    p.add_argument("output_json", type=Path)
    p.add_argument("output_arrays", type=Path)
    args = p.parse_args()
    lib.num_threads(1)
    rows, arrays = [], []
    previous = None
    for i in range(args.start, args.stop):
        r = DISTANCES[i]
        h0, overlap, g0, enuc, rhf, dressed, hf_energy = integrals(r)
        h, eri, constant = freeze_core(h0, overlap, g0, enuc, rhf)
        hd, gd, ed = freeze_core(h0, overlap, g0, enuc, dressed)
        hq = parity_hamiltonian(h, eri, constant)
        active_fci = float(np.linalg.eigvalsh(hq[np.ix_(SECTOR, SECTOR)])[0])
        dressed_fci = float(fci.direct_spin1.kernel(hd, gd, NORB, (2, 2), ecore=ed)[0])
        parity_floor = float(np.linalg.eigvalsh(hq)[0])
        angles, state, tries = optimize(hq, constant, SEED + i, previous)
        previous = angles.copy()
        energy = float(np.einsum("i,ij,j->", state, hq, state))
        hf_index = OCCUPATIONS.index(TARGET_OCCUPATION)
        assert abs(hq[hf_index, hf_index] - hf_energy) < 2e-9
        assert energy >= parity_floor - 2e-10
        sector_weight = float(np.sum(state[SECTOR]**2))
        rows.append(dict(index=i, r_angstrom=float(r), rhf=hf_energy, fci=active_fci,
            hcore_fci=dressed_fci, parity_floor=parity_floor, variational=energy,
            physical_sector_weight=sector_weight, constant=constant, trials=tries))
        arrays.append((h, eri, hq, angles, state))
        print(f"{i:2d} {r:.3f} Å E={energy:.7f} exact={active_fci:.7f} sector={sector_weight:.8f}", flush=True)
    args.output_json.write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n")
    np.savez_compressed(args.output_arrays, **{
        key: np.stack(data) for key, data in zip(("h", "eri", "hamiltonian", "angles", "state"), zip(*arrays))
    })


if __name__ == "__main__":
    main()
