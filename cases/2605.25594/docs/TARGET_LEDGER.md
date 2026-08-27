# Target Ledger

All 73 eligible atomic items now have a final disposition. No item remains
pending, and no reduced/proxy artifact is promoted to paper-exact reproduction.

| Final boundary | Target ids | Atomic items | Code state | Final disposition |
| --- | --- | ---: | --- | --- |
| Measured paper-scale compute capacity | `T001-T008`, `T010-T024` | 71 | Paper-scale campaign, configs, target analyzers, checkpoints and acceptance criteria are ready; every target passes an attested reduced invariant. | `externally_blocked` |
| Unpublished Appendix Fig. 11 constants | `T009` | 2 | Analytic runner and limiting-family checks pass in isolation; exact curve constants are not uniquely specified. | `externally_blocked` |

The compute diagnosis is target-specific even though the physical bottleneck is
shared: every mapped item has its own target projection, reduced check, affected
scope and future evidence path in `causal_diagnoses.json`.

Reopening the 71 compute-blocked items requires a high-memory or distributed
eigensolver allocation and execution of `config/paper_scale.json`. Reopening the
two Fig. 11 items requires author-published Gamma cutoffs, normalization and
fitting protocol.
