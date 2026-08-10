# Lessons Learned

## What worked

- Two independent numerical paths—exact constrained-chain dynamics and MPS
  residuals—share only paper-derived definitions, so agreement is meaningful.
- Symmetry orbit bases reduce memory without changing the Hamiltonian.
- Exact pair blocking turns the L=30 entropy calculation into a 15-site
  three-state MPS problem without changing the constrained Hamiltonian.
- Digest-bound lane checkpoints and a final resume/merge make time-step and
  bond refinements independently schedulable and auditable.
- Analytic MPS monomials and tangents reproduce the three printed leakage
  anchors on very small rings.
- Freezing NPZ hashes before render preserves the boundary between science and
  appearance.

## Difficulties and reusable lessons

| Difficulty | Lesson |
| --- | --- |
| Coordinate singularities at the Neel chart boundary | Integrate to a declared chart boundary and reconstruct the symmetry-related half-orbit; never regularize the physical flow into a different equation. |
| Paper-size Hilbert spaces grow exponentially | Use an exact representation change or symmetry reduction, keep reduced runs exploratory, and make every deferred paper-scale path executable with config, checkpoints, outputs and acceptance. |
| Generic MPS truncation could leave the constrained space | Measure forbidden adjacent-excitation weight independently; do not rely on norm conservation alone. |
| Source omits the deformed closed-form residual | Cross-check the matrix Hamiltonian by independently projecting it to the printed flow, then classify the stable difference as `parameter_ambiguity`. |
| A generated curve can disagree after local checks pass | Preserve the failed target and classify it as `reproduction_defect`, `parameter_ambiguity`, `insufficient_compute`, or `inconclusive`; require all five hard gates before `paper_error_candidate`. |
| Whole-figure scoring hides weak panels | Keep 15 subpanel targets and comparisons, including both failed S2 panels. |

## New Failure Modes

`parameter_ambiguity_after_convergence`: printed upstream
definitions can pass independent local checks while an indispensable downstream
quantity remains unspecified. Future cases should record projection checks and
finite-size convergence, keep the conservative assignment, and require both a
paper-exact procedure and fresh independent reviewer before considering
`paper_error_candidate`.

## Reusable Checks Or Tools

The case suggests a reusable checker that binds a derived flow both to a matrix
Hamiltonian projection and to a residual observable. No harness-global file is
changed in this per-paper commit; the proposal is preserved here for later
triage.
