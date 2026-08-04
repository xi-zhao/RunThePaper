# Method trace

1. Enumerate (S_k) exactly in image notation.
2. Count cycles and evaluate permutation traces without constructing the full
   (d^{kN_A}\)-dimensional matrices.
3. Transcribe source Eq. A3 with both global normalizers.
4. Solve its small dense Gram system for (k=3).
5. Trace-normalize the resulting coefficient vector on (A^{\otimes k}).
6. Compare the exact finite-(t) coefficients with the source and frozen
   first-order formulas.

This local exact computation is stronger and cheaper than an A100 run for the
chosen hypothesis. No GPU was used.
