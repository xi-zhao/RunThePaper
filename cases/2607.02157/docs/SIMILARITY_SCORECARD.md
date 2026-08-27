# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The score measures numerical similarity, not visual styling. Line width, color,
marker choice, layout, and 3D camera angle are not counted as scientific
mismatches when the underlying numerical feature matches.

## Case Score

- Overall score: **79.18 / 100**
- Similarity level: **numerical_feature_reproduction**
- Machine-readable record: `outputs/checks/similarity_scorecard.json`

## Whole-paper Reproduction Measure

- Reproduction degree: **79.02 / 100**
- Scope coverage: **43 / 43 eligible items = 100%**
- Covered-item fidelity: **79.02 / 100**
- Uncovered eligible items: **0**
- Explicitly excluded non-numerical items: **3** (Main Fig. 1(a-c))
- Evidence grade: **E1** (`science_not_verified`, `execution_not_attested`)

The 79.18 historical score aggregates three targets with authored target
weights.  The 79.02 public reproduction degree instead gives every atomic
eligible display item one vote and assigns zero to uncovered items.  The latter
is the comparable whole-paper metric; neither number is a lifecycle-completion
claim.

The A100 paper-exact campaign lifted `parameter_match` from `reduced_scale`
(cap 70) to `paper_exact` (cap 100). Every target is now bound by
`reference_comparison = visual_feature_contract` (cap 80): we compare curve
features against the published panels, not against author data or digitized
curves. This is the honest ceiling without the authors' numerical data — we
do not digitize their figures (pixel-derived data is not scientific
reproduction).

## Targets

| Target | Figure | Score (capped) | Raw | Key evidence |
| --- | --- | ---: | ---: | --- |
| T001 (critical) | Fig. 2 | 80 | 86 | 14/14 feature-contract checks at paper-exact ensembles; cluster row near-quantitative (chi_m peak 2.19 vs ~2.25; beta*W_irr 0.499 vs ~0.52); TFIM peak 1.80+-0.11 over 100 realizations; NMSE minima at the capacity peaks; aggregation convention adjudicated |
| T002 | Fig. S1 | 80 | 86 | G(omega) peak 2.72 @ 0.355 (closed form 2.27, paper ~2.3); OBC spectral fingerprints match panel c exactly |
| T003 | Fig. S2 | 77 | 77 | tau/h orderings and critical-region peaks; full-Pauli NMSE minima aligned and on the paper's absolute scale; deep-MBL memory inversion confirmed at full scale |

## What blocks a higher score

1. `visual_feature_contract` reference (cap 80): the paper publishes no
   numerical data. The only paths above 80 require the authors' data
   (`author_data`, cap 100) or digitizing the Fig. 2 curves (`digitized_curve`,
   cap 95) — the latter we decline on principle, since pixel-derived agreement
   is not scientific reproduction.
2. T003 raw (77): the deep-MBL tail and the multi-step panels carry genuine
   physical caveats (memory inversion, partial decoupling) that hold it just
   below the cap.

## Per-step identity as internal evidence

The central theoretical identity beta*W_irr = chi_d (Eq. 13) holds at machine
precision (max residual 8.9e-16) across every production run — the strongest
internal consistency evidence this framework admits.
