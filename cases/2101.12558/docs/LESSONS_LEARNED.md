# Lessons Learned

- A DFT+DMFT paper can print U, J, temperature, layers, vacuum, and cutoffs yet
  still omit inputs that determine the numerical answer.
- “Code ready” must be a first-class state distinct from reproduced.
- Every stacked layer axis needs its own target even when several axes share
  one physical run.
- An A100 does not automatically solve a CPU-heavy CT-HYB/QE workflow.
- Validation models are useful only when named as method validation and kept
  outside paper-target scoring.

Harness backlog: make missing pseudopotential/projector/continuation identity a
standard fail-closed checklist for electronic-structure cases.

## New Failure Modes

| Failure mode | Detection |
| --- | --- |
| Printed global DFT+DMFT parameters hide indispensable backend identity | Require pseudopotential hashes, coordinates, projector gauge, sampling controls, and continuation metadata before execution promotion. |
| A stacked figure is counted as one target | Inventory each independent axis and layer observable before implementation. |

## Reusable Checks Or Tools

| Candidate | Reuse |
| --- | --- |
| Public-backend pseudopotential hash gate | Every plane-wave reproduction case |
| Reconstructed-slab provenance marker | Every surface calculation lacking exact coordinates |
| Code-ready versus executed target state | Every compute-deferred scientific case |
