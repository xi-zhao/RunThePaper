# Derivation Trace

## Formula Lane Rule

Every numerical dependency is represented in `EQUATION_CARDS.json`, traced to
the final published PDF, independently checked, and connected to executable
code. Source data are used only after independent generation.

## EQ001 — Potts-like coloring objective

- Source: Eq. (2), Sec. 3.5.
- Derivation: replace each vertex's one-hot Boolean color variables by a single
  local label. The first term rewards assigning a color; the second adds a
  positive cost exactly when an edge has equal endpoint labels.
- Limiting check: for `B>A`, changing either endpoint of a violated edge to an
  unused valid color strictly lowers the objective. Exact enumeration verifies
  every accepted output against every graph edge.
- Code: `proper_coloring_indices`, `paper_figure_target_indices`.
- Status: verified.

## EQ002 — Multilevel Rydberg Hamiltonian

- Source: Eq. (3), Sec. 4.1, Appendix A parameter tables.
- Local space: one preparation state `|g>` and `k` Rydberg color states.
- Drive: each real laser channel contributes
  `Omega_i(t)/2 (|g><ri| + |ri><g|)`.
- Diagonal terms: `-Delta_i(t)` for each occupied Rydberg level, plus every
  same-level and cross-level pair energy `C6/R^6`.
- Hermiticity: drive matrices are symmetric and all remaining operators are
  real diagonal; the stored inter-level C6 matrix is symmetric.
- Units: `2pi MHz -> rad/us`; `2pi GHz um^6 -> 2pi*1000 rad/us um^6`.
- Code: `_interaction_energies`, `_operators`, `simulate_program`.
- Status: verified.

## EQ003 — Physical encoding interval

- Source: Eq. (4), Sec. 4.2.
- Derivation: the lower bound keeps the intended detuning larger than the
  attractive cross-level edge term; the upper bound preserves the positive
  same-color edge penalty even after the worst `alpha-1` attractive neighbors.
- Independent check: the simulator never converts the potential to a binary
  blockade. Retaining negative cross-level tails reproduces the paper's loss of
  robustness in the square K4 and `k=chi-1` examples.
- Code: `_interaction_energies`; distribution and proper-coloring checks.
- Status: verified, with Figure 7 protocol-c held closed by a source conflict.

## EQ004 — Annealing schedules and propagation

- Source: Eqs. (5)-(6), Sec. 4.3.
- Parameters: `ti=0.4 us`, `tf=8.0 us`, `T=8.4 us`, 300 samples.
- Boundary check: the cubic detuning reaches `-1` at `ti` and `+1` at `tf`;
  the Rabi profile reaches one at `ti`, stays at one, and returns to zero at T.
- Numericalization: initialize `|gg...g>` and apply 299 left-endpoint sparse
  exponentials. The final norm error is recorded for each case.
- Phase: the printed drives are real, so the exported control convention is
  `phi_i(t)=0`.
- Code: `AnnealingSchedule.normalized`, `simulate_program`,
  `hardware_control_rows`.
- Status: verified.

## Closed Source Ambiguity

Figure 7 protocol-c is not numerically opened. Appendix A.2 specifies the k=2
profile `Omega/2pi=(3,7) MHz`, `Delta/2pi=(8,19) MHz`, while the extracted
caption presents a conflicting equal-Omega protocol. Selecting either without
author clarification would manufacture a paper-exact input.
