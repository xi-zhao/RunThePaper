# Figure Classification

Every source figure and table is listed. `target` means independent formulas or
numerics generate structured data. `deferred_blocked` is used only with a named
blocker accepted by the harness.

| Paper item | Class | Decision | Reason |
| --- | --- | --- | --- |
| Fig. 1 | schematic_context | excluded | Experimental layout and product architecture cartoon |
| Fig. 2 | numeric_reproduction | target T001 | Central single-ion phase-space, population, concurrence |
| Fig. 3 | numeric_reproduction | target T002 | Chain-length infidelity and duration; disclosed scaling is reconstructed |
| Fig. 4 | numeric_reproduction | target T003 | Interconnect timing and memory amortization; panel-b source inconsistency audited |
| Table S1 | numeric_reproduction | target T004 | Gate operating point and derived distance/coupling |
| Table S2 | numeric_reproduction | target T005 | Lifetime-to-decay formula |
| Table S3 | numeric_reproduction | deferred_blocked | Component estimates need missing source simulations/calibrations |
| Fig. S1 | numeric_reproduction | target T007 | Ion-chain modes and toggle closure; population panels remain partial |
| Table S4 | numeric_reproduction | target T007 | Covered by the same multi-mode closure target |
| Table S5 | numeric_reproduction | deferred_blocked | MQDT Stark-map data and manual state tracking absent |
| Fig. S2 | numeric_reproduction | deferred_blocked | Same missing MQDT Stark-map dataset |
| Fig. S3 | numeric_reproduction | target T008 | Analytic thermal-dephasing feature reproduction |
| Table S6 | numeric_reproduction | target T008 | Same decay + thermal model |
| Fig. S4 | algorithm_trace | excluded | Explanatory circuit diagram, no numerical observable |
| Table S7 | numeric_reproduction | target T009 | Exact gate-count arithmetic |
| Table S8 | numeric_reproduction | deferred_blocked | Unreleased circuit/code matrices and decoder metadata |
| Table S9 | numeric_reproduction | deferred_blocked | Same missing BB code-capacity simulator |
| Table S10 | numeric_reproduction | deferred_blocked | Exact BB matrix/circuit/decoder/seed contract absent; runtime alone is not the blocker |
| Table S11 | numeric_reproduction | deferred_blocked, historical T010 evidence | Printed Fowler inputs miss the table by factors of roughly 2-8 |
| Table S12 | numeric_reproduction | deferred_blocked | Exact APM matrix/circuit/decoder/seed contract absent |
| Fig. S5 | numeric_reproduction | deferred_blocked, historical T010 evidence | Implemented analytic law is quarantined because its printed constants do not close against Table S11 |
| Table S13 | numeric_reproduction | target T011 | Circular lifetime, distance, and error-floor formulas |
| Fig. S6 | numeric_reproduction | target T012 | Unitary gate trajectory plus disclosed open-system floors; partial |
| Fig. S7 | numeric_reproduction | target T013 | Circular thermal scaling from disclosed analytic model |
| Table S14 | numeric_reproduction | target T014 | Ten-mode error-budget arithmetic from Eq. S24 |

The detailed blocker names, target links, and reasons are machine-readable in
`figure_coverage.json`.
