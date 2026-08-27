# Paper Map

## Identity

- **Paper ID:** 2608.03987
- **Title:** *Realified tensor networks: quantum circuit simulation on
  real-valued matrix accelerators*
- **Authors:** Yusheng Zhao, Xiwei Pan, Enji Xiong, Chengkai Zhu, Jinguo Liu
- **Source:** arXiv:2608.03987v2 (5 August 2026)
- **Local PDF:** `../raw/paper.pdf`
- **Local source:** `../paper-source/main.tex`
- **Data release:** Zenodo `10.5281/zenodo.21791682`

## Reproduction Goal

Enumerate the whole paper and independently reproduce every theoretical
numerical item that follows from the paper model. The atomic denominator is six
items: Figure 8, Figure 9(a), Figure 9(b), Table 1 core, Table 1 extension, and
Table 5. The primary calculation must use a clean-room implementation built
from the paper's equations, method description, parameters, and raw circuit
inputs. Author numerical code, optimized trees, result arrays, digitized
curves, and source pixels are prohibited as scientific inputs; published
values may be used only after generation for post-hoc comparison.

Tables 2-4 remain visible in the full inventory as experimental measurements.
They require the paper's Ascend/A800 hardware executions and therefore do not
enter the formula- or model-driven reproduction denominator. An A100 run could
be reported separately as a portability experiment, not as a paper-exact
replacement for those measurements.

## Paper Structure

| Section | Role | Reproduction relevance |
| --- | --- | --- |
| 1 Introduction | Motivation and hardware problem | Context only |
| 2 Realified representation | Defines green tensors, multiplication, and structure tensor | Analytic context |
| 3 Cost law and differentiation | Proves the arithmetic law and memory bound | EQ001 gate |
| 4 Implementation | Compiler/executor strategies | Needed for later performance extension |
| 5 Evaluation | 67 circuits, optimizer protocol, complexity, performance/correctness | Figures 8-9, Table 1, and measured Tables 2-4 |
| Appendix: reoptimization landscape | Independent time/space/read-write complexity | Table 5 target and method trace |
| Appendix: implementation/precision | Runtime and correctness details | Experimental context; optional portability study |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Theorem 1, Eq. (8), `eq:law` | `o = 1 + 2m + r` and analytic band | verified; numeric gate passed |
| EQ002 | Figure 9 caption, `fig:pipe` | relative convert-only/full-anneal gap | source verified; independent result differs |
| METHOD001 | Section 5 + Zenodo release | author-data reference reconstruction | executed/reference |
| METHOD002 | Eq. (8), Appendix NNI description, raw circuits | clean-room circuit-to-tree optimization | executed, 67/67 |
| METHOD003 | hardware implementation section | optional A100 portability extension | planned/optional |
| METHOD004 | Appendix independent-audit definitions | independent loop-volume complexity accumulator | declared; not implemented |

## Display-item Inventory

The source contains **33 atomic display items**: 24 schematic panels, 6
theoretical numerical items, and 3 experimental-measurement tables. The table
below summarizes the ten numbered figures; the authoritative panel- and
table-level enumeration is `figure_coverage.json` and
`FIGURE_CLASSIFICATION.md`.

| Item | Caption summary | Class | Decision |
| --- | --- | --- | --- |
| Figure 1 | End-to-end realification overview | schematic_context | excluded |
| Figure 2 | Symmetrizing the multiplication tensor | schematic_context | excluded |
| Figure 3 | Realified matrix product | schematic_context | excluded |
| Figure 4 | Conjugation and global phase rules | schematic_context | excluded |
| Figure 5 | Tree freedom / two equivalent realifications | algorithm_trace | excluded |
| Figure 6 | Algebraic identities of the structure tensor | schematic_context | excluded |
| Figure 7 | Pass, ride, and merge cost cases | schematic_context | excluded |
| Figure 8 | Cost-law scatter for 67 circuits | numeric_reproduction | T008 |
| Figure 9 | Pipeline comparison for 67 circuits | numeric_reproduction | T009 |
| Figure 10 | Forward/backward pullback wiring | schematic_context | excluded |

## Numerical Table Inventory

| Item | Content | Current decision |
| --- | --- | --- |
| Table 1 core (`tab:bench`, 9 rows) | core random-circuit complexity audit | target T010; declared but uncovered |
| Table 1 extension (`tab:bench`, 3 rows) | extension-circuit complexity audit | target T011; declared but uncovered |
| Table 2 (`tab:main`) | Ascend 910 wall-clock comparison | experimental measurement; excluded from theory denominator |
| Table 3 (`tab:struct`) | Ascend 910 structured-family timings | experimental measurement; excluded from theory denominator |
| Table 4 (`tab:precision`) | Ascend f32/A800 c64 amplitude comparison | experimental measurement; excluded from theory denominator |
| Table 5 (`tab:audit-ind`) | independent optimizer complexity audit | target T012; method not implemented |

## Assumptions

- The Zenodo release matches the manuscript state dated 2026-08-04 as its
  README states.
- Figure similarity is judged numerically; typography and marker size are
  presentation diagnostics.
- Figure 9 is explicitly scoped to an optimizer search budget; clean-room
  optimizers may expose additional low-cost trees. Such differences are
  reported as optimizer sensitivity rather than hidden.
- Inventory completion is not scientific completion. T010-T012 remain zero-
  credit uncovered items until independent artifacts and checks exist.
