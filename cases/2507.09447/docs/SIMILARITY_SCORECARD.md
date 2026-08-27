# Similarity Scorecard

The canonical machine-readable scorecard is
`outputs/checks/similarity_scorecard.json`. Its author-side score is
`83.08/100` across eight atomic targets. This score measures reproduction
degree; it is not an independent-review completion verdict.

## Target results

| Target | Scientific disposition | Score | Boundary |
| --- | --- | ---: | --- |
| T001 / Fig. 3 | paper-scale feature match | 90.00 | fresh reviewer must recheck the refreshed bundle |
| T002 / Fig. 4 | paper-scale feature match | 90.00 | fresh reviewer must recheck the refreshed bundle |
| T003 / Fig. 5 | paper-scale feature match | 90.00 | R089 paper-error candidate remains reviewer-owned |
| T004 / Fig. S1 | corrected reduced-scale feature match | 70.00 | exact author grid/render choices are unpublished |
| T005 / Fig. S2 | corrected reduced-scale feature match | 70.00 | exact author grid/render choices are unpublished |
| T006 / one-way OBC claim | exact analytic reproduction | 90.00 | finite clean-room ensemble has zero multiset error |
| T007 / Fig. S3 | code-ready, paper-scale compute blocked | 32.50 | L=12 x 2 pilot only; L=1000 x 1600 not run |
| T008 / Fig. S4 | attempted, feature not reproduced | 27.50 | 0/18 declared protocols pass; fresh review is required |

## New scientific evidence

- The S1/S2 transfer recurrence now uses `t+gamma` as the forward denominator,
  matching the ED Hamiltonian. Non-symmetric row-residual tests prevent the
  previous direction swap from returning unnoticed.
- The isolated S1/S2 rerun passes with density overlaps `0.8861` and `0.8143`;
  every declared input was read and forbidden-source access was zero.
- The one-way OBC Hamiltonian is triangular, hence its eigenvalue multiset is
  exactly the onsite multiset; the finite check has maximum error `0`.
- Fig. S3 has independent arbitrary-precision ED and QR implementations. The
  measured pilot projects the full local dense-ED campaign to about 3,629 CPU
  days. Its 112–256-bit arithmetic contract is not provided by a standard A100
  FP32/FP64 path; even an optimistic idealized `50x` speedup is about 73 days.
- Fig. S4 executes the published energy and size grid. The baseline exponential
  fit has `R²=0.0186`; a predeclared sweep over three ensemble sizes, three seeds,
  and two QR intervals yields `0/18` supporting protocols. This robust negative
  result is preserved rather than tuned or hidden behind a metadata blocker.

## Pixel evidence

Main Figs. 3–5 retain their declared scientific-region pixel comparisons:
`94.7068`, `94.4138`, and `96.2507`. Supplement targets do not claim
paper-exact pixel comparability because the stochastic/render contracts are
not fully published. Pixel evidence never supplies scientific input data.

## Remaining adjudication

The author side has 100% implementation coverage for the 21 numeric items:
all have target contracts and code. T007 is an objective compute blocker and
T008 is an attempted scientific non-reproduction with a probable
paper-discrepancy hypothesis, not an external blocker. A fresh-context reviewer
must independently re-enumerate the scope, rederive the observable, and run an
independent falsification before it can decide whether this becomes a
`paper_error_candidate` or an author-side reproduction defect.
