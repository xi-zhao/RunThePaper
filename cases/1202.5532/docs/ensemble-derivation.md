# Exact product-state average: a diagnostic of the unspecified ensemble

For J_z=0, let U(t) be the one-particle unitary and P_A the projection on the
left half. Set A=U^dagger P_A U. For an initial occupation vector n_i in {0,1},

    Var(N_A) = sum_i n_i A_ii - sum_ij n_i n_j |A_ij|^2.

For a permutation-invariant initial-state ensemble define p1=E[n_i] and
p2=E[n_i n_j] for i != j. Since A is a rank-r projector, tr(A)=tr(A^2)=r,

    E_n[Var(N_A)] = (p1-p2) * (r - sum_i A_ii^2).

Independent fair occupations have p1=1/2,p2=1/4. Uniform fixed half filling
has p1=1/2,p2=(L-2)/(4*(L-1)). Therefore, at every time and for every disorder
configuration, the fixed-half mean number variance is exactly L/(L-1) times
the independent-fair-occupation result. This is not a fitted normalization.
It applies only at J_z=0 and only to the average pure-state number variance;
it must NOT be applied to entanglement entropy or interacting curves.

The generator averages all product states analytically before disorder
sampling, eliminating initial-state sampling noise without substituting
another physical model. It validates the formula against an explicit sum of
all 64 Slater-determinant product-state evolutions on four L=6 field sets.
60000 fresh L=10 field configurations supply disorder means and SEM on the
existing source time grid. Both ensembles are retained with their exact
pairing. No source y value is read by generation.

The original paper does not state the magnetization sampling measure. A
comparison can favor or disfavor these TWO candidate measures under the
frozen Hamiltonian, boundary conditions and reference-reading assumptions;
it cannot authenticate the authors' RNG or exclude every other correlated
initial-state measure. The inference is supplementary to, not a replacement
for, the long-chain convergence checks. It does not silently change the
declared fixed-half ensemble in any existing calculation. In particular, the
early exploratory sentence at checks/derivation.md:18 used independent fair
occupations; it does not describe the later fixed-half source-grid generation.
The current object contracts and this explicitly paired comparison take
precedence for this ensemble question. Historical derivation bytes are retained.

The first 60000-field execution used the previously declared source time grid,
whose abscissae differ from the separately extracted Figure 2(a) black curve
by at most 0.000474. A separate, identically seeded run uses that black curve's
exact extracted abscissae, not an interpolated ordinate. Both outputs remain.
Reference plotted error half-widths enter the pre-existing comparison scale;
their unknown sampling semantics do not justify a calibrated significance or
independent-point p-value. The 47 times are correlated.
