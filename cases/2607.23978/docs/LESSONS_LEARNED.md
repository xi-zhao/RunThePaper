# Lessons Learned

## Case summary

- Paper: *Non-Hermitian-enhanced quantum sensing in an optical interferometer*
- Final scientific status: all public theory lanes reproduced; public-source subset only
- Main blocker: absent Supplement
- Main finding: printed observable/order does not saturate the claimed bound

## Reusable lessons

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| Derive before plotting | Literal Eqs. (3)+(5) produce an exact `+4` discrepancy that a visual imitation would hide. | Require symbolic/numeric identity tests for every claimed saturation or bound. |
| Preserve competing interpretations | Silently changing the operator order would erase a scientific result. | Keep literal and paper-intended lanes with separate outputs and explicit provenance. |
| A partial public source is a real blocker | `A1/A2` and POVM elements cannot be inferred scientifically from colored curves. | Mark missing-source inputs as blocked; never digitize them into the runner. |
| Theory-only panels need scoped pixel evidence | Experimental markers lower literal foreground similarity even when theory is exact. | Predeclare a mask generated from frozen independent arrays; keep whole-crop metrics diagnostic. |
| Paper-size images belong in the runner | Manual resizing weakened the proof chain. | Declare comparison renders as isolated-run outputs. |
| Panel order is a scientific contract | Fig. 2(e,f) uses the reverse `p` order from Fig. 2(c,d). | Trace each panel to its caption rather than inheriting loop order. |

## Efficiency

The complete public theory run takes 1.87 s on CPU. Matrix dimensions are `2 x 2`, and 301–1000 point grids dominate only plotting, so GPU execution would add orchestration cost without meaningful speedup.

## New Failure Modes

| Failure mode | Detection |
| --- | --- |
| A plotted bound is reproduced by silently changing a printed operator order. | Evaluate literal and claim-consistent lanes and store their exact difference. |
| A caption-dependent panel order is inherited from a previous plotting loop. | Validate each panel's parameter mapping independently against its caption. |
| Mixed experimental panels are scored as if experimental symbols were a theory output. | Require explicit content scope and a hashed theory mask; otherwise reject the render contract. |

## Reusable Checks Or Tools

| Check/tool | Reuse |
| --- | --- |
| Competing-interpretation identity test | Papers whose printed formula conflicts with a claim or curve. |
| Density-matrix/Kraus physicality gate | Quantum-sensing and open-system reproductions. |
| Semantic render-content contract and binary mask | Theory curves embedded in mixed experimental panels. |

## Harness backlog

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| P1 | Add a declared theory-only raster mask for mixed experimental panels. | Literal foreground mean was 50.74 despite exact analytic gates. | implemented in Harness H098 |
| P1 | Require all pixel-comparison render artifacts in the isolated run contract. | Earlier registered copies were manual. | implemented in this case |
| P1 | Flag a reproduced figure that contains an audit-only curve absent from the source. | Literal-order audit initially contaminated Fig. 3(a). | implemented in this case |
| P2 | Validate caption panel order against target metadata. | Fig. 2(e,f) order initially followed the wrong loop. | proposed |
