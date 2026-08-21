# Lessons learned

- A memory-light exact representation can be both faster and more auditable
  than the dense implementation suggested by a many-body Hilbert space.
- A visually close published fit is itself a scientific claim. When raw points
  and selection rules are absent, keep the independently computed mismatch and
  test alternative hypotheses in fresh review.
- “First components” must be interpreted from the paper's basis convention;
  here they are the Jz states near the saddle at m=-j, not a reordered central
  window.
- Figure pixels may guide post-freeze layout but may never settle the disputed
  finite-N coefficient.

## New Failure Modes

| Failure mode | Detection |
| --- | --- |
| Published finite-size fit lacks a level-selection contract | compare two parity blocks, freeze an explicit selector, and require fresh falsification |

## Reusable Checks Or Tools

| Candidate | Scope |
| --- | --- |
| dense-versus-tridiagonal eigenvalue cross-check | case-local now; reusable for banded many-body sectors |
