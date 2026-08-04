# Derivation Trace

## Eq. (9): coherent over-rotation

For `A=X+Z`, `A^2=2I`.  Therefore

`exp(-i theta pi A) = cos(sqrt(2) theta pi) I - i sin(sqrt(2) theta pi) A/sqrt(2)`.

The implementation evaluates the same matrix exponential and verifies
unitarity numerically.

## Eq. (10): ordinary Pauli twirl

Expanding Eq. (9) in the Pauli basis gives identity amplitude
`cos(sqrt(2) theta pi)` and equal X/Z amplitudes
`-i sin(sqrt(2) theta pi)/sqrt(2)`.  Dropping off-diagonal Pauli-basis
coherence yields

`E_PT(rho)=(1-2p)rho+p X rho X+p Z rho Z`,

with `p=sin^2(sqrt(2) theta pi)/2`.  At `theta=0.05`, the independent value is
`p=0.024270800923...`, consistent with the paper's `p approximately 0.0243`.

## Proxy circuit

The public paper does not enumerate the generated Plaquette circuit locations.
The smoke target therefore states its own circuit: logical `|+>` encoded as a
three-data-qubit GHZ state, two ideal adjacent-ZZ checks for three rounds,
Eq. (9) or Eq. (10) on each data qubit at the beginning of every round, and
final logical-X parity measurement.

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

### EQ001

- Source:
- Latex:
- Role:
- Derived from:
- Steps:
- Symbols:
- Numerical form:
- Code pointer:
- Status:
- Open questions:
