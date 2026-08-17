# Lessons learned

## What worked

- Deriving the complex contour and the origin patch before coding prevented a real-axis-only proxy from masquerading as the paper problem.
- A second numerical formulation was essential: agreement between Riccati shooting and finite differences turned the Table II issue into an auditable scientific question rather than an unexplained mismatch.
- Hash-freezing data before looking at EPS figures kept numerical and presentation optimization cleanly separated.
- Analytic anchors at N=2 and massive N=1 gave cheap, strong checks for otherwise visually dense spectra.

## New Failure Modes

1. The isolated-run contract initially used a summary object for `expected_parameters`. The selector is exact and fail-closed, so the contract—not the physics—was invalid. Future cases should compare the selected JSON object byte-for-byte before launching.
2. Connecting the same sorted eigenvalue rank across a missing complex interval invented long diagonal lines. A per-N energy rank is not a global eigenstate label. The renderer now joins only locally continuous adjacent samples and tests this rule.
3. Paper tables often print truncated rather than conventionally rounded values. Tolerances must be tied to the displayed precision and must never be widened to hide a growing systematic discrepancy.
4. A high aggregate score cannot close a paper-review question. Table II remains explicitly visible even though the overall score exceeds 90.

## Reusable rule

For spectral plots with branch loss or exceptional points, declare branch semantics before rendering and fail closed on any cross-gap line. Scientific point arrays remain primary; line segments are a presentation contract, not new data.

## Reusable Checks Or Tools

- Add a generic spectrum-render check that rejects a line segment whenever the adjacent parameter gap or eigenvalue jump exceeds the target's declared continuity contract.
- Add a run-contract preflight that evaluates `parameter_selector` and compares the selected object with `expected_parameters` before opening the sandbox.
- Keep the existing protocol-v2 requirement that only a fresh reviewer may promote a stable discrepancy to a paper-error candidate.
