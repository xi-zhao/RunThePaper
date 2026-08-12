# Lessons learned

## New Failure Modes

1. A subscription-gated supplement is a scope blocker, not permission to infer
   unseen panels or geometry from the main figures.
2. Experimental panels can still have code-ready analysis contracts. Missing
   data postpones execution, while deterministic synthetic inputs validate only
   the method.
3. A printed aggregate and its underlying samples are different evidence. The
   140/45 aT combination is reproducible; the 36 estimates are not.
4. Result-normalized coupling curves must say exactly what is independent: the
   Eq. (1) mass dependence is derived, while the finite-volume normalization is
   blocked.
5. Exact-step/RK4 and FFT/direct-filter pairs provide cheap, genuinely distinct
   numerical cross-checks.
6. Scientific labels should expose `synthetic`, `point-source`, and
   `statistical component only` directly on figures so visual polish cannot
   hide evidence limitations.
7. An available A100 is not automatically the right backend; data access and
   scientific parity are the controlling constraints here.

## Reusable Checks Or Tools

- Bind a version-matched Matplotlib font cache into every isolated plotting
  bundle so font discovery cannot silently spawn a forbidden subprocess.
- Compare scientific-data hashes before and after the source-aware render lane.
- Require experimental reanalysis runners to fail closed on missing hashed
  inputs while still exposing executable schemas, checkpoints, and acceptance.
- Keep synthetic method validation, printed-aggregate reproduction, and
  paper-exact experimental reproduction as distinct machine states.
