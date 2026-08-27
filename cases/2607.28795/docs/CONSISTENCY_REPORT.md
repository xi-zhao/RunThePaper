# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 2 | T002 and T004 match all declared paper comparisons. |
| feature_match | 1 | T003 validates the method only at reduced scale. |
| partial_match | 1 | T001 reproduces structure but contradicts part of the printed construction. |
| input_match_only | 0 | No target is accepted merely because inputs match. |
| blocked | 13 | Numerical paper items deferred in `figure_coverage.json`. |
| not_in_scope | 11 | Non-numerical schematics/context excluded. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Tables I/VI | partial_match | `outputs/checks/reported_result_comparison.json` | 4/8 weight rows exact; mitten-300 pivots rank 56/58 rather than 60/60 | missing element-map convention, transcription error, or erratum |
| T002 | Table V | exact_match | same check | 32/32 rows exact | Eq. E15 fully determines the table |
| T003 | Fig. 8 | feature_match | `outputs/checks/T003_science.json` | sizes, trials, hardware, and baseline differ | intentional bounded run; production task skipped |
| T004 | Table X | exact_match | same check | 24/24 comparisons pass rounding tolerance | printed arithmetic is self-consistent |

No original pixels or paper-reported target values entered numerical
generation. Paper scalars were transcribed only after v4 numerical hashes were
frozen and are bound to that attestation in the author-results manifest.
