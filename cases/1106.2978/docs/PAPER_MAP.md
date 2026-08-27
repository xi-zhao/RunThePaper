# Full-paper numerical inventory

## Publication

- Paper ID: `1106.2978`
- DOI: `10.1103/PhysRevLett.107.137201`
- Main paper: five pages
- Supplemental material: none found
- Tables: none
- Author computational code or numerical arrays: none found

## Figures and quantitative targets

| Publication item | Classification | Decision | Target |
|---|---|---|---|
| Main Fig. 1 | ladder-tensor-network schematic | exclude | — |
| Main Fig. 2(a) | numerical magnetization profiles, 9 finite curves and isotropic asymptote | reproduce all | T001 |
| Main Fig. 2(b), main axes | numerical current-size curves, 9 finite curves and isotropic asymptote | reproduce all | T002 |
| Main Fig. 2(b), inset | easy-axis exponential current decay | reproduce | T003 |
| Text after reduced transfer matrix | easy-plane thermodynamic current and maximum near 1.63 | verify | T004 |
| Isotropic discussion | connected long-range correlation kernel | verify | T005 |
| Isotropic discussion | weak-coupling current/profile crossover | verify | T006 |
| Theorem, Eqs. (4)-(10) | exact finite MPO and Lindblad fixed point | reproduce and cross-check | T007 |
| Corollaries (ii)-(v) | triangularity/full rank, auxiliary cutoff and polynomial degree | verify separately | T008-T010 |
| Eqs. (13)-(18) | transfer observables and hopping/current identities | compare with dense traces | T011-T012 |
| Text before Eq. (19) | `O(n^2)` contraction cost and root-of-unity cutoff index/parity/dimension | verify separately against full Eq. (7) and the printed `m=3` matrix | T013-T014 |
| Eq. (19) | reduced easy-plane transfer matrix | verify | T015 |
| Text after Eq. (19) | exponential finite-size convergence and flat thermodynamic profile | verify spectrum, fitted convergence and profile | T020 |
| Easy-axis paragraph | coupling-independent profile and insulating exponent | verify | T016 |
| Easy-axis paragraph | infinite transfer-matrix rank for `Delta>=1` | prove with extendable nonsingular minors | T021 |
| Isotropic limit and Eqs. (20)-(22) | amplitudes, transfer identities, `alpha` and continuum equation | verify all | T017-T019 |
| Eqs. (8)-(10) and the surrounding proof | boundary divergence that closes the finite-chain theorem | verify explicitly | T007 |
| Eqs. (13)-(14) | general transfer-MPO formula before observable specialization | compare with direct MPO contraction | T011 |
| Isotropic-current paragraph | current-ratio asymptote in the thermodynamic limit | verify independently | T002 |

All 24 numerical publication items are explicitly mapped to a target; 21 target
contracts are used because a small number of statements are alternative tests
of the same scientific object. Every target is determined by printed equations. Plot sample density and
numerical tolerances are declared reproduction choices; they do not replace or
fit physical parameters.
