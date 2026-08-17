# Paper Review Protocol V2

## Inventory-first scope

The paper contains four quantitative targets: Main Figure 1, Main Figure 2 top,
Main Figure 2 bottom, and the finite-size crossing-drift claim.  There is no
supplement and no numerical table.  This inventory was fixed before result
comparison.

## Falsification work performed

The reproduction attempts to falsify the paper through fermionic-sign and
Hermiticity checks, exact disorder-RMS checks, the analytic Poisson limit, an
independent GOE ensemble, finite-size crossover ordering, and explicit crossing
drift.  It also attempts to falsify itself through unit tests, deterministic
seeds, checkpoint coverage, isolated execution and immutable data hashes.

All current scientific checks pass.  Differences in curve noise, the missing
L=16 series and non-identical crossing coordinates are explained by the declared
reduced scale and omitted publication metadata.  They are reproduction-boundary
effects, not evidence that the paper is wrong.

## Current disposition

- paper-error candidates: `0`;
- confirmed paper errors: `0`;
- reproduction-code defects found: `0`;
- fresh-context reviewer submission: missing.

Only a new reviewer who first enumerates the paper independently and then reads
the formulas, code, generated data and falsification bundle may promote a stable
discrepancy.  This case does not fabricate that review result.
