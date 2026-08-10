# Lessons Learned

## Case Summary

- PaperID: `1811.08017`.
- Status: `review_pending` after complete numerical coverage.
- Targets: Main Figs. 2 and 4, every numerical subpanel and curve.
- Blocker: only fresh-context independent review.

## Reusable Lessons

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| Solve printed inequalities exactly before using asymptotic forms. | Float resolution cannot distinguish adjacent integers near `10^25`, even in log space. | Use a fast float bracket followed by arbitrary-precision `n`/`n-1` verification. |
| Cross-check scalar prose against abstract, formulas and figures. | The body says `591x` for propane while all independent evidence supports about `1591x`. | Add a scalar-claim consistency check to every reproduction. |
| Select optimized method order pointwise. | A single globally chosen Suzuki order changes the envelope shown in Fig. 2. | Preserve each branch, then minimize only where the paper prescribes it. |
| Freeze data before visual tuning. | Close visual agreement must not become hidden numerical fitting. | Record CSV hashes, then allow only presentation fields in RenderContract. |

## New Failure Modes

`scalar_prose_internal_inconsistency`: a reported scalar may disagree with the
paper's own abstract, equations and plotted result. The case should preserve the
formula-derived value and publish the inconsistency with independent evidence.

## Harness Backlog

Add an automated cross-source scalar-claim audit that compares abstract/body
claims with independently generated check values and requires an explicit
discrepancy record when they disagree, but keep it inconclusive
until the protocol-v2 paper-error gates are satisfied.

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Minimal-integer inequality verifier | Any rigorous resource curve can be shifted by rounding or a nonminimal segment count. | Case utility first; promote after a second use. |
| Cross-source scalar-claim audit | Abstract/body/figure disagreements occur independently of this model. | Harness checker backlog. |
| Frozen-data RenderContract | Separates scientific generation from legitimate layout tuning. | Existing harness contract; keep mandatory. |
