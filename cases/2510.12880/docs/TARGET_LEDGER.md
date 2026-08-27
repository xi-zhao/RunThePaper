# Target Ledger

## Item-Level Result

- Eligible scientific items: `9`
- Covered items: `4`
- Uncovered items: `5`
- Coverage: `44.44%`
- Covered-item fidelity: `92.03/100`
- Reproduction degree: `40.90/100`
- Supporting claims not double-counted: `2`

The historical two-panel similarity score remains `95/100`; it answers how
well the already-generated Fig. 5 panels match. The reproduction degree answers
how much of the whole paper's independently adjudicable scientific scope has
been covered.

## All Eligible Items

| Target | Scientific item | Paper location | Covered | Fidelity / gap |
| --- | --- | --- | --- | --- |
| V001 | periodic exact-point projector, MPS, and `2^N+1` manifold | main exact-point/MPS sections and supplement | yes | `89`; accepted at N=4,6, with paper-subset cap |
| V002 | periodic phase and product-state controls | Main Fig. 4 discussion and purely biquadratic supplement | yes | `90`; analytic-reference cap |
| T001 | ground-state squared-fidelity panel | Main Fig. 5(a) | yes | `94.12`; one retained source-marker discrepancy |
| T002 | first-excited-subspace squared-fidelity panel | Main Fig. 5(b) | yes | `95`; all 25 marker comparisons pass |
| V003 | open-chain exact-point degeneracy `2^(N+1)-1` | Supplement Edge states and Fig. S1 | **no** | no open-boundary nullity/rank artifact |
| V004 | open-chain `theta=pi/2` degeneracy `2N+1` | Supplement purely biquadratic `theta=pi/2` | **no** | no open-chain zero-mode sequence |
| V005 | open-chain `theta=3pi/2` energy `-(N-1)` and fourfold degeneracy | Supplement purely biquadratic `theta=3pi/2` | **no** | no open-chain product-state/spectrum artifact |
| V006 | even triplet-x/triplet-y parity at `theta=0` | Supplement fractionalized variational ansatz | **no** | no bond-basis coefficient/parity artifact |
| V007 | second-order onset and all-order uniform-positive-w sector | Supplement bond-conserved-quantity perturbation section | **no** | no perturbation-order/matrix-element artifact |

## Uncovered Item Diagnoses

| Target | Direct cause | Root cause | Code responsibility | Next discriminating test |
| --- | --- | --- | --- | --- |
| V003 | open-boundary exact-point calculation is not implemented | earlier scope treated S1 as only a schematic | code defect not excluded because no claim-specific path exists | count Hamiltonian nullity and fractionalized-state rank for even N=2,4,6 |
| V004 | open `theta=pi/2` spectrum is not implemented | periodic V002 scope silently omitted the separate open-boundary claim | code defect not excluded | compute N=2,4,6,8 nullities and cross-check a combinatorial recurrence |
| V005 | open `theta=3pi/2` product manifold is not implemented | periodic uniform-z check was mistaken for coverage of the open construction | code defect not excluded | verify four product states, `-(N-1)` energy, edge `w` labels, and full nullity |
| V006 | bond-basis coefficient support is not implemented | selection-rule prose was not recognized as an independent analytic result | code defect not excluded | expand small-N MPS coefficients and check both parities plus `U_x/U_y` eigenvalues |
| V007 | perturbation orders and transition matrix elements are not implemented | representative phase spectra were mistaken for the perturbative mechanism | code defect not excluded | calculate first/second order, reachable sectors, then compare a small-N no-crossing scan |

These five are method/implementation gaps, not publication-input or compute
blockers. W1 records them without running new science. W2 must attempt the
listed tests before deciding whether any claim is supported, falsified, or
limited by resources.
