# Consistency report

## Source-to-implementation consistency

- Five equal square-drive steps, printed hopping values and the ideal-transfer
  limit are represented explicitly in the configuration and model.
- The sublattice offset is not silently normalized: both the printed
  onsite-difference reading and the displayed-equation reading are frozen.
- The weak-drive Bloch vector, harmonic coupling and `M=1` repeated-zone
  truncation are traceable to equation cards EQ005-EQ006.
- Every numerical paper item maps to exactly one T001-T009 contract; no
  schematic item enters numerical coverage.

## Independent consistency checks

- unitarity and Hermiticity residuals pass;
- the ideal bulk evolution equals identity to `3.48e-16`;
- full-evolution winding and gauge-aware Fukui Chern calculations satisfy the
  bulk-edge relation for the three representative phases;
- coarse and fine weak-drive time products give the same integer Chern result;
- the hand-derived weak-drive strip Hamiltonian agrees to roundoff with a
  separately implemented inverse-Bloch-Fourier quadrature construction;
- the isolated runner recorded zero forbidden source/reference accesses.

## Open inconsistencies

The definition of `delta_AB` and its coefficient in the displayed Hamiltonian
differ exactly by a factor of two. Exact Pauli eigenvalue algebra, two frozen
branches and the independent topology calculations exclude a numerical
factor-two artifact. This is therefore a probable paper-claim discrepancy,
but protocol-v2 still forbids emitting a paper-error candidate before a fresh
reviewer attempts to falsify it.

T003 and T006 crossed the 80-point render threshold through line/camera/axes
changes after data hashes were frozen. T007 and T008 remain below 80. Their
governing matrices agree under two independent partial-Fourier constructions,
all invariants pass and the full paper-scale run completed. The direct cause is
missing exact finite-strip/boundary/display metadata; the root cause is
publication underspecification, not a remaining reproduction-code repair loop.
