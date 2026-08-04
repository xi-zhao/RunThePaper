# Numerical Methods

The smoke target uses Qiskit Aer already available in the local environment.
The coherent branch inserts the one-qubit unitary directly.  The twirled branch
attaches the normalized I/X/Z Pauli channel to explicit identity markers at the
same data-qubit locations.  Both circuits use the same ideal encoding,
stabilizer-extraction, and final-measurement operations.

This is a shot-based `proxy_model`, not Plaquette's full-state or near-Clifford
implementation.  The random seed is fixed and all aggregate counts are written
before plotting.  Clopper-Pearson intervals quantify binomial shot noise.

## Method Cards

### NUM001

- Target:
- Equations/method cards:
- Parameters:
- Grid or benchmark:
- Boundary conditions:
- Solver:
- Tolerance:
- Random seed:
- Output schema:
- Validation checks:
- Numerical risks:

## Efficiency And Reuse Plan

- Baseline implementation:
- Main bottleneck:
- Efficient implementation choice:
- Complexity or scaling:
- Performance bottleneck removed:
- Optional harness promotion candidate:
- Case-specific parts that should not enter the harness:
- Performance evidence:
