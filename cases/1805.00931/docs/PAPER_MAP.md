# Paper Map

## Identity

- Paper ID: `1805.00931`
- Title: *Exact Spectral Form Factor in a Minimal Model of Many-Body Quantum Chaos*
- Authors: Bruno Bertini, Pavel Kos, Tomaž Prosen
- Publication: *Physical Review Letters* **121**, 264101 (2018)
- DOI: `10.1103/PhysRevLett.121.264101`
- Source: <https://arxiv.org/abs/1805.00931>
- Local PDF: `raw/paper.pdf`
- Local TeX: `paper-source/SelfDualQCArxiv.tex`
- Source audit: the archive contains TeX and rendered figure assets, but no author
  numerical code or numerical arrays.

## Reproduction Goal

Reconstruct every numerical figure panel and numerical table from the kicked-Ising
Hamiltonian, the disorder average, the dual transfer matrix, and the operator-algebra
multiplicity formulas. Figure pixels are never numerical inputs. The original figure
assets are opened only after generated datasets are frozen, for visual comparison and
render-contract work.

The exact paper scales are computationally extreme: Figure 2 uses `L=15`, 9490
disorder realizations and times through 1000, while the Figure 3 transfer vector has
dimension `4**t` through `t=15`. This case therefore reports a transparent feature-scale
run: Figure 2 uses exact diagonalization at `L=8`; Figure 3 reaches paper-exact `t=9`
at three representative widths and uses `t<=9` / `t=7` elsewhere. Table I is evaluated at
the full paper range `t=2..17` from the proved dihedral ranks plus the explicitly
derived exceptional sectors. Reduced scale is a state blocker, not hidden as completion.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main introduction | Scientific claim | A local spin-1/2 Floquet model has exact RMT spectral correlations in the thermodynamic limit. |
| Kicked-Ising model | Model definition | Defines `H_I`, `H_K`, `U_KI`, quasienergies and SFF. |
| Space-time duality | Numerical/analytic bridge | Rewrites the disorder-averaged SFF as `tr(T**L)`. |
| Transfer-matrix spectrum | Main proof | Unit-modulus spectrum reduces to a commutant of `U, Mx, My, Mz`. |
| Odd/even time results | Main result | Gives exact odd-time and conjectured large even-time multiplicities. |
| Supplement: Properties 1--4 | Proofs | Establishes contraction, phase restrictions and dihedral ranks. |
| Supplement: Theorem 1 | Proof | Proves completeness of the dihedral commutant for odd `t`. |
| Supplement: even `t` | Exceptional sectors | Constructs `Z`, the `t=8,10` extras and the `t=6,10` minus-one pairs. |
| Supplement: integrable model | Cross-check | Jordan-Wigner/Bogoliubov diagonalization at zero field. |
| Supplement: numerical methods | Reproduction algorithm | Direct basis propagation for Figure 2 and matrix-free power iteration for Figure 3/Table I. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main Eqs. (1)--(3) | Kicked-Ising Hamiltonian and Floquet operator | verified |
| EQ002 | Main SFF equations | `K(t)=|tr(U**t)|**2` | verified |
| EQ003 | Main Gaussian average | Independent longitudinal-field ensemble | verified |
| EQ004 | Main RMT paragraph | Finite-`N` COE reference curve | verified |
| EQ005 | Main duality and transfer equations | `Kbar(t)=tr(T**L)` | verified |
| EQ006 | Main Eq. for `O_sigma` | Gaussian dephasing contraction | verified |
| EQ007 | Figure 3 paragraph | Transfer-matrix spectral gap | verified |
| EQ008 | Main odd/even results + supplement | Thermodynamic SFF multiplicities | verified |
| EQ009 | Supplement numerical methods | Direct propagation and matrix-free iteration | verified |

## Figure/Table Inventory

| Item | Caption summary | Class | Decision |
| --- | --- | --- | --- |
| Main Figure 1 | Pictorial space-time transfer-matrix construction | schematic_context | excluded |
| Main Figure 2 main axes | Disorder-averaged SFF through long integer times | numeric_reproduction | T001 |
| Main Figure 2 inset | Short-time SFF window | numeric_reproduction | T002 |
| Main Figure 3 left | Gap versus disorder for several `t`, `hbar=0` | numeric_reproduction | T003 |
| Main Figure 3 right | Gap versus disorder for several mean fields | numeric_reproduction | T004 |
| Main Table I | Multiplicities of transfer eigenvalues `+1` and `-1` | numeric_reproduction | T005 |
| Supplemental material | Proofs and equations only; no additional figures/tables | not_in_scope | no additional target |

## Assumptions and Conventions

- Computational-basis bit `0` is `sigma_z=+1`, bit `1` is `sigma_z=-1`.
- `U=exp(-i H_K) exp(-i H_I)`; changing the global sign convention conjugates
  eigenphases but leaves the SFF and transfer-spectrum moduli invariant.
- Disorder samples use NumPy `PCG64` with the frozen seed in the run config.
- The transfer action is applied as `A -> U (O_sigma ⊙ A) U†`, exactly equivalent
  to `(U ⊗ U*) O_sigma` under row-major vectorization.
- Figure 3's unit and minus-unit eigenspaces are removed using formula-derived
  dihedral and exceptional operators before Arnoldi estimates the leading subunit mode.
