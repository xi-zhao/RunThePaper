# Lessons Learned

## What worked

- A 120-degree reciprocal basis makes complete hexagonal shells and every Fourier shift explicit.
- Kubo curvature avoids fragile boundary-gauge bookkeeping in a truncated plane-wave basis.
- One implementation seam supports the two-layer, conduction/valence and spin four-state models.
- Freezing hashes before reference access makes render optimization auditable.

## Pitfalls

| Pitfall | Evidence | Prevention |
| --- | --- | --- |
| incomplete/asymmetric reciprocal cutoff | transition gap converges slowly near 1.74 degrees | use complete shells and report cutoff-to-cutoff error |
| confusing source pixels with scientific evidence | visually close curves can still be copied rather than derived | isolated raw-free numerical runner and provenance checks |
| blank backgrounds inflating score | full-canvas mean 89.07 versus scientific foreground 61.82 | primary score only on predeclared numerical axes/maps |
| using a fitted continuum proxy for DFT | would conceal a missing first-principles workflow | keep DFT panels deferred with concrete QE plan |
| sending small dense matrices to A100 | overhead exceeds 11.341 s local total | choose hardware from measured bottleneck, not availability alone |

## Reusable improvements

- Promote a generic complete-shell plane-wave/Fourier-link helper only after a second moire case proves the interface.
- Add a harness field for separately normalized source/generated scientific crops; this case demonstrates why one full-panel resize understates line-plot fidelity.
- Require external-computation panels to record missing software/pseudopotential metadata separately from wall-time limitations.

## New Failure Modes

- A case-specific comparison script and the Harness both wrote
  `pixel_evidence.json`; the latter must remain the sole authoritative state
  projection. Scientific-region diagnostics now use the distinct
  `scientific_pixel_metrics.json` artifact.
- A prose-only derivation summary can be scientifically meaningful yet fail
  structural audit. The compact summary must retain rendered equations and
  point to the full derivation trace.

## Reusable Checks Or Tools

- Run `build_pixel_layout_crops.py` followed by `build_pixel_evidence.py` after
  the physics-project and target-contract checks; never hand-author the
  authoritative pixel state.
- Keep numerical checks, scientific pixel diagnostics, and Harness gate files
  in separate namespaces so rerunning one projection cannot invalidate
  another artifact's hash or schema.
