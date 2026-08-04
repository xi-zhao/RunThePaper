# Derivation Trace

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until its formula dependencies are traceable and
the formula gate is not closed.

## Convention

For a normalized two-band texture,

\[
P(\mathbf k)=\frac{1+\mathbf n(\mathbf k)\cdot\boldsymbol\sigma}{2},
\qquad |\mathbf n|=1.
\]

The standard rank-one quantum metric is
\[
g_{ij}=\frac12\operatorname{tr}(\partial_iP\,\partial_jP)
=\frac14\partial_i\mathbf n\cdot\partial_j\mathbf n.
\]
Define \(K=\int_{\rm BZ}\operatorname{tr}g\,d^2k\). The displayed
projector definition in the paper gives \(E_D=K/2\) in flat isotropic
coordinates, hence \(E_D\ge\pi|C|\) is equivalent to \(K\ge2\pi|C|\).

## Equation Cards

### EQC001 — Projector mismatch

- Source: main-text Eq. `HS` contains
  \(\operatorname{tr}[P(\mathbf k)P(\mathbf k-\mathbf q)]\), followed by its
  small-\(\mathbf q\) expansion.
- Latex:
  \(D(\mathbf k,\mathbf q)=\operatorname{tr}[P_{\mathbf k}(1-P_{\mathbf
  k+\mathbf q})]=(1-\mathbf n_{\mathbf k}\cdot\mathbf n_{\mathbf
  k+\mathbf q})/2\).
- Steps: insert both Pauli decompositions, use
  \(\operatorname{tr}\sigma_a=0\) and
  \(\operatorname{tr}(\sigma_a\sigma_b)=2\delta_{ab}\).
- Numerical form: a dot product of two unit vectors, clipped only at floating
  point roundoff.
- Code pointer: `code/src/chern_jump_geometry.py:projector_mismatch`.
- Status: verified algebraically.

### EQC002 — Small-\(\mathbf q\) metric limit

- Source: paragraph following Eq. `HS`; the paper expands the same form factor
  to quadratic order and identifies the Dirichlet energy.
- Latex:
  \(D(\mathbf k,\mathbf q)=q_iq_jg_{ij}(\mathbf k)+O(q^3)\).
- Steps: Taylor-expand \(\mathbf n(\mathbf k+\mathbf q)\). Differentiating
  \(\mathbf n^2=1\) gives
  \(\mathbf n\cdot\partial_i\mathbf n=0\) and
  \(\mathbf n\cdot\partial_i\partial_j\mathbf n
  =-\partial_i\mathbf n\cdot\partial_j\mathbf n\). The quadratic term is then
  \(q_iq_j\partial_i\mathbf n\cdot\partial_j\mathbf n/4\).
- Numerical form: use the symmetric \(\pm\mathbf q\) average to cancel odd
  finite-\(q\) corrections.
- Code pointer: `code/src/chern_jump_geometry.py:directional_mismatch`.
- Status: verified.

### EQC003 — Isotropic jump second moment

- Source: Eq. `hsapprox` and the Dirichlet definition; reconstructed as a
  normalized four-direction probe.
- Latex:
  \[
  K_{\rm jump}(q)=\frac{2}{q^2}\int_{\rm BZ}\bar D(\mathbf k,q)d^2k
  =K+O(q^2),
  \]
  where
  \(\bar D=(D_{+x}+D_{-x}+D_{+y}+D_{-y})/4\).
- Steps: each axis pair gives \(q^2g_{ii}+O(q^4)\); averaging the two axes gives
  \(q^2\operatorname{tr}g/2+O(q^4)\).
- Numerical form: evaluate shifts by periodic interpolation so \(q\) is not
  restricted to an integer grid step.
- Code pointer: `code/src/chern_jump_geometry.py:jump_metric_estimator`.
- Status: verified for the explicitly fixed probe.

### EQC004 — Topological bound and normalization

- Source: paragraph following Eq. `hij` and the displayed Dirichlet
  definition.
- Latex:
  \[
  K=\int\operatorname{tr}g\ge\int|\Omega| \ge
  |\int\Omega|=2\pi|C|,\qquad E_D=K/2\ge\pi|C|.
  \]
- Steps: the pointwise trace inequality supplies the first inequality, the
  triangle inequality the second, and
  \(C=(2\pi)^{-1}\int\Omega\) the last equality.
- Normalization check: for the Pauli projector,
  \(\operatorname{tr}(\partial_iP\partial_jP)=2g_{ij}\), so the paper's
  displayed factor \(1/4\) yields \(E_D=K/2\). The later prose factor
  \(E_D=(1/4)\int\operatorname{tr}g\) cannot yield its stated bound and is
  treated as a factor-of-two typo.
- Code pointer: `code/src/chern_jump_geometry.py:geometry_observables`.
- Status: normalization verified.

### EQC005 — Chern number on a periodic grid

- Source: massive Dirac paragraph specifies the model and \(C=1\).
- Latex:
  \[
  C=\frac{1}{4\pi}\sum_{\triangle}
  2\operatorname{atan2}\!\left[
  \mathbf a\cdot(\mathbf b\times\mathbf c),
  1+\mathbf a\cdot\mathbf b+\mathbf b\cdot\mathbf c+\mathbf c\cdot\mathbf a
  \right].
  \]
- Steps: split each periodic momentum plaquette into two oriented spherical
  triangles and sum their signed solid angles. This is gauge-free for the
  \(\mathbf n\) texture and integer-stable away from singular plaquettes.
- Code pointer: `code/src/chern_jump_geometry.py:chern_number_solid_angle`.
- Status: independent discretization; checked against the paper's \(C=1\)
  sector.

### EQC006 — Paper LLG flow

- Source: Eq. `LLG equation`.
- Latex:
\[
  \partial_t\mathbf n=-\mathbf n\times\mathbf h+
  \gamma\mathbf n\times(\mathbf n\times\mathbf h),\quad
  (2\pi)^2\mathbf h=2\lambda_T\mathbf d-\lambda_D\nabla^2\mathbf n.
\]
- Derivation: insert
  \(P=(I+\mathbf n\cdot\boldsymbol\sigma)/2\) and the corresponding
  two-band effective Hamiltonian into the single- and double-commutator
  projector flow. The Pauli identity
  \([\mathbf a\cdot\boldsymbol\sigma,\mathbf b\cdot\boldsymbol\sigma]
  =2i(\mathbf a\times\mathbf b)\cdot\boldsymbol\sigma\)
  gives the precession term; applying it twice gives the double-cross damping
  term.
- Independent check:
  \(\mathbf n\cdot(\mathbf n\times\mathbf h)=0\) and
  \(\mathbf n\cdot[\mathbf n\times(\mathbf n\times\mathbf h)]=0\), hence
  \(d|\mathbf n|^2/dt=0\) in the continuum.
- Numerical form: periodic second-order Laplacian, RK4 time stepping, and
  pointwise normalization after each complete step.
- Code pointer: `code/src/chern_jump_geometry.py:llg_rhs` and
  `code/src/chern_jump_geometry.py:rk4_step`.
- Status: verified from the projector equation and Pauli algebra.

### EQC007 — Lyapunov check

- Source: Eq. `Lyapunov`.
- Latex:
  \(\dot H_S=-\gamma\operatorname{tr}[\Pi_P(\partial H_S/\partial P)^2]\le0\).
- Derivation: write \(G=\partial H_S/\partial P\). Cyclicity gives
  \(\operatorname{tr}(G[P,G])=0\), so the Hamiltonian part conserves energy.
  For the dissipative part,
  \(\operatorname{tr}\{G[P,[P,G]]\}=
  \operatorname{tr}\{\Pi_P(G)^2\}\ge0\), because \(\Pi_P\) is the orthogonal
  tangent projection. Multiplying by \(-\gamma\) proves the inequality.
- Role: acceptance rule for the discretized flow. The executable check allows
  only a small integrator tolerance and separately tracks \(C\).
- Code pointer: `code/scripts/run_validation.py`.
- Status: verified.

### EQC008 — The published bath has no momentum-transfer form factor

