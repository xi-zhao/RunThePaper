# Propane speedup inconsistency — no erratum verdict

The filename is retained for historical links. Under protocol-v2 this document
records an unresolved discrepancy, not an adjudicated correction to the paper.

## Preserved observation

For Main Fig. 2 at `t=6000`, the paper body states that qDRIFT uses `591` times
fewer gates for propane. The abstract gives an upper range endpoint of `1591`.
Independent evaluation of the appendix bounds with the parameter values printed
over the propane panel gives

`N_best-Trotter / N_qDRIFT = 1585.0849345`.

The difference between `1585.08` and `1591` is compatible with the displayed
molecular parameters being rounded. It cannot be reconciled with `591` under
the current formula implementation. Carbon dioxide and ethane independently
give `305.7885` and `1003.1617`, matching the body's `306` and `1006` within 1%.

## Current protocol-v2 assessment

`inconclusive`; `paper_error_candidate_emitted=false`.

Evidence already present:

- paper-grid parameters as published;
- independently generated and isolated-attested v2 data;
- 60-digit integer-boundary checks;
- a quantified gap and consistency checks against the abstract and other panels;
- an explicit test of all four plotted comparator families, none of which
  produces `591x`.

Evidence still missing before `paper_error_candidate`:

- a fresh inventory-first protocol-v2 independent review;
- a second genuinely distinct numerical method, not another wrapper over the
  same formulas;
- a strict tolerance basis that accounts for the unpublished unrounded
  molecular parameters;
- falsification of interpretations beyond the four comparator families
  actually plotted in Fig. 2.

A failed precision, invariant, or method-parity check would instead be a
`reproduction_defect`. The v1 float-boundary defect was fixed in v2 and is not
evidence against the paper.

Machine-readable evidence:
`outputs/checks/panel_target_acceptance.json`, panel `T001/propane` and
falsification attempt `PV2-004`.
