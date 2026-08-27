# Derivation Trace

## Core object

The paper uses one linear two-mode Gaussian system in three roles:

1. its first-moment drift defines the effective nonreciprocal coupling;
2. its first and second moments define battery energy and ergotropy;
3. its frequency-domain response defines optical transmission.

The completed campaign evaluates every theory-numerical lane. Closed analytic
expressions drive the steady-state and scattering targets, while an exact
affine Gaussian propagator drives the time-domain targets. A separate finite-
Fock implementation is used only to diagnose the published Figure S1 cutoff.

## EQ001 — squeezing-dependent NRC

- Source: `paper-source/Manuscript.tex:95-123`.
- Under the balanced nonreciprocity condition, the surviving forward coupling
  is
  `J_eff = -/+ 2 i J (cosh(r_a)cosh(r_b) -
  exp(i Delta theta)sinh(r_a)sinh(r_b))`.
- Dividing its magnitude by `2J` gives `G`.
- If `r_a=r_b=r` and `Delta theta=0`, the hyperbolic identity
  `cosh^2(r)-sinh^2(r)=1` gives `G=1`.
- With `r_a+r_b=2r`, setting `Delta theta=pi` gives
  `G=cosh(r_a+r_b)=cosh(2r)`, independent of amplitude asymmetry.
- If one mode is unsqueezed, the phase-dependent term vanishes and the same
  maximum `cosh(2r)` is obtained.
- Code: `src/squeezing_nonreciprocity.py::effective_enhancement`.

## EQ002 — steady-state battery energy

- Source: `paper-source/Manuscript.tex:137-149`.
- Write each case as `E_i^ss = E^ss + A_i sinh^2(r)`, with
  `E^ss=64J^2 epsilon^2/(2J+kappa)^4`.
- The three coefficients are rational functions of `J` and `kappa`; their
  common denominator exposes the exact invariant:

  `E_a^ss + E_b^ss - E^ss = E_c^ss`.

- This identity is checked on broadcast grids, independently of the author
  arrays.
- For Figure S3, divide every branch by its nonsqueezed baseline at the same
  coupling:

  `R_i(r;J) = E_i^ss(r;J) / E^ss(J)`.

  Since the added terms are proportional to `sinh^2(r)`, all nine branches
  obey `R_i(0;J)=1`. At the three published couplings the absolute baselines
  are `1.5241579`, `1.0412328`, and `0.1176048`, so absolute-energy curves
  cannot all start at one. The visible S3 endpoints instead equal the
  formula-derived normalized endpoints. This is an internal source-figure
  semantics check, not pixel digitization: source pixels are inspected only
  after both absolute and normalized arrays have been generated.
- Code: `src/squeezing_nonreciprocity.py::steady_state_energy` and
  `::steady_state_energy_enhancement`.

## EQ003 — coupling derivative and optimum

- Source: `paper-source/Manuscript.tex:451-457`.
- Differentiate EQ002 while holding `r`, `kappa`, and `epsilon` fixed.
- Each derivative has denominator `(2J+kappa)^5`; the numerator sign therefore
  determines maxima and minima.
- The plotted optimum is the first positive-to-negative zero as `J` increases.
  A negative-to-positive zero is a local minimum and is not labelled
  `J_op`.
- For cases (b) and (c), solving the numerator for `sinh^2(r)` gives the
  threshold curve. The global plotted threshold is its maximum over the paper
  `J` interval.
- Code:
  `src/squeezing_nonreciprocity.py::steady_state_energy_derivative`.

## EQ004 — forward transmission

- Source: `paper-source/Manuscript.tex:515-601`.
- The lower-triangular Langevin drift makes the reverse coefficient `T_ab`
  identically zero.
- The forward output has a normal channel `g_N` and a counter-rotating
  anomalous channel `g_A`. Squaring and adding their independently routed
  amplitudes gives the general `T_ba(omega,omega_s)`.
- At `omega_s=0`, the denominators coincide. Expanding
  `|g_N|^2+|g_A|^2` yields

  `cosh(2r_a)cosh(2r_b) -
  cos(Delta theta)sinh(2r_a)sinh(2r_b)`.

- Under `Gamma=2J`, differentiating the zero-frequency rational prefactor gives
  `J'_op=sqrt(kappa_a kappa_b)/2`.
- Code: `src/squeezing_nonreciprocity.py::forward_transmission`.

The main-text TeX has a misplaced brace around the cosine term. The
supplemental scattering matrix and its final two-channel equation fix the
unambiguous expression used here.

## EQ005 — Gaussian moment closure

- Source: `paper-source/Manuscript.tex:315-381`.
- A quadratic Hamiltonian and jump operators linear in `a,b` preserve Gaussian
  states. In the adjoint master equation, a monomial of degree at most two maps
  to an affine combination of monomials of degree at most two.
- Therefore all moments needed for battery energy, power, and ergotropy form a
  finite system `dot(m)=A m+c`.
- This establishes the method before any Hilbert-space truncation is chosen.
- Execution: T002A is reproduced. TS01 is generated from the exact affine
  Gaussian system and compared with an independent finite-Fock probe. The
  source's strong-coupling amplitude is rejected as unconverged because the
  supplement omits its cutoff.
- Code:
  `src/squeezing_nonreciprocity.py::gaussian_battery_energy_dynamics`
  and `::gaussian_master_equation_energy_dynamics`.

## EQ006 — passive energy and ergotropy

- Source: `paper-source/Manuscript.tex:488-513`.
- Subtract first moments to form the centered occupation and anomalous moment.
- Their single-mode symplectic invariant is `Jcal`.
- The passive Gaussian state has occupation
  `(sqrt(Jcal)-1)/2`; multiplying by `omega_b` gives passive energy.
- Vacuum gives `Jcal=1`; a coherent displacement cancels from the centered
  moments. Both are independent limiting checks.
- Execution: T002D and TS04 are reproduced; passive energy is nonnegative and
  total energy minus passive energy remains a valid ergotropy margin.
- Code: `src/squeezing_nonreciprocity.py::gaussian_invariant`,
  `::passive_state_energy`, and `::steady_state_ergotropy`.
