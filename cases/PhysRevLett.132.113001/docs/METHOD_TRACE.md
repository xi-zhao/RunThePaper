# Method Trace

## METHOD001 — Continuous eigenbranch tracking

- Inputs: analytic Dirac diagonal, analytic same-n \(z\) matrix, ascending field grid.
- Algorithm: diagonalize from high to low field and maximize eigenvector overlap
  with the preceding step; start from the analytic \(k=0\) eigenvector.
- Output: five branch-resolved shifts for each \(n\).
- Checks: exact \(z\)-spectrum and finite continuous branches.
- Code: `src/hydrogen_metrology/stark.py`.

## METHOD002 — Frozen-data reference lane

The isolated runner writes and hashes all scientific CSV/PNG artifacts without
access to `raw/` or `references/`.  Only after freezing does
`scripts/validate_against_paper.py` load printed comparison values.  It records
hashes before and after and fails if any scientific artifact changes.

## METHOD003 — Missing-data boundary

`scripts/run_paper_scale.py --validate-only` inventories the four required
author tables.  Execution mode refuses to proceed until all tables pass their
exact schemas.  Raster figures are not accepted as an input format.