- Source: published Supplemental Material Eqs. (50) and (103).
- Latex:
  \[
  H_I=\lambda\sum_{\mathbf k,\alpha}c^\dagger_{\mathbf k}
  [b^\dagger_{\alpha,\mathbf k}V_\alpha(\mathbf k)
  +b_{\alpha,\mathbf k}V^\dagger_\alpha(\mathbf k)]c_{\mathbf k}.
  \]
- Consequence: both fermion operators carry the same \(\mathbf k\). The bath
  probes orbital matrix elements at fixed momentum; it does not contain the
  overlap \(P_{\mathbf k}(1-P_{\mathbf k+\mathbf q})\) used by EQC001.
- Independent index check: the bilinear is
  \(c^\dagger_{\mathbf k}V(\mathbf k)c_{\mathbf k}\), not
  \(c^\dagger_{\mathbf k+\mathbf q}V c_{\mathbf k}\). Projecting it into the
  band basis therefore produces same-\(\mathbf k\) orbital rotations, whereas
  a density-transfer detector necessarily carries two different fermion
  momenta.
- Code pointer:
  `code/src/detector_sum_rule.py:paper_bath_complete_vertex_strength`.
- Status: verified.

### EQC009 — Ohmic matrix-space bath is damping, not a click model

- Source: Supplemental Material Eqs. (74)–(85) and (104).
- Latex:
  \[
  \mathcal J(\omega,\mathbf k)=\sum_\alpha
  \delta(\omega-\Omega_\alpha)|V_\alpha\rangle\langle V_\alpha|
  \simeq\eta\omega e^{-\omega/\omega_c}I_{\rm HS},\qquad
  \gamma=2\pi\eta\lambda^2.
  \]
- The source uses this spectral superoperator to obtain
  \(\dot P=i[P,\partial_PH_S]-\gamma[P,[P,\partial_PH_S]]\).
  It does not derive a completely positive master equation, detector
  instrument, or Lindblad jump operators. The assumed \(n_B\) in Eq. (54)
  never enters Eqs. (68)–(85), because the retained calculation follows the
  mean bath amplitude and drops noise correlations.
- Independent checks: a sum of matrix-space outer products is positive;
  the Ohmic replacement \(\eta\omega e^{-\omega/\omega_c}I_{\rm HS}\) keeps
  that positivity, and \(\gamma\) vanishes continuously when either
  \(\lambda\) or \(\eta\) vanishes.
- Status: verified as a deterministic damping model; it cannot by itself
  define counting statistics.

### EQC010 — Detector-fixed spectator density probe

- Source: Supplemental Material Eq. (29) supplies
  \(\rho_{\mathbf q}=\sum_{\mathbf k,i}c^\dagger_{\mathbf k+\mathbf q,i}
  c_{\mathbf k,i}\). This is an independent weak probe, not Eq. (103).
- Latex:
  \[
  H_{\rm probe}=\lambda\sum_{\mathbf q}
  (b^\dagger_{\mathbf q}\rho_{\mathbf q}
  +b_{\mathbf q}\rho_{-\mathbf q}),
  \quad
  \rho_{\mathbf q}=\sum_{\mathbf k,m,n}
  F_{mn}(\mathbf k,\mathbf q)
  \gamma^\dagger_{m,\mathbf k+\mathbf q}\gamma_{n,\mathbf k},
  \]
  with
  \(F_{mn}=\langle u_{m,\mathbf k+\mathbf q}|u_{n,\mathbf k}\rangle\).
- Steps: insert
  \(c_{\mathbf k,i}=\sum_nu_{n,i}(\mathbf k)\gamma_{n,\mathbf k}\)
  into \(\rho_{\mathbf q}\) and sum over orbital \(i\).
- Code pointer: `code/src/detector_sum_rule.py:density_probe_weight`.
- Status: algebraically verified.

### EQC011 — What a calibrated record actually measures

