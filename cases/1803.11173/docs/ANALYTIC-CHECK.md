# Distinct analytic checks (same researcher, no independent-review claim)

This file supplies checks separate from the two-copy twirl derivation in derivation.md. Numerical corroboration is retained in validation.json but is not needed to establish the exact counterexamples below.

## A. One-qubit rotation/Bloch geometry: all three Equation (7) branches
For rho=(I+r.sigma)/2, a Haar pure state has r uniformly distributed on the real unit sphere. Rotational symmetry gives E r_i=0 and E r_i r_j=delta_ij/3, since sum r_i^2=1. Set V=Z/2, H=X. The commutator derivative is minus r_y, giving Var=1/3 when only the input state is Haar. The printed first branch gives -Tr rho^2 Tr[V,H]^2/D^2 = 2/4=1/2. There are no step sizes or fit parameters in this contradiction.

For rho=|0><0|, V=X/2 and Haar-rotated H=X, let H'=s.sigma. Then the derivative is proportional to s_y and Var=1/3. Here -Tr[V,rho]^2=1/2 and Tr H^2=2, so printed branch 2 gives 1/4. For both sides Haar, g is one component of r cross s with independent uniform r,s: E[(r_x s_y-r_y s_x)^2]=1/9+1/9=2/9. Printed branch 3 gives 1/4. The corrected two-copy formulas produce all three Bloch integrals exactly.

Adding cI to H leaves [V,H'] unchanged. The original branch-2/3 prefactor Tr(H+cI)^2 changes. In the original allowed case H=I, rho=|0><0| and V=X/2, g is identically zero, whereas printed branch 2 gives 1/4. Thus the missing trace subtraction is not merely a choice of rotation-angle units. If one explicitly imposes a traceless observable, the finite-D denominator discrepancy still survives the preceding examples.

## B. Direct product differentiation and positive control for Equation (3)
Let U(theta)=exp(-i theta Z/2) H_ad, where H_ad is Hadamard, rho=|0><0| and measured observable X. The prepared state has E=cos theta, hence g=-sin theta. The printed split U_-=I, U_+=U and V=Z/2 predicts i<0|[Z/2,U^dagger X U]|0>=0. Its exact corrected generator is H_ad^dagger Z H_ad/2=X/2, giving -sin theta. At theta=0.7 the derivative is -0.644217687237691. This is an original-definition inconsistency for general noncommuting W_k. Moving W_k to U_- is an equivalent repair.

Positive control: take W_k=I, initial rho=(I+X)/2, same V=Z/2 and H=X. Both the printed and corrected formula give -sin theta. More generally [W_k,V]=0 is sufficient for their equivalence. The repair preserves the intended conventional parameter-cut identity; it does not refute that identity.

## C. 1-design zero mean does not imply small variance
Averaging a state over the n-qubit Pauli group is a 1-design and gives I/D. The trace of a commutator is zero, proving mean zero without Haar integration. For initial |0>^n, V=Y_1/2 and H=X_1, Pauli conjugation leaves computational basis states, so g takes +1 or -1 equally: variance one for every n. This verifies the paper's distinction between a 1-design mean and a 2-design second moment and challenges an unjustified stronger reading.

## D. Independent stationary-state sum for the numerical model
The Pauli-string transition matrix is doubly stochastic. It preserves the all-identity string, connects every other string, and has positive self-loops. The invariant distribution on the nonidentity sector is therefore uniform. The boundary sum factorizes: sum_{P0}d(P0)=2/3, sum_P b(P)=2, with d(I)=0. Thus Var(g)_infinity=(2/3)2^(n-1)/(4^n-1). This combinatorial normalization independently agrees with the exact U_+-Haar formula: for V=P/2 and pure product input, -Tr[V,rho]^2=2(<V^2>-<V>^2); averaging the first axis gives 2(1/4-1/12)=1/3. Multiplication by D/(D^2-1) gives D/[3(D^2-1)]. The agreement connects the Pauli-path calculation and the quantum Haar calculation without using reference figures.

For a fixed Y first generator with the explicit RY initial state, <Y>=0 and the corresponding coefficient is 1/2, hence a factor 3/2. For a literal sqrt(H_ad) initial state with all axes uniformly resampled, the norm of the Bloch vector remains one and the original 1/3 coefficient remains unchanged. Full-angle exp(-i theta P) instead of exp(-i theta P/2) changes gradient variance by four, not by 3/2. These are distinct, testable convention predictions, not assertions about author code.

## E. Tail, direction, sums and measurement scaling
Chebyshev plus the independently derived variance yields a fixed-epsilon tail O(poly(n)/2^n). If K=poly(n) parameter components each obey a common bound, E||gradient||_2^2 <= K C/2^n and Markov's inequality bounds the largest directional derivative over all unit directions at that point. This accounts for 'any reasonable direction' under bounded parameter count and normalization. The paper does not establish a landscape-wide adaptive optimizer lower bound solely from this single-point concentration.

For a polynomial sum of bounded local observables, Cauchy-Schwarz bounds cross-covariances by the product of their standard deviations, so a polynomial number and size of coefficients cannot remove exponential suppression. Identity-shift invariance and a zero-commutator generator are positive limiting checks. Exponentially growing operator coefficients are excluded from this bounded-scale statement.

Independent Pauli shots have variance at most one; averaging M shots produces O(M^-1/2) standard error. Keeping gradient signal/noise fixed for g_rms~2^(-n/2) requires M of order 2^n for the usual unbiased parameter-shift shot estimator when outcome variance stays O(1). The original O(epsilon^-alpha) precision argument remains conditional on the measurement-access model; it is not a universal theorem that every possible optimization procedure fails.

## F. Original schematic and depth remarks
Figure 2's open CZ chain and nonrepeated initial layer agree with the numerical paragraph, apart from its false label RY(pi/4)=sqrt(H_ad). The two initial states have fidelity (1+1/sqrt(2))/2=0.8535533905932737, so they are not related just by global phase. Squaring the principal sqrt(H_ad) recovers H_ad, while squaring RY(pi/4) gives RY(pi/2), not H_ad.

The geometric cartoon in Figure 1 is qualitative; an exponentially small variance means typical gradients are small, not an identically flat function. The literal real dimension of the normalized complex-vector sphere is 2D-1, with global phase quotient having real dimension 2D-2; the paper's dimension wording is schematic and the exponential dependence is unchanged.

The main-text O(n^(1/d)) depth sentence is an original argument, not accompanied by a proof of a design-precision bound for all architectures. Our finite 1D depth calculation tests the displayed observable; a single plateau cannot establish a complete unitary 2-design or a universal d-dimensional mixing theorem. That stronger interpretation remains unestablished, and no additional model or theorem was added as a reproduction task. Pretraining and structured initialization are suggestions in the conclusion, not numerical claims to reproduce.
