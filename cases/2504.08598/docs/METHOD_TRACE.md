# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### MTH001 — Sparse multilevel evolution

- Source: Eq. (3), Sec. 4.3.
- Inputs: coordinates, C6 matrices, Omega/Delta maxima, Eqs. (5)-(6), 300 samples.
- Steps: enumerate basis, build all-pair diagonal interactions and per-level
  sparse drives, apply one matrix exponential per interval, decode colorings.
- Code: `src/rydberg_qudit.py:simulate_program`.
- Checks: norm, graph validity, deterministic outputs, author-reference metrics.
- Status: verified.

### MTH002 — Graph and hardware compiler

- Source: Tables 1-2 and Secs. 4-6.
- Outputs: `paper_atom_coordinates.csv`, `paper_hardware_controls.csv`.
- Invariants: one atom per vertex; one channel per Rydberg level; Phi=0; ground
  is preparation-only except explicit appendix audits.
- Status: verified with tetrahedron sqrt(2) interpretation recorded.

### MTH003 — Reference-side comparison

- Source: Strathclyde dataset DOI.
- Metrics: curve correlation/errors, raw-index TVD, sorted TVD, paper-target
  fidelity, all-proper-coloring fidelity.
- Code: `scripts/reproduce_qudit_annealing.py`.
- Status: verified.

### MTH004 — Pasqal cross-check

- Status: not applicable.
- Reason: public Pulser/Pasqal simulation has one Rydberg level per atom; EV20
  requires k distinct levels plus inter-level C6 terms. A qubit translation
  would change the Hamiltonian.

Only `verified` opens final numerical execution. An independently checked
`reconstructed` method may open exploratory execution; `source_only` and
`blocked` do not.
