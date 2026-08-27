# Consistency Report

## Author-side gates passed

- Formula verification: `10/10` cards passed or source-traced; `F010` is explicitly source-only.
- Frozen run parameters equal the isolated run's actual parameters.
- Isolated execution: attested for `T001…T007`, with no forbidden accesses or unused declared inputs.
- Scientific closure: all target-local checks pass on the repaired outputs.
- Paper-scale counts: Fig. 3, Fig. 4, Fig. S4 chaotic ensembles, and Fig. S5 each use `2000` realizations.
- Fig. S4 modes: exact printed even vector `4,6,8,10,12,14,16,18,20,22`; `M=22` is present and checked.
- Fig. S5 scope: all `28` collision-free configurations, including initial `(3,4)`; Fig. S6 alone excludes the initial configuration for FFT comparisons.
- OTOC normalization: the same per-realization/time conditional normalization is used by the main and appendix OTOC paths.

## Convergence evidence

For Fig. 3, the extrema were recomputed on `41`- and `81`-point grids over `0.8…2.8` and then checked after extending the time domain to `1000`. The maximum grid-refinement shift is `0.025`; the maximum shift after domain extension is `0`. For `t>=100`, the mean PT distance is `1.863` times the dip value and the mean SFF proxy is `14.577` times the dip value, preventing a truncated-domain extremum from being mistaken for the paper feature.

## Boundary and reviewer ownership

Original pixels, author numerical arrays, and author code were not used as numerical inputs. Experimental red points and hardware characterization remain outside the eligible theory denominator.

The old fresh review reported `16` defects. These author-side checks supply replacement evidence but do not adjudicate those items. Their independent status remains pending until a new reviewer consumes the newly frozen bundles. Eq. S8's `Y` definition/prose tension is recorded as evidence only, not author-decided as a paper error.

Remaining lifecycle gates are fresh-context independent review and score-independent scientific-region pixel evidence. They must not be conflated with an unexecuted paper-scale theory run.
