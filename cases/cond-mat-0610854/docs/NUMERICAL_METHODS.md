# Numerical Methods

The reduced-scale campaign uses complete dense diagonalization in each
half-filled sector.  It evaluates 15 disorder points for `L=8,10,12,14` with
160, 64, 32 and 2 realizations respectively, plus 96 independent `512 x 512`
GOE matrices.  The scale is deliberately smaller than the paper but the model,
observable, boundary condition and disorder normalization are unchanged.

The paper-scale implementation covers `L=8,10,12,14,16`, the same 15-point
declared disorder grid, a reconstructed realization schedule, and the printed
`1000 x 3432` GOE campaign.  It supports deterministic 64-way sharding,
checkpoint/resume, exact coverage checks, NumPy CPU execution and CuPy
`eigvalsh` on A100.  L=10/L=12 sample counts and the complete original W grid
are not printed, so this profile is correctly named `paper_scale_reconstructed`,
not `paper_exact`.

No author program, author numerical array, extracted curve or source pixel is
used.  Manuscript formulas, printed parameters and printed limiting results are
the only scientific inputs from the publication.
