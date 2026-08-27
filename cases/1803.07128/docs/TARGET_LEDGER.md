# Target Ledger

| Target | Paper item | Numerical panels | Formula cards | Parameter status | Scientific status | Data | Figure |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| T001 | Fig. 4 | 3 | EQ001--EQ004 | `paper_exact` | passed | `outputs/data/T001_fig4_squeezing_kernel.npz` | `outputs/figures/T001_fig4_squeezing_kernel.png` |
| T002 | Fig. 5 | 6 | EQ003--EQ005 | `reconstructed_missing_metadata` | passed | `outputs/data/T002_fig5_svm_boundaries.npz` | `outputs/figures/T002_fig5_svm_boundaries.png` |
| T003 | Fig. 6 | 3 | EQ001, EQ002, EQ006 | `reconstructed_missing_metadata` | passed | `outputs/data/T003_fig6_fock_perceptron.npz` | `outputs/figures/T003_fig6_fock_perceptron.png` |
| T004 | Fig. 8 | 2 plus one inset view | EQ001, EQ002, EQ007, EQ008 | `reduced_scale`; paper-scale code ready | passed | `outputs/data/T004_fig8_variational_classifier.npz` | `outputs/figures/T004_fig8_variational_classifier.png` |
| T005 | Appendices B-D, universal separability claim | no display | EQ001, EQ002, EQ009 | `not_applicable` | qualified pass; source-discrepancy candidates await fresh review | `T005_counterexample_search.json` plus two check artifacts | none (analytic claim) |

T001-T004 share the attested isolated run `1803.07128-independent-v1`. Only
T001 is eligible for `final_reproduction`; the remaining display targets stay
exploratory until the missing paper metadata is available. T005 is a separate
analytic claim, not another view of Fig. 6. Its dedicated theorem probe uses
single-mode Vandermonde rank, an independent analytic Gram matrix, all 64
binary labellings on a six-point set and exact counterexamples.

T005 supports the corrected finite-set result when physical phase vectors are
distinct modulo `2*pi`. It also finds that Proposition 1 is false as written
and that nonzero pairwise overlaps do not prove multi-mode independence. These
are source-discrepancy candidates, not confirmed paper errors, until a fresh
review independently rederives and attempts to falsify them.

For T004, `paper-scale code ready` means the 21-condition cutoff/seed campaign,
checkpoint/resume protocol, A100/CPU route, independent dense cross-check and acceptance
rules exist. It does not mean the campaign ran or that the target became paper-exact.

The atomic denominator is therefore 15 eligible reproduction items: all 14
displayed numerical items and the independent analytic T005 item are covered.
Coverage is `15/15`; evidence grade and paper-error adjudication remain separate.
