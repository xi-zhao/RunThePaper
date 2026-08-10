# Lessons Learned

## Case summary

- All 19 numerical panels/insets were grouped into nine auditable targets.
- The central SU(2), revival and exact-toy features reproduce strongly.
- Long-time scaling and finite-size entropy trends remain the dominant gaps.

## Reusable lessons

| Lesson | Why it matters | Future practice |
| --- | --- | --- |
| Dense sampling must follow the observable, not only the full plot range | A coarse t-grid visually missed the narrow first-revival minimum despite a correct single-point check | declare separate scientific inset grids in the numerical contract |
| Finite-size flow can cross the acceptance feature only at a larger reduced size | N=20 gap ratios looked Poisson-like; N=24 showed the expected GOE flow | measure at least one higher-size canary before classifying a method failure |
| A passed local assertion is not the same as paper-scale trend reproduction | T006 early collapse passed while m_c scaling did not | score individual claims and record an explicit open failure verdict |
| Random-model figures support invariant comparisons, not pointwise pixels | the paper omits its Gaussian realization | fix a new seed and compare N+1 support/perfect-return invariants |
| Source-PDF composites should be presentation-only | several supplement figures are split across active source PDFs | assemble them only after data freezing and keep them out of run inputs |
| A deferred compute target still needs a complete executable contract | a prose-only large-run plan cannot prove scientific reproducibility | commit paper-scale code/config/entrypoint/shards/checkpoints/outputs/acceptance before requesting hardware |
| Dense FSA storage is a modeling error at N=32 | FSA layers occupy disjoint Hamming-distance support | stream one layer and checkpoint it, reducing memory by O(N) without changing the observable |
| Stable differences require ordered attribution | a failed metric alone cannot distinguish code, convergence, missing input, or source claim | audit those four categories in order and never default to blaming the paper |

## What worked

- Shared sparse connectivity made nine Hamiltonian variants inexpensive.
- Symmetry resolution before level statistics prevented sector-mixing errors.
- The isolated runner reproduced every data hash with zero forbidden access.
- Post-freeze rendering preserved all nine numerical hashes.
- A compact independently generated MPO exactly matched the small open-chain
  constrained Hamiltonian; two-site DMRG then matched its two lowest exact
  eigenvalues and resumed from checkpoints.
- The paper-scale smoke exercised every target and the second invocation
  skipped every digest-matched completed work unit.

## Pain points and detection

- `python scripts/run_reproduction.py` initially could not import sibling
  `src/`; direct-entry tests should be part of every new case.
- Reduced T008 state selection shows level hybridization; future tracking should
  follow states by overlap continuity across N, not only energy proximity.
- Full-image pixel metrics reward white canvas; foreground-region score must stay
  primary and full-canvas score must be diagnostic only.

## New Failure Modes

| Failure mode | Detection | Response |
| --- | --- | --- |
| observable narrower than declared global sampling grid | compare exact checked extremum with plotted grid extremum | add a separately declared dense numerical window before freezing |
| finite-size crossing mistaken for method failure | run one higher-size canary and inspect trend | keep partial status until the flow is visible; never lower the scientific criterion silently |
| random-realization figure judged pointwise | paper omits its seed/array | compare invariant ensemble or algebraic properties and disclose a new seed |

## Reusable Checks Or Tools

| Candidate | Why reusable | Suggested destination |
| --- | --- | --- |
| inset sampling-resolution check | detects scientifically missed narrow extrema before rendering | future Harness checker/backlog |
| direct-entry import smoke test | catches case-local `scripts/` versus `src/` path failures | case template test |

## Harness backlog candidate

Add a reusable check that compares the numerical sampling density against the
narrowest declared inset feature and warns when the global grid cannot resolve
it.  This case records the lesson locally because this per-paper commit is not
allowed to modify global harness files.
