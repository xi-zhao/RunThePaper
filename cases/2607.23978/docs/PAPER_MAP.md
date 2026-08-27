# Paper Map

## Identity

- Paper ID: `2607.23978`
- Title: *Non-Hermitian-enhanced quantum sensing in an optical interferometer*
- Authors: Xiaojian Huang, Lei Xiao, Bingzi Huo, X. X. Yi, Peng Xue
- Source: <https://arxiv.org/abs/2607.23978> (v1, 27 July 2026)
- Local PDF: `raw/2607.23978.pdf` (SHA-256 `df2bfff245515c179b38daef9494e1ae019d8d455f96925407febde09e0cfc9d`)
- Local source: `raw/2607.23978-source.tar` (SHA-256 `50d13108946e3564bd291f76ad490ee5cc6522633d5e61a6eba60cd916352655`)

## Reproduction Goal

Recompute every theory curve that the public manuscript defines from its
density matrix, observables, polar decomposition, and amplitude-damping
channel. Experimental apparatus and measured photon-counting points are
context only. The missing Supplemental Material is recorded as a blocker for
the non-optimal observables and the full three-port POVM calculation; no curve
is inferred from source pixels.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Theoretical framework | Defines the qubit state, encoding, observables, and error propagation | Supplies the complete noiseless optimal-curve formulas. |
| Experimental implementation | Polar decomposition and Sagnac readout | Supplies normalized fringe formula but delegates optical construction details to missing Supplement. |
| Results | Fringe and variance panels | Non-optimal observable matrices are not stated. |
| Noise | Amplitude-damping Kraus channel | Supplies `p=0.01`, `theta=0.3 pi`, and the channel exactly. |
| Conclusion | Full-POVM interpretation | The actual POVM elements are delegated to missing Supplement. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| QS001 | Eqs. (1)-(2) | Probe density matrix and phase encoding | verified |
| QS002 | Eqs. (3)-(5) and following paragraph | Error propagation, optimal observables, Fisher bounds | inconsistency isolated and numerically testable |
| QS003 | Eqs. (6)-(11) | Polar normalization, fringe, expectation, observable variance | verified for stated observables |
| QS004 | Eq. (12) | Amplitude-damping channel | verified |
| QS005 | Eqs. (13)-(14) | Noise derivative and complete-POVM CFI | variance derivative verified; POVM inputs missing |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1 | Optical apparatus | experimental_context | Excluded. |
| Fig. 2(a-b) | Non-optimal fringe curves plus data | numeric_reproduction | Blocked: `A1`, `A2` and calibration are only in absent Supplement. |
| Fig. 2(c-d) | Optimal Hermitian/non-Hermitian fringe curves plus data | numeric_reproduction | Theory curves targeted; measured points excluded. |
| Fig. 2(e-f), optimal series | Complex expectations of optimal observables | numeric_reproduction | Targeted from trace formulas. |
| Fig. 2(e-f), non-optimal series | Complex expectations of `A1`, `A2` | numeric_reproduction | Blocked by missing matrices. |
| Fig. 3(a) | Noiseless optimal variances vs `p` | numeric_reproduction | Targeted; also exposes the Eq. (3)/Eq. (5) ordering inconsistency. |
| Fig. 3(b-c) | Noisy variance and its `gamma` derivative | numeric_reproduction | Theory curves targeted; measured symbols excluded. |

## Scientific Inconsistency Found During Derivation

With the state in Eqs. (1)-(2) and the matrix `A_nH` printed in Eq. (5), the
literal Eq. (3) numerator `Tr[rho A_nH^dagger A_nH]-|<A_nH>|^2` gives

`(Delta theta)^2 = 1/F_nH + 4`,

not the claimed `1/F_nH`. Reversing the operator order to
`Tr[rho A_nH A_nH^dagger]-|<A_nH>|^2`, equivalently applying the printed
formula to `A_nH^dagger`, gives exactly `1/F_nH` and the red Fig. 3(a) curve.
The reproduction preserves both lanes and does not silently repair the paper.

## Missing Source Inputs

- The TeX cites Supplemental Material, but the arXiv PDF and source archive
  contain only the seven-page main text and Figs. 1-3.
- Public web search found no author-hosted supplement as of 3 August 2026.
- Consequently `A1`, `A2`, the optical phase calibration, normalized-loss
  construction details, and explicit complete-POVM elements are unavailable.
