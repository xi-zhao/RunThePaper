# Consistency Report

## Current classification

No discrepancy is yet classified as a confirmed paper error or
`paper_error_candidate`.  Local machine checks now provide two distinct paths
where applicable, but a fresh-context reviewer has not yet completed the
protocol.  The following source-level conflicts are frozen for formal
falsification.

### DISC_WICK_SIGN — inconclusive

- Source pinpoint: Main Eq. (4b), TeX lines 128-133.
- Printed claim: the connected density covariance equals `+|G_xy|^2`.
- Independent derivation: fermionic Wick contraction gives `-|G_xy|^2` for
  distinct sites.
- Checks completed: exact Fock-state evaluation and an independent Slater
  projector calculation agree at `-0.0946745562`; the printed positive value
  has the opposite sign.
- Remaining gate: fresh-context review.
- Impact: likely a sign/definition issue; plotted positive magnitudes and their
  exponents are unaffected.

### DISC_RELEVANCE_INEQUALITY — inconclusive

- Source pinpoint: paragraph beginning “Characterizing the algebraic scaling
  phase,” Main TeX line 163 / PDF page 4 lower left.
- Printed sentence: long-range hopping is relevant for `p>3/2`.
- Internal cross-checks: Main lines 141, 149, 161; Eqs. (6), (8)-(10); and
  Supplement Eqs. (10)-(19) all require relevance for `p<3/2`.
- Checks completed: canonical-dimension calculation, direct infrared kernel
  quadrature, and an RG flow-ratio check all select relevance below `p=3/2`.
- Remaining gate: fresh-context review.
- Impact: apparent local inequality typo; subsequent formulas use the intended
  regime.

### DISC_PHASE_LABEL_SWAP — inconclusive

- Source pinpoint: Main Fig. 2 caption, Main TeX line 101; Supplement Fig. 1
  caption, Supplemental TeX line 113.
- Printed labels: `(gamma=0.3,p=1.25)` is called CFT and
  `(gamma=0.3,p=5)` algebraic.
- Internal cross-checks: the phase definition, `p_c=3/2`, surrounding
  supplement prose, the printed exponents `b=0.3`/`a=1.7`, and the colors in
  the curves imply the reverse phase names.
- Checks completed: analytic exponent classification and the independently
  generated parameter-to-scaling trajectories both place the long-range pair
  on the algebraic side and the `p=5` pair on the short-range side.
- Remaining gate: fresh-context review and paper-scale convergence.
- Impact: likely caption labels only; parameter values and plotted curves remain
  reproducible.

Machine-readable local evidence is frozen in
`outputs/checks/paper_consistency_checks.json`.  It explicitly records
`paper_error_candidate_emitted=false`.
