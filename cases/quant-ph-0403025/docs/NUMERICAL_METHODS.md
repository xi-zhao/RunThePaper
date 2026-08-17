# Numerical Methods

## NUM001: printed closed-form curves

- Targets: T001-T003.
- Inputs: `epsilon` on the printed `[0, 1/2]` interval.
- Method: evaluate Eqs. (22), (23), (35), and (36) in double/extended
  precision. The H numerator uses extended precision because its low-error
  terms cancel in the printed expression.
- Grid: 2001 uniform points; the continuous functions, not the grid, are the
  paper-exact scientific object.
- Outputs: two CSV files containing input error, output error, success
  probability, and the identity comparator.

## NUM002: independent five-qubit projector

Construct all four printed stabilizers as 32 by 32 Pauli tensor products,
form the rank-two projector, and project all 32 T-basis error strings. Aggregate
accepted and decoded-error norms by Hamming weight. This independently derives
both Fig. 2 curves without assuming their closed polynomials.

## NUM003: independent Reed-Muller enumeration

Construct the punctured truth tables of the four linear and six quadratic
Boolean monomials. Enumerate all 16 words in L1 and 1024 words in L2, then sum
their probability weights and the complemented coset. This independently
derives Fig. 3 and the H success probability.

## Complexity

The largest dense matrix is 32 by 32 and the largest discrete set has 2048
words of length 15. Runtime and memory are effectively constant. GPU execution
would add overhead and no scientific fidelity.