For a filled lower band and an energy-resolved incident probe,
\[
R(\mathbf q,\omega)=2\pi\lambda^2J(\mathbf q,\omega)\nu(\omega)
\sum_{\mathbf k}D(\mathbf k,\mathbf q)
\delta[\omega-\Delta_{\mathbf k,\mathbf q}],
\]
The calibrated spectral integral is
\[
A_{\rm cal}(\mathbf q)=
\int_{\{J\nu>0\}}\frac{R(\mathbf q,\omega)}
{2\pi\lambda^2J(\mathbf q,\omega)\nu(\omega)}d\omega
=\sum_{\mathbf k}\operatorname{tr}
[P_{\mathbf k}(1-P_{\mathbf k+\mathbf q})].
\]
This is just Fermi's golden rule plus unoccupied-band completeness. Calibration
must occur before the frequency integral. A detector zero or an omitted
frequency window removes information rather than being repaired by a global
normalization.

- Code pointer:
  `code/src/detector_sum_rule.py:calibrated_density_response`.
- Status: derived and normalization-checked.

### EQC012 — The conditional no-dark theorem

Combining EQC011 with EQC002–EQC004 gives
\[
K_{\rm click}(q)=\frac{2}{q^2}\overline{A_{\rm cal}(q)}
\longrightarrow \int_{\rm BZ}\operatorname{tr}g\,d^2k
\ge 2\pi|C|.
\]
The statement requires a scalar density vertex, four controlled small
momenta, spectral resolution, a nonzero calibrated kernel, and the
\(q\rightarrow0\) extrapolation. It is not a lower bound on raw total counts.

- Code pointer:
  `code/src/detector_sum_rule.py:density_probe_metric_estimator`.
- Status: verified by composition of the previous cards.

### EQC013 — The paper bath's isotropic vertex ensemble is geometry-blind

Let \(\{V_a\}\) be an orthonormal Hilbert–Schmidt basis, as implied by the
identity superoperator in EQC009. Completeness gives
\[
\sum_a V_aXV_a^\dagger=\operatorname{tr}(X)I.
\]
For a two-band rank-one projector \(P\) and \(Q=1-P\),
\[
\sum_a\operatorname{tr}(QV_aPV_a^\dagger)
=\operatorname{tr}(Q)\operatorname{tr}(P)=1.
\]
The same result holds for a Chern texture and a constant trivial texture.
Hence the published bath's complete same-\(k\) orbital response is
texture-blind rather than bounded by quantum geometry.

- Code pointer:
  `code/src/detector_sum_rule.py:paper_bath_complete_vertex_strength`.
- Status: algebraically verified.

### EQC014 — Raw-rate and vertex no-go limits

The rate in EQC011 scales as \(\lambda^2J\nu\), so it can be made arbitrarily
small by weakening the coupling; thermal absorption also vanishes at
\(T=0\), while a filled lower band has no lower-energy spontaneous-emission
channel. Furthermore, an orbital vertex \(M\not\propto I\) measures
\[
D_M(\mathbf k,\mathbf q)=
\operatorname{tr}[P_{\mathbf k}M^\dagger
(1-P_{\mathbf k+\mathbf q})M].
\]
At \(q=0\), the scalar vertex vanishes because \(P(1-P)=0\), but a generic
\(M\) produces a nonzero constant term. Its small-\(q\) coefficient is
therefore not the standard quantum metric.

- Code pointers: `code/src/detector_sum_rule.py:raw_absorption_rate` and
  `code/src/detector_sum_rule.py:orbital_vertex_weight`.
- Status: limiting cases and projector algebra verified.

### EQC015 — Exact extended-Hubbard field

- Source: official Supplemental Eqs. (117), (123), (124), (127), and (128).
- Interaction:
  \[
  v(\mathbf q)=U+2V(\cos q_x+\cos q_y).
  \]
- Exact two-band field:
  \[
  (2\pi)^2\mathbf h(\mathbf k)=2\lambda_T\mathbf d(\mathbf k)
  -\frac1{\pi^2}\int_{\rm BZ}d^2q\,
  v(\mathbf q)\mathbf n(\mathbf k-\mathbf q).
  \]
- Derivation: varying the symmetric double momentum integral in the
  Hartree–Fock functional produces two equal contributions. For
  \(P=(I+\mathbf n\cdot\boldsymbol\sigma)/2\),
  \(\operatorname{tr}(P_{\mathbf k}P_{\mathbf k-\mathbf q})
  =[1+\mathbf n_{\mathbf k}\cdot\mathbf n_{\mathbf k-\mathbf q}]/2\);
  the two contributions cancel the factor \(1/2\) and give the printed
  convolution.
