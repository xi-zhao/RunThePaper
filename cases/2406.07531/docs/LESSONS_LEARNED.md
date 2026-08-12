# Lessons Learned

1. A method paper can expose clear equations while leaving the production
   calculation underdetermined through thresholds, grids, structures, and
   solver details.
2. Code readiness, method validation, and target reproduction must be separate
   states.
3. An A100 is not automatically the best resource for periodic
   quantum-chemistry workloads dominated by memory and CPU scaling.
4. Printed scalar values are useful falsification anchors but cannot create
   missing spectra.
5. A missing supplement is a source-material blocker, not permission to
   digitize figures or infer hidden tables.
6. Paper review must distinguish a reproducibility limitation from a proven
   scientific error.

## New Failure Modes

- A code-ready paper-scale plan can be mistaken for an executed target unless
  target data, execution, and review are modeled as separate states.
- Grouped parameter notes are not enough: every configuration needs target
  coverage, a complete inventory, source mapping, and explicit author-artifact
  boundaries.
- A derivation index without rendered equations passes human inspection too
  easily but fails durable scientific audit.

## Reusable Checks Or Tools

- `campaign.py` expands every target into hash-bound, resumable work units.
- `run_isolated_numerics.py` proves the clean Git SHA and forbidden-access
  boundary for the numerical runner.
- `render_frozen.py` checks that post-freeze plotting leaves numerical hashes
  unchanged.
- the protocol-v2 review bundles keep inventory and falsification phases
  separate without fabricating an independent verdict.
