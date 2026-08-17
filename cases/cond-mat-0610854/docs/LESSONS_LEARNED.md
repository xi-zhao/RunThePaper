# Lessons Learned

## New Failure Modes

1. Dense many-body level statistics can reproduce the physical crossover at a
   bounded scale, but reduced disorder counts visibly increase curve noise and
   must never be hidden by rendering.
2. High scientific-region pixel similarity is useful for presentation QA but
   is background-sensitive; foreground-only diagnostics and the 70-point
   evidence cap keep it from overstating scientific exactness.
3. Paper-scale compute readiness is a separate deliverable from paper-scale
   execution.  Sharding, checkpoints, A100 support and acceptance rules are all
   implemented even when the full campaign is deferred.
4. Missing W-grid and sample-count metadata are a publication provenance limit,
   not automatically a paper error and not evidence of a code defect.
5. Direct cause, root cause and code-fault checks should be recorded per target;
   otherwise a generic `partial` state hides whether more compute, author input
   or a software repair is actually needed.

## Reusable Checks Or Tools

- exact Hermiticity and conditioned-disorder-RMS unit checks;
- deterministic `(L,W,sample_id)` shard manifests with overlap detection;
- Poisson/GOE limiting-ensemble science gates;
- post-freeze RenderContract hash invariants;
- schema-v4 per-target causal diagnosis separating direct cause, root cause and
  reproduction-code fault assessment.
