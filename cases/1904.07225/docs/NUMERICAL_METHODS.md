# Rerun / 复算

NMQA beats direct frequency estimates at five of the low budgets. Jeffreys smoothing on the same uniform counts gives lower held-out prediction error at all nine budgets under both grouping schemes.

Use the [code instructions](../code/README.md). The default stages run into a new directory.

- The default square-field runner is in `code/scripts/run_reproduction.py`.
- [Six-ion aggregate scores](../outputs/checks/ion-holdout-scores.json)
- [Earlier reproduction](PREVIOUS-ANALYSIS.md)

Keep config/binary_data.npz from the pinned author repository outside the published tree. Run predict_ion_holdout.py, tune_ion_holdout.py and score_ion_holdout.py from a working directory with the paper-grid and lambda configurations. The original square-field rerun remains available.

[Selected numerical results](../outputs/data/overview.json) · [Scientific scope](../outputs/checks/completion_assessment.json)
