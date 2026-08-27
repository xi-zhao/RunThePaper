# Method Trace

## MTH001 — vectorized analytic evaluation

- Inputs: paper-exact dimensionless parameters from the figure captions and
  closed expressions EQ001-EQ004.
- Method: evaluate the equations with NumPy on declared grids; no source curve
  is used to generate the numerical result.
- Independent checks:
  - hyperbolic limiting identities for T001;
  - exact energy invariant and deposited author arrays for T002C/T003;
  - absolute-versus-normalized `r=0` limits and all nine formula-derived
    endpoint values for TS03;
  - general-to-reduced scattering identity and the analytic optimum for T004.
- Rendering happens only after the numerical arrays and checks exist.
- Author data are comparison evidence, never generator inputs.

## MTH002 — quadratic open-system propagation

- Inputs: the quadratic squeezed-frame Hamiltonian, local linear jumps, and
  collective squeezed-reservoir channel.
- State representations:
  - cutoff-free first and second Gaussian moments provide the formal
    propagation used by T002A and TS01;
  - a finite two-mode Fock basis provides a bounded sensitivity diagnostic
    because the source says that its simulations use a finite-dimensional
    Hilbert-space truncation but does not disclose the cutoff.
- Evolution:
  - the Gaussian branch exponentiates the constant affine moment generator;
  - the finite-Hilbert branch vectorizes the density matrix in column-major
    order and applies the sparse Lindblad matrix exponential with a Krylov
    propagator.
- Method boundary: cutoff 10 is used only in an exploratory three-detuning
  surface probe. The 6/8/10 cutoff scan shows that truncation changes panel
  amplitudes materially, so no inferred cutoff is promoted to a paper
  parameter or used to generate the formal TS01 artifact.
- Validation contract:
  - preserve Hermitian-conjugate Gaussian moment pairs and non-negative
    occupations;
  - preserve trace and Hermiticity;
  - keep final density matrices positive within tolerance;
  - keep occupations in the finite-basis physical range;
  - cross-check both finite-Hilbert branches against Gaussian propagation
    before truncation effects become appreciable;
  - for Figure S1, require weak-coupling resonance to lie within 1% of the
    global energy peak, matching the qualitative source-image resolution;
  - require strong coupling to gain at least 5% at
    `|omega_s/J| >= 0.75`, so a grid-level peak shift alone cannot pass.
- Code:
  - `src/squeezing_nonreciprocity.py`;
  - `src/finite_hilbert_dynamics.py`;
  - `src/ts01_feature_contract.py`;
  - `scripts/run_target.py`.
