# Method Trace

## MTH001 — Complete-shell plane-wave diagonalization

- Source: main Eq. (4), supplement four-band sections.
- Inputs: printed material parameters, twist angle, reciprocal-shell cutoff and k points.
- Outputs: eigenvalues/eigenvectors.
- Algorithm: construct complete hexagonal shells; add kinetic blocks and exact Fourier links; call Hermitian eigensolvers.
- Code: `src/twisted_tmd/model.py`.
- Checks: Hermiticity, symmetry-related corner degeneracy, cutoff convergence.
- Status: verified.

## MTH002 — Observable extraction

- Source: main Fig. 3 discussion and Fig. 4 caption.
- Inputs: independently generated spectra/eigenvectors.
- Outputs: DOS/filling, Kubo curvature, Chern integrals, adjacent-band gaps and phase boundaries.
- Code: `src/twisted_tmd/model.py`, `src/twisted_tmd/reproduction.py`.
- Checks: Chern signs, full 0-8 filling range, printed critical-angle neighborhoods.
- Status: verified.

## MTH003 — Isolated execution and freeze

- Source: PRAgent harness policy.
- Inputs: only declared source code/config.
- Outputs: attestation, file-access log, output hashes.
- Algorithm: execute in a raw/reference-free staged directory and hash every numerical target before rendering.
- Status: verified by `1807.03311-independent-v2` (11.341 s, zero forbidden accesses).

## MTH004 — Post-freeze RenderContract

- Inputs: frozen arrays, layout/style contract, source panels as references.
- Outputs: generated figures, comparisons and pixel metrics.
- Allowed changes: presentation only.
- Forbidden changes: physics, numerical arrays or source sampling.
- Status: implemented.
