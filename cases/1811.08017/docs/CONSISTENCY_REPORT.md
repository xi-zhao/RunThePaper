# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| feature_match | 2 | Formula-derived branches, scalings and reported audit values agree. |
| not_in_scope | 2 | Non-numerical pseudocode/circuit context. |
| partial_match / deferred / failed | 0 | No numerical target remains open. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Remaining difference |
| --- | --- | --- | --- | --- |
| T001 | Main Fig. 2 | feature_match | `target_checks.json`, `panel_target_acceptance.json`, six formula gates, three pixel regions | Typography and rasterization; propane body speedup conflict remains `inconclusive`. |
| T002 | Main Fig. 4 | feature_match | `target_checks.json`, E14/E28 traces, three pixel regions | Typography and minor layout only. |

All scientific checks and pixel contracts pass. No source pixel or author array
was used as a numerical input.

## Protocol-v2 paper assessment

| Issue | Current assessment | Why it cannot be promoted |
| --- | --- | --- |
| propane body `591x` versus formula result `1585.08x` and abstract `1591x` | `inconclusive` | all four plotted comparator families have been falsified as explanations, but there is no fresh inventory-first review, only one independent method, and only rounded published inputs |

The numerical pipeline may report `reproduction_defect` when its own precision,
formula parity, convergence, or provenance checks fail. It may not self-emit
`paper_supported` or `paper_error_candidate`; those are fresh-review outcomes.
