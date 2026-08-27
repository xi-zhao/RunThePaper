# Paper Map

## Identity

- Paper ID: `2506.06669`
- Title: *Remote Entanglement Generation Via Enhanced Quantum State Transfer*
- Journal: *PRX Quantum* **7**, 010348 (2026)
- DOI: `10.1103/4x8d-cmyx`
- Source: `https://arxiv.org/abs/2506.06669`
- Audited document: `raw/2506.06669.pdf`, 24 pages including the Supplement

## Reproduction boundary

The unit of coverage is one independently judgeable paper item: a theoretical
curve/panel or a no-display quantitative claim. Experimental measurements,
schematics and a table of measured device parameters are fully enumerated but
do not enter the computational reproduction denominator.

Source figures may be read after numerical arrays are frozen for comparison and
RenderContract tuning. They are never numerical inputs. Author arrays, source
pixels and author numerical code are not accepted as scientific evidence.

## Atomic inventory and current measure

| Population | Items | Coverage treatment |
| --- | ---: | --- |
| Display items audited | 117 | complete paper inventory |
| Theoretical numerical display items | 56 | eligible |
| Experimental measurement items | 53 | excluded from computational denominator |
| Schematics | 7 | excluded |
| Measured source-parameter table | 1 | excluded input, provenance-audited |
| Independent no-display claims | 4 | eligible |
| **Eligible reproduction items** | **60** | denominator |
| **Covered** | **55** | independently generated evidence accepted |
| **Uncovered** | **5** | explicitly listed below |

The authoritative reproduction measure is therefore:

- coverage: **55/60 = 91.67%**;
- mean fidelity over covered items: **69.30/100**;
- reproduction degree: **63.52/100** (`coverage × fidelity`);
- evidence grade: **E1**;
- lifecycle state: **partial**, because the critical-item gate, current run
  attestation and fresh-context review are not closed.

The older ten-target aggregate, **68.73/100**, is retained only for backward
comparison. It is not the paper-level coverage denominator.

## Equation and method inventory

| ID | Source | Role | Current boundary |
| --- | --- | --- | --- |
| QS001 | Main Eq. (1); Supp. Sec. 3 | single-excitation XY Hamiltonian | source traced; literal Hermiticity claim C001 open |
| QS002 | Main Eqs. (2)-(9); Supp. Secs. 3, 5 | zig-zag spectrum and PST | representative cases run; universal C002 open |
| QS003 | Main after Eq. (9); Supp. Sec. 6 | three-qubit analytic populations | verified |
| QS004 | Main Eq. (12); Supp. Sec. 4 | isospectral FST deformation | numerically used; phase-gauge C004 open |
| QS005 | Main Fig. 4 discussion | two-dimensional Kronecker-sum extension | reconstructed |
| QS006 | Supp. Sec. 10 | Lindblad relaxation/dephasing | source traced |
| QS007 | Supp. Sec. 9 | Gaussian parameter-noise ensemble | seed/grid partly unreported |
| QS008 | Main Eqs. (10)-(11); Supp. Sec. 5 | large-m even-site elimination | final limit supported; C003 open |
| QS009 | Supp. Sec. 10 | effective flattop-Gaussian pulse | reconstructed; physical transfer functions absent |

## Display-item map

| Paper group | Atomic class | Eligible items | Coverage |
| --- | --- | ---: | --- |
| Main Fig. 1(a-d) | qualitative schematics | 0 | excluded; T001 remains auxiliary diagnostic evidence |
| Main Fig. 2(a-f) | experimental population maps | 0 | excluded; T002/T003 theory counterparts do not replace the measurements |
| Main Fig. 3(a-b) | 10 theory curves + 10 measured series | 10 | 10/10 via T004 |
| Main Fig. 3(c-e) | measured tomography/noise series | 0 | excluded; T005 is auxiliary theory evidence |
| Main Fig. 4(a-c,e) | measured population/tomography | 0 | excluded |
| Main Fig. 4(d,f) | 4 theory curves + ideal W density | 5 | 5/5 via T007 |
| Supp. Fig. S1, S4(a) | schematics | 0 | excluded |
| Supp. Table S1 | measured device parameters | 0 | audited input only |
| Supp. Figs. S2, S3(a-h) | simulated maps | 9 | 9/9 via T002 |
| Supp. Figs. S4(b-c), S5, S6 | hardware calibration histories | 0 | excluded experimental evidence |
| Supp. Fig. S7(a-c) | 9 measured series | 0 | excluded |
| Supp. Fig. S7(d-f) | 12 simulated series | 12 | 12/12 via T008 |
| Supp. Fig. S8(a-c) | 7 measured series | 0 | excluded |
| Supp. Fig. S8(d-f) | 12 simulated series | 12 | 12/12 via T006 |
| Supp. Fig. S9(a-d) | fidelity curve + 3 matrices | 4 | 4/4 via T009 |
| Supp. Fig. S10(a) | W-state fidelity curve | 1 | **0/1, D001** |
| Supp. Fig. S10(b-d) | 3 population maps | 3 | 3/3 via T010 |

## Uncovered items preventing 100% coverage

| ID | Paper item | Direct cause | Root cause status | Code fault | Next discriminating test |
| --- | --- | --- | --- | --- | --- |
| D001 | Supp. Fig. S10(a) | generated crossover `m=10`, paper reports `m=6` | unresolved among method/input/code/paper discrepancy | not excluded | pulse-contract audit, convergence and independent backend |
| C001 | Main Eq. (1) Hermiticity | no literal-versus-corrected operator test | legacy scope-definition gap confirmed | not excluded | compare both operators and dynamics |
| C002 | zig-zag PST for every allowed `m` | sampled figures do not prove the universal quantifier | legacy scope-definition gap confirmed | not excluded | property tests over size/parity/`m` |
| C003 | large-`m` half-chain reduction | no independent Schur/index adjudication | legacy scope-definition gap confirmed | not excluded | symbolic Schur complement plus asymptotic cross-check |
| C004 | FST Bell-state phase gauge | fidelity-only evidence does not decide the complex phase | legacy scope-definition gap confirmed | not excluded | phase-aware amplitudes/density/fidelity cross-check |

No item is labelled a paper error at this stage. Each possible discrepancy
remains an open hypothesis until reproduction-code faults are independently
excluded and a fresh reviewer attempts falsification.
