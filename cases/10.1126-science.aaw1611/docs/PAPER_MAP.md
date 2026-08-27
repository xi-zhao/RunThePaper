# Paper Map

## Identity and scientific question

- Paper: *Strongly correlated quantum walks with a 12-qubit superconducting processor*.
- DOI: 10.1126/science.aaw1611.
- Main question: how calibrated hopping and attractive on-site interactions shape one- and two-photon quantum walks on a finite superconducting chain.
- Numerical object: Bose-Hubbard evolution in fixed-particle-number sectors.

## Full-paper inventory

The main paper and 35-page supplement are enumerated in `figure_coverage.json`: 92 items, including 38 theoretical numerical targets, 41 experimental measurements, 12 non-numeric panels, and Table S1 as a source-parameter table.

## Equation inventory

| Cards | Role | Status |
| --- | --- | --- |
| EQC001-EQC003 | Hamiltonian, fixed-sector basis, coherent evolution | source/symbolic gate passed |
| EQC004-EQC006 | density, entropy, correlation, concurrence, velocity | source/symbolic gate passed |
| EQC007-EQC008 | two-particle correlator, double occupancy, hard-core limit | source/symbolic gate passed |
| EQC009 | disorder and detuning-renormalized hopping for S9-S10 | verified from Supplement Sec. IV.C |
| EQC010 | fidelity and optional Lindblad model for S11 | reconstructed; realization conventions unpublished |

## Target families

- T001: six one-photon density panels.
- T002: three information-spreading panels/regions.
- T003: fifteen two-photon theory panels, including twelve S20 matrices.
- T004: one double-occupancy panel.
- T005: twelve S9-S10 disorder panels plus one S11 fidelity figure.

## Assumptions and boundaries

- Printed MHz values are converted to angular rad/ns by `2*pi*1e-3`.
- Equal on-site frequencies are removed as a fixed-number global phase.
- S9-S10 use a deterministic source-independent representative seed within the paper-declared 50-realization equivalence class.
- S11 uses an explicit standard Lindblad reconstruction; it is not author-realization exact.
- Source pixels and digitized values are forbidden as numerical-runner inputs.
- Printed S20 label times are the scientific time contract; the post-hoc -5 ns optimum is comparison-only.
