# Formula verification

All five independent formulas are numerically open and regression-tested. “Open” means the implementation is trusted for audit; it does not endorse the corresponding frozen answer.

- Exact dispersion: matches PRL SM Eq. trace.
- Discrete search: 36-shell proof bound; agrees with a much larger independent scan after enforcing sums of two squares.
- Finite-(k) threshold: exact symbolic rearrangement and numerical classification at the benchmark point.
- Mapping: source general formula, direct zero of the ODE denominator, and residue exponent agree.
- (O(k^6)) coefficients: recovered from the exact dispersion at small (s); selected (k) makes the derivative vanish.

Run: `python3 -m unittest discover -s tests -v` from this workspace (or use the repository-relative command in the reproduction report).
