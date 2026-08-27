# Consistency Report

## Summary

| Outcome | Count | Meaning |
| --- | ---: | --- |
| exact analytic or author-data reproduction | 5 | T001, T002A, T002C, T002D, T003 |
| complete analytic feature reproduction | 3 | TS02, TS03, TS04 |
| partial with versioned evidence gap | 1 | T004 final formula passes; deposited data are stale |
| partial with rejected paper claim | 1 | TS01 exact dynamics contradict published cutoff-sensitive amplitude |
| declared but not run | 0 | full numerical scope is executed |

## Per-Target Consistency

| Target | Level | Evidence | Remaining difference and attribution |
| --- | --- | --- | --- |
| T001 | exact analytic | `t001_checks.json` | absolute plotted `r` is unspecified by the caption |
| T002A | exact numerical | `t002a_checks.json` | raster styling only |
| T002C | exact author-array | `t002c_checks.json` | none scientifically |
| T002D | exact author-array | `t002d_checks.json` | raster styling only |
| T003 | exact author-array plus invariant | `t003_checks.json` | raster layout only |
| T004 | partial | `t004_checks.json` | Zenodo arrays are from an earlier manuscript version |
| TS01 | partial; quantitative source claim rejected | `ts01_checks.json` | undisclosed, unconverged finite-Fock cutoff |
| TS02 | complete analytic feature | `ts02_checks.json` | no independent source array was released |
| TS03 | complete analytic reproduction with source correction | `ts03_checks.json` | no independent source array; printed absolute-energy label conflicts with unit intercepts |
| TS04 | complete analytic feature | `ts04_checks.json` | no independent source array was released |

The scientific visual-fidelity score is `90.31/100`; the separate presentation
diagnostic is `66.23/100`. Scientific status is nevertheless
terminal because all claims and numerical panels have been adjudicated; image
similarity is not allowed to override a verified or rejected physics claim.
