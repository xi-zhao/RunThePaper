# Target Ledger

| Target | Observable | Paper parameters | Planned local evidence | Paper-scale boundary |
| --- | --- | --- | --- | --- |
| T001 | `P(r)` | `L=16`, `W=3,7,11`; GOE 1000×3432 | exact ED at smaller `L`, analytic Poisson, independent GOE | full `L=16` and GOE campaign is sharded/A100-ready |
| T002 | `<r>` | `L=8,10,12,14,16` | full spectra through locally affordable sizes | full printed sample counts deferred to campaign |
| T003 | crossing enlargement | same data as T002 | exact scientific subset of T002 | same campaign as T002 |
| T004 | crossing drift | adjacent size curves | interpolate crossings with bootstrap errors | full-size conclusion needs paper-scale data |

`code_ready_compute_deferred` will mean the complete implementation, immutable config, shard plan, checkpoint/resume and acceptance contract exist; it will not mean the paper-scale calculation ran.
