# Formula verification

All ten equation cards are source-traced and independently checked before the
numerical runner is invoked.

- Rotating-spectrum and LLL limits are exact.
- Every ideal density is normalized independently on a larger test grid.
- The Laughlin coefficient norm, relative-density peak, and angle-correlation
  normalization are analytic invariants.
- The Gaussian quartic coefficient is derived from the harmonic curvature, so
  the unpublished tweezer power cancels.
- The interaction and driven spectrum implementation is runnable but is not
  promoted to paper-exact because the paper omits the full coupled-channel map
  and Supplement Fig. S2(c) drive amplitude.
- Ramsey frequencies/coherence times and imaging widths are printed anchors;
  omitted fit amplitude/phase are not treated as scientific claims.

Machine-readable results are written by `check_formula_gate.py` to
`outputs/checks/formula_verification.json`.
