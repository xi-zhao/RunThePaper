# Consistency Report

## Exact Matches

- All paper `M` grids, `t`, `epsilon`, model parameters, and reported `lambda`
  inputs are preserved.
- All four series in every selected panel are independently generated.
- Every analytic `N` is sufficient and every `N_min` is the least passing
  integer.
- First-order randomised and second-order deterministic `N` values are exactly
  equal; the second-order gate counts are exactly twice the first-order values.
- The paper's XX `M=15` order-of-magnitude examples and TFIM `M=19`
  `1.89e12` gate-gap example agree.
- Pixel registration, line density, ink overlap, and proximity contracts pass
  for all eight panels.  Fig. 3 is raster-identical to the source reference;
  Fig. 2 differs only below the binary-ink threshold and receives pixel 100.

## Qualified Claim

Consistency label: `partial_match` for the prose claim that second-order
randomised always has the best gate complexity.

The numerical figures themselves show:

- second-order randomised has the smallest `N` at every plotted `M`;
- first-order randomised has the smallest `g` for XX `M=7,9,11` and TFIM
  `M=5,8,12`;
- second-order randomised becomes gate-optimal at XX `M=13` and TFIM `M=15`.

This is a paper-interpretation qualification, not a reproduction mismatch.

## Parameter-Method Boundary

The paper reports `lambda=7.071` (XX) and `lambda=8.00` (TFIM).  Under the
stated local-map normalization, the independent Choi-bound audit obtains
approximately `4.24264` and `2.0`, respectively.  The reported values are
larger, so they remain conservative inputs to the error bounds.  This case
does not silently replace the published figure parameters with the tighter
audit values.

## Provenance Boundary

- Generated: formulas, search results, CSV/JSON, plots.
- Reference-only: source Fig. 2/3 PNGs, crops, pixel differences.
- Forbidden and unused: traced/digitised source coordinates, sampled source
  pixels as numerical inputs, precomputed author result JSON.
