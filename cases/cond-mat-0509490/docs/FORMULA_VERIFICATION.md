# Formula Verification

All seven cards are source-traced and independently gated.

- EQ001: critical dispersion limit and antiperiodic momentum grid.
- EQ002: direct ODE norm conservation.
- EQ003-EQ004: symbolic LZ mapping plus direct BdG comparison; maximum frozen-grid probability gap is `0.00222`.
- EQ005: Gaussian integral and independent `N=4096` sum; fitted exponent is `-0.5`.
- EQ006: lowest-mode coefficient `2 pi^3` and exact `tau_Q/N^2` collapse.
- EQ007: independently executed forward/reverse BdG sweeps, compared mode by mode and after the finite-chain density sum.

Machine result: `outputs/checks/formula_gate.json`.
