# Derivation Trace

## 1. Quantum lane

For `N_b` spin-1/2 particles restricted to the permutation-symmetric sector, `S=N_b/2` and the Hilbert dimension is `N_b+1`. In the `S^z` basis,

`S_-|S,m> = sqrt(S(S+1)-m(m-1)) |S,m-1>`.

The source TeX prints `S±=Sx±Sy`; the missing imaginary unit is a typographical error. Standard angular-momentum algebra, the later supplement commutator derivation, and complete positivity all require `S±=Sx±iSy`. This correction is explicit rather than silently patched.

With column-major vectorization,

`vec(A rho B) = (B^T kron A) vec(rho)`.

Therefore Eq. (2) becomes a sparse matrix on `(N_b+1)^2` components. The left trace vector is a null vector of this matrix, which is tested directly. Finite-time magnetization follows from `exp(Lt)rho(0)` with the paper's all-`+x` state. Spectra are either fully diagonalized at reduced `N_b` or solved near the imaginary axis with Arnoldi; every sparse eigenpair has a residual check.

The unique finite-size NESS is obtained by replacing one dependent row of `L rho=0` with `Tr rho=1`. Expectations and variances are then evaluated directly from spin matrices.

For the paper-scale `N_b=600` path, Eq. (2) is also rearranged as

`L rho = (kappa/S) D[J] rho`, with `J=S_-+i omega_0 S/kappa`.

For nonzero drive, `J` is invertible and
`rho_ss proportional to (J^dagger J)^-1=J^-1(J^-1)^dagger`.  This is a reconstructed
algebraic execution identity rather than unpublished author methodology.  The
lower-bidiagonal inverse is built in logarithmic scale and normalized as a Gram
matrix.  It is checked in two ways: full-density/moment agreement with the original
trace-constrained solve at small N, and a residual against the independently assembled
Liouvillian at the requested N.  These checks establish backend parity; they do not by
themselves resolve the S2 caption/observable inconsistency.

## 2. Thermodynamic lane

Divide collective spins by `S` and factorize products after their commutators vanish as `1/S`. This gives supplement Eq. (S7), implemented term for term. Substitution shows

`d(mx^2+my^2+mz^2)/dt = 0`,

so all phase trajectories remain on the unit sphere. The paper coordinates are `Q=mz` and `P=atan2(my,mx)/2` modulo `pi`.

For `omega_x=0`, the supplement's conserved scalar is evaluated from the printed logarithm/arctangent expression. The principal `atan2` branch creates the stated branch cut; ODE trajectories and scalar-field contours are generated independently.

## 3. Numerical-scale decision

All formulas and printed dimensionless couplings are exact. T016–T024 are
nevertheless `paper_subset`, because the supplement does not publish the
trajectory initial coordinates or complete plotting grids; those are generated
independently. Full quantum panels use reduced `N_b` because paper sizes up to
600 make repeated non-Hermitian Liouvillian solves unnecessarily expensive for
this campaign. Their status must remain `partial`/`reduced_scale`; render
styling cannot promote either reduced or reconstructed targets to complete.
