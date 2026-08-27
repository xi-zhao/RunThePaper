# Paper Map

## Identity

- Paper ID: `2607.08212`
- Title: *Möbius-Guided Diagonal-Gate Compilation with Native Multiqubit Controlled-Phase Gates on Neutral-Atom Processors*
- Authors: Hairuo Huang, Yanwu Gu, Chen Huang, Xi Zhao, Meng-Jun Hu, Dong E. Liu, Jingbo Wang
- Source: <https://arxiv.org/abs/2607.08212>
- Local PDF: `raw/paper.pdf`
- Local source: `paper-source/main.tex`

## Reproduction Goal

Verify the compiler's algebraic core and the auditable Fig. 3 mechanism, then
test every locally feasible routed mechanism under an explicitly approved proxy.
The case covers Möbius inversion, Fig. 3 accounting, all eight workload classes,
20-100-qubit scaling, and native-error sensitivity. It does not claim to
regenerate the unpublished author route traces or exact Figs. 4-8 curves.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| II | Projector-phase primitive and Möbius representation | Exact local algebra, suitable for exhaustive checks |
| III | Benchmark families and Fig. 3 mechanism | Clause expansion is specified; concrete six-clause input is absent |
| IV | Zoned architecture and no-fault model | Table I is public; full geometry and throughput contract are absent |
| V | Routed numerical comparisons | Figs. 4-8 require missing generators, seeds, partitions, and route traces |
| Appendices A-B | Inversion and locality proofs | Used to validate the executable transform |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| MOB001 | Eqs. (4)-(6) | Projector-phase accumulation / zeta transform | verified |
| MOB002 | Eqs. (7), (9), Appendix A | Möbius inverse | verified exhaustively |
| MOB003 | Eqs. (21)-(22) | 3-SAT violating-pattern expansion | verified for all eight polarities |
| MOB004 | Eq. (23), Table I | Routed no-fault roll-up | verified on declared proxy route state |
| METHOD001 | Algorithm 1 | Frontend-to-router workflow | executable through approved proxy backend |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1 | Hardware/Möbius schematic | schematic context | rendered as reference only |
| Fig. 2 | Compiler pipeline | algorithm trace | guides module boundaries |
| Fig. 3(a) | ZAP decomposition | numeric/algorithm target | gate census exact; generated depth 121 vs paper 128 |
| Fig. 3(b) | ZX no-insert | numeric/algorithm target | blocked by absent source circuit and ZX configuration |
| Fig. 3(c) | Möbius-native circuit | numeric/algorithm target | support stream transcribed; count and depth exact |
| Figs. 4-5, 8 | Fidelity/move/stage plots | numerical targets | eight-family proxy complete; exact author panels blocked |
| Fig. 6 | Duration and compile-time scaling | numerical target | three-family 20-100 q proxy complete; local timings only |
| Fig. 7 | Native-error sensitivity | numerical target | three ZAP-comparison surfaces complete; break-even contours not reproduced |
| Fig. 9 | ZX insert diagnostic | algorithm trace | deferred with ZX baseline |
| Table I | Hardware proxy parameters | parameter reference | captured in routing config |

## Assumptions

- Phase equality is checked modulo `2π`.
- Fig. 3 support positions are transcribed from the vector source panel and are
  treated as source reference, not author data.
- The six-CNOT/seven-phase CCZ template is derived from the parity phase
  polynomial and lowered with `CNOT = H-CZ-H` as stated by the paper.
- Proxy routed claims use only explicitly declared geometry, seeds, partitions,
  and generators and are capped as `proxy_model`.
