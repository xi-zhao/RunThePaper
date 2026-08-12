# Paper review protocol v2

The reproduction is also an attempt to falsify the paper, not merely to imitate its plots.

## Required order

1. A fresh reviewer reads only the paper/inventory bundle and independently enumerates every numerical panel and quantitative claim.
2. That inventory is frozen and hashed before the reviewer sees our formulas, code, generated arrays, checks, or discrepancy notes.
3. The reviewer then inspects the falsification bundle and classifies each target as supported, reproduction defect, insufficient information/compute, inconclusive discrepancy, or paper-error candidate.
4. A paper-error candidate requires two genuinely distinct strong checks, an explicit falsification attempt, source pinpoints, quantified impact, and exclusion of implementation, parameter, finite-size, timestep, and compute explanations.

## Current review leads, not conclusions

- Fig. 4 panel references in the surrounding prose are shifted relative to the caption/assets.
- The main-text verbal area force is twice the exact per-edge contribution obtained from Eq. (1) and Appendix Eqs. (A11–A12).
- The appendix uses `∇E` notation for a vector whose sign is that of the force in at least part of the area derivation.

These remain `inconclusive` until the fresh-context channel validates them. None changes the numerical model because the runner derives force directly from the energy.

## Reviewer isolation

The numerical runner cannot read `raw/` or source figures. The inventory reviewer cannot read the reproduction workspace. The falsification reviewer receives only the frozen inventory and a hash-bound bundle of formulas, code, generated data, and checks; it does not receive the original conversational explanation.
