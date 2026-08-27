# Paper Map

## Identity

- Paper ID: `2607.15597`
- Preprint: arXiv:2607.15597v1, submitted 17 July 2026
- Title: *Deterministic atom-shuttle interconnects via ultrafast atom-ion entangling gate*
- Author: Mu Qiao
- Subjects: quantum physics; atomic physics
- Formal publication: `unpublished`
- Source: <https://arxiv.org/abs/2607.15597>
- Local inputs: `raw/paper.pdf`, `raw/paper.txt`, `paper-source/main.tex`, `paper-source/figures/`

The DOI `10.48550/arXiv.2607.15597` is the arXiv record DOI, not a journal DOI.

## Reproduction Goal

Independently regenerate the paper's central gate dynamics and the analytic
scaling claims that can be evaluated from disclosed formulas and parameters.
The case also audits every numerical figure/table. Items that depend on an
unreleased BB/APM circuit generator, per-shot decoder, optimized toggle
durations, or MQDT Stark-map state tracking are named as blocked rather than
silently treated as reproduced.

## Core Model

The core object is one atom-ion geometric-phase gate operating point. Its
state is the branch-conditioned pair of oscillator displacements and phases.
One trap period closes both displacements; the invariant is a conditional
phase of pi at `omega_g / omega = 1/(2 sqrt(2))`. Rydberg lifetime,
anharmonicity, chain length, and architecture-level use then act as explicit
extensions of this gate object.

## Paper Structure

| Section | Role | Reproduction lane |
| --- | --- | --- |
| Main text, single-ion gate | Hamiltonian, phase-space closure, CZ phase | Independent analytic numerics (`T001`) |
| Main text, ion-chain scaling | Toggle feasibility, lifetime-limited infidelity | Reconstructed disclosed scaling (`T002`) |
| Main text, hybrid architecture | Shuttle time and amortized storage cost | Independent formulas + source inconsistency audit (`T003`) |
| SM S1-S4 | Derivation, parameters, decay, Magnus force | Formula/table checks (`T004`-`T006`) |
| SM S5 | Multi-mode closure | Independent normal modes/closure attempt (`T007`) |
| SM S6 | MQDT polarizability | Blocked: no exported Stark-map data/state tracking |
| SM S7 | Anharmonic thermal robustness | Analytic feature reproduction (`T008`) |
| SM S8 | qLDPC Monte Carlo | Formula projections reproduced; direct MC blocked |
| SM S9 | Circular Rydberg extension | Analytic lifetime/thermal feature reproduction (`T010`-`T012`) |

## Equation/Method Inventory

| ID | Source | Role | Gate |
| --- | --- | --- | --- |
| EQC001 | Main Eq. (1), SM Eqs. S1-S3 | Branch forces from matched C4 and Magnus interactions | verified |
| EQC002 | SM Eq. S5 | Forced-oscillator displacement and geometric phase | verified |
| EQC003 | Main text, SM after Eq. S5 | CZ phase and coupling condition | verified |
| EQC004 | Derived from EQC001-EQC002 | Motion-traced spin density matrix and concurrence | verified |
| EQC005 | SM Tables S2-S3 | Process-averaged Rydberg decay | verified |
| EQC006 | SM Eqs. S14-S15 | Anharmonic thermal dephasing approximation | reconstructed |
| EQC007 | Fig. 3 caption/prose | Chain-length gate-duration surrogate | reconstructed |
| EQC008 | Main architecture prose | Shuttle/QCCD/photon link timing | reconstructed |
| EQC009 | Fig. 4(b) caption/prose | One-time transfer cost amortization | verified; source figure conflicts |
| EQC010 | SM Fowler-ansatz paragraphs | qLDPC distance projection | source-only |
| EQC011 | SM Eqs. S10-S11 | Multi-mode toggle closure | verified |
| EQC012 | SM S1-S4 | Operating distance and Magnus coupling/power | verified |
| EQC013 | SM S9 | Circular-state decay and thermal floors | source-only |

## Figure/Table Inventory

The complete executable decision is in `FIGURE_CLASSIFICATION.md` and
`figure_coverage.json`. There are 11 source figures (3 non-numeric) and 14
numerical tables. Main Fig. 2 is the strict central physics target. Main
Fig. 4(b) receives an explicit consistency check because the plotted rising
lines contradict the caption's `2 p_T / N_ops` amortization law.

## Assumptions and Open Inputs

- The TeX source and source-figure PDFs are complete; no author numerical data
  or code accompanied arXiv v1.
- Main Fig. 3 discloses the plateau, crossover, and linear growth but not the
  optimized duration-vs-N data. The local curve is therefore reconstructed,
  not claimed as an exact curve reproduction.
- The thermal curve is generated from the paper's analytic dephasing model,
  not from the unavailable five-order QuTiP simulation.
- qLDPC tables require Stim, `ldpc`, exact BB/APM matrices, schedules, decoder
  priors, and seeds. None are present in the source archive or local env.
- The MQDT target requires the exact Peper-Kuroda basis and manual adiabatic
  overlap tracking. The paper gives summary values but not the numerical
  Stark-map dataset.
