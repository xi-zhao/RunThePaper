# Target Ledger

The existing v4 artifacts are reduced-scale feature evidence.  The new shared
`paper_scale_theory` implementation is code-ready but has **not** been run at
paper scale.  Code readiness does not promote any target to paper-exact or
complete.

| Target | Paper item | Existing evidence | Paper-scale contract | Current scientific assessment | Remaining boundary |
| --- | --- | --- | --- | --- | --- |
| T002 | Main Fig. 2(b) | Reduced-scale time traces in `outputs/data/fig2b_edge_density.csv` | `main_trace_phase` blocks at L=738, q=8, six phases and exact printed depths/times | `inconclusive` pending full convergence and fresh review | The target caption does not print L; L=738 comes from cited theory Ref. 1704.04498. |
| T003 | Main Fig. 3(d), 3(e), 3(f) | Reduced central/two-node proxy sweeps | 0.025-Er detuning decks for Vp=3…8, six phases, central tube and eight-node paper-derived tube proxy | `inconclusive` pending full run | The author per-tube population table and Gaussian-width convention were not released; tube result cannot be called author-equivalent. |
| T004 | Main Fig. 4 main theory series and inset | Two of six central double crossings resolved at reduced scale | Derived from frozen T003 rows using the printed 0.015 rule; all six crossings required | `inconclusive` pending full run | A stable boundary difference is not a paper error without protocol-v2 convergence and independent review. |
| T005 | Supp. Fig. S1(a), S1(b), S1(c), S1(d), S1(e), S1(f) | Reduced L=81 cloud traces | Exact stated L=369, Gaussian FWHM≈123 sites, Vp/Vd, trap edges and time axis; q/phase convergence included | `inconclusive` pending full run | FWHM is numerically fragile; q=6→8 and phase 6→12 must pass. |
| T006 | Supp. Fig. S2 theoretical imbalance and edge-density series | Reduced finite-time proxy curves | Explicit 3000-tau dynamics on the same central/tube detuning deck | `inconclusive` pending full run | The experimental 200-tau series is comparison-only and its raw values remain unavailable. |

All five rows reference `implementations.paper_scale_theory` in
`figure_coverage.json`.  The safe entrypoint prepares a 2,784-block manifest;
`paper_scale_run_contract.json` declares the full production, q-grid, size,
phase and tube-quadrature convergence campaign.

## Experimental reference items excluded from the theory denominator

| Paper item | Reference target | Evidence boundary |
| --- | --- | --- |
| Main Fig. 2(a) | T002 | The source release contains the plotted PDF and caption, but no in-situ FWHM array, calibration record or uncertainty table. |
| Main Fig. 3(a) | T003 | No six-phase shot values, SEM array or empirical-fit inputs are present for the \(V_p=4\) panel. |
| Main Fig. 3(b) | T003 | No six-phase shot values, SEM array or empirical-fit inputs are present for the \(V_p=6\) panel. |
| Main Fig. 3(c) | T003 | No six-phase shot values, SEM array or empirical-fit inputs are present for the \(V_p=8\) panel. |
| Main Fig. 4 experimental points | T004 | No fitted boundary samples or covariance information are present. |
| Supp. Fig. S2 experiment | T006 | No 200-tau experimental imbalance values, uncertainties or fit inputs are present. |

These measurements stay in the full-paper inventory as comparison evidence,
but they are not deferred scientific-compute targets and do not enter the 13
item theory denominator. The runner never substitutes source pixels, digitized
curves, synthetic measurements or author code for their missing arrays.
