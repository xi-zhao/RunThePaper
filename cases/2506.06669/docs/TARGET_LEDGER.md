# Target Ledger

## Coverage-bearing targets

| Target | Atomic paper items | Items covered | Formula gate | Scientific result |
| --- | --- | ---: | --- | --- |
| T002 | Supp. Fig. S2 + S3(a-h) | 9/9 | verified | analytic/direct error `1.67e-16`; private coupler transfer remains outside exactness |
| T004 | Main Fig. 3(a-b), ten solid theory curves | 10/10 | verified | trace error `<1.8e-15`; Bell fidelity about `0.922` |
| T006 | Supp. Fig. S8(d-f), twelve theory series | 12/12 | verified | 100 samples/point; robustness ordering passes |
| T007 | Main Fig. 4(d) four theory curves + Fig. 4(f) ideal density | 5/5 | reconstructed | trace and corner symmetry pass; fidelity below critical-item floor |
| T008 | Supp. Fig. S7(d-f), twelve theory series | 12/12 | verified | 50 samples/point; robustness ordering passes |
| T009 | Supp. Fig. S9(a-d) | 4/4 | reconstructed | reported fidelity anchors within `0.0021` |
| T010 | Supp. Fig. S10(b-d) only | 3/3 | reconstructed | large-`m` suppression passes; target score is physics-capped |
| D001 | Supp. Fig. S10(a) only | **0/1** | reconstructed | crossover `m=10` versus paper `m=6` |
| C001 | Main Eq. (1) literal Hermiticity claim | **0/1** | source only | no literal-versus-corrected operator test |
| C002 | zig-zag PST for every allowed `m` | **0/1** | source only | no universal property-test suite |
| C003 | large-`m` half-chain reduction | **0/1** | reconstructed | no independent Schur/index adjudication |
| C004 | isospectral FST Bell-state phase gauge | **0/1** | source only | no complex-phase claim test |

Total: **55 covered / 60 eligible = 91.67% coverage**.

## Auxiliary diagnostic targets outside the denominator

| Target | Calculation | Why it is not a source-display coverage item |
| --- | --- | --- |
| T001 | Fig. 1(c-d)-inspired eigensystem calculation | the published panels are qualitative schematics |
| T003 | theoretical five-site PST counterpart to Main Fig. 2(d-f) | the published panels are measurements |
| T005 | ideal endpoint-density counterpart to Main Fig. 3(c-d) | the published panels are measured tomography; dashed ideal support is not a separate numerical panel |

These computations remain valuable scientific evidence and remain in the
historical scorecard, but they cannot increase the atomic paper-item numerator.

## Explicit uncovered-item diagnoses

| ID | Direct cause | Root cause | Code-fault status | Required next evidence |
| --- | --- | --- | --- | --- |
| D001 | numerical mismatch | unresolved | not excluded | pulse contract, convergence, independent backend |
| C001 | evidence chain incomplete | confirmed legacy scope-definition gap | not excluded | literal/corrected Hermiticity and dynamics test |
| C002 | evidence chain incomplete | confirmed legacy scope-definition gap | not excluded | parity/spectrum/endpoint property tests |
| C003 | evidence chain incomplete | confirmed legacy scope-definition gap | not excluded | symbolic Schur and asymptotic cross-check |
| C004 | evidence chain incomplete | confirmed legacy scope-definition gap | not excluded | phase-aware amplitude/density/fidelity cross-check |

The full statements, evidence paths, alternative hypotheses and next tests live
in `causal_diagnoses.json` and are embedded into
`outputs/checks/similarity_scorecard.json`.

## Frozen evidence boundary

The existing NPZ and science JSON artifacts were generated independently of
source pixels. Source images enter only the post-run comparison and constrained
render-optimization lanes. The current authority still reports E1 because the
run attestation is stale against the new inventory and fresh-context review has
not yet been completed; this W1 audit does not pretend otherwise.
