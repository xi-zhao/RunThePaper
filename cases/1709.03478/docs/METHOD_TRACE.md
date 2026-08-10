# Method Trace

## METHOD001 — Lowest-band continuum solver

- Source: paper Eq. (1), with the real-space discretization described in cited
  Ref. 1704.04498.
- Rule: build the open-boundary symmetric tridiagonal Hamiltonian and select
  the lowest L eigenstates; obtain localized primary-band orbitals from the
  projected-position operator.
- Code: `src/reproduce_spme.py::{continuum_tridiagonal,lowest_band,primary_basis,primary_hopping}`.
- Invariants: eigenvector orthogonality, observable bounds, positive primary
  hopping and decreasing hopping with lattice depth.
- Status: implemented and unit-tested.

The paper-scale edge-density path does not replace the printed preparation by
a Wannier-box shortcut: it diagonalizes the finite-difference Hamiltonian
sliced to the center third, embeds those occupied eigenstates in the full grid
and measures the same spatial center projector after release.

## METHOD002 — Phase-resolved checkpoint blocks

- Core object: one immutable numerical parameter block, identified by a hash
  of profile, target, phase, lattice depth node and detuning grid.
- State transition: `planned → complete checkpoint`; `--resume` accepts a
  checkpoint only when both its full config hash and serialized task match.
- Granularity: T002 per phase; T003–T004 per (Vp, depth node, phase); T005 per
  (trap, Vd, phase); T006 per (depth node, phase).
- Code: `src/paper_scale_campaign.py::{build_tasks,execute_task,run_campaign}`
  and `scripts/run_paper_scale.py`.
- Status: 2,784 production/convergence blocks build successfully; tiny smoke
  and checkpoint-resume paths are tested.  Full blocks are unrun.

## METHOD003 — Tube-depth quadrature

The supplement prints lattice-beam waist 150 μm and transverse cloud widths
42 μm and 12 μm.  With the disclosed 1/e²-radius assumption,

\[
n(y,z)\propto e^{-2(y^2/w_y^2+z^2/w_z^2)},\qquad
f(y,z)=e^{-2(y^2+z^2)/w_b^2}.
\]

With \(u=\sqrt{2}y/w_y\) and \(v=\sqrt{2}z/w_z\), the normalized atom
distribution is \(e^{-u^2-v^2}/\pi\).  Product Gauss–Hermite quadrature acts
directly on the nonlinear observable:

\[
\langle O\rangle\approx\sum_{ij}\frac{4w_iw_j}{\pi}
O(f_{ij}V_p,f_{ij}V_d),\quad
f_{ij}=e^{-(w_yu_i/w_b)^2-(w_zv_j/w_b)^2}.
\]

Four-quadrant symmetry merges an order-(8,4) rule into eight explicit positive
nodes.  The order-(10,6) profile gives fifteen nodes and refines both axes.
This is derived from the paper method but remains `paper_scale_method_proxy`,
because the width convention and author's discrete per-tube atom counts are
absent.

## METHOD004 — Aggregation and scientific acceptance

- Phase means and standard deviations are computed only from generated
  checkpoints.
- Tube means use the explicit normalized node weights; the central tube is
  calculated separately at depth factor 1.
- Main Fig. 4 uses only linear interpolation between generated neighboring
  Vd rows at the printed threshold 0.015.
- Acceptance requires all five targets, bounded observables, six resolved
  central double crossings, nonnegative widths and the stated width trend.
- Code: `paper_scale_campaign.py::{_tables_for_profile,_acceptance,aggregate_campaign}`.

## METHOD005 — Protocol-v2 evidence boundary

The campaign includes four independent convergence axes: q=6→8, L=610→738,
six→twelve phases and eight→fifteen tube nodes.  It also runs two distinct
checks: normalization/orthogonality invariants and an alternative sparse-CSR
ARPACK eigensolve at a frozen production probe.  Shared preparation and
observable definitions are disclosed, so a fresh reviewer must still judge
the independence strength.

The runner never self-emits `paper_error_candidate`.  A solver invariant or
alternative-solver mismatch is `reproduction_defect`; incomplete convergence
or an otherwise stable scientific discrepancy is `inconclusive`.  Only a
fresh protocol-v2 reviewer may promote a preserved discrepancy after explicit
falsification and a complete cited discrepancy record.
