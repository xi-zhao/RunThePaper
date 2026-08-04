# Derivation Trace

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until its formula dependencies are traceable and
the formula gate is not closed.

## Equation Cards

### MOB001-MOB002: Zeta accumulation and Möbius inversion

- Source: Eqs. (4)-(9), Appendix A.
- Role: convert between a diagonal basis-state phase table and projector-phase hyperedges.
- Steps:
  1. A projector gate on support `S` contributes its phase exactly when `S` is contained in the occupied set `T`.
  2. Summing those contributions gives the subset-zeta transform `F(T)`.
  3. Inclusion-exclusion cancels every proper subset and leaves `theta_S`.
  4. Phases are wrapped modulo `2π`; empty support is retained only for roundtrip validation and omitted from executable gates.
- Numerical form: dictionaries keyed by sorted support tuples.
- Code pointers: `src/mobius_compiler.py:mobius_inversion`, `zeta_reconstruct`, `wrap_phase`.
- Status: verified on every three-variable Boolean phase table (`256/256`).

### MOB003: Literal-controlled 3-SAT clauses

- Source: Eqs. (21)-(22).
- Role: expose the degree-three conditional phase before gate lowering.
- Steps:
  1. Positive literals are violated at `x_j=0`; negative literals at `x_j=1`.
  2. The product projector marks the unique violating assignment.
  3. Expanding every `(1-x_j)` produces occupation projectors only.
  4. The full three-variable support always survives with phase `±π`, equivalent modulo `2π`.
- Numerical form: enumerate all eight local basis assignments and apply MOB002.
- Code pointer: `src/mobius_compiler.py:clause_phase_table`.
- Status: verified for all eight polarity patterns.

### MOB004: Routed no-fault roll-up

- Source: Eq. (23), Table I.
- Role: combine routed gate, transfer, crosstalk-idle, and coherence exposure.
- Steps:
  1. Count storage-local one-qubit gates, shared-zone two-qubit gates, and retained native blocks.
  2. Count activation/deactivation once per moved atom and nonparticipating atom layers during entanglers.
  3. Accumulate total scheduled duration and each qubit's busy duration.
  4. Evaluate the product in log space to avoid underflow.
- Limiting case: one storage-local phase has `log F = log(F_1q)`, duration `t_1q`, and zero motion.
- Code pointer: `src/proxy_router.py:route_gate_stream`.
- Status: formula verified; route-state inputs are `proxy_model`, not paper-exact.

## Remaining Exact-Reproduction Boundary

Eq. (23) is executable, but the author route-state inputs remain unpublished.
The approved toy geometry tests the mechanism and software path only; it is not
the paper's Fig. 4-8 routed ensemble.
