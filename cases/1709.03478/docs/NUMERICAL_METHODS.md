# Numerical Methods

## Physical model and representation

The independent solver discretizes the paper's continuum bichromatic
Hamiltonian in primary-site coordinates.  Eight midpoint grid points per site
give an N=qL real symmetric tridiagonal operator.  Only the lowest L states are
selected.  CDW and Gaussian-cloud preparations use localized primary-band
orbitals.  The expansion preparation separately diagonalizes the sliced
center-third Hamiltonian and releases its occupied eigenstates into the full
system, matching the paper method.  Finite-time observables use spectral
phases in t/τ and stationary observables use the diagonal ensemble.

No numerical runner input includes `raw/`, `references/`, source PDFs, original
figures, digitized curves or author arrays.

## Paper-scale deck

`config/paper_scale_rerun.json` is schema v2 and contains the complete
top-level `parameters` object consumed by the runner.

| Target | Production scale | Printed/method inputs |
| --- | --- | --- |
| T002 | L=738, q=8, six phases | Vp=4; Vd=0, 0.57, 1.04; 0…3000 τ |
| T003–T004 | L=738, q=8, six phases, central + eight tube nodes | Vp=3…8; independent 0.025-Er Vd grids; stationary I/D; threshold 0.015 |
| T005 | L=369, q=8, six phases | FWHM≈123 sites; Vp=4; four Vd values; trap edge 0/0.003 Er; 0…3000 τ |
| T006 | L=738, q=8, six phases, central + eight tube nodes | Explicit finite-time I/D at 3000 τ on the Vp=4 scan |

The T003/T004/T006 tube average is a documented method-derived proxy, not an
author-histogram match.  Central-tube rows and proxy rows stay separate in
every CSV.

## Convergence campaign

| Profile | Purpose | Blocks |
| --- | --- | ---: |
| `production_q8_l738` | production evidence; T005 remains at its printed L=369 | 432 |
| `grid_reference_q6` | q=6→8 discretization check for all targets | 432 |
| `size_reference_l610` | L=610→738 finite-size check for T002/T003/T004/T006 | 384 |
| `phase_reference_12` | six→twelve deterministic phase nodes | 864 |
| `tube_reference_15` | order-(8,4)→(10,6) product-Hermite refinement: eight→fifteen tube nodes | 672 |
| **Total** | production plus protocol-v2 convergence | **2,784** |

Each block is atomic and resumable.  The full deck contains approximately
226,560 selected-band eigensolves before alternative-solver checking: 113,376
full-system solves plus 113,184 isolated center-third preparation solves.  This
is why the paper-scale computation is code-ready but not claimed as locally
run.

## Independent checks and adjudication

The first check verifies eigenvector orthogonality, preparation projection and
observable normalization across frozen production blocks.  The second rebuilds
a frozen Hamiltonian as sparse CSR and solves it using ARPACK `eigsh`, rather
than the main LAPACK tridiagonal path.  Target-specific absolute convergence
tolerances live in the config and are reported without tuning after seeing
source pixels.

`outputs/checks/paper_scale/checks/protocol_v2_assessment.json` is deliberately
conservative: unrun or unconverged work is `inconclusive`; solver disagreement
is `reproduction_defect`; `paper_error_candidate` requires a later fresh
reviewer satisfying the full protocol-v2 evidence contract.
