# Formula verification

The machine-readable gate is `outputs/checks/formula_verification.json`.

- EQ001: source traced; transverse and long-range limits checked.
- EQ002: source traced; initial magnitude and exponential decay checked.
- EQ003: source traced; exact-step and RK4 response paths cross-checked.
- EQ004: source traced; initial, late-time, and removable limits checked.
- EQ005: source traced; measured amplification retained as a printed parameter.
- EQ006: source traced; FFT and direct least-squares normalization cross-checked.
- EQ007: source traced; printed uncertainty combination checked numerically.

All seven formula cards are open for the declared feature targets. Finite-cell
geometry and experimental PSD/data remain unavailable, so those paper-exact
claims stay blocked even though their analysis code exists.
