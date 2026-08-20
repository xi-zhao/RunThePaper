# Method Trace

## MTH001 — Clean-room Harper eigensolver

- Inputs: printed `p/q`, Bloch phases and Eq. (1).
- Steps: assemble the Hermitian cyclic matrix; diagonalize at two Chambers
  extrema; sort and pair 2q roots into q bands.
- Outputs: interval arrays for Figs. 1–5 and eigenvectors for Fig. 6.
- Independent checks: Hermiticity, transfer-matrix band edges, flux and energy
  symmetries, operator bound, direct eigenvector residual.
- Code: `src/hofstadter_reproduction/model.py`.

## MTH002 — Recursive-cell transformation

- Inputs: generated band intervals and the printed L/C maps.
- Steps: select the computed bounding pure-case bands, interpolate the cell
  boundary, transform the local alpha coordinate, and normalize cell energy.
- Outputs: Figs. 3–4 data.
- Checks: transformed coordinates remain in `[0,1]`, with 1162 L2 and 513 C2
  band intervals at the declared cutoff.
- Code: `src/hofstadter_reproduction/campaign.py`.

## MTH003 — Field-window union

- Inputs: generated band intervals and printed `delta-alpha=0.01`.
- Steps: rasterize interval occupancy and apply a one-dimensional maximum
  filter only along magnetic field.
- Output: Fig. 5 binary spectrum.
- Check: connected-band count stays below the paper's finite bound.

## MTH004 — Magnetic-period eigenfunction

- Inputs: printed rational approximants.
- Steps: compute the largest periodic eigenpair, phase-fix and normalize it,
  then apply the exact modular-inverse permutation.
- Outputs: every Fig. 6 series.
- Checks: printed energies, direct residual, normalization and permutation.

## MTH005 — Post-freeze renderer

This method runs only after numerical output hashes are frozen. It may read the
paper figures to adjust presentation fields listed in `render_contract.json`.
It may not change formulas, parameters, arrays, targets or checks.
