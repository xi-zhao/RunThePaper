# Lessons Learned

1. A minimum-over-random-samples threshold is not portable when the paper omits
   sample identity.  The interrupted pilot used such a threshold; it was
   replaced by claim-aligned ensemble means and distribution distances, then
   evaluated on a fresh declared seed.
2. Missing random seeds do not justify digitizing source bars into the
   generator.  Regenerate the disclosed ensemble, freeze it, then use source
   pixels only as post-run distribution evidence.
3. The level-1 energy has analytic beta dependence.  Eliminating that search
   dimension makes full paper-scale RQAOA practical without weakening the
   formula trace.
4. Exact normalization matters: a high RQAOA ratio is trustworthy only when
   every denominator is independently proved at zero gap.
5. Direct SSIM is scientifically misleading when plotted samples differ.
   Explicitly mark it not applicable and replace it with a metric invariant to
   the missing identity—in this case sorted colored-bar heights.

The reusable harness lesson is that stochastic figures need an explicit
`sample_identity` contract and a distribution-aware post-run comparison mode.

## New Failure Modes

- `random_extreme_threshold_mismatch`: using a minimum/maximum observed in an
  unpublished 16-sample ensemble as a hard threshold for a different ensemble.
- `false_instance_pixel_pairing`: comparing bar positions as though two random
  samples shared identity.
- `source_feedback_leak`: choosing generated seeds or values after looking at
  the reference bar heights.

## Reusable Checks Or Tools

- A `sample_identity` declaration and distribution-aware comparison belong in
  the shared harness; the requests are recorded in
  `PRAgent-workflow/HARNESS_BACKLOG.md`.
- The general workflow lesson is recorded in
  `PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.
- This case's post-run prototype is
  `scripts/build_comparisons.py`; it records sorted distribution MAE,
  Wasserstein distance, and proof that source pixels were evaluation-only.
