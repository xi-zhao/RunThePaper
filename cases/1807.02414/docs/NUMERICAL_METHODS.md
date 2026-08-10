# Numerical Methods

## TBA and Onsager quadrature

- Rapidity domain: `[-8,8]`.
- Quadrature: uniform midpoint Nyström rule.
- Production grid: 384 points per species.
- Convergence grids: 192, 256, 384 points per species.
- Linear algebra: dense SciPy solves of the TBA and scattering resolvents.
- Randomness: none.
- Target parameters: ell=7 for Fig. 1; ell=3,4,7 for the text values.

The largest production matrix is `2688 x 2688`. Dense solves are appropriate
here because the complete isolated campaign finishes in about four seconds and
the matrix is small enough for local memory.

## Generated schemas

- `T001_fig1_domain_wall.npz`: x, times, three Euler curves, three projected
  diffusive curves, susceptibility, Onsager coefficient, spin diffusivity, and
  provenance labels.
- `T002_diffusion_constants.json`: ell, Delta, independent value, paper value,
  and post-generation error.

## T003 purification TEBD

- Initial mixed state: exact product purification of the paper's locally
  normalized `exp(plus/minus mu Sz)` density matrices.
- Hamiltonian: the printed XXZ bond operator, exponentiated exactly on each
  two-spin bond.
- Integrator: second-order even/odd TEBD on grouped physical+ancilla sites.
- Memory policy: retain only t=10/20/40 magnetization profiles; checkpoint the
  MPS and diagnostics instead of retaining the full time history.
- Execution: NumPy smoke path and optional CuPy A100 path.
- Convergence: dt=0.05/0.025, chi=512/768, L=256/320, all machine-declared in
  `config/tdmrg_paper_scale.json`.

## Full non-diagonal Eq. (13) lane

- Construct `W`, `w`, and the full discretized `D_tilde` from the dressed
  scattering matrix exactly as printed after Eq. (9).
- Initialize the spectral occupation perturbation as
  `delta n = plus/minus n(1-n) h_dr mu`; the magnetization readout contracts
  back to the independently computed susceptibility.
- Solve the constant-coefficient linear PDE in spatial Fourier space. A Strang
  step alternates exact diagonal advection with the eigendecomposed full
  diffusion operator.
- Convergence variants cover dt=0.1/0.05, rapidity N=192/256, and spatial
  N=2048/3072 on x in [-64,64]. The optional CuPy path targets the A100.

## Acceptance checks

- all particle densities positive;
- `|chi-1/4| < 2e-5`;
- normalized susceptibility weights;
- positive Onsager coefficient;
- all profiles odd and bounded by `1/2`;
- printed Onsager values matched within 2%;
- numerical output hashes unchanged after rendering.
- for T003, norm/truncation/boundary gates plus normalized-RMS time-step,
  bond-dimension, and finite-size convergence at all three paper times.
- for full Eq. (13), diffusion-spectrum reality/positivity, response
  normalization, real/odd/plateau profiles, and time/rapidity/space convergence.
