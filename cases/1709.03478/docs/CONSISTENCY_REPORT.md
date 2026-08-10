# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | No author numerical arrays are available for exact comparison. |
| feature_match | 4 | T002, T003, T005 and T006 pass their declared physical feature checks. |
| partial_match | 1 | T004 resolves two of six central double thresholds. |
| blocked | 4 | Four experimental figure groups lack author measurements or fit inputs. |
| not_in_scope | 1 | Fig. 1 is a schematic. |

## Per-target consistency

| Target | Level | Evidence | Difference and likely reason |
| --- | --- | --- | --- |
| T002 | feature_match | final \(\mathcal D\): 0.683309, 0.044705, 0.003972 for \(V_d=0,0.57,1.04\) | Correct ordering; the intermediate curve is lower than the source, consistent with reduced phase/tube preparation and unavailable author details. |
| T003 | feature_match | all six endpoint trend assertions pass at \(V_p=4,6,8\) | Correct stationary coexistence structure; curves use a two-phase/two-node proxy. |
| T004 | partial_match | central double thresholds at \(V_p=4\): [0.4512, 0.8480], and \(V_p=6\): [0.2578, 0.6402] | Four upper crossings are absent at the reduced ensemble, so the full phase line is not accepted. |
| T005 | feature_match | four ordering checks pass with/without trap | Correct localization ordering; reduced cloud is noisier and rescaled. |
| T006 | feature_match | finite-time imbalance rises and edge density falls | Correct transition structure; experimental 200-tau series is unavailable. |

The scorecard assigns 63.55 overall (`numerical_feature_reproduction`).  Pixel
metrics are `not_applicable`: independent figures are not registered to paper
panel geometry.  Five post-freeze comparison boards support visual auditing
but do not upgrade source-figure inspection into numerical equality.
