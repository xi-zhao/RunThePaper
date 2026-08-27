# Target Ledger

Each numerical subpanel is an independent target. All generated arrays come
from the isolated runner; source figures enter only the post-freeze comparison
stage.

| Target | Paper panel | Parameter match | Formula/method gate | Scientific status | Data | Figure/comparison | Key result or gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T_FIG1A | Main Fig. 1(a) | `reduced_scale` | EQ-MPS, EQ-FLOW, EQ-GAMMA verified | physically_consistent | `outputs/data/T_FIG1_tdvp.npz` | `outputs/figures/T_FIG1_reproduction.png`; `comparison-artifacts/T_FIG1A_side_by_side.png` | period 9.635 vs 9.488; leakage 0.1746 vs 0.17 |
| T_FIG1B | Main Fig. 1(b) | `reduced_scale` | EQ-H, MTH-T2 verified | physically_consistent | `outputs/data/T_FIG1_dynamics.npz` | `outputs/figures/T_FIG1_reproduction.png`; `comparison-artifacts/T_FIG1B_side_by_side.png` | exact L=18,20; paper L is unreported; legacy L=30,32 pair is only a candidate; Z2 revival range 0.962 |
| T_FIG2A | Main Fig. 2(a) | `reduced_scale` | EQ-H, EQ-R, MTH-DIH verified | partial | `outputs/data/T_FIG2.npz` | `outputs/figures/T_FIG2_reproduction.png`; `comparison-artifacts/T_FIG2A_side_by_side.png` | r=0.402..0.533 in smaller blocks; finite-size scatter exceeds source sequence |
| T_FIG2B | Main Fig. 2(b) | `reduced_scale` executed | EQ-H, EQ-ENT, MTH-T2 verified | physically_consistent | `outputs/data/T_FIG2.npz` | `outputs/figures/T_FIG2_reproduction.png`; `comparison-artifacts/T_FIG2B_side_by_side.png` | L=18 six-site late entropy 3.96 from zero vs 2.45 from Z2; L=30 code-ready below |
| T_FIG2C | Main Fig. 2(c) | `reduced_scale` executed | EQ-H, EQ-ENT, MTH-T2 verified | physically_consistent | `outputs/data/T_FIG2.npz` | `outputs/figures/T_FIG2_reproduction.png`; `comparison-artifacts/T_FIG2C_side_by_side.png` | Z2 late oscillation std 0.119 vs zero-state 0.033; L=30 code-ready below |
| T_FIG4A | Main Fig. 4(a) | `reduced_scale` | EQ-MPS, EQ-FLOW, EQ-GAMMA verified | physically_consistent | `outputs/data/T_FIG4_tdvp.npz` | `outputs/figures/T_FIG4_reproduction.png`; `comparison-artifacts/T_FIG4A_side_by_side.png` | spin-1 period 10.314 vs 10.304; leakage 0.3183 vs 0.32 |
| T_FIG4B | Main Fig. 4(b) | `reduced_scale` | EQ-H, MTH-T2 verified | physically_consistent | `outputs/data/T_FIG4_dynamics.npz` | `outputs/figures/T_FIG4_reproduction.png`; `comparison-artifacts/T_FIG4B_side_by_side.png` | exact L=12,14; paper L is unreported; legacy L=20,22 pair is only a candidate; Z2 range 1.856 |
| T_FIG4C | Main Fig. 4(c) | `reduced_scale` | EQ-MPS, EQ-FLOW, EQ-GAMMA verified | physically_consistent | `outputs/data/T_FIG4_tdvp.npz` | `outputs/figures/T_FIG4_reproduction.png`; `comparison-artifacts/T_FIG4C_side_by_side.png` | spin-2 period 10.892 vs 10.870; leakage 0.4123 vs 0.41 |
| T_FIG4D | Main Fig. 4(d) | `reduced_scale` | EQ-H, MTH-T2 verified | physically_consistent | `outputs/data/T_FIG4_dynamics.npz` | `outputs/figures/T_FIG4_reproduction.png`; `comparison-artifacts/T_FIG4D_side_by_side.png` | exact L=10,12; paper L is unreported; legacy L=14,16 pair is only a candidate; Z2 range 3.681 |
| T_FIGS1_HM020 | Supp. Fig. S1, h=-0.2 | `paper_exact` | EQ-DEF-FLOW verified | physically_consistent | `outputs/data/T_FIGS1.npz` | `outputs/figures/T_FIGS1_reproduction.png`; `comparison-artifacts/T_FIGS1_HM020_side_by_side.png` | closed orbit retained |
| T_FIGS1_H000 | Supp. Fig. S1, h=0 | `paper_exact` | EQ-DEF-FLOW verified | physically_consistent | `outputs/data/T_FIGS1.npz` | `outputs/figures/T_FIGS1_reproduction.png`; `comparison-artifacts/T_FIGS1_H000_side_by_side.png` | deformed/undeformed flow identity holds to 1.4e-16 |
| T_FIGS1_H020 | Supp. Fig. S1, h=0.2 | `paper_exact` | EQ-DEF-FLOW verified | physically_consistent | `outputs/data/T_FIGS1.npz` | `outputs/figures/T_FIGS1_reproduction.png`; `comparison-artifacts/T_FIGS1_H020_side_by_side.png` | closed orbit retained |
| T_FIGS1_H040 | Supp. Fig. S1, h=0.4 | `paper_exact` | EQ-DEF-FLOW verified | physically_consistent | `outputs/data/T_FIGS1.npz` | `outputs/figures/T_FIGS1_reproduction.png`; `comparison-artifacts/T_FIGS1_H040_side_by_side.png` | distorted closed orbit retained |
| T_FIGS2A | Supp. Fig. S2(a) | `unknown` (grid/formulas exact; residual procedure omitted) | EQ-DEF-H, EQ-DEF-FLOW, EQ-GAMMA verified | failed | `outputs/data/T_FIGS2.npz` | `outputs/figures/T_FIGS2_reproduction.png`; `comparison-artifacts/T_FIGS2A_side_by_side.png` | stable minimum h=0.07; protocol-v2 `parameter_ambiguity` |
| T_FIGS2B | Supp. Fig. S2(b) | `unknown` (grid/formulas exact; residual procedure omitted) | EQ-DEF-H, EQ-DEF-FLOW, EQ-GAMMA verified | failed | `outputs/data/T_FIGS2.npz` | `outputs/figures/T_FIGS2_reproduction.png`; `comparison-artifacts/T_FIGS2B_side_by_side.png` | fluctuation decreases through h=0.08; not eligible for `paper_error_candidate` |

