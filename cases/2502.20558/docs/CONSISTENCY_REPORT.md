# Consistency Report

## Passed Checks

- Formula gate: 10/10 cards open; no numerical target depends on a closed card.
- Workspace tests: 42/42 pass.
- Reproduction run: T001-T006 complete with no failed target.
- Figure coverage contract: 315 inventory items, 279 numeric items, 279 targeted,
  zero deferred, and zero pixel-only coverage; the fixed final-disposition
  denominator contains 272 eligible atomic items after supporting items are not
  double-counted.
- Scorecard: 29/29 targets have final evidence-backed projections; the sole
  essential-physics warning is the externally blocked Error Model B definition.
- Provenance: generated CSV files declare `independent_numerics` or
  `analytic_reference`; no generated data row is digitized from a source plot.

## Scientific Consistency

- T001 reproduces the information-ordering feature but not absolute logical
  error; the proxy is permanently exploratory.
- T002 reproduces the printed cube-root lifecycle trend.
- T003 exactly evaluates the Appendix-G algorithm-counting rules.
- T004/T005 reproduce lifecycle invariants and conventional role splitting;
  the SWAP boundary pairing remains a documented gap.
- T006 exactly reproduces analytic Table-I rows and excludes simulated rows.

## Remaining Inconsistencies

No reproduced target fails its declared acceptance check. All 272 eligible
atomic items are finalized: 26 reproduced, 1 externally blocked, and 245
attempted but not reproduced. The circuit-level MLE/MWPM scope reached the
current clean-room system-capability limit; the independent source audit found
one objective publication-definition blocker in Error Model B. See
`outputs/checks/final_disposition_evidence.json`.
