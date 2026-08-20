# Formula Verification

- EQ001: source equation and PT origin patch condition derived.
- EQ002: wedge angles and contour chain rule derived.
- EQ003: paper WKB formula traced; `N=2` limiting case verified symbolically.
- EQ004: Riccati equation and decaying WKB boundary condition derived.
- EQ005: Eq. (11) converted to an overflow-safe but algebraically identical
  log-domain root.
- EQ006: massive `N=1` spectrum verified by completing the square.
- EQ007: all four opening oscillator sequences verified by completing the
  square with a complex linear coefficient.
- EQ008: the Airy matching derivative rederived from the Wronskian and checked
  at five real energies.
- EQ009: the classical gamma-function period and turning/escape geometry
  checked, including the exact `N=2` harmonic limit.
- EQ010: the Hermitian WKB formula is evaluated without the PT sine factor;
  an independent real-axis eigensolver verifies the square-well limit.
- EQ011: dominant balance of Eq. (11) gives the two-thirds logarithmic
  exponent, and log-domain roots recover it within `0.01418`.

Formula gates are open for implementation. Numerical acceptance still requires
the executable cross-checks and isolated-run evidence described in the target
contracts.
