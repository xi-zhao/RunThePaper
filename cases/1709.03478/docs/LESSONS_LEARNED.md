# Lessons Learned

## Case summary

- Paper: Lüschen et al., one-dimensional quasiperiodic mobility edge.
- Final state: exploratory numerical-feature reproduction with partial Fig. 4.
- Main result: independent continuum numerics reproduce complementary
  imbalance/edge-density trends.
- Main blockers: unavailable experimental arrays/tube histogram and unresolved
  upper thresholds at reduced phase-diagram scale.

## What worked

- A tridiagonal continuum solver made (L=369) feature sweeps feasible locally.
- Projected-position Wannier functions gave one coherent preparation model for
  both CDW and center-cloud observables.
- Separating stationary diagonal-ensemble curves from explicit (3000\tau)
  dynamics corrected an initially conflated method without touching source data.
- A hash-verified freeze boundary made it mechanically clear when source
  figures were allowed to enter the rendering workflow.

## Difficulties and reusable lessons

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| Captions can distinguish stationary and finite-time theory even when axes look similar. | Reusing one curve can silently change the physical object. | Give stationary/dephased and finite-time observables separate method cards and output schemas. |
| Lowest-band projection leaks small norm from ideal preparations. | Directly using nominal normalization can produce a nonzero edge density at (t=0). | Normalize (N_c(t)) by the same projected representation's computed (N_c(0)). |
| A fixed threshold can be below a finite-size floor. | Small smoke systems can never produce a requested crossing. | Inspect observable floors before phase-boundary extraction and classify unresolved crossings rather than extrapolating them. |
| Source-looking curves do not imply author-data equivalence. | Sparse phase/tube proxies can preserve topology while shifting magnitudes. | Cap scores, declare `reduced_scale`, and require author metadata for paper-exact claims. |
| Scientific assertions should distinguish validity from completeness. | Two valid boundaries support coexistence but not a full phase diagram. | Let the runner pass core validity while target status remains `partial` with explicit completeness counts. |

## New Failure Modes

| Failure mode | Detection | Resolution |
| --- | --- | --- |
| Matplotlib tries to spawn a font-manager helper inside the OS sandbox. | Isolated v1 subprocess denial. | Declare a prebuilt font cache as a non-scientific runner input. |
| A visual source is accidentally read before data freeze. | Compare audit inventory and freeze flag. | Post-freeze script verifies all CSV hashes before opening any image. |
| Fig. 4 upper crossings disappear for some (V_p). | Store `null` crossings and count resolved boundaries. | Preserve partial status; request a converged large-scale run. |

## Reusable Checks Or Tools

The post-freeze hash verifier/comparison-board pattern is reusable, while this
paper's continuum preparation and threshold semantics should remain case-local.
No global harness files were changed in this strict case-only task.
