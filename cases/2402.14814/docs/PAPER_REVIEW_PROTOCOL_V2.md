# Paper Review Protocol v2

The case acts as both a reproduction and a paper audit. Conclusions are fail-closed:

1. Inventory every numeric item from the full PDF and supplement before judging results.
2. Re-derive formulas and protocol endpoints independently of the plotted pixels.
3. Classify implementation defects separately from possible paper defects.
4. For a paper-error candidate, require at least two distinct strong checks, an explicit attempt to falsify the discrepancy, source pinpoints, and a fresh-context independent reviewer.

Current result: no `paper_error_candidate` is emitted. `DISC_S1_ENERGY_OFFSET` and `DISC_S3_LAUGHLIN_FREQUENCY` remain `inconclusive`; `R001` is a repaired reproduction defect. Machine-readable evidence is in `outputs/checks/paper_consistency_checks.json`.
