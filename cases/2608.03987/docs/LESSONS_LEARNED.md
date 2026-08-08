# Lessons learned

## Scientific lessons

- The tensor hypergraph is the useful core model: one lowering path covers
  random, Clifford+T, QAOA, and VQE circuits.
- Exact algebraic claims and optimizer-dependent empirical claims need separate
  acceptance gates. Figure 8 can pass even when Figure 9 retains differences.
- A normalized overhead ratio is not enough when its denominator changes with
  the tree; the underlying real arithmetic cost must be audited as well.
- Stochastic tree search is part of the scientific method. Matching search-step
  counts does not make two optimizers equivalent.

## Reproducibility lessons

- Record every input member opened by the primary calculation. Here that makes
  the raw-input-only boundary inspectable rather than rhetorical.
- Test circuit topology and tensor classes before attributing a discrepancy to
  optimization.
- Use an exact dynamic-programming solver on tiny networks as an oracle for the
  cost model and local tree moves.
- Store seeds, configuration hashes, topology hashes, tree child pairs, and
  tree hashes so a stochastic campaign is resumable and auditable.

## Case-specific traps

- qsim `sqrt(Y)` is real while `sqrt(X)` is structurally complex; gate names are
  not a safe proxy for nonzero imaginary entries.
- Expectation networks require an explicit rank-2 middle operator on every
  wire, including identity operators, to separate ket and bra topology.
- A post-hoc comparison against author results must remain downstream of the
  optimizer and must never become an implicit search target.
