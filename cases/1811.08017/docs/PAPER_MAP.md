# Paper Map

## Paper identity and source scope

- arXiv:1811.08017, *A Random Compiler for Fast Hamiltonian Simulation*.
- Published as Earl Campbell, *Physical Review Letters* **123**, 070503
  (2019), DOI `10.1103/PhysRevLett.123.070503`.
- The arXiv TeX contains the main article and its appendices in one source. No
  separate supplementary file, author implementation, or author numerical
  array is present.

## Scientific claim

qDRIFT samples Hamiltonian terms with probability proportional to their
strength. Its rigorous resource bound depends on the one-norm `lambda`, rather
than explicitly on the term count `L`, and is substantially lower than the
compared Trotter-Suzuki bounds for the three molecular parameter sets studied.

## Complete figure and table inventory

| Paper item | Type | Numerical decision |
| --- | --- | --- |
| Main Fig. 1 | qDRIFT pseudocode | non-numerical context |
| Main Fig. 2, propane | five resource-bound curves | T001, independently generated |
| Main Fig. 2, carbon dioxide | five resource-bound curves | T001, independently generated |
| Main Fig. 2, ethane | five resource-bound curves | T001, independently generated |
| Main Fig. 3(i) | controlled-`exp(i tau Z)` circuit schematic | non-numerical context |
| Main Fig. 3(ii) | general controlled-`exp(i tau H_j)` circuit schematic | non-numerical context |
| Main Fig. 4, propane | two phase-estimation resource curves | T002, independently generated |
| Main Fig. 4, carbon dioxide | two phase-estimation resource curves | T002, independently generated |
| Main Fig. 4, ethane | two phase-estimation resource curves | T002, independently generated |
| Table I | symbolic big-O scaling laws | formula context; no evaluated entries |

The ten display items are represented atomically. The two aggregate target IDs
are intentionally retained because the accepted isolated run attests the two
three-panel datasets. Coverage and panel acceptance are nevertheless recorded
independently for all six numerical panels.

## Numerical prose claims tied to the targets

| Claim | Paper location | Evidence target | Current status |
| --- | --- | --- | --- |
| speedups range from 306x to 1591x | abstract | T001 | formula result is consistent with the range |
| at `t=6000`: 591x, 306x, 1006x for propane, CO2, ethane | main-text numerics paragraph | T001 | CO2/ethane agree; propane is a preserved stable discrepancy |
| crossover occurs around `t=10^7–10^8` at `10^23–10^25` gates | main-text numerics paragraph | T001 | curve-level claim; checked from generated bounds, with rounding caveat |
| at `P_f=5%`: 1406x, 304x, 789x | appendix comparison | T002 | all three agree within 1% |
| phase estimation gains 2–3 orders of magnitude at 5% failure | main text | T002 | supported at the feature-check level |

The propane `591x` disagreement is not labeled a paper error. The current
protocol-v2 assessment is `inconclusive` until a fresh inventory-first reviewer,
a second independent numerical method, strict tolerance justification using
unrounded inputs, and falsification of interpretations beyond the four plotted
comparator families are available. The completed self-audit is recorded in
`PAPER_REVIEW_PROTOCOL_V2.md`.

## Parameter provenance

The panel headers explicitly print `(lambda, Lambda, L)`:

| Molecule | Qubits | lambda | Lambda | L |
| --- | ---: | ---: | ---: | ---: |
| propane | 46 | 426.61 | 6.58466 | 241582 |
| carbon dioxide | 54 | 608.414 | 10.3658 | 113959 |
| ethane | 60 | 768.138 | 4.07041 | 467403 |

Only these printed parameter values, captions, and paper formulas enter the
numerical runner. The vector figures and extracted raster panels are
post-generation comparison evidence and never numerical inputs.

The Fig. 2 caption also describes truncating small Hamiltonian terms. The
source package contains no term-level molecular coefficient arrays, so that
preprocessing statement cannot be rerun independently. This missing
indispensable author input does not affect formula evaluation from the aggregate
tuples printed above; it remains an explicit caption-level review boundary.
