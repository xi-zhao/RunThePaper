# Consistency Report

| Target | Scientific level | Evidence | Remaining difference | Cause |
| --- | --- | --- | --- | --- |
| T001 | exact formula/parameter match | center normalization, Fock-series error `8.77e-13`, narrowing widths | only rendering/camera | none scientific |
| T002 | feature match | six generated boundaries, strong named-dataset accuracy, monotonic capacity | point locations and exact scores differ | missing seeds/generator/SVC metadata |
| T003 | feature match | finite Fock map reaches unit train accuracy and imperfect generalization | epoch paths/test score differ | missing dataset/cutoff/order metadata |
| T004 | reduced-scale feature match; paper-scale code ready | 4 blocks, 32 params, 5000 steps, nonlinear boundary and loss reduction | exact landscape/loss trace differ; high-cutoff campaign unexecuted | missing initialization/optimizer/cutoff; cutoff 8 feature evidence |
| T005 | qualified analytic reproduction | full rank for six single/multi-mode probes; 64/64 labels interpolated; exact counterexamples reproduced | printed statement needs modulo-phase qualification and Proposition 1 fails as written | probable paper-claim discrepancy; fresh review pending |

## Scope

- Displayed numerical items covered: 14/14.
- Independent analytic claims covered: 1/1.
- Whole-paper reproduction-item coverage: 15/15 (100%).
- Non-numerical figures excluded: 8 atomic schematic items across Figs. 1--3 and 7.
- Experimental/image-only content: none.

All reported consistency claims refer to independently generated arrays. Pixel similarity is the final visual metric, while formula, parameter and isolated-run evidence determine whether a target is scientifically eligible for completion.

The new cutoff/seed campaign can test whether Fig. 8's scientific feature survives
truncation and random training choices. Because the author training instance is not
specified, it cannot by itself prove an exact pixel discrepancy or a paper error.
Likewise, T005's exact counterexamples are sufficient to open a discrepancy
candidate but not to confirm a paper error without fresh-context adjudication.
