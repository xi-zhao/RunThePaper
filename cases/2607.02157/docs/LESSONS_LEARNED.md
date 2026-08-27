# Lessons Learned

## Case Summary

- Paper: Thermodynamics of Quantum Reservoir Computing
- PaperID: 2607.02157
- Outcome: numerical_feature_reproduction, 70.0/100 (reduced_scale cap; raw
  77-86), all three numerical figures covered, 22/22 feature contracts.

## What Worked Well

- Formula lane first: independently re-deriving the central identity
  (beta*W_irr = chi_d) before coding turned it into a per-step machine
  invariant — every production run carries an 8.9e-16 consistency proof.
- Coverage contract discipline: declaring all three numeric figures as targets
  up front forced the S1/S2 pipelines to exist from day one instead of
  becoming "deferred supporting figures".
- Optimize only against a frozen correct baseline: the 4x speedup (map cache,
  batched entropies, analytic Gibbs relative entropies) was accepted only with
  exact regression evidence.

## New Failure Modes

- **Unpublished convention adjudicated by symmetry**: the paper omits the
  cluster-chain boundary condition. The periodic-chain scan came out exactly
  symmetric about alpha = 0.5 — a CZ-duality (H(alpha) -> H(1-alpha)) the
  authors never mention — contradicting their asymmetric curves. The wrong
  convention was detected only because the full scan was run; a single
  parameter point would have looked plausible. Fingerprints that resolved it:
  duality symmetry of the scan + OBC spectral widths/edge modes vs Fig. S1c.
- **Self-contradictory preprocessing prose**: the stated MG rescaling
  ("linearly rescaled to [-1,1]") cannot produce the paper's own reported
  statistics (mean ~ 0, sigma_s^2 = 0.11). Calibrating to the *published
  statistics* rather than the verbal recipe is the reproducible choice.
- **Estimator-convention traps in SI algebra**: the accumulation factor G is
  defined with an implicit normalization split across S43/S49; implementing
  S43 verbatim and dividing by sigma_s^2 again gave a 10x-off peak. The S52
  closed-form value (~2.3) was the cross-check that caught it.
- **Ordering contracts need a validity region**: multi-step (tau/h) capacity
  orderings hold where the paper's curves are readable but invert reproducibly
  in the deep-MBL tail where the published curves are visually degenerate.
  Blanket "monotone everywhere" contracts overfit the paper's plotted range.

## Reusable Checks Or Tools

- Duality/symmetry fingerprinting as a boundary-condition adjudicator
  (candidate harness lesson: when a lattice-model convention is unpublished,
  test whether a symmetry of one convention contradicts the paper's asymmetry
  before running the full scan).
- Per-step thermodynamic identity as a run invariant (identity_residual_max
  column in every scan row) — cheap, catches bookkeeping bugs instantly.
- Feature contracts as JSON (`check_feature_contracts.py`) with values read
  from the paper's panels: makes `visual_feature_contract` scoring auditable.
- Shuffle-control estimator-bias diagnostic for binned Holevo capacities
  (proposed, not yet implemented — needed before trusting tail values).

## Feed-Forward

- Abstract experience: appended to `PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`
  (unpublished-convention adjudication; calibrate to published statistics).
- Concrete tool requests: HARNESS_BACKLOG.md H067 (convention-adjudication
  check pattern), H068 (binned-estimator bias diagnostic). copied_to_backlog
- Machine-readable digest: blocked — `build_case_learning_digest.py` requires
  the full `physics_reproduction_project.json` manifest, which this first-pass
  case does not author (backlog H069: digest should degrade gracefully to
  LESSONS + scorecard inputs).
