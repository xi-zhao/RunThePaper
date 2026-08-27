# Derivation Trace

## Scope

This paper is primarily an algorithm-and-simulation paper. The derivation gate
covers only equations that feed local executable targets. Circuit-level
surface-code results without public code/data remain outside the numeric gate
instead of being filled with inferred curves.

## 1. Delayed-erasure decoding object

For an observed lost lifecycle `i`, enumerate every possible loss location,
cancel subsequent gates, use the resulting detector response to construct a
detector-error hypergraph `D_i`, and weight each possibility by its conditional
probability. Add the lossless Pauli model and optionally the earliest-loss
combination term. The main paper sets the latter weight to zero.

The local proxy preserves the information ordering—hidden loss time, final SSR
flag, and decoding with or without that flag—but replaces the surface code by a
distance-five repetition code. It tests the decoder mechanism, not the paper's
absolute logical-error rate.

## 2. Error-channel normalization

An entangling-gate error rate `p_CZ` induces the per-qubit probability
`p = 1-sqrt(1-p_CZ)`. Splitting this probability into loss fraction `L` and a
biased Pauli channel keeps total probability equal to `p`; this is checked
symbolically and numerically.

## 3. Threshold/lifecycle relation

The paper's linear correctable boundary between pure loss and pure Pauli limits
is solved algebraically after substituting
`p_loss=L p_threshold` and `p_Pauli=(1-L) p_threshold`. Appendix H reports the
empirical non-SWAP loss-only trend `7 / lifecycle^(1/3)`, which is recomputed on
the Fig. 4(b) lifecycle domain.

## 4. Lifecycle counting

A rotated distance-`d` surface-code stabilizer round contains
`4 d (d-1)` entangling gates. Conventional data qubits persist through every
noisy round; measure qubits are reinitialized and measured each round. Counting
gate endpoints and completed lifecycles gives the data, measure, and all-qubit
averages used in Figs. 14(c) and 16(a). The all-qubit average is invariant under
SWAP relabeling, which is the specific analytical claim tested here.

## 5. Algorithm lifecycle counts

Appendix G gives closed counting rules for GHZ, 15-to-1 distillation, H/T
small-angle synthesis, and an adder. The code evaluates those rules directly at
the Fig. 6(b) settings. No plot coordinates are sampled.

## Gate outcome

Machine-readable cards: `EQUATION_CARDS.json`. Reader-facing rendering:
`DERIVATION.md`. Gate record:
`outputs/checks/formula_verification.json`.
