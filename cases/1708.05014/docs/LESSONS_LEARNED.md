# Lessons Learned

1. The symmetric-sector model makes a broad 24-region feature reproduction possible
   in seconds.  Paper scale still needs sharded Arnoldi/propagation, but an algebraic
   change of numerical object can matter more than hardware: the shifted-jump Gram
   steady state turns the `N_b=600` NESS from a Liouville-space LU into an
   `(N_b+1)`-state construction while retaining an independent Liouvillian residual.
2. Full-canvas pixel similarity is misleading for sparse scientific plots: `89.27`
   versus a foreground mean of `39.77`. Both must be stored, with foreground primary.
3. Sparse phase portraits need more formula-derived initial conditions for visual
   fidelity. RenderContract must not invent those trajectories after freeze.
4. Source text and source figures can disagree. Freezing centered variances, second
   moments, and squared means exposed the S2 conflict without pixel-derived inputs.
5. Formula cards need harness-native gate vocabulary. A scientifically correct card
   with ad hoc status names cannot drive the authoritative state reliably.
6. Attestation should bind immutable numerical data and its hash manifest; derived
   audit reports can then be refreshed without invalidating the numerical run.
7. The A100 is useful only when the numerical method maps cleanly to it and a CPU
   cross-check preserves auditability.
8. A resumable result must bind the implementation hash as well as config and result
   hashes.  Otherwise a code change can silently mix old and new shards under one run.
9. Smoke CSVs must carry `execution_profile=smoke`; using paper-scale labels on reduced
   backend tests creates evidence that can be accidentally promoted.

## New Failure Modes

- Source prose and source curves may name different observables.
- A high full-canvas score may be dominated by empty background.
- Render-only densification can silently invent scientific trajectories.
- Ad hoc formula-card states can make valid science unreadable to the state model.
- Config-only checkpoints can silently mix results from different code revisions.
- Smoke outputs can look structurally identical to paper-scale evidence unless the
  execution profile and output root are explicit.

## Reusable Checks Or Tools

- Require foreground scientific-region metrics alongside full-canvas diagnostics.
- Freeze alternative observable interpretations when source semantics conflict.
- Bind isolated-run attestations to numerical data and its hash manifest, then derive
  refreshable reports downstream.
- For long campaigns, hash config + implementation + result, shard on immutable
  physical parameter tuples, and make aggregation fail closed on any missing job.
- Search for exact algebraic steady states or reduced sufficient statistics before
  allocating high-memory brute-force solves; validate them against the original
  operator on small and requested scales.
