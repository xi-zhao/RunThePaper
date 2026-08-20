# Numerical methods

## Primary solver

The primary solver integrates the real covariance matrix of the printed open
chain. The generator is tridiagonal, so the commutator is applied with banded
row/column operations rather than dense matrix multiplication. `DOP853` uses
declared relative/absolute tolerances. Each final covariance is checked for
antisymmetry, purity, and parity-consistent fidelity bounds.

## Static solver

Fig. 2(a) uses Hermitian diagonalization of `iA` followed by low-order subset-sum
enumeration. Curves are labelled by fermion parity, not inferred from line style.

## Cross-checks

1. small-N covariance dynamics is compared with direct spin-Hilbert-space
   evolution;
2. thermodynamic kink density is compared with an independent periodic
   momentum-mode calculation;
3. exact Gaussian fidelity must lie between the paper's `F1` and `F2` bounds;
4. convergence is checked by tightening ODE tolerances on representative slow,
   intermediate, and fast quenches.

Scientific arrays are written before any renderer sees the paper figures.
