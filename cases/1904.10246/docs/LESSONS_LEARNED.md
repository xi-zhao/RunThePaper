# Lessons Learned

## Case Summary

- Paper: *Amplitude Estimation without Phase Estimation*
- PaperID: `1904.10246`
- Final status: complete scientific reproduction; pixel workflow complete
- Main reproduced targets: Figure 2, Tables 1–2, Appendix Figure A
- Main blockers: none; absent author raw random arrays are an evidence boundary, not an executable blocker

## What Worked

- Verifying probability, likelihood, schedule sums, QAE candidates, and resource formulas before Monte Carlo execution prevented method mistakes from being disguised as noisy agreement.
- One guarded entrypoint per target made output ownership explicit and auditable.
- Reported slopes and analytic bounds provided strong independent evidence when author samples were unavailable.

## What Was Difficult

- The likelihood is multimodal because amplification aliases \(\theta\); local optimization alone is unsafe.
- Source EPS files could not be rasterized without Ghostscript, requiring a frozen-PDF reference lane.
- Table content was exact on the first pass, while layout initially failed; scientific and pixel states needed separate repair logic.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Verify the estimator before simulation | Monte Carlo plots can look plausible under an incorrect likelihood branch | Require small analytic cases and global-domain checks before target readiness |
| Separate source reference from generated data | Pixel similarity can otherwise hide copied or digitized evidence | Store provenance on every dataset, panel crop, and scorecard row |
| Treat layout as its own state | A scientific pass does not imply a visual pass | Keep numerical outputs stable while repairing only rendering contracts |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Local maximum of an aliased likelihood | multiple amplified probabilities share local modes | use a global coarse search followed by bounded local refinement |
| Conflating query stage with query count | LIS and EIS have different sums | make query accounting an independently tested formula |
| Excess whitespace in table render | first Table 1 IoU was `0.569` | derive canvas/crop aspect ratio before styling text |
| Assuming EPS tool availability | Ghostscript was absent | test source renderer early and retain PDF-page fallback evidence |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Explicit per-target execution | every multi-artifact paper | four separate guarded runs, four separate checks |
| Analytic plus stochastic assertions | author raw arrays unavailable | Figure 2 slope/CR checks and Figure A percentile checks |
| Cell-exact table contracts | paper publishes finite values | 6/6 Table 1 entries and 37/37 Table 2 cells |
| Before/after pixel evidence | a contract fails after science passes | Table 1 IoU `0.569 → 0.88899` |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Scientific pass with layout-contract failure | first Table 1 render | require independent scientific and pixel terminal states |
| Missing legacy source renderer | EPS extraction lane | check executable availability and record a source-preserving fallback |
| Unpublished stochastic realization | Figures 2 and A | cap evidence tier and compare reported summaries rather than claiming raw identity |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| global-MLE small-case test pattern | detects alias/local-optimum errors | keep case-local until validated on another likelihood paper |
| table crop/aspect preflight | prevents predictable pixel failures | future harness backlog candidate |
| PDF-page reference fallback record | preserves source provenance when EPS tooling is absent | future harness backlog candidate |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| batched coarse-to-fine MLE | full Figure 2 in `19.03 s` | case-local |
| explicit `--target-id` dispatcher | target isolation passed for four targets | pattern already supplied by harness wrapper |
| closed resource-row evaluator | 37 exact cells in `0.60 s` | case-local |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| medium | add a first-class PDF-page fallback for source-figure rasterization | Ghostscript was unavailable while PDF registration remained valid | recorded case-locally; protected harness files were intentionally unchanged in this Trial |
| low | add aspect-ratio preflight guidance for table pixel targets | avoided a second science run and isolated visual repair | recorded case-locally; protected harness files were intentionally unchanged in this Trial |

## Prompt Or Workflow Changes

- Keep the mandatory order: paper map → formula/method verification → readiness → explicit target execution → independent checks → pixel evidence → audit.
- When author randomness is absent, state the evidence cap early and never substitute digitized source curves for independent numerics.
- Do not promote these case observations during a controlled Trial whose protocol forbids harness changes.
