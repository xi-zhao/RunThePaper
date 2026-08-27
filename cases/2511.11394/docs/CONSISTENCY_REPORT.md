# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| numerical feature match | 3 targets | Exact trajectory, local geometry, and interaction trends agree with the paper. |
| partial match | 1 target | The small-\(q\) mechanism is correct, but the source's Fig. 1 numerical convention is unrecoverable. |
| externally constrained | 0 | Every numeric main/supplementary figure has an executable target. |

## Per-Target Assessment

| Target | Assessment | Matching evidence | Remaining difference |
| --- | --- | --- | --- |
| Small-\(q\) LLG (T001) | `partial_match` | Monotone \(E_D\), conserved \(C=1\), reduced trace deviation | At \(t=15\), \(E_D/\pi=1.4167\) rather than near 1; source plot has a factor-four energy normalization. |
| Exact versus small-\(q\) (T002) | `feature_match` | \(E_D(4.32)=3.1452\), \(C=0.9965\), later exact transition, small-\(q\) remains topological | Author mesh and raw curve data are unavailable. |
| Local geometry (T003) | `feature_match` | Correct periodic location and shape of initial arcs, exact bubble, and small-\(q\) arcs; exact mean deviation \(3.18\times10^{-4}\) | Pointwise source arrays are unavailable. |
| \(U,V\) sweeps (T004) | `feature_match` | Transition time increases monotonically from \(4.4\) to \(6.5\) as \(V\) grows; increasing \(U\) accelerates transition | Sweep uses \(N=61\), while the source mesh is not reported. |

## Rejected Explanations

- The early failure was not caused by RK4 instability: norm error is below
  \(2.3\times10^{-16}\).
- It was not fixed by arbitrary time rescaling.
- A node-centered grid is not a valid representation of the finite-mesh
  transition because it symmetry-pins the bubble center.
- Centered differences underresolve the shrinking bubble and violate the
  linked \(E_D\simeq\pi\), \(C\simeq1\), peak-height constraints.

## Source-Level Limitation

The paper provides figures but no author numerical arrays, mesh size, grid
origin, derivative stencil, integrator, or time step. Accordingly, the
successful targets remain `exploratory` numerical-feature reproductions, not
paper-exact benchmark replications.
