# Method Trace

| Method | Targets | Inputs | Scientific falsification |
| --- | --- | --- | --- |
| M001 geometric boundary construction | T001,T003,T005 | Eq. (6), zigzag/armchair orientation | coordination, endpoint localization and width convergence |
| M002 dense ribbon eigensolver | T001,T003 | M001 graph, t2/t, Rashba ratios | Hermiticity, TR, independently sampled bulk gap and full-BZ baseline-subtracted spectral flow across both orientations and three widths |
| M003 continuum eigensolver | T002,T003 | Eqs. (1)-(4) | direct gaps at four Rashba ratios |
| M004 Fukui Berry flux and cylinder flow | T004,T005 | periodic Bloch matrix and helical cylinder | grid quantization, opposite sectors and explicit level permutation |
| M005 S-matrix and random disorder propagation | T006 | printed TR constraint and scalar TR disorder | null-space residual plus 32 seeded ensembles with R=0 |
| M006 Landauer-Buettiker solve | T008,T009 | helical channel graph, Fig. 2 voltages | charge conservation and spin-resolved currents |
| M007 edge-field/operator construction | T007 | printed interaction prose | Grassmann/TR transform, dimension counting, `u,T` fits and perturbation inventory |
| M008 first-star microscopic projection | T010 | Eq. (7), plane-wave first star | explicit 8x8 matrix and SI scale |
| M009 Coulomb shell/RPA/RG | T012,T013 | Fig. 3, Eq. (8), printed g0/cutoff/gap | derived beta coefficients, independent interband polarization with angular/UV convergence, screening, ODE and root |
| M010 full-BZ Kubo proxy | T003 | full spinful Bloch Hamiltonian | finite-Rashba conventional current with explicit spin nonconservation |
| M011 Pauli/lattice symmetry audit | T003,T004 | continuum kinetic matrices and primitive-cell lattice Hamiltonian | unique symmetric SO mass, direct edge Zeeman gap, intervalley/translation diagnosis and continuous optimizer that falsifies the minimal translation-preserving bulk path |
| M012 RenderContract | T001 only | frozen band CSV hash | data hash unchanged before/after rendering |

Author code, author arrays and digitized figure coordinates are absent from all
method inputs.  `raw/` and `references/` are forbidden roots for M001-M011.
M010 is deliberately labelled a proxy because the target paper does not print
the externally cited conserved-spin-current operator; no acceptance rule may
silently promote it to paper-exact.
