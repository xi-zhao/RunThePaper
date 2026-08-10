# Protocol-v2 paper assessment

## Verdict boundary

This is a self-audit artifact, not a fresh independent review. Its current
conclusion is `inconclusive`; it emits zero `paper_error_candidate` findings.
The machine-readable counterpart is
`outputs/checks/panel_target_acceptance.json#falsification`.

All paper-scale numerical grids were executed in accepted isolated run
`1811.08017-paper-exact-v2`. Therefore `insufficient_compute` does not explain
any remaining uncertainty. The historical v1 adjacent-integer precision error
was a `reproduction_defect`; it was corrected before the v2 run and is not
evidence about the paper.

## Active falsification matrix

| ID | Paper statement tested | Source pinpoint | Test and outcome | Classification |
| --- | --- | --- | --- | --- |
| PV2-002 | Fig. 2 qDRIFT and Trotter-Suzuki resource formulas | TeX lines 176–187, 763–839 | Full grid, exact `N`/`N-1` Decimal boundaries, positivity, monotonicity, and `t^2` scaling pass. | `inconclusive`: no formula mismatch, but no fresh reviewer |
| PV2-003 | Fig. 2 caption: `epsilon=10^-3`, five curve families, best of orders 2/4/6/8, Hamiltonian truncation | TeX line 147 | Grid, series, and order selection pass. The supplied paper package has no molecular term-coefficient arrays, so the caption's truncation preprocessing cannot be independently rerun. The printed aggregate tuples are sufficient to evaluate all plotted bounds. | `inconclusive` / missing indispensable author input for preprocessing only |
| PV2-004 | Fig. 2 speedups and crossover claims | TeX lines 76 and 194 | CO2 and ethane match within 1%; all crossover features pass. For propane, all four plotted comparator families were tested and none gives `591x`; the best gives `1585.0849345x`, consistent within 1% with the abstract's `1591x`. | stable discrepancy, `inconclusive` because rounded parameters, only one independent method, and no fresh review |
| PV2-005 | Fig. 4 E14/E28 laws, caption, `P_f=5%` ratios, and 2–3-order gain | TeX lines 196 and 949–1029 | A separate checker directly evaluates both closed laws, their `P_f^-3`/`P_f^-2` slopes, and all three ratios. All checks pass. | `inconclusive`: no stable mismatch, but no fresh reviewer |
| PV2-006 | “Any foreseeable device” would benefit | TeX line 194 | The numerical crossover premise passes. The universal future-device statement has no bounded hardware model in the paper, so it is not numerically identifiable from the declared method. | `inconclusive`, not a compute blocker |

The exact source paths and line pinpoints are frozen in
`config/panel_acceptance.json#protocol_v2.source_pinpoints`.

The missing-input finding is backed by a complete inventory of
`raw/arxiv-source.tar` (SHA-256
`2a046aff351d26255c945c19b1deefeeedc9c9e5a0b6aea5d9f3a1653d3c50aa`):
`MoleculesPlotTidy2.pdf`, `Phase-estimation.pdf`,
`PhaseEstimateCosts2.pdf`, and `qDRIFT_arXiv_V2submit.tex`. There is no
standalone data or code member. This proves only what the supplied archive
contains; it does not infer the contents of unpublished author inputs.

## Propane alternative-comparator test

At `t=6000`, the speedup relative to qDRIFT is:

| Comparator family | Computed ratio |
| --- | ---: |
| deterministic first order | 839727493991.041 |
| randomized first order | 313858.095376 |
| deterministic higher order, best of 2/4/6/8 | 16617.327310 |
| randomized higher order, best of 2/4/6/8 | 1585.084935 |

This rules out the four comparator families actually drawn in Fig. 2 as a
route to `591x`. It does not reconstruct unpublished unrounded molecular data
or prove that no unprinted interpretation was intended.

## Promotion gate

The case has paper-exact frozen outputs, a complete run, exact-boundary or
closed-form checks, source pinpoints, and a quantified discrepancy. Promotion
to `paper_error_candidate` is still forbidden because:

- only one genuinely independent numerical method addresses the propane
  discrepancy; protocol-v2 requires two;
- the paper publishes rounded aggregate molecular parameters, so a strict
  unrounded-parameter tolerance is unavailable;
- interpretations beyond the four plotted comparators have not been excluded;
- the required inventory-first fresh-context review is absent.

`paper_supported` is also reserved for that fresh reviewer. Until those gates
are satisfied, stable agreement and disagreement alike remain `inconclusive`.
