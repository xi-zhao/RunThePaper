# Target Ledger

The short IDs are internal handles; the descriptive name is the actual target.

| ID | Descriptive target | Paper figures | Formula basis | Status | Primary evidence |
| --- | --- | --- | --- | --- | --- |
| T001 | Small-\(q\) LLG energy and geometry | Main 1; Supp. 1–2 | EQC004–EQC007 | `partially_reproduced` | `outputs/checks/fig1_small_q_energy.json` |
| T002 | Exact versus small-\(q\) extended-Hubbard trajectory | Main 2; Supp. 3, 5 | EQC004–EQC006, EQC015–EQC016 | `evidence_compared` | `outputs/checks/fig2_exact_vs_small_q.json` |
| T003 | Near-ideal local metric and Berry curvature | Main 3; Supp. 4 | EQC004–EQC006, EQC015–EQC017 | `evidence_compared` | `outputs/checks/fig3_trace_deviation_maps.json` |
| T004 | Interaction-robustness \(U,V\) sweeps | Supp. 6 | EQC005, EQC015 | `evidence_compared` | `outputs/checks/sm_fig6_parameter_sweeps.json` |
| V001 | Independent finite-\(q\) projector-mismatch theorem check | new validation | EQC001–EQC005 | `evidence_compared` | `outputs/checks/jump_sum_rule_validation.json` |
| V002 | Detector-level go/pivot/stop check | new validation | EQC008–EQC014 | `evidence_compared` | `outputs/checks/detector_sum_rule_validation.json` |

## Main Quantitative Checkpoints

| Quantity | Paper | Reproduction |
| --- | ---: | ---: |
| \(\lambda_D\) for \(U=8,V=0.75,Q=\pi/2\) | \(1.183\) | \(1.1828772769\) |
| \(T_{\rm short}\) | \(4.32\) | evaluated exactly at \(4.32\) |
| \(E_D(T_{\rm short})\) | \(\pi\) approximately | \(3.1451543417\) |
| \(C_{\rm num}(T_{\rm short})\) | \(1\) | \(0.9964910847\) |
| mean trace deviation, exact | near zero | \(3.1826\times10^{-4}\) |
| \(U=8,V=0.75\) transition in sweep | finite, early | \(t_{C<0.5}=4.6\) on \(N=61\) |