## Code-ready paper-scale extensions

| Targets | Implementation | Paper/candidate parameters | Work units | Checkpoint/resume | Compute status |
| --- | --- | --- | ---: | --- | --- |
| T_FIG1A, T_FIG1B, T_FIG4A-D | `main_paper_scale` | TDVP spins 1/2,1,2 with three-ring convergence; legacy candidate quench pairs L=30,32 / 20,22 / 14,16; public t Omega=0..300 range | 15 (3 TDVP + 12 quench) | TDVP ring/heatmap-row checkpoints; streaming Krylov state plus scalar observables every 10 samples | `ready`, 256-GiB campaign not run; quench L provenance remains `parameter_ambiguity` |
| T_FIG2A | `main_paper_scale` | named k=0, inversion-even sector; 15 explicitly declared candidate `(s,L)` blocks | 15 | each size is an immutable, digest-bound lane; completed sizes survive restart | `ready`, but omitted paper L sequence remains `parameter_ambiguity` |
| T_FIG2B, T_FIG2C | `fig2_tdmrg_paper_scale` | periodic L=30; S6 to t Omega=100; S1 to t Omega=120 | 6 | digest-bound MPS checkpoints every 2 time units; six-way shard command; unsharded resume/merge | `ready`, full paper-scale campaign not run |


The main campaign uses the same independently implemented constrained
Hamiltonian as the reduced evidence, but changes the execution model. It calls
Krylov propagation one sample interval at a time and persists only the current
state, magnetization, norm, and energy. It therefore never materializes the
full `number_of_times x Hilbert_dimension` state array. A 12-unit CPU smoke,
backend-parity, interruption/resume, aggregation, and config-load suite passes;
these are algorithm checks only and are not paper-scale evidence.

The code-ready route is an exact pair-block representation of the constrained
Hamiltonian followed by finite-MPS TEBD. Its executable contract is
`run_contract.fig2_tdmrg_paper_scale.json`; it separately checks time-step and
bond convergence, norm and energy drift, forbidden-state leakage, entropy
bounds, and the paper's generic-versus-scarred features. The completed L=8
smoke test is algorithm evidence only and is not listed as paper-scale data.

The two S2 failures are retained as generated scientific findings. The
deformed matrix Hamiltonian independently projects to the printed flow within
`3.9e-4`, and the residual curves converge from L=10 to L=14 within `1.4e-7`.
The supplement omits the closed deformed residual construction and numerical
orbit-integral procedure, so protocol-v2 assigns `parameter_ambiguity`.
`paper_error_candidate` is ineligible because `paper_exact` and
`fresh_independent_review` fail, although convergence, two independent
cross-checks, and source pinpoint pass. Source pixels were never used to change
either curve. The formal audit is `outputs/checks/paper_claim_audit.json`.
