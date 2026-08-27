# Target Ledger

| Target | Paper item | Attempt | Final disposition | Primary evidence |
| --- | --- | --- | --- | --- |
| T001 | Fig. 10(a), logical infidelity | literal Fig. 9 clean-room Monte Carlo | `attempted_not_reproduced` | `outputs/data/attested_steane_subset.csv`, `outputs/checks/frozen_reference_comparison.json` |
| T002 | Fig. 10(b), acceptance | literal Fig. 9 clean-room Monte Carlo | `attempted_not_reproduced` | `outputs/data/attested_steane_subset.csv`, `outputs/checks/frozen_reference_comparison.json` |
| T003 | Fig. 11, seconds per shot | non-comparable local mechanism proxy | `externally_blocked` | `outputs/checks/publication_input_audit.json` |
| T004 | sampling uncertainty law | repeated independent Bernoulli estimates | `reproduced` | `outputs/data/attested_sampling_scaling.csv`, `outputs/checks/attested_science_checks.json` |

T001/T002 were not tuned against digitized curves. Their configuration and
outputs were frozen before reference comparison. T003 is the only external
blocker; its missing object is the authors' environment/timing identity, not a
case contract or review artifact.
