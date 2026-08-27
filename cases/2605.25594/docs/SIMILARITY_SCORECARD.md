# Similarity Scorecard

## Overall

- Scientific similarity score: `34.19/100`
- Similarity level: `feature_not_accepted`
- Atomic final resolution: `73/73` (`100%`)
- Paper-exact reproduced: `0/73`
- Objectively externally blocked: `73/73`
- Attempted but not reproduced: `0/73`

The final-disposition result does not erase the useful partial evidence. The
case independently reproduces several Anderson-model features at reduced or
paper-subset scale, but no atomic item is promoted to paper-exact completion.
The score stays separate from lifecycle/final disposition.

## Proven boundaries

| Boundary | Targets | Atomic items | Evidence |
| --- | ---: | ---: | --- |
| Current compute capacity | 23 | 71 | 12,495 frozen eigensystems; measured A100 timings imply an 11.37-day serial lower bound; the current L=38 reduction needs at least 44.87 GiB before eigensolver workspace, versus 18 GiB locally. |
| Publication underspecification | 1 (`T009`) | 2 | Appendix Fig. 11 omits the numerical Gamma cutoffs, ordinate normalization and parameter-selection protocol required for unique paper-exact curves. |

All 24 target implementations execute through raw/reference-free code paths at
reduced validation scale. The compute-blocked targets have runnable paper-scale
code and config; `T009` has an attested analytic implementation whose limiting
families pass.

## Existing feature evidence

- A100 `L=24/28/31` data place the gap-ratio midpoint at `W=16.56-16.60`.
- The critical spectral tail is approximately `0.48`, versus the paper's `0.52`.
- Average/typical susceptibility separation grows in the localized regime.
- The broadened-Drude analytic runner reproduces both Lorentzian and power-law limits.

These are feature-level results, not substitutions for the missing paper-scale
finite-size ladders or undisclosed Appendix parameters.

## Machine-readable record

See `outputs/checks/similarity_scorecard.json`,
`outputs/checks/authoritative_reproduction_state.json`,
`outputs/checks/resource_benchmark.json`, and
`outputs/checks/publication_input_audit.json`.
