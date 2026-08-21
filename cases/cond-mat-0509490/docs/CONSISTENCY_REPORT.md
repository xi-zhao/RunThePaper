# Consistency Report

The independently generated evidence supports all five modeled claim groups.

- Critical dispersion ratio: `0.9999937`.
- Direct BdG norm error: below `6.7e-9`.
- Maximum BdG-versus-LZ probability gap: `0.00222`.
- Density exponent: `-0.5000000`.
- Finite-sum versus analytic density error: below machine precision in the fit window.
- `tau_Q/N^2` probability collapse spread: zero on the frozen Gaussian grid.
- Forward kink and reverse flip sweeps: separately integrated from opposite endpoints, then compared mode by mode and after a finite-chain density sum. The maximum probability gap is `3.76e-10`, the maximum density gap is `2.44e-11`, and the largest norm drift is `1.12e-8`. No forward array is reused as reverse output.

## Paper-side discrepancy under review

The line after Eq. (23) prints the second term of the transformed annihilation operator with `gamma_k^dagger`. Fermionic momentum pairing, direct two-mode operator composition, and the paper's own Eq. (24) require `gamma_{-k}^dagger`. This is a local subscript discrepancy: it does not alter the later scalar Landau-Zener probability because the following state already uses the correct `(k,-k)` pair. A refreshed fresh-context reviewer must adjudicate the final paper-error status after the repaired run is frozen.

The statements that an earlier simulation fitted prefactor `0.16` and LZ coefficient `59` cite external work. The analytic values `1/(2pi)=0.15915` and `2pi^3=62.0126` are compatible, but this case does not pretend to possess the earlier authors' numerical arrays. Scientific paper adjudication belongs to the fresh review output.
