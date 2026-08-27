# Method trace

## M1 — Formula-only dispersion

- Inputs: Eq. (1), fused-silica Sellmeier constants, and the related paper's
  printed PCF pitch/hole diameter.
- Assumption: scalar capillary effective radius, independently swept.
- Output: `omega'(omega)` and phase-matching roots.
- Boundary: the exact Nature fibre model is unavailable; no Fig. 2 path is a
  scientific input.

## M2 — Phase matching

Broad-bracket bisection evaluates NRR, Hawking-partner, and backreaction roots
from Eqs. (1), (B.1), and (B.3).  Formula/root ordering passes; exact paper
wavelength alignment remains blocked.

## M3 — Analytic-signal UPPE

The independent PyTorch pseudo-spectral solver implements the positive-
frequency projection and THG/SPM/conjugated-SPM channels.  IFRK4 and fixed-step
Dormand-Prince share the same domain model.  The campaign enumerates all six
probe wavelengths, six pump powers, and five prechirps in Supplement Fig. 1.

## M4 — Counterfactual and convergence

Four batched states isolate the conjugated-SPM contribution without changing
initial conditions.  Reduced tests cover the exact linear limit, frequency
projection, and two-integrator parity.  Full grid/step convergence is coded
but unrun.

## M5 — Fig. 4 theory

`hawking_peak_profile` and `sideband_spectrum` implement Eqs. (C.3), (C.4),
and (D.1).  All six printed `mu` values are evaluated over a declared
width/modulation/backreaction grid.  The source markers are never fit inputs.

## M6 — Fig. 5 theory and review

The runner generates the equal-slope consequence of Eqs. (D.2-D.3) in a
dimensionless gauge.  The experimental points, slope magnitude, and intercepts
cannot be reconstructed.  Any line-selection discrepancy is comparison-only
until protocol-v2 fresh review.
