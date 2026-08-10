# Method Trace

## MTH001 — Independent analytic sweep

- Source: Main Eqs. (1)-(2), Table I, full supplement.
- Inputs: `gamma=1`, `phi` on 1001 equally spaced points from 0 to pi.
- Algorithm: enumerate connection-point pairs; independently evaluate closed
  forms; require equality; freeze every visible series to CSV.
- Outputs: 18 numeric columns (phase, normalized phase, and four coefficients
  for each setup; duplicate individual rates are retained for provenance).
- Code: `src/giant_atoms/model.py`, `src/giant_atoms/reproduction.py`.
- Checks: Table-I parity, braided decoherence-free point, non-braided zero
  coupling, nonnegative individual rates.
- Status: verified in an isolated attested run.

## MTH002 — Hash-guarded RenderContract

- Source access: source figure only after MTH001 froze the CSV hash.
- Allowed: canvas, axes, fonts, line styles, palette, ticks, legend, grid.
- Forbidden: changing any physical parameter or numeric array.
- Code: `src/giant_atoms/render_contract.py`.
- Status: passed; the output records both data and reference hashes.

## MTH003 — Checkpointed paper-scale campaign

- Interface: one JSON config plus `run_campaign`; CLI details do not leak into
  the scientific implementation.
- Sharding: eight contiguous phase-index shards, each stored as an immutable
  NPZ bound to the complete config SHA-256.
- Resume: existing shards are reused only after their fingerprint, bounds,
  phase grid, finite arrays, and independent-formula residual validate.
- Aggregation: requires every index exactly once before writing the combined
  CSV, acceptance JSON, manifest, and state.
- Acceptance: general-sum/Table-I parity, decisive `phi=pi/2` identities,
  nonnegative decay, and 1001/2001 shared-grid invariance.
- Code: `src/giant_atoms/campaign.py`,
  `scripts/run_paper_scale_campaign.py`.
- Status: code-ready; smoke and resume paths passed, full repeat campaign not
  launched because the equivalent paper-exact data are already attested.

## MTH004 — Protocol-v2 reproducer audit

- Role: actively try to falsify Main Fig. 2 and inspect formula/caption
  consistency without claiming independent-review authority.
- Checks: alternative implementation, limiting case, grid refinement, curve
  inventory, and a two-method audit of the supplement's mirror equation.
- Code: `src/giant_atoms/paper_audit.py`,
  `scripts/run_protocol_v2_audit.py`.
- Artifact: `outputs/checks/paper_review_protocol_v2.json`.
- Status: audit passed; paper assessment remains `inconclusive` pending fresh
  protocol-v2 review.
