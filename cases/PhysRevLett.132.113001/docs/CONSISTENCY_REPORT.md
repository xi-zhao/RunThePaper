# Consistency and Paper Review Report

## Supported

- T001/T002: exact Stark-basis identity and field scaling pass.
- T003: six calculated components and Stark ordering pass.
- T004-T008: printed scalar normalizations and arithmetic are reproducible.
- T010: all 20 printed Stark shifts agree within 2.16 kHz under a declared
  simplified hyperfine model.
- T011/T012: decimal assembly and sigma-convention calculations are explicit.

## Open scientific limitations

- T009 is leading-Dirac only, not the complete supplemental QED calculation.
- Four experimental arrays are missing and therefore cannot be reproduced or
  scored through source-image digitization.
- Exact hyperfine coefficients are not available in the accessible sources.

## Review observations

1. Rounded inputs leave a 52.23-Hz binding-frequency gap.  Classification:
   `inconclusive_rounding_guard_digits`; `paper_error_candidate=false`.
2. The 4.5-sigma CODATA-2010 wording uses a one-sided uncertainty convention.
   Classification: `methodological_convention_inconclusive`;
   `paper_error_candidate=false`.
3. Displayed Table I rows require additional 2.32-kHz statistical and
   1.30-kHz systematic quadrature components to reach the reported totals.
   This is a disclosure/closure observation, not evidence of a paper error.

No paper-error candidate is emitted without protocol-v2 fresh-context review
and an independent attempt to falsify the discrepancy.
