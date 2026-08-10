# Method Trace

1. Enumerate the complete constrained periodic product basis from the local
   no-adjacent-excitation rule.
2. Form normalized orbits under translation by two for quench dynamics, or
   under the full translation/reflection group for the Fig. 2(a) sector.
3. Build the projected Hamiltonian by applying the paper's local `Sx` matrix
   to a representative and converting edge counts into normalized orbit
   matrix elements.
4. Validate reduced matrices against unreduced small-system matrices before
   any paper-size run.
5. Evolve the reduced-size initial vectors with a sparse Krylov exponential;
   compute sublattice magnetization and exploratory entropy in the orbit basis.
6. For paper-scale Fig. 2(b,c), pair physical sites into the exact three-state
   constrained basis `|00>,|01>,|10>`. This turns the periodic three-site PXP
   operator into a nearest-neighbour Hamiltonian on 15 blocks whose invariant
   globally constrained subspace is exactly the original physical Hilbert
   space.
7. Evolve both product states with a symmetric finite-MPS/tDMRG product
   formula. Run primary, halved-time-step, and enlarged-bond lanes; checkpoint
   the complete MPS and observable prefix every `2/Omega`, then merge only
   config-digest-matched lane outputs.
8. Contract three-block and one-block reduced density matrices for the six-site
   and one-site entropies. Check norm and true energy drift, forbidden-state
   weight, entropy bounds, refinement differences, time coverage, and the
   generic-versus-scarred separation.
9. Independently construct the variational MPS and tangent vectors, then apply
   the same Hamiltonian to evaluate the TDVP residual. No original figure or
   digitized quantity appears in this path.
10. Write self-describing NPZ data and JSON checks before rendering plots.

For Supplement Fig. S2, an additional falsification step projects the
independently assembled deformed matrix Hamiltonian onto the two MPS tangents
and compares those velocities with the printed flow. This gate passes before
the residual curve is evaluated. The remaining minimum mismatch is therefore
reported rather than visually fitted away. Because the closed deformed
residual construction and numerical orbit-integral procedure are omitted,
protocol-v2 assigns `parameter_ambiguity`. `paper_error_candidate` remains
blocked by the non-paper-exact method and absent fresh independent review.

The two numerical paths share only the paper-derived Hamiltonian and local
spin convention. Exact dynamics do not consume TDVP data; TDVP residuals do
not consume exact-dynamics curves.

The paper does not disclose a Fig. 2 time step, bond dimension, truncation
cutoff, or explicit evolution package. Those are independent implementation
choices, recorded in `config/fig2_tdmrg_paper_scale.json` and accepted only
after the two refinement lanes agree. They are never presented as recovered
author settings.
