# Consistency Report

## Formula Gate

Status: `passed`

Evidence:

- `outputs/checks/formula_verification.json`
- Fibonacci basis dimensions match the paper for PBC and OBC.
- Particle-hole anticommutation check gives max error `0.0`.
- `H = H+ + H-` gives Frobenius error `0.0`.
- FSA projected-minus-tridiagonal norm for `L=12` is `6.59e-15`.

## Numerical Feature Consistency

Status: `physically_consistent`

Evidence:

- `outputs/checks/pxp_feature_checks.json`
- `Z2` local-correlation period is `2.375`, close to the paper's reported `~2.35`.
- `Z2` has stronger revival than the vacuum state.
- Scar overlaps are strongly enhanced over the median overlap.
- FSA closes to `L+1` states.

## Remaining Differences

The case is not a complete reproduction because:

- exact diagonalization is local `L=16`, not paper `L=32`;
- symmetry sectors are not fully resolved;
- dynamics uses finite-size exact evolution, not iTEBD;
- level statistics is therefore only a weak local proxy.

Similarity status: `numerical_feature_reproduction`.
