# Lessons Learned

## Case summary

- Paper: PRL 132, 113001 (2024)
- Status: partial / numerical feature reproduction
- Main evidence: exact Stark-basis identity, 20-value post-freeze table check,
  six-component spectrum, and decimal metrology reconstruction.
- Blockers: unpublished experimental arrays, gated formal supplement,
  higher-order QED terms, and missing fresh-context review.

## Reusable lessons

| Lesson | Why it matters | Future practice |
| --- | --- | --- |
| Separate gross Stark physics from small hyperfine resolution | A good feature match can coexist with a non-paper-exact branch model | Score and document the approximation independently |
| Printed table rows may not close to reported totals | Silent redistribution would hide scientific ambiguity | Emit an explicit residual quadrature component |
| Decimal arithmetic is required at optical-frequency scales | Binary float can erase Hz-level discrepancies at PHz scale | Use `Decimal` before classifying a discrepancy |
| Data absence is different from compute shortage | More GPU time cannot recreate unpublished measurements | Require fail-closed schemas and hashes |
| Source panels belong after the freeze | Visual tuning must not alter physical arrays | Hash scientific outputs before and after comparison rendering |

## Paper-review boundary

Rounding and sigma-convention observations were recorded as `inconclusive`.
Neither is promoted to a paper-error candidate without protocol-v2
fresh-context falsification.  This case reinforces that reproduction and peer
review share evidence but require distinct lifecycle gates.

## New Failure Modes

- `rounded-claim nonclosure`: PHz-scale printed inputs can leave an apparently
  meaningful Hz-scale residual solely because guard digits are unavailable.
- `displayed-ledger nonclosure`: visible table rows may be a summary rather
  than the complete set used in a reported aggregate uncertainty.

## Reusable Checks Or Tools

- Post-freeze scalar-table validator: hash scientific artifacts, compare
  printed values, and prove the hashes are unchanged.
- Missing-author-data schema gate: require exact columns and hashes before any
  experimental reanalysis starts.

## Harness backlog

No cross-case Harness change was made from this case-only branch.  A possible
future generic helper is a reusable post-freeze scalar-table comparison lane
that automatically proves scientific hashes remained unchanged.
