# Claim--evidence map

This file records the frozen evidence behind manuscript-level quantitative
claims. The authoritative source is `claim-metrics/summary.json`, generated from
PRAgent revision `09ab3fb65c5dc2d2cf05a4fbf3c8a42b4d4de5f5`.

| Manuscript claim | Authoritative evidence | Interpretation boundary |
|---|---|---|
| The public cohort contains exactly 100 paper-reproduction cases. | `summary.json → population.papers`; `data/cohort_100.json` | The three PRAgent-only cases named in the README are excluded independently of score. |
| All 3,933 Claim Checks have a direct, uniquely verified Claim mapping. | `claim-mapping-audit/records.csv`; `claim-mapping-audit/summary.json` | Mapping completeness is structural and does not imply reproduction success. |
| All 3,933 Checks have a terminal disposition. | `summary.json → check_metrics`; `claim-metrics/checks.csv` | 100% final resolution means 100% honest accounting, not 100% reproduction. |
| Check outcomes are 2,068 reproduced, 1,134 objectively blocked, 731 attempted but not reproduced and 0 pending. | `summary.json → check_metrics.disposition_counts` | The categories are mutually exclusive and exhaust the fixed denominator. |
| Equal-weight numerical-Claim success coverage is 40.55%. | `summary.json → claim_metrics.successful_claim_coverage`; `claims.csv` | Claims are macro-averaged; papers with many panels do not dominate the result. |
| Equal-weight Claim blocker and attempted-failure rates are 21.93% and 37.52%. | `summary.json → claim_metrics` | Objective blockers require proof; unsuccessful agent-side work is not relabelled as external. |
| Conditional Claim Fidelity is 92.97/100. | `summary.json → claim_metrics.conditional_fidelity` | It uses only successful mass with trusted primary scientific-region evidence. |
| Fidelity evidence covers 23.37% of successful Claim mass. | `summary.json → claim_metrics.fidelity_success_mass_coverage` | The remaining successful mass has no invented or imputed pixel score. |
| Conditional Claim Reproduction Degree is 37.70/100, with bounds 8.81--39.88/100. | `summary.json → claim_metrics.reproduction_degree_*` | The point estimate is success coverage × measured conditional Fidelity; bounds assign missing successful Fidelity 0 or 100. Components and bounds must accompany the product. |
| Mean and median paper-level successful Claim coverage are 56.16% and 58.57%. | `summary.json → distributions.paper_successful_claim_coverage`; `papers.csv` | This describes the curated cohort, not a random sample of physics. |
| Conditional paper Fidelity is available for 32 papers, with mean 93.38/100 and median 93.71/100. | `summary.json → distributions.paper_conditional_fidelity`; `papers.csv` | Papers without trusted comparisons are omitted from this conditional distribution and remain visible through evidence coverage. |
| Fifteen Claims have no numerical Check. | `non_numeric_claims.csv`; `summary.json → non_numeric_claims` | Eleven are pure theory: five verified by formula/invariant and six partially verified. Four experimental/meta Claims are excluded from numerical Fidelity. |
| The terminal audit produced no numerical rerun candidate. | `rerun_queue.csv`; `summary.json → queues.numerical_rerun_targets` | No A100 or local physics rerun was needed to obtain the frozen headline. |
| 346 reproduced Targets remain eligible for optional pixel-evidence work. | `pixel_evidence_queue.csv`; `summary.json → queues.pixel_evidence_targets` | This is a render-evidence queue, not missing scientific reproduction and not a request to alter numerical arrays. |

## Fidelity guardrail

A score is admitted only when all linked Targets have passed lifecycle-valid
`scientific_region_v1` comparisons, the generated crop comes from an independent
render, and the Check is already scientifically reproduced. Source pixels may
guide layout in the RenderContract but cannot become numerical data or change a
scientific disposition.

## Prohibited claims

- “PRAgent fully reproduced all 100 papers.”
- “100% final resolution means 100% successful reproduction.”
- “92.97 Fidelity applies to every successful Claim.”
- “A high pixel score proves the physics is correct.”
- “Every objective blocker is impossible in principle.”
- “A paper-error candidate proves the publication is wrong.”

## Permitted headline

> Across a fixed public cohort of 100 physics papers, PRAgent mapped and
> terminally adjudicated all 3,933 numerical Claim Checks. Equal-weight
> numerical-Claim success coverage was 40.55%; 21.93% was objectively blocked
> and 37.52% was attempted but not reproduced. Conditional Fidelity was
> 92.97/100 on the 23.37% of successful Claim mass with trusted scientific-region
> comparisons, yielding a conditional Reproduction Degree of 37.70/100 with
> bounds 8.81--39.88/100.
