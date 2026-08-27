# Target Ledger

The completed artifacts below remain `parameter_match=reduced_scale`,
`artifact_stage=exploratory`, and independently generated. A separate,
unexecuted paper-scale code channel now covers every target through
`config/paper_scale.json`, `run_contract.paper_scale.json`, and the 31 explicit
contracts in `config/paper_scale_acceptance.json`. The accepted reduced-scale
artifacts now also pass independent target-level formula/method checks. This
closes their atomic feature dispositions, but does not replace paper-scale
parameter/reference gates or change the partial lifecycle status.

## Paper-scale channel ledger

| Targets | Implementation key | Paper-scale scope | Execution state | Remaining science gate |
|---|---|---|---|---|
| T001–T017 | `paper_scale_regular_qsd` | L=200/400/600/800, sharded QSD and streamed observables | code_ready_final_run_not_executed | paper-scale parameters and strict reference |
| T018 | `paper_scale_time_qsd` | L=800 time series | code_ready_final_run_not_executed | paper-scale parameters and strict reference |
| T019–T021 | `paper_scale_quantum_jump` | L=200 quantum jumps | code_ready_final_run_not_executed | paper-scale parameters and strict reference |
| T022 | `paper_scale_qsdc_control` | L=400 QSDc | code_ready_final_run_not_executed | paper-scale parameters and strict reference |
| T023 | `paper_scale_autocorrelation` | L=400 unequal-time correlation | code_ready_final_run_not_executed | paper-scale parameters and strict reference |
| T024 | `paper_scale_density_identity` | independent 250+250 at L=400 | code_ready_final_run_not_executed | strict reference missing |
| T025 | `paper_scale_random_hopping` | L=200 binary random hopping | code_ready_final_run_not_executed | paper-scale parameters and strict reference |
| T026–T028 | `paper_scale_histogram_qsd` | 3×5000 streamed L=200 entropies | code_ready_final_run_not_executed | paper-scale parameters and strict reference |
| T029–T031 | `paper_scale_histogram_qsdc` | 3×5000 streamed L=200 entropies | code_ready_final_run_not_executed | paper-scale parameters and strict reference |

Machine acceptance requires complete scalar checkpoint coverage, finite
aggregates, disjoint seeds, verified hashes, zero persisted full states,
orthonormality residual ≤1e-10, and each target's declared paper conditions.
The smoke channel may exercise these contracts at tiny scale, but only a final
paper-scale run can satisfy the length/sample-count clauses.

## Existing reduced-scale artifacts

| Target | Source axis | Observable | Generated artifact | Status |
|---|---|---|---|---|
| T001 | Fig. 1(c) | half-chain entropy vs L | `main_fig1_numeric_cde.png` | physically_consistent |
| T002 | Fig. 1(c) inset | small-L entropy | same | physically_consistent |
| T003 | Fig. 1(d) | effective c | same | physically_consistent |
| T004 | Fig. 1(d) inset | effective c, linear view | same | physically_consistent |
| T005 | Fig. 1(e) | residual entropy | same | physically_consistent |
| T006 | Fig. 1(e) inset | residual entropy, log view | same | physically_consistent |
| T007 | Fig. 2(a) | interval entropy | `main_fig2_abc.png` | physically_consistent |
| T008 | Fig. 2(a) inset | area-law zoom | same | physically_consistent |
| T009 | Fig. 2(b) | BKT entropy transform | same | physically_consistent |
| T010 | Fig. 2(b) inset | raw half entropy | same | physically_consistent |
| T011 | Fig. 2(c) | BKT c transform | same | physically_consistent |
| T012 | Fig. 3(a) | fixed MI | `main_fig3_abcd.png` | physically_consistent |
| T013 | Fig. 3(a) inset | fixed MI log tail | same | physically_consistent |
| T014 | Fig. 3(b) | MI vs cross ratio, weak | same | physically_consistent |
| T015 | Fig. 3(c) | MI vs cross ratio, strong | same | physically_consistent |
| T016 | Fig. 3(d) | equal-time correlation | same | physically_consistent |
| T017 | Fig. 3(d) inset | size collapse | same | physically_consistent |
| T018 | Supp. Fig. 4(a) | entropy vs time | `supp_figure_qj_abcd.png` | physically_consistent |
| T019 | Supp. Fig. 4(b) | QJ interval entropy | same | physically_consistent |
| T020 | Supp. Fig. 4(b) inset | QJ effective c | same | physically_consistent |
| T021 | Supp. Fig. 4(c) | QJ fixed MI | same | physically_consistent |
| T022 | Supp. Fig. 4(d) | QSDc fixed MI | same | physically_consistent |
| T023 | Supp. autocorr (a) | unequal-time C | `supp_autocorrelation_ab.png` | physically_consistent |
| T024 | Supp. autocorr (b) | density identity | same | physically_consistent |
| T025 | Supp. random hopping | interval entropy | `supp_random_hopping.png` | physically_consistent |
| T026 | Supp. stats QSD .25 | entropy distribution | `supp_entropy_statistics.png` | physically_consistent |
| T027 | Supp. stats QSD 2 | entropy distribution | same | physically_consistent |
| T028 | Supp. stats QSD 6 | entropy distribution | same | physically_consistent |
| T029 | Supp. stats QSDc .25 | entropy distribution | same | physically_consistent |
| T030 | Supp. stats QSDc 2 | entropy distribution | same | physically_consistent |
| T031 | Supp. stats QSDc 6 | entropy distribution | same | physically_consistent |

## Analytic atomic items

| Target | Atomic item | Disposition | Evidence |
|---|---|---|---|
| T032 | QCLM-CROSSOVER-LENGTH | externally_blocked | parameterized clean-room implementation plus the parameter audit in `outputs/checks/claim_implementation_closure/T032.json` and `causal_diagnoses.json`; publication omits the required numeric parameters and decision criterion |
| T033 | QCLM-NORM-QSD | reproduced | exact conserved-rate check and isolated claim attestation |
| T034 | QCLM-NORM-QJ | reproduced | independent projector rederivation and isolated claim attestation |
| T035 | QCLM-NORM-QSDC | reproduced | independent Gauss-Hermite stochastic-process check and isolated claim attestation |
| T036 | QCLM-AUTOCORR-G0-BESSEL | reproduced | independent Legendre-quadrature Bessel check and isolated claim attestation |

Authoritative atomic result: 121 eligible, 121 finalized, 120 reproduced,
1 externally blocked, 0 attempted-not-reproduced, and 0 pending. The complete
machine projection is `outputs/checks/authoritative_reproduction_state.json`.
