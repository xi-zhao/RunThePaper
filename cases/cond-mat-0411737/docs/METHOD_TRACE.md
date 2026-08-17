# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### METHOD001 — Geometric zigzag ribbon construction

- Source: Eq. (6), definition of `nu_ij`, Fig. 1 caption.
- Role: create the complete T001 Bloch matrix without an author code path.
- Inputs: `t`, `t2`, number of zigzag chains, reduced momentum and spin.
- Outputs: Hermitian matrix, site coordinates and edge labels.
- Algorithm: enumerate an expanded set of neighbouring unit cells, identify
  first neighbours by unit bond length, identify second neighbours by their
  unique two-step path, attach exact Bloch phases and project back to one cell.
- Checks: coordination counts, Hermiticity, time reversal, `t2=0` particle-hole
  spectrum and width convergence.
- Code: `src/kane_mele/model.py`.
- Status: implemented and verified.

### METHOD002 — Band and edge-state extraction

- Source: prose surrounding Fig. 1.
- Role: separate bulk subbands from edge-localized gap-traversing states.
- Inputs: eigenpairs of METHOD001.
- Outputs: energy, spin, edge weight and inverse participation ratio for every
  state and momentum.
- Algorithm: dense Hermitian diagonalization at each momentum; compute the
  probability on the outer two zigzag chains.
- Checks: Kramers crossing at `k_x=pi/a`, gap agreement, localization and
  `N=16,20,24` stability.
- Code: `src/kane_mele/model.py`, `scripts/run_reproduction.py`.
- Status: implemented and verified.

### METHOD003 — Independent analytic checks

- Source: continuum/RG/transport paragraphs.
- Role: falsify implementation and paper-claim errors independently of the
  ribbon diagonalizer.
- Inputs: printed formulas and constants only.
- Outputs: analytic gap, conductance coefficients, bare/Rashba/RG gap estimates.
- Checks: symbolic limits, unit conversions, independent scalar root solve.
- Code: `src/kane_mele/model.py` and focused tests.
- Status: implemented and verified.
