# Lessons Learned

## Case Summary

- Paper: *Quantum Speed Limit for Non-Markovian Dynamics*
- PaperID: `1302.5069`
- Reproduced: all formulas and all numerical regions of both main figures
- Blockers: none for execution; final paper-level adjudication awaits fresh review

## What Worked

- The closed-form Lorentzian survival amplitude was checked against an independently integrated two-variable pseudomode ODE.
- A critical-safe `sinhc` form avoided cancellation at the weak/strong-coupling boundary.
- Scientific CSVs were frozen before any reference figure was opened; the render step verifies their hashes before and after plotting.
- Matching the original canvas and axes geometry raised all predeclared scientific regions above 96 without changing physics.

## Generalized Experience

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| Audit operator conventions independently of plotted formulas | A missing ladder-operator factor can coexist with numerically correct figures generated from a separately printed solution | Add convention-level matrix tests whenever a master equation defines operators in prose |
| Test reductions outside commuting examples | A familiar closed-system identity may silently require an unstated commutation condition | Generate a positive noncommuting 2x2 counterexample for trace-norm reductions |
| Separate data freeze from render tuning | It permits high pixel fidelity without contaminating scientific numerics | Bind RenderContract to immutable data hashes |

## New Failure Modes

| Failure mode | Detection |
| --- | --- |
| Printed operator normalization inconsistent with downstream exact solution | Compare literal matrix definitions and dissipator scaling |
| Intermediate time derivative uses terminal rather than instantaneous state | Differentiate the defining overlap directly |
| Trace norm of a non-Hermitian product replaced by its trace | Compare singular values against the claimed expectation value |

## Reusable Checks Or Tools

| Candidate | Reuse |
| --- | --- |
| critical-safe hyperbolic ratio | stable open-system amplitudes across exceptional/critical points |
| post-freeze data-hash render manifest | every figure reproduction with a separate visual optimization channel |
| 2x2 noncommuting positive-matrix counterexample | claimed norm/expectation identities |

## Failure Modes

The three source discrepancies must remain reviewer questions until protocol-v5 independently excludes implementation error, parameter ambiguity and alternative conventions.

## Harness Backlog

No new Harness patch is required by this case; all evidence fits the existing whole-paper claim, isolation and RenderContract models.
