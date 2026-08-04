# Formula Verification

Machine-readable result:
`outputs/checks/formula_verification.json`.

All eleven formula cards have source traces, independent checks, and open
numeric gates.

| Formula | Plain-language role | Gate | Independent check |
| --- | --- | --- | --- |
| EQC001 | spin-1 Cartesian basis and \(\pi\)-rotations | open | direct matrix exponentiation gives diagonal \(R_x,R_y\) |
| EQC002 | Hamiltonian and conserved \(w\)-sectors | open | commutators and small-\(N\) sector partition |
| EQC003 | exact-point bond projector | open | spectral and polynomial projectors agree below \(10^{-12}\) |
| EQC004 | fractionalized states are zero modes | open | every constructed MPS has vanishing exact-point energy |
| EQC005 | cluster stabilizer representation | open | explicit local action matches \(XZX\) signs |
| EQC006 | cluster-state MPS tensors | open | printed matrices and \(w\)-sign swap agree |
| EQC007 | physical bond-dimension-four MPS | open | printed \(C\) tensor, normalization, and sector support tests |
| EQC008 | ground-state squared fidelity | open | source point distinguishes amplitude from amplitude squared |
| EQC009 | first-excited projector fidelity | open | basis-independent eigenspace projection and one-flip sector test |
| EQC010 | product-state energy bounds | open | exact representative energies and mirror symmetry |
| EQC011 | \(2^N+1\) degeneracy | open | full sector nullity counts for \(N=4,6\) |

## Source Ambiguities Resolved

| Source issue | Resolution | Numerical consequence |
| --- | --- | --- |
| odd-bond \(W\) line omits one \(\pi\) | use the supplement and the stated \(W^2=1\) identity | conserved eigenvalues remain \(\pm1\) |
| two \(s=0\) tensor lines use \(M^{+1}\) | use \(M^0\), as required by definitions and printed output matrices | physical MPS has correct sector support |
| Fig. 5 says “overlap” | use squared fidelity, fixed by visible values | both panels match; unsquared amplitudes do not |

## Gate Command

```bash
python private validation harness/scripts/check_formula_gate.py case/2510.12880 --write
```
