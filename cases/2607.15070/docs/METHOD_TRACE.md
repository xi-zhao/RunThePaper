# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### MTH001 - positive Bessel-series evaluator with independent quadrature

- Source: paper Eqs. (36)-(37), transformed only by the identities documented
  in EQC004.
- Role: evaluate all paper curves without digitizing or copying source paths.
- Inputs: explicit target id; dimensionless `alpha_0>0`, `m_0>=0`;
  target-owned paper parameter grid; relative tail tolerance.
- Outputs: target-owned CSV, scientific-check JSON, PNG and PDF figures.
- Algorithm steps:
  1. Expand each thermal denominator into positive exponentials.
  2. Integrate each proper-time term analytically into `K_1`.
  3. Sum only positive terms until the Bessel argument exceeds the declared
     tail cutoff; repeat with a tighter cutoff at selected points.
  4. Independently integrate the original proper-time expressions in
     `u=log(tau)` at selected paper parameters.
  5. Check analytic limits, monotonicity, curve ordering, positivity, and the
     ratio identity.
  6. Write structured data before rendering.
- Parameters: `m_0={0,0.5,1,1.5}`; Figure 2 axes `alpha_0=0..30` and
  `0..12`; Figure 3 axis `alpha_0=0..25`; paper normalizations.
- Code pointer: `code/scripts/casimir_model.py`;
  `code/scripts/run_reproduction.py`.
- Checks: positive-term convergence, tighter-cutoff agreement, direct
  adaptive-quadrature agreement, exact `alpha_0=0` Landau limit, small- and
  large-coupling behavior.
- Status: `verified`.
- Open questions: the source bundle has no author data or plotting script;
  curve-level comparison therefore uses analytic references and a separate
  source-image pixel lane, never source pixels as generated data.

Only `verified` opens final numerical execution. An independently checked
`reconstructed` method may open exploratory execution; `source_only` and
`blocked` do not.
