# Lessons Learned

1. Full figure inventory must precede implementation.  It caught the Fig. 6
   caption's bottom-to-top energy ordering and prevented a reversed seven-panel
   mapping.
2. A theory-only target and its unavailable experimental overlay must be
   separate state objects.  Otherwise a good model curve can falsely imply the
   experiment was reproduced.
3. Post-freeze rendering needs its own contract.  Axis geometry can be improved
   after data hashes are fixed, while physical arrays and parameters remain
   immutable.
4. Pixel metrics on mixed panels need an explicit contamination flag.  A lower
   score is more honest than deleting experimental markers or tracing the
   author's curve.
5. Code-ready paper scale is valuable even when it is not executed: it proves
   how the result would be converged and resumed, but must never be reported as
   an attested paper-scale result.
6. Reproduction and peer review are one workflow.  Missing inputs and stable
   discrepancies must be classified separately, and no paper-error claim may
   bypass fresh-context falsification.

## New Failure Modes

- **Caption-order inversion:** a multi-panel caption may enumerate conditions
  in the opposite direction from panel labels.  Freeze a panel-to-parameter
  table and visually verify both endpoints before computing.
- **Mixed-panel scope inflation:** reproducing a theory curve can be mistaken
  for reproducing overlaid experimental points.  Model each branch and each
  missing author array separately in figure coverage.
- **Pixel-score pressure:** a mixed source panel can tempt the renderer to erase
  experimental markers or trace the visible curve.  Retain the contamination,
  cap the evidence tier, and let the score fall.
- **Code-ready/executed confusion:** a complete A100 plan can be mistaken for an
  attested run.  Store plans and production outputs in separate namespaces and
  require a run attestation for promotion.

## Reusable Checks Or Tools

- `scripts/apply_render_contract.py` verifies all frozen data hashes while
  applying only declared canvas/axis transformations.
- `scripts/build_comparisons.py` is the sole source-pixel reader and proves
  before/after numerical hashes are identical.
- The paper-scale runner provides config/implementation hash-bound sharding,
  deterministic disjoint seeds, checkpoint/resume, aggregation, and explicit
  target acceptance.
- Harness figure coverage, formula gate, physics project, target contracts,
  claim ledger, pixel evidence, isolated execution, and protocol-v2 review
  bundles form a reusable end-to-end gate sequence.
