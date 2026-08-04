# Derivation Trace

This is a formula-heavy case. Numerical code may use only equations represented
in `EQUATION_CARDS.json` and opened by the formula gate.

## 1. Core business/physics object

The reusable object is not a plot. It is a `MinimumVarianceLeaf` determined by
a full-rank density matrix \(\rho\) and a Hamiltonian \(H\). Its state is:

- \(H_\rho\), the effective state Hamiltonian;
- eigenpairs \((E_{\rho,i},|\Psi_i\rangle)\);
- populations \(p_i\);
- normalized optimal representatives \(|\varphi_i\rangle\);
- invariants that prove the ensemble reconstructs \(\rho\) and attains the QFI
  convex roof.

Changing \(\beta\), \(H_0\), size, observable, or time does not change this core
model. Those are target configurations around the same object.

## 2. EQ001–EQ003: from the Lyapunov equation to the optimal ensemble

Write the full-rank density matrix in its eigenbasis:

\[
\rho=\sum_m\lambda_m|m\rangle\langle m|,\qquad \lambda_m>0.
\]

The paper defines \(H_\rho\) by

\[
\frac12\{H_\rho,\rho\}=\sqrt\rho H\sqrt\rho.
\]

Taking matrix element \(mn\) gives

\[
\frac{\lambda_m+\lambda_n}{2}(H_\rho)_{mn}
=\sqrt{\lambda_m\lambda_n}H_{mn},
\]

so

\[
(H_\rho)_{mn}
=\frac{2\sqrt{\lambda_m\lambda_n}}{\lambda_m+\lambda_n}H_{mn}.
\]

The factor is real and symmetric in \(m,n\), therefore Hermiticity of \(H\)
implies Hermiticity of \(H_\rho\). For a thermal state
\(\rho=e^{-\beta H_0}/Z\), with \(H_0|m\rangle=e_m|m\rangle\),

\[
\frac{2\sqrt{\lambda_m\lambda_n}}{\lambda_m+\lambda_n}
=\operatorname{sech}\!\left[\frac{\beta(e_m-e_n)}{2}\right].
\]

This is the preferred numerical form: the partition function cancels and no
exponentially small density-matrix eigenvalue has to be divided directly.

Diagonalize

\[
H_\rho|\Psi_i\rangle=E_{\rho,i}|\Psi_i\rangle.
\]

The Yu construction is

\[
p_i=\langle\Psi_i|\rho|\Psi_i\rangle,\qquad
|\varphi_i\rangle=\frac{\sqrt\rho|\Psi_i\rangle}{\sqrt{p_i}}.
\]

It passes three algebraic checks.

Normalization:

\[
\langle\varphi_i|\varphi_i\rangle
=\frac{\langle\Psi_i|\rho|\Psi_i\rangle}{p_i}=1.
\]

Reconstruction:

\[
\sum_i p_i|\varphi_i\rangle\langle\varphi_i|
=\sqrt\rho\left(\sum_i|\Psi_i\rangle\langle\Psi_i|\right)\sqrt\rho
=\rho.
\]

Representative energy:

\[
\begin{aligned}
\langle\varphi_i|H|\varphi_i\rangle
&=\frac{\langle\Psi_i|\sqrt\rho H\sqrt\rho|\Psi_i\rangle}{p_i}\\
&=\frac{\langle\Psi_i|\{H_\rho,\rho\}|\Psi_i\rangle}{2p_i}\\
&=E_{\rho,i}.
\end{aligned}
\]

The paper and Yu's convex-roof result then identify this reconstructed ensemble
as variance-minimizing:

\[
4\sum_i p_i\operatorname{Var}_{\varphi_i}(H)=F_Q(\rho;H).
\]

The implementation must verify this last equality numerically, not merely rely
on visual plots.

## 3. EQ008: independent QFI form

The SLD equation is

\[
\frac12\{\rho,L_\rho^{(H)}\}=i[\rho,H].
\]

In the \(\rho\) eigenbasis,

\[
(L_\rho^{(H)})_{mn}
=2i\frac{\lambda_m-\lambda_n}{\lambda_m+\lambda_n}H_{mn}.
\]

Substitution into the paper's commutator trace gives

\[
F_Q(\rho;H)
=2\sum_{m,n}
\frac{(\lambda_m-\lambda_n)^2}{\lambda_m+\lambda_n}
|H_{mn}|^2.
\]

This provides an independent check against the optimal-ensemble variance.
When \([\rho,H]=0\), all contributing off-diagonal elements vanish, so
\(F_Q=0\) and \(H_\rho=H\) on the support.

## 4. EQ004: leaf-canonical state

For the barycenter \(\rho_0\), use the eigenbasis of \(H_{\rho_0}\). Maximizing
the Shannon entropy of populations at fixed mean energy gives

\[
p_i=\frac{e^{-\beta E_{\rho_0,i}}}
{\sum_j e^{-\beta E_{\rho_0,j}}}.
\]

Applying the reconstruction identity from section 2 yields

\[
\rho_{\beta|\mathcal L_H(\rho_0)}
=\frac{\sqrt{\rho_0}e^{-\beta H_{\rho_0}}\sqrt{\rho_0}}
{\operatorname{tr}[\rho_0e^{-\beta H_{\rho_0}}]}.
\]

This is used for the black curves in Main Fig. 1.

## 5. EQ006: spin-chain numerical model

The paper uses

\[
H=\sum_\ell\left[
\sigma_\ell^x\sigma_{\ell+1}^x+
\vec h\cdot\vec\sigma_\ell+
D(\sigma_\ell^z\sigma_{\ell+1}^y-\sigma_\ell^y\sigma_{\ell+1}^z)
\right].
\]

The nonintegrable parameters are

\[
\vec h=\left(\frac{\sqrt5+5}{8},\frac12,\frac{\sqrt5}{2}\right),
\qquad D=\frac{\pi}{20}.
\]

The density matrix is thermal in a different Hamiltonian \(H_0\):

- main-text family: \(\vec h_0=(0,0,3/2)\), \(D_0=0\);
- supplemental family: \(\vec h_0=(0,0,1/2)\), \(D_0=0\).

The source omits boundary conditions. The initial reconstruction uses open
boundaries because the text says the generic \(H\) has no obvious global
symmetry, whereas uniform periodic couplings would preserve translation.
Open versus periodic will be tested at small size against source-figure
features and disclosed until resolved.

Hermiticity sanity checks:

- every Pauli string is Hermitian;
- operators on distinct sites commute, so
  \(\sigma_\ell^z\sigma_{\ell+1}^y\) and
  \(\sigma_\ell^y\sigma_{\ell+1}^z\) are Hermitian;
- all coefficients are real;
- therefore \(H=H^\dagger\).

## 6. EQ005: typicality curve

For each optimal representative,

\[
o_i=\langle\varphi_i|O|\varphi_i\rangle
=\frac{\langle\Psi_i|\sqrt\rho O\sqrt\rho|\Psi_i\rangle}{p_i}.
\]

Sort by \(E_{\rho,i}\), estimate the smooth shell average
\(f_{O,\mathcal L}(E_{\rho,i})\) using consecutive levels, then define

\[
r_i=|o_i-f_{O,\mathcal L}(E_{\rho,i})|,\qquad
N_\Delta=\#\{i:r_i>\Delta\}.
\]

The plotted quantity is

\[
\log_d N_\Delta=\frac{\log N_\Delta}{\log d}.
\]

The paper specifies a shell size of order \(\sqrt d\), but not its exact
integer or edge convention. Candidate centred rolling and non-overlapping
shells will be compared at \(L=6\). This affects parameter matching, not the
validity of the formula.

## 7. EQ007: dynamics representative

The paper chooses the representative minimizing

\[
\delta_i=
\frac{|E_{\rho,i}-\langle H\rangle|}
{\sqrt{\operatorname{Var}_{\varphi_i}(H)+F_Q(\rho;H)/4}}.
\]

The numerator and denominator both have energy units. Evolve the exact mixed
state and every selected pure state with \(U(t)=e^{-iHt}\):

\[
\langle O\rangle_{\rho,t}
=\operatorname{tr}[U(t)\rho U^\dagger(t)O],
\qquad
\langle O\rangle_{\varphi_i,t}
=\langle\varphi_i|U^\dagger(t)OU(t)|\varphi_i\rangle.
\]

The first reconstruction of the 68% and 95% bands uses empirical quantiles of
representatives inside the caption's \(\delta\)-shell. This convention remains
explicitly reconstructed until a stronger source-level confirmation is found.

## 8. EQ009: spectral compression

For a normalized pure state \(|\chi_i\rangle\), its energy-basis probabilities
are

\[
q_{\Psi i}=|\langle\Psi|\chi_i\rangle|^2,\qquad
\sum_\Psi q_{\Psi i}=1.
\]

The diagonal entropy and participation number are

\[
S_{{\rm diag},i}=-\sum_\Psi q_{\Psi i}\log q_{\Psi i},
\qquad
N_{{\rm part},i}=e^{S_{{\rm diag},i}}\in[1,d].
\]

For a decomposition \(\mathcal D=\{w_i,|\chi_i\rangle\}\),

\[
\overline S_{\rm diag}(\mathcal D|\rho)
=\sum_iw_iS_{{\rm diag},i}.
\]

The plotted finite-size gain is

\[
\Delta s_{\rm diag}(L)
=\frac{\overline S_{\rm diag}^{\rm eig}
-\overline S_{\rm diag}^{\rm mv}}{L}.
\]

A positive size-independent limit means that the ratio of effective
participation numbers is exponential in \(L\). The numerical check must retain
the sign and reproduce the paper's ordering:
minimum-variance representatives below spectral-decomposition representatives.

## 9. Numerical gates before target execution

The first executable check must use a small deterministic positive density
matrix and verify:

1. \(H_\rho\) satisfies its Lyapunov equation;
2. \(p_i>0\), \(\sum_i p_i=1\), and every representative is normalized;
3. the ensemble reconstructs \(\rho\);
4. representative energies equal \(E_{\rho,i}\);
5. \(4\) times the optimal average variance equals spectral QFI;
6. commuting \(\rho,H\) gives QFI zero and \(H_\rho=H\);
7. spectral-compression probabilities normalize.

Only after these checks pass may the figure runners consume the core module.
