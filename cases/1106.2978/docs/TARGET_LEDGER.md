# Target ledger

The whole-paper inventory contains 25 publication items: 24 independently
checkable numerical items and one non-numerical schematic.  The numerical
items are covered by 21 executable target contracts; several closely coupled
paper statements intentionally share one target.  None is deferred for
compute or missing inputs.

| Targets | Scientific object | Current evidence |
| --- | --- | --- |
| T001-T003 | every numerical region of Main Fig. 2 | formula-generated arrays, dense-NESS cross-check, scientific-region pixels `94.0463/88.4407/89.7941` |
| T004 | easy-plane thermodynamic current | closed form, finite transfer and limiting coefficients agree |
| T005 | printed isotropic correlation kernel | finite MPO is reproducible; printed kernel violates exact mirror-plus-spin-flip symmetry; review pending |
| T006 | weak-coupling current and profile | both printed limits pass independently |
| T007-T012 | exact MPO theorem, Cholesky structure, cutoff, polynomial degree and observables | explicit physical MPO agrees with a full dense Liouvillian through `n=4`; all finite identities pass |
| T013 | `O(n^2)` transfer complexity | deterministic operation-count exponent `1.9736` for `n>=80` |
| T014 | root-of-unity cutoff index, hopping parity and auxiliary dimension | full Eq. (7) contradicts the printed `r=m`, parity and `H_(m+1)` statement; actual `r=m-1` cutoff matches the printed `m=3` three-state example; review pending |
| T015-T019 | reduced transfer matrix, easy-axis and isotropic asymptotics | matrix identities, `alpha`, amplitudes and continuum convergence pass |
| T020 | easy-plane transfer-spectrum convergence | subleading/leading eigenvalue ratio agrees with an independent finite-current convergence fit; flat bulk profile converges monotonically |
| T021 | infinite transfer rank for `Delta>=1` | analytic hopping witness and arbitrarily extendable nonsingular shifted minors agree |

Main Fig. 1 is `non_numeric`: it is a tensor-network schematic, not a numerical target. A process exit never decides status; formula provenance, paper parameters, scientific checks, isolated execution and an explicit pixel state do.
