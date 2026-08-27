# Target Ledger

The target is an execution projection; `figure_coverage.json` is the authority
for the atomic denominator.  The formal-PRL main article is included from v6;
its unavailable Supplemental Material remains an explicit unknown remainder.

| Target | Scope | Status | Atomic items |
| --- | --- | --- | --- |
| T001 | Fig. 2 reduced-feature proxy: depth-20 histogram/PT/post-selection XEB | 18q proxy feature evidence; not paper-exact | F02-HIST, F02-PT, F02-XEB |
| T002 | Fig. 5 reduced-feature proxy: depth-14 histogram/PT/post-selection XEB | 18q proxy feature evidence; not paper-exact | F05-HIST, F05-PT, F05-XEB |
| T003 | Fig. 6 reduced-feature proxy: conditional histograms/PT and marginal behavior | 18q proxy feature evidence; not paper-exact | F06-20-HIST, F06-20-PT, F06-14-HIST, F06-14-PT, C14-MARGINAL-VALUE |
| T004 | Independent analytic-law checks | uncovered; zero-credit causal target | F03-COST, C08-GPU-EFFICIENCY-LAW |
| T005 | Big-head factorization, reuse scaling, and 20-cycle partition | uncovered; zero-credit causal target | C01-HEAD-TAIL-FACTOR, C02-BATCH-REUSE-SCALING, C03-20C-PARTITION |
| T006 | Table I and 20-cycle contraction-cost profile | uncovered; zero-credit causal target | TB1-NSUB, TB1-STOTAL, TB1-TSUB, TB1-THEAD, TB1-TTAIL, TB1-TTOTAL, C11-20C-COMPUTE-PROFILE |
| T007 | Published one-A100 and 60-GPU runtime claims | uncovered; zero-credit causal target | TB2-OURS-RUNTIME, C04-60GPU-RUN |
| T008 | Table III exact 53-qubit amplitude/probability rows | uncovered; zero-credit causal target | TB3-R1, TB3-R2, TB3-R3, TB3-R4, TB3-R5 |
| T009 | Complex64 precision validation | uncovered; zero-credit causal target | C07-COMPLEX64-PRECISION |
| T010 | Branch-merging and GPU performance profile | uncovered; zero-credit causal target | C09-BRANCH-MERGE, C10-A100-EFFICIENCY, C12-14C-COMPUTE-PROFILE |
| T011 | Mixed top-probability/random-bitstring XEB claim | uncovered; zero-credit causal target | C05-MIXED-XEB |
| T012 | Marginal-probability/XEB normalization identity | uncovered; zero-credit causal target | C13-MARGINAL-XEB-IDENTITY |
| T013 | Peak-tensor complex64 memory estimate | uncovered; zero-credit causal target | C06-PEAK-MEMORY |
| T014 | Formal-PRL noisy-state fidelity cost law | reduced fidelity-path smoke executed; exact method definition is source-blocked | C15-NOISY-FIDELITY-COST |
| T015 | Formal-PRL 43-qubit EFGH full-state campaign | streaming runner smoke executed; exact EFGH member and V100S execution are external | C16-FULL43-STATE, C17-FULL43-PARTITION, C18-FULL43-RUNTIME |
| T016 | Formal-PRL 50-qubit state, partition, batch cost, histogram and runtime | streaming/histogram runner smoke executed; 8-PiB/1000-GPU-day paper-scale campaign is resource-blocked | C19-FULL50-STATE, C20-FULL50-PARTITION, C21-FULL50-BATCH-COST, C22-FULL50-PT-HIST, C23-FULL50-RUNTIME |
| T017 | Cited follow-on one-million-sample result | correlation/XEB sampler smoke executed; cited method and 53-qubit backend are external | C24-FOLLOWON-1M-SAMPLES |

Every known uncovered target now has a code-ready path and a terminal causal
boundary.  A reduced smoke proves that the path is executable; it never earns
paper-scale credit.  T016 is compute-blocked by its measured resource contract,
while T014, T015 and T017 also require frozen external scientific inputs.
