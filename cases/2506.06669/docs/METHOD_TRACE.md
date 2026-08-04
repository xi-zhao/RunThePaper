# Method Trace

## NUM001 — Closed-system state transfer

- Source: main Eqs. (1)–(11), Supplement Secs. 3, 5 and 6.
- Role: eigensystems, analytic three-site scans and unitary PST/FST dynamics.
- Inputs: site count, integer deformation `m`, coupling scale `J`, detuning, time grid.
- Algorithm: construct the zero/single-excitation tridiagonal Hamiltonian, diagonalize it once, and propagate amplitudes spectrally; use the printed analytic formula independently for the three-site identity check.
- Code: `code/src/state_transfer.py::{zigzag_hamiltonian,three_site_populations,unitary_populations}`.
- Checks: Hermiticity, mirror symmetry, analytic spectrum, population normalization and perfect endpoint transfer.
- Status: verified.

## NUM002 — Open-system Bell/W dynamics

- Source: main Eq. (12), Supplement Sec. 10.
- Role: Fig. 3, Fig. 4, Fig. S9 and Fig. S10 theory outputs.
- Inputs: FST Hamiltonian, independent `T1/T2/Tphi` channels, phase-gauged Bell/W projector and declared pulse envelope.
- Algorithm: embed vacuum plus the single-excitation sector, vectorize the density matrix, and integrate the Lindblad equation with adaptive `solve_ivp`.
- Code: `code/src/state_transfer.py::{collapse_operators,lindblad_trajectory,pulsed_lindblad_final}`.
- Checks: trace preservation, Hermiticity, positive density eigenvalues, target fidelity and solver-evaluation bounds.
- Status: verified for fixed Hamiltonians; QS009 pulse transfer remains reconstructed.

## NUM003 — Static-noise ensemble

- Source: Supplement Sec. 9 and Figs. S7–S8.
- Role: independently regenerate every published simulation-only noise panel.
- Inputs: paper sample counts (50 PST, 100 FST), three noise channels, fixed disclosed seeds and scan arrays.
- Algorithm: draw independent Gaussian perturbations, solve each Hamiltonian from scratch and aggregate mean/standard deviation of normalized fidelity.
- Code: `code/src/state_transfer.py::sample_parameter_noise` and `code/scripts/run_reproduction.py`.
- Checks: zero-noise normalization, exact sample count and large-`m` robustness ordering.
- Status: verified as a deterministic replacement realization; paper seeds/grids are unreported.
