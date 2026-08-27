# Target Ledger

| Target ID | Paper item | Type | Scientific dependencies | Gate | Status | Data output | Presentation artifact | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T008 | Figure 8 | numeric scatter | EQ001, METHOD002 | verified | feature_match | `outputs/data/fig8_cost_law.csv` | `outputs/figures/fig8_cost_law.{pdf,svg,png,tiff}` | `outputs/checks/numerical_feature_checks.json#targets/T008` | Clean-room 67-circuit run; exact law residual `4.44e-16`; author overhead correlation `0.9881`. |
| T009 | Figure 9(a,b) | numeric pipeline comparison | EQ002, METHOD002 | verified | partial_match | `outputs/data/fig9_pipeline.csv` | `outputs/figures/fig9_pipeline.{pdf,svg,png,tiff}` | `outputs/checks/numerical_feature_checks.json#targets/T009` | Clean-room 67-circuit run; 57/67 below `5e-4`, versus 66/67 in paper. |
| T010 | Table 1 core | nine-row numerical table | EQ001, METHOD002 | implementation incomplete | declared_uncovered | planned: `outputs/data/table1_random_complexity_audit.csv` | planned: independently emitted core rows | planned: per-row law and paper-table comparison | Existing evaluator contains some needed quantities, but no independent table emitter or acceptance check exists. |
| T011 | Table 1 extension | three-row numerical table | EQ001, METHOD002 | implementation incomplete | declared_uncovered | planned: `outputs/data/table1_random_complexity_audit.csv` | planned: independently emitted extension rows | planned: per-row law and paper-table comparison | Kept separate because the paper explicitly distinguishes the extension rows. |
| T012 | Table 5 | twelve-row numerical table | METHOD004 | method incomplete | blocked_missing_method | planned: `outputs/data/table5_independent_complexity_audit.csv` | planned: independently emitted table | planned: independent time/space/read-write complexity checks | The loop-volume complexity accumulator and `kappa` audit are not implemented. |

Primary evidence is `independent_reimplementation`. Author-released numeric
records are reference-only and are never inputs to the optimizer.

The five targets represent six atomic numerical items because T009 covers two
separately scored panels. At the W1 inventory stage, 3/6 items have acceptable
generated artifacts and T010-T012 deliberately receive zero coverage credit.
