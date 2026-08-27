# Derivation Trace

See `EQUATION_CARDS.md` for the canonical formula cards. This file records the
human-readable derivation chain and current proof status.

## Derivation Phase Rule

Before adding a numerical target, the agent must identify:

- the equation cards that define the model;
- the mathematical operation that turns them into a numerical object;
- the validation identity or limiting case that checks the formula.

For this paper the first derivation pass prioritizes the chain:

```text
Bloch Hamiltonian
-> real-space open-chain Hamiltonian
-> similarity transform / beta ansatz
-> generalized Brillouin zone
-> non-Bloch winding number
```

## D1: Bloch Hamiltonian to Real-Space Open Chain

Source: model paragraph and Fig. 2 caption in `nonHermitian.tex`.

For `t3 = 0`, the Bloch Hamiltonian can be written in the off-diagonal SSH form:

```text
H(k) =
[[0, t1 + gamma/2 + t2 exp(-ik)],
 [t1 - gamma/2 + t2 exp(+ik), 0]]
```

Using unit cells `(A_n, B_n)`, the open-boundary finite Hamiltonian has:

```text
A_n <- B_n:     t1 + gamma/2
B_n <- A_n:     t1 - gamma/2
A_n <- B_{n-1}: t2
B_n <- A_{n+1}: t2
```

This is exactly the convention implemented by `open_chain_hamiltonian`.

The finite Hamiltonian is off-diagonal in sublattice space. After grouping all
`A` sites before all `B` sites:

```text
H = [[0, C],
     [D, 0]]
```

Therefore `E^2` is an eigenvalue of `C D`. The pilot uses this block structure
to compute eigenvalues as `+/- sqrt(eig(CD))`, because direct diagonalization of
the non-normal finite matrix can numerically break the exact `E -> -E` symmetry
near strongly asymmetric hopping points.

## D2: Expected Transition for Fig. 2

The paper's shortcut solution gives the true open-boundary transition:

```text
t1 = +/- sqrt(t2^2 + (gamma/2)^2)
```

For `t2 = 1` and `gamma = 4/3`, this is:

```text
sqrt(1 + (2/3)^2) = sqrt(13/9) = 1.201850425
```

The conventional Bloch gap-closing points are:

```text
t1 = +/- t2 +/- gamma/2
```

For the Fig. 2 parameters these include `+1/3`, `+5/3`, `-1/3`, and `-5/3`.
The pilot check should verify that the open-chain zero-mode region is bounded
near `+/- 1.20185`, not by the Bloch gap-closing points.

## D3: Evidence Boundary Status

The initial derivation pass recorded that no digitized reference data had been
extracted yet. That statement is now superseded by the current evidence files:

- `outputs/checks/all_digitized_curves.json`
- `outputs/checks/pixel_evidence.json`
- `internal-reference-curves/*.csv`

The current boundary is narrower and more precise:

- formula gates for the scored targets are verified;
- generated objects are independent numerics or analytic references;
- digitized source curves and pixel-layout crops validate alignment to the
  paper figures;
- author plotting data is unavailable, so author-data equivalence and 100
  percent reproduction are not claimed.

Public notes must state this evidence boundary before using curve or pixel
agreement as validation.
