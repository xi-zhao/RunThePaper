# Lessons Learned

## What worked

- Treating text-only numerical values as formal targets prevented the paper's
  most direct quantitative claim from disappearing behind a one-figure count.
- Root-of-unity parity signs are domain rules, not plotting details. Encoding
  them in one TBA object kept density, velocity, susceptibility, and diffusion
  conventions consistent.
- The isolated numerical runner made the no-pixel/no-author-code boundary
  provable: 387 audited accesses and zero denied attempts.
- Freezing data before rendering allowed source-aware typography and line
  styling without letting the source image alter the physics.

## What remains difficult

- A visually close scalar spin-mode projection is not the same as solving the
  full non-diagonal diffusion operator. Similar pixels cannot erase that model
  distinction.
- Full-operator and tDMRG final convergence runs remain compute-heavy. Their
  implementations, configs, checkpoints, and acceptance contracts are now
  ready; copying curve or marker coordinates would still be invalid.
- The ell=7 value retains a 1.78% residual even after grid convergence. The
  correct response is to expose the residual, not introduce a fitted factor.

## New Failure Modes

- A scalar hydrodynamic projection can achieve a high pixel score while still
  omitting spectral-mode coupling. Detect this by comparing the implemented
  operator rank/structure with the paper equation before scoring pixels.
- A convergence check can be scientifically valid yet still miss the Harness
  top-level `status` field. Future runner templates should validate check-file
  schemas inside the isolated run.
- A target can be labelled `target` with reduced-scale data and thereby hide
  the absence of a paper-scale implementation. Code readiness must be derived
  from parameter/failure state, not only the coverage decision label.

## Reusable Checks Or Tools

- Root-of-unity TBA invariant check: positive densities, `chi=1/4`, odd
  velocities, and normalized susceptibility weights.
- Dual pixel reporting: strict foreground RGB similarity plus colored-curve
  proximity F1, both explicitly post-freeze.
- Mixed-state purification TEBD with snapshot-only storage and resumable MPS
  checkpoints; full spectral-GHD evolution with a reusable NumPy/CuPy path.

## Reusable harness lessons

| Lesson | Future rule |
| --- | --- |
| Printed numerical claims matter | Enumerate quantitative text and commented duplicate tables during paper audit. |
| Render similarity needs two scores | Report strict RGB difference and tolerant scientific curve geometry separately. |
| Operator reductions need first-class status | Preserve `reduced_scale` even when physical parameters are paper-exact. |
| Compute may defer execution, not implementation | Require runnable code, config, entry point, outputs, and scientific acceptance before recording a compute blocker. |
| Immutable run IDs are useful | Bump the ID for any input/check change and keep one authoritative run in final artifacts. |
