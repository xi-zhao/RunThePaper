# Paper Review Protocol V2

## Current conclusion

Classification: `inconclusive`; `paper_error_candidates=0`.

The case independently follows the printed ibDET equations and exposes every
main-text numerical panel as a target. The shared algebra passes independent
small-system tests, but no material-scale target array exists yet. Missing
production parameters, unavailable Supplement Tables S6/S7, and deferred
many-body compute prevent a conclusion about the plotted material results.

## Inventory-first boundary

The fresh reviewer must first enumerate numerical figures and quantitative
claims from the paper-only inventory bundle. Only after that inventory is
frozen may the reviewer open the falsification bundle containing equation
cards, code, generated data, and run evidence. The original reproduction
conversation, this report, and author implementation code are prohibited.

## Required falsification checks

1. Re-derive Eqs. (1)-(4), including the Hartree-Fock subtraction and the
   embedded-GW replacement sign.
2. Check whether every printed material basis, pseudopotential, k mesh,
   embedding size, frequency grid, broadening, and structure is recoverable.
3. Recompute at least one Si convergence point and one Na nonlocal correction
   with an implementation independent of this case.
4. Test embedding-size, frequency-grid, broadening, k-grid, and backend
   convergence before comparing printed anchors.
5. Attempt to explain any discrepancy through reproduction defects, parameter
   ambiguity, finite-size effects, and alternative observables before calling
   it a paper error.

## Candidate threshold

A paper-error candidate requires two distinct passing strong checks, an
explicit falsification attempt, a source pinpoint, a quantitative discrepancy,
and exclusion of reproduction and compute ambiguity. None currently meets
that threshold.

## Fresh-review state

Review bundles are generated for a future fresh context. No review result is
fabricated in this case; independent review remains missing.
