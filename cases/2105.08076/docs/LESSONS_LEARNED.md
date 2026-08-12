# Lessons Learned

## Case Summary

- Paper ID: `2105.08076`
- Numerical panels: 9/9 implemented
- Reduced feature checks: 7/9 passed
- Paper-scale status: A100 code ready, production unrun
- Paper audit: three stable but still inconclusive discrepancies

## What Worked

- Representing trajectories by occupied orbitals kept the Gaussian simulation
  compact and made particle-number and orthogonality invariants explicit.
- One ensemble cache supported all nine targets without duplicating stochastic
  work.
- Freezing CSV hashes before extracting source figures preserved a clean split
  between scientific generation and render optimization.
- A paper-scale plan with condition IDs, unique seeds, shards, checkpoints, and
  acceptance contracts turned “insufficient local compute” into executable work
  instead of an empty deferral.

## What Was Difficult

- Published figure captions omit several stochastic-integration and fitting
  details, so reduced parameters are reconstructed rather than paper-exact.
- Small systems can reproduce phase ordering while giving seriously biased
  asymptotic exponents.  This happened for T003 and propagated to T007.
- A visually similar curve is not enough: the full-canvas mean is 88.16, but
  the scientific-region mean is only 46.99 and two physics assertions fail.

## Generalized Lessons

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| Separate finite-size trend checks from asymptotic exponent checks | Ordering can pass while the scientific exponent fails | Store both checks and let the asymptotic check block the target |
| Make expensive deferrals executable | “Needs GPU” is otherwise unverifiable | Require paper-scale code, immutable config, sharding, resume, and acceptance |
| Pixel evidence follows data freeze | Render tuning can otherwise contaminate science | Verify numerical hashes before and after every RenderContract pass |
| Audit prose, equations, and captions separately | Local paper typos can coexist with correct downstream numerics | Record source pinpoints and impact boundaries per discrepancy |

## New Failure Modes

| Failure mode | Evidence | Detection |
| --- | --- | --- |
| Finite-size slope masquerades as asymptotic slope | T003 `0.76566` vs `0.25` | require convergence family before paper-exact promotion |
| Analytic reference plotted beside mismatching simulation | T007 identity passes while simulated slopes fail | require an assertion on generated simulation data |
| Layout similarity hides scientific mismatch | 88.16 canvas vs 46.99 foreground | foreground scientific crop is the primary pixel metric |
| First-use font discovery violates isolation | initial run attempted subprocesses | preseed deterministic Matplotlib font cache |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| analytic-versus-simulation assertion splitter | prevents a correct reference curve from masking failed generated data | Harness target-contract validation after a second confirming case |
| isolated Matplotlib font-cache seeder | avoids first-use subprocess discovery inside numerical sandboxes | isolated-run setup helper |

## Harness Backlog Candidate

Add a reusable rule that automatically creates a separate generated-data
assertion whenever a target contains both analytic reference curves and
simulation curves.  The analytic identity must never be allowed to satisfy the
simulation agreement gate by itself.  This remains a case-local lesson until a
second case confirms the same pattern.
