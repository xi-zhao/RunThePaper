# Formula verification

The machine-readable gate is `EQUATION_CARDS.json`. Before implementation:

- the open-boundary summation limit was checked against Eq. (1);
- the Majorana signs were checked in both `J=0` and `W=0` limits;
- covariance normalization is `Gamma^2=-I` for a pure state;
- the KZM square-root scaling follows algebraically from Eqs. (4)-(10);
- the LZF `N^2` scaling follows from the parity-accessible gap `4 pi W/N`;
- the fidelity bounds were traced to the cited method paper rather than
  guessed from the source plot.

No scientific implementation may proceed unless
`check_formula_gate.py` reports every card open.
