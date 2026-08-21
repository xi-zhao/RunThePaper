# Lessons Learned

1. A paper without figures can still have a complete, high-value scientific reproduction; inventing a paper-figure target would weaken the evidence model.
2. Closed-form formulas benefit from an independent dynamics path. Here direct BdG integration tests the LZ mapping instead of merely re-evaluating the same exponent twice.
3. Literature-fit comparisons must remain distinct from data owned by the reproduced paper.
4. Universal claims need declared numerical validation grids, but those grids must not be mislabeled as undisclosed paper parameters.

## New Failure Modes

- A figure-free paper can be falsely classified as having no reproduction scope. The inventory must include equations and quantitative prose, not only plotted panels.
- Re-evaluating the Landau-Zener closed form would be circular. A direct time-dependent BdG solve is required as an independent path.

## Reusable Checks Or Tools

- `src/dziarmaga_ising/model.py::bdg_excitation_probability` supplies a reusable two-level direct-dynamics cross-check.
- `scripts/build_scorecard.py` records formula-level targets with an explicit `pixel_status=not_comparable` instead of inventing pixel evidence.
