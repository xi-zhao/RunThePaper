# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Independent reason |
| --- | --- | --- | --- |
| EQ-PRECISION-FUNCTIONS | searched error functions | verified | strict monotonicity and infinite-\(N\) limit derived |
| EQ-ANALYTIC-BOUNDS | \(N^{analytic}\) | verified | re-derived from \(N\ge x\Rightarrow e^{x/N}\le e\) |
| EQ-GATE-COMPLEXITY | \(N\mapsto g\) | verified | counted exponentials per product-formula step |
| EQ-LAMBERT-W-CROSSCHECK | continuous threshold | verified | algebraically inverted and substituted back |
| EQ-CHOI-DIAMOND-BOUND | reported-\(\lambda\) audit | verified | independently constructed local superoperators and Eq. (32) Choi bounds |
| EQ-MODEL-TERM-COUNTS | horizontal grids | verified | terms counted from each Liouvillian decomposition |

There are no closed formula dependencies. The Choi calculation itself is
verified, but it does not recover the paper-reported \(\lambda\) values under
either the literal equations or the frozen source convention. The frozen
panels therefore use the values explicitly reported in Section 5.4 and record
the parameter discrepancy separately.
