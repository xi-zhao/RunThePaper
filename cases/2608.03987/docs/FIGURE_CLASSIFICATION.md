# Figure and Table Classification

The full arXiv v2 source contains 33 independently enumerable display items:
24 schematic panels, 6 theoretical numerical items, and 3 hardware-measurement
tables. Only the 6 theoretical numerical items enter the PRAgent reproduction
denominator. The three measured tables remain visible in the inventory but are
not treated as outputs of a formula- or model-driven numerical runner.

| Atomic item | Item type | Scientific role | Decision | Target | Scientific object |
| --- | --- | --- | --- | --- | --- |
| Fig. 1(a) | figure panel | schematic | excluded | — | circuit/amplitude overview |
| Fig. 1(b) | figure panel | schematic | excluded | — | complex tensor-network overview |
| Fig. 1(c) | figure panel | schematic | excluded | — | local realification rewrite |
| Definition 1 illustration | figure panel | schematic | excluded | — | realification of one complex tensor |
| Definition 2 illustration | figure panel | schematic | excluded | — | multiplication tensor mechanism |
| Fig. 2(a) | figure panel | schematic | excluded | — | oriented multiplication tensor |
| Fig. 2(b) | figure panel | schematic | excluded | — | permutation-symmetric structure tensor |
| Fig. 3 | figure panel | schematic | excluded | — | realified matrix product |
| Fig. 4(a) | figure panel | schematic | excluded | — | conjugation sign flip |
| Fig. 4(b) | figure panel | schematic | excluded | — | global-phase rotation |
| Fig. 5(left) | figure panel | schematic | excluded | — | `(AB)C` realification tree |
| Fig. 5(right) | figure panel | schematic | excluded | — | `A(BC)` realification tree |
| Fig. 6(a) | figure panel | schematic | excluded | — | matrix-product identity |
| Fig. 6(b) | figure panel | schematic | excluded | — | permutation invariance |
| Fig. 6(c) | figure panel | schematic | excluded | — | conjugate covariance |
| Fig. 6(d) | figure panel | schematic | excluded | — | cascade/associativity rule |
| Fig. 6(e) | figure panel | schematic | excluded | — | unit rule |
| Fig. 6(f) | figure panel | schematic | excluded | — | norm-square rule |
| Fig. 6(g) | figure panel | schematic | excluded | — | reverse-mode rule |
| Fig. 7(pass) | figure panel | schematic | excluded | — | `1x` pass mechanism |
| Fig. 7(ride) | figure panel | schematic | excluded | — | `2x` ride mechanism |
| Fig. 7(merge) | figure panel | schematic | excluded | — | `3x` merge mechanism |
| Fig. 8 | figure panel | theoretical numerical | target | T008 | 67-circuit cost-law scatter |
| Fig. 9(a) | figure panel | theoretical numerical | target | T009 | three-pipeline random-circuit overheads |
| Fig. 9(b) | figure panel | theoretical numerical | target | T009 | 67-circuit relative pipeline gaps |
| Table 1 core | table | theoretical numerical | target | T010 | nine-row random-circuit complexity audit |
| Table 1 extension | table | theoretical numerical | target | T011 | three-row extension complexity audit |
| Table 2 | table | experimental measurement | excluded | — | Ascend 910 random-circuit timings |
| Table 3 | table | experimental measurement | excluded | — | Ascend 910 structured-circuit timings |
| Table 4 | table | experimental measurement | excluded | — | Ascend/A800 amplitude differences |
| Table 5 | table | theoretical numerical | target | T012 | independent optimizer complexity audit |
| Fig. 10(a) | figure panel | schematic | excluded | — | forward contraction wiring |
| Fig. 10(b) | figure panel | schematic | excluded | — | reverse-mode pullback wiring |

T008 and T009 have existing clean-room numerical evidence. T010-T012 are real
scientific targets, not placeholders: their paper objects and acceptance
criteria are declared, but no acceptable table artifact exists yet, so they
remain uncovered. Source pixels, author result arrays, and author numerical
code are prohibited as scientific inputs for all five targets.