- Exact low-rank evaluation: after \(\mathbf p=\mathbf k-\mathbf q\),
  \[
  \begin{aligned}
  \int v(\mathbf q)\mathbf n(\mathbf k-\mathbf q)d^2q
  =&\,U\mathbf N_0+2V[
  \cos k_x\,\mathbf C_x+\sin k_x\,\mathbf S_x\\
  &+\cos k_y\,\mathbf C_y+\sin k_y\,\mathbf S_y],
  \end{aligned}
  \]
  where, for example,
  \(\mathbf C_x=\int\cos p_x\,\mathbf n(\mathbf p)d^2p\).
  This is an identity, not an approximation.
- Independent checks: compare the five-moment expression with the direct
  periodic convolution on a small even grid; for a constant texture the
  interaction field is parallel to \(\mathbf n\) and produces no torque.
- Code pointers:
  `code/src/chern_jump_geometry.py:extended_hubbard_convolution` and
  `code/src/chern_jump_geometry.py:exact_extended_hubbard_rhs`.
- Status: verified.

### EQC016 — Extended-Hubbard small-\(q\) coupling

- Source: official Supplemental Eqs. (129)–(134).
- Expansion:
  \(v(\mathbf q)\simeq(U+4V)-V(q_x^2+q_y^2)\).
- With radial cutoff \(Q\),
  \[
  \lambda_D=\frac1{4\pi}\int_0^Q
  [(U+4V)-Vq^2]q^3dq
  =\frac1{4\pi}\left[(U+4V)\frac{Q^4}{4}
  -V\frac{Q^6}{6}\right].
  \]
- Numerical checkpoint:
  \((U,V,Q)=(8,0.75,\pi/2)\) gives
  \(\lambda_D=1.1828772769\ldots\), agreeing with the reported \(1.183\).
- Code pointer:
  `code/src/chern_jump_geometry.py:extended_hubbard_lambda_d`.
- Status: verified.

### EQC017 — Trace-condition deviation

- Source: main Fig. 3 color bar and Supplemental Fig. 4.
- Observable:
  \[
  \Delta_{\rm tr}(\mathbf k)=
  \frac12\left[\operatorname{tr}g(\mathbf k)-|F_{12}(\mathbf k)|\right].
  \]
- For the Pauli projector,
  \(g_{ij}=(\partial_i\mathbf n\cdot\partial_j\mathbf n)/4\) and
  \(F_{12}=-
  \mathbf n\cdot(\partial_x\mathbf n\times\partial_y\mathbf n)/2\).
- The pointwise trace inequality requires
  \(\Delta_{\rm tr}\ge0\). A negative numerical value therefore diagnoses
  derivative or resolution error and must not be silently clipped in the
  structured data.
- Numerical form: the supplement says energy and Chern use the same finite
  mesh but does not disclose its derivative stencil or grid origin. Direct
  comparison shows that periodic spectral derivatives on an \(N=141\)
  half-cell-shifted grid recover all three linked signatures at
  \(T_{\rm short}\): \(E_D=3.1452\simeq\pi\), numerical
  \(C=0.9965\), and a peak of order \(10^2\). A node-centered grid is
  invalid for this finite-mesh transition because it samples
  \((\pi,\pi)\) exactly and symmetry-pins the bubbling spin. Centered
  differences and the solid-angle Chern number are retained as independent
  resolution diagnostics.
- Code pointer:
  `code/src/chern_jump_geometry.py:local_geometry`.
- Status: verified.

## Resolved Physical Bridge

The bridge has a **pivot** outcome:

1. The Mera–Ozawa bath used to produce the geometric flow does not define the
   desired finite-\(q\) clicks and is not supplied with a quantum-trajectory
   unraveling.
2. A separately fixed, weak scalar density probe does reduce—after
   frequency-by-frequency calibration—to EQC003 and inherits the Chern bound.
3. This static sum rule is adjacent to the established quantum-weight/static
   structure-factor literature. The remaining potentially new claim is the
   time-resolved, no-postselection monitoring of approach to saturation, not
   the static bound itself.
