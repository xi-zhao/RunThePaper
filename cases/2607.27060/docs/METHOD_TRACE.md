# Method Trace

## MTH-BINARY-LOWER-BOUND

- Source: paper Sec. 4 and Appendix A.
- Role: compute the least integer `N >= 1` satisfying the selected strictly
  decreasing precision bound.
- Inputs: positive `t`, `lambda`, `M`, `epsilon`, and one verified precision
  function.
- Output: exact integer `N_min`.
- Algorithm:
  1. Set `lower=1`, `upper=1`.
  2. Double `upper` while `epsilon_hat(upper) > epsilon`.
  3. While `lower < upper`, use `mid=(lower+upper)//2`.
  4. If `mid` fails, set `lower=mid+1`; otherwise retain it by setting
     `upper=mid`.
  5. Return the common endpoint.
- Invariant: all integers below `lower` fail; `upper` passes.  Strict
  monotonicity is proven in `DERIVATION_TRACE.md`.
- Independent checks:
  - the returned point passes;
  - its predecessor fails unless the return is one;
  - a small exhaustive integer scan is used in case tests as an oracle;
  - first-order randomised and second-order deterministic searches must agree
    because their predicates are identical.
- Difference from a literal Appendix-A transcription: the passing midpoint is
  retained (`upper=mid`), preventing an off-by-one return. This implements the
  paper's stated minimisation problem and is certified by the two-sided
  threshold checks.
- Code pointer: `src/trotter_bounds.py::minimum_steps`.
- Status: `verified`.
- Open questions: none.

## MTH-PARAMETER-MAP

- Source: paper Secs. 5.1–5.4 and Fig. 2/3 captions and axes.
- Role: bind each frozen panel to the paper's model, method, parameter tuple,
  and complete `M` grid.
- Inputs:
  - XX: `t=2`, `lambda=7.071`, `epsilon=1e-3`,
    `M=[7,9,11,13,15,17,19]`;
  - TFIM: `t=5`, `lambda=8.0`, `epsilon=1e-5`,
    `M=[5,8,12,15,19]`.
- Outputs: one structured row per paper `M` value and all four visible series.
- Checks:
  - XX term count `M=2P+3` maps `P=2..8` to the seven plotted values;
  - TFIM `M=|E_n|+2n` maps the stated interaction graphs for `n=2..6` to
    `[5,8,12,15,19]`;
  - generated parameters must exactly equal the manifest's paper parameters;
  - runner target/model/method must match the guarded target ID.
- Code pointer: `src/trotter_bounds.py::TARGET_SPECS` and
  `scripts/run_target.py`.
- Status: `verified`.
- Open questions: the selected figures use the paper-reported local-norm
  parameters; this case does not reinterpret them from source pixels.

## MTH-INDEPENDENT-PROVENANCE

- Source: frozen campaign contract and paper-reproduction invariant.
- Role: prevent author outputs or source pixels from entering generated data.
- Inputs: only paper formulas and explicit scalar/list parameters in the case
  manifest.
- Outputs: case-owned JSON/CSV data, checks, and plots.
- Checks:
  - author code is absent from the declared inputs and is not accessed;
  - runner refuses an unguarded or mismatched target;
  - source PNGs are read only by comparison/pixel tooling after scientific
    outputs exist;
  - every dataset records its final execution run.
- Code pointer: `scripts/run_target.py` and case tests.
- Status: `verified`.
- Open questions: none.

## MTH-LOCAL-LAMBDA-AUDIT

- Source: paper Sec. 5.3 and the frozen local Choi-bound implementation.
- Role: independently check whether the published `lambda` inputs are safe
  upper values for the local maps.
- Method: construct one- and two-qubit column-vectorised GKSL superoperators,
  form their Choi matrices, evaluate the two partial-trace operator norms, and
  test the equality condition.
- Result: the independent bounds are about `4.24264` (XX) and `2.0` (TFIM),
  below the paper inputs `7.071` and `8.0`.  The published values are therefore
  conservative for the selected resource-bound figures, but are not claimed
  here as tight local norms.
- Evidence: `outputs/checks/xx_spin_chain_lambda_method.json` and
  `outputs/checks/tfim_lattice_lambda_method.json`.
- Code pointer: `src/local_norms.py` and `scripts/check_local_lambda.py`.
- Status: `verified` as a safety audit; not used to replace paper parameters.
