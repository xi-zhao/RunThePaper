# Similarity Scorecard

- Model: scientific-evidence-first v3
- Overall score: 16.0/100
- Level: feature_not_accepted
- Targets scored: 9
- Known eligible reproduction items: 30
- Scientifically covered items: 0
- Item coverage: 0%
- Data-backed target rate: 0
- Essential paper-scale failures: 9

Each target receives 16/50 for independently tested shared method features,
0/35 for numerical closeness, and 0/15 for reproduced panel scope. The
scorecard intentionally gives no credit for code readiness as if it were a
computed panel.

The 30-item denominator comprises 28 theoretical items in the published main
figures plus the two explicitly cited supplemental tables. It is a lower bound:
the inaccessible formal supplement may contain additional numerical content,
which is recorded as a source-scope blocker rather than guessed.

Pixel status is not applicable because no material-specific generated figure
exists. The two displayed method-validation plots are outside the nine paper
targets.

All 30 uncovered items are emitted individually by the authoritative
`reproduction_measure.uncovered_item_details[]` projection. Their target-level
diagnosis is direct cause `parameter_values_unavailable`, root cause
`unresolved/open`, and code-fault status `not_excluded`.
