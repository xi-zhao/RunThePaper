# Method Trace

1. Parse only printed equations, definitions, and parameter conventions.
2. Freeze `config/paper_exact.json` before any rendering work.
3. Evaluate closed-form spectrum and LZ formulas.
4. Independently integrate the two-component BdG equation with adaptive DOP853 in both physical sweep directions.
5. Evaluate finite half-integer momentum sums and stable logarithmic products.
6. Check unitarity, limiting cases, exponent, prefactor, finite-size collapse, and reverse-sweep symmetry from separately generated trajectories.
7. Render an auxiliary validation board from generated CSV files.

The scientific runner has no path to `raw/`, `references/`, source images, author code, or author arrays.
