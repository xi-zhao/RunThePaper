# Derivation trace

1. Transcribe the XXZ Hamiltonian and maximally biased edge Lindblad operators.
2. Use the paper's exact `R = S_n S_n^dagger` MPO construction, including the
   generic anisotropic amplitudes and the separately regularized Delta=1 limit.
3. Contract only the diagonal auxiliary subspace.  This gives tridiagonal `T`
   and magnetization vertex `V`; a path returning to auxiliary state zero in n
   steps never visits an index above `floor(n/2)`, making the finite truncation
   exact.
4. Evaluate `Z_n=<0|T^n|0>`, one- and two-point functions with scaled forward
   and backward products, and the conserved current
   `J=(epsilon/2) Z_(n-1)/Z_n` from `Im W=-(epsilon/4)T`.
5. At Delta=1/2, independently check that the generated transfer matrix closes
   to the printed 3x3 matrix and that its leading eigenvalue yields the printed
   thermodynamic current.
6. Independently solve the Lindblad fixed-point equation in the full Hilbert
   space for n=2,3,4.  Agreement with the transfer result checks Hamiltonian,
   dissipator, observable conventions and MPO contraction together.
7. Construct the physical MPO explicitly and test the theorem, commutator,
   triangularity, rank, exact auxiliary cutoff and coupling-polynomial degree.
8. Count band operations directly for the `O(n^2)` claim; treat the printed
   root-of-unity cutoff index, hopping parity and auxiliary dimension as a
   separate full-Eq.-(7) substitution problem, cross-checked against the
   paper's own `m=3` reduced matrix.
9. In the isotropic limit, test the amplitude recurrence, double commutator,
   boundary identities, normalization constant `alpha` and convergence to the
   continuum cosine profile independently.
10. In the easy-plane regime, diagonalize the finite reduced transfer matrix
    and compare its subleading/leading eigenvalue ratio with an independently
    fitted finite-current convergence ratio and the flattening bulk profile.
11. For `Delta>=1`, construct an arbitrarily extendable shifted triangular
    minor. Its nonzero diagonal gives a direct, finite certificate of the
    paper's infinite-rank statement without inferring rank from a truncated
    numerical matrix alone.
12. Freeze generated CSV/JSON data and hashes. Rendering and pixel comparison
   happen only after this boundary.
