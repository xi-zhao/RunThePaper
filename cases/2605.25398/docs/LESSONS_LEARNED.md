# Lessons Learned

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Experimental papers can still have a reproducible theoretical core. | A paper may mix hardware photos, experimental data, and clean numerical theory. Treating the whole paper as "experimental" would miss the reproducible model. | Classify panels carefully and separate theoretical curves from measured points. |
| Missing reference curves should cap the score, not invalidate the reproduction. | Many arXiv sources include figures but not raw curve data. The Agent can still reproduce physical features from formulas. | Score feature-level matches, but cap complete-reproduction claims until author data or digitized curves exist. |
| Use analytical feature checks when exact data are unavailable. | Here, exact experimental data are missing, but the paper gives strong internal checks: PT minimum near `t*`, Haar entropy, PR separation, and `t^2/t^4` OTOC slopes. | Turn paper-derived feature claims into machine-readable checks. |
| Reuse eigendecomposition across time before optimizing anything else. | Many quantum dynamics papers repeatedly evaluate `exp(-iHt)`. Recomputing dense exponentials can waste time and introduce noise in performance claims. | Diagonalize Hermitian matrices once and reuse phases across all time grids. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Mixing theoretical and experimental panels | Fig. 2 contains hardware panels plus probability bars. | Label panel-level scope, not just figure-level scope. |
| Overclaiming without author data | The main curves match features, but not exact author points. | Use `missing_reference_curve` as a clear failure type and cap the score below complete reproduction. |
| Forgetting post-selection normalization | The paper's probabilities are conditional on collision-free two-click events. | Every boson-sampling case should state full state count, retained state count, and normalization rule. |
| Treating OTOC as a separate object | In this paper, OTOC-equivalent observables are the same two-photon probabilities under a mapping. | Reuse the probability kernel and document the mapping in the derivation trace. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Panel-level classification | Mixed theory/experiment papers. | Fig. 2 was split into hardware context and probability-distribution target. |
| Feature checks before visual comparison | Missing author data or noisy experimental figures. | Main checks pass through `reproduction_feature_checks.json`. |
| Keep domain-specific physics in the case | Boson-sampling formulas are not a general harness primitive yet. | The permanent/probability code stays in `case/2605.25398/src/`. |
| Promote abstract rules only | Harness should stay general. | The reusable lesson is panel-level mixed-source handling, not "boson sampling" itself. |

## New Failure Modes

- `mixed_panel_scope`: one figure can contain schematics, hardware photos, experimental measurements, and theoretical numerical panels.
- `missing_reference_curve`: arXiv source figures are available, but curve data and author seeds are missing.
- `conditional_distribution_mismatch`: boson-sampling experiments may normalize over a retained subset of outcomes, not the full Hilbert space.

## Reusable Checks Or Tools

- Add a panel-level scope field to target specs.
- Add a generic reference-data availability field: `author_data`, `digitized_curve`, `source_figure_only`, `none`.
- Add a generic "analytical feature check" pattern for cases where raw paper curves are missing.

## copied_to_backlog

- Added a new harness backlog item for panel-level mixed-source figure classification.
- Added abstract experience about missing reference curves and analytical feature checks to `PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.
