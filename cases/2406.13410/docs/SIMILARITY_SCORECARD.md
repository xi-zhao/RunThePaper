# Similarity Scorecard

- Overall: `70.00/100` — numerical feature reproduction
- Scientific-region foreground pixel mean: `54.156/100` — primary render metric
- Full-canvas pixel mean: `91.950/100` — layout diagnostic only
- Scientific assertions: `51/51` passed across `17/17` targets
- Generated-data provenance: independent numerics for `17/17`
- Final-reproduction eligible targets: `0/17`

The score is capped at 70 because the only published references are mixed
source figures; author arrays are unavailable.  Five targets use exact analytic
or dimensionless branches, three use reduced reconstructed MD, and nine use
printed parameter subsets plus explicitly reconstructed short-range inputs.

High visual similarity cannot override a failed physics assertion.  Conversely,
the scientific-region pixel mean is intentionally depressed by experimental
markers that cannot be removed or digitized without violating the source-pixel
boundary.
