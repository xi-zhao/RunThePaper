# Paper review protocol v2

This case is both a reproduction and a paper audit.  A mismatch is not a paper
error merely because a code path differs from a published curve.

## Evidence order

1. Freeze the complete inventory of numerical figures, subfigures, formulas,
   and quantitative claims from the article and supplement.
2. Derive and implement the equations without author code, author numerical
   arrays, digitized curves, or source pixels.
3. Run the scientific channel in isolation and freeze numerical arrays/hashes.
4. Only then open source figures for RenderContract comparison.
5. Have a fresh-context reviewer inspect the paper, equation cards, code, and
   frozen data while attempting to falsify both the reproduction and paper.

## Current discrepancies

- The published measured/modelled fibre dispersion coefficient table is
  absent.  A Sellmeier-plus-capillary surrogate recovers the qualitative UV
  root ordering for the declared geometry but does not recover the printed
  1551 nm horizon.  This is `missing_parameters/model_mismatch`, not evidence
  that the paper is wrong.
- Historical Fig. 5 vector extraction suggested that the displayed Hawking
  line used a different 1100 nm exclusion policy from the Methods prose.  That
  observation remains a comparison-only `source_discrepancy`; it cannot be a
  paper-error candidate until raw points/fits and a fresh independent review
  exist.

No paper-error candidate is currently promoted.
