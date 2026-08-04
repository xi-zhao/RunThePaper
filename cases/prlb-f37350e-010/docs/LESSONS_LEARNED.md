# Lessons Learned

## Case summary

- Final status: `benchmark_gold_invalid`.
- Source issue: two older non-PRL sources stitched into one record.
- Physics issue: complex-pair counting was combined with a real-mode
  propagator convention.

## Reusable lessons

| Lesson | Why it generalizes | Future check |
| --- | --- | --- |
| Compare the full quadratic action, not an isolated interaction coefficient. | Complex conjugate pairs double kinetic and interaction terms together. | Derive the inverse propagator both from the Hessian and mode expansion. |
| Verify the named asymptotic regime numerically. | A correct formal series can be described in the opposite physical limit. | Plot truncation error against the expansion parameter. |
| Treat source identity as a scientific gate. | Correct equations from multiple papers do not make a single-paper reproduction. | Require one DOI/version contract before paper-scope credit. |
| Check symbols as well as numeric expressions. | A duplicated `lambda_v` silently erases the singlet observable. | Compare requested quantity names to source equation labels. |

## Iteration accounting

Three iterations were attempted. Iterations 1 and 2 were discarded for a
standard-library compatibility issue and a NumPy JSON-boundary issue.
Iteration 3 was the first acceptable iteration: 5/5 tests and 8/8 audit checks
passed.

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| paired-mode half-factor collision | frozen Tasks 2-3 | compare the full quadratic action with the local Hessian |
| asymptotic-regime inversion | frozen Task 3 | measure truncation error across the claimed limit |
| composite-paper identity | whole record | require one DOI/version source contract before paper credit |

## Reusable Checks Or Tools

| Candidate | Why reusable | Destination |
| --- | --- | --- |
| quadratic-action normalization audit | catches real/complex Fourier-mode factor errors | harness backlog |
| asymptotic-regime trend gate | detects series described in the wrong physical limit | harness backlog |
| source-contract split detector | prevents multi-paper prompts receiving single-paper credit | campaign source audit |
