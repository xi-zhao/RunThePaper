# Distinct analytic checks and precise claim boundaries

These are same-agent mathematical checks, not a proof-kernel certificate or fresh-context review. They use only the fixed v2 source. Numerical controls in `results/verification.json` supplement but do not substitute for the derivations below.

## A1 — infinitesimal Choi tangent and time-ordered products

Let P=|Phi><Phi|, Q=I-P, and C(dt)=P+dt (L tensor id)(P)+O(dt²). Positivity to first order requires Q(L tensor id)(P)Q >=0. In an orthonormal traceless operator basis, the latter is the Kossakowski matrix up to normalization and transpose conventions. Diagonalizing a positive matrix produces jump operators with nonnegative rates. Trace preservation fixes the anticommutator term; the remaining antisymmetric part is a Hamiltonian commutator. This supplies the necessary direction independently of the time-ordered product argument for sufficiency. Conditions: finite dimension, sufficiently regular time-local generator, and divisibility of intermediate propagators. It does not assert that every arbitrary negative coefficient in a redundant jump representation is a negative canonical rate.

## A2 — algebraic total variation and a false-negative control

For absolutely continuous E, write dE/dt=v_plus-v_minus, |dE/dt|=v_plus+v_minus. The initial minus final E equals integral(v_minus-v_plus), hence I(E)=2 integral(v_plus). This proves the sign and factor two without differentiating the implementation. Local CPTP monotonicity gives v_plus=0 almost everywhere. Constant entanglement (identity or local unitary channel) is a valid Markovian limit; 'strictly decreasing' is not literally necessary.

A concrete demonstration of insufficiency uses the qubit depolarizing family Lambda_p(rho)=p rho+(1-p)I/2, first decreasing continuously from p=1 to 1/5, then increasing only from 1/5 toward 1/4. Every whole map is CPTP and invertible. The Choi state is separable for p<=1/3, so system-ancilla negativity remains zero throughout the increase. However, for p2>p1>0 the unique intermediate map has ratio r=p2/p1>1, and Choi eigenvalues (1+3r)/4, (1-r)/4 repeated three times. It is not CP. At p1=.2 and p2=.25 its eigenvalues are 1.1875,-.0625,-.0625,-.0625, norm 1.375, yet both monitored entanglements are zero. This is a checking control for the author's sufficient-only statement, not a new requested model result. Smooth the temporal transition while remaining below p=1/3 if differentiability is needed; the same algebra applies.

## A3 — trace norm, inverse-map condition, and the pointwise derivative caveat

For any Hermitian normalized Choi C, sum eigenvalues=1. Splitting its positive and negative eigenvalues gives ||C||_1=1-2 sum_negative lambda. Thus norm=1 iff every eigenvalue is nonnegative. This derivation does not rely on a numerical eigenvalue routine. For a known invertible TP evolution, its inverse is trace-preserving on the full linear operator space: if Tr E(X)=Tr X for all X, set X=E^{-1}(Y). Hermiticity preservation follows likewise. Therefore the intermediate inverse construction has exactly the prerequisites of the trace-norm test. At singular times there is no unique inverse; the paper explicitly identifies this and does not supply a universal repair. Infinite-dimensional maximal entanglement is an idealization, while the finite-r Gaussian witness is a legitimate finite-energy sufficient test.

Pointwise literal check: use the paper's own dephasing class with gamma(t)=1-t on [0,2]. The whole coherence factor exp[-2t+t²] lies in (0,1], so the whole maps are CPTP and invertible. At t=1, gamma=0 and g(1)=0, but integral_1^(1+epsilon) gamma=-epsilon²/2. Every epsilon>0 with epsilon<=1 gives f_NCP=exp(epsilon²)>1. Thus 'g(t)=0 iff E_(t+epsilon,t) is CP' is false if interpreted for a finite interval starting exactly at a rate crossing. The limit statement measures the first-order non-CP rate; it is zero at that point. For t>1 it is positive and the integral detects the non-Markovian interval. This caveat does not refute the central integrated criterion for regular dynamics, and it does not alter either oscillator figure.

The normalized measure D=I/(1+I) maps [0,infinity] monotonically into [0,1], since dD/dI=1/(1+I)²>0, D(0)=0 and lim D=1. Nonintegrable negative rates give divergence rather than a finite value.

## A4 — Kraus/Choi probabilities versus master-equation coherence

The matrix elements satisfy d rho00/dt=0 and d rho01/dt=-2 gamma rho01. Independent channel representation: Lambda_q(rho)=p_plus rho+p_minus sigma_z rho sigma_z with p_plus=(1+q)/2, p_minus=(1-q)/2. Its orthogonal Bell Choi projectors have these eigenvalues, so their trace norm is |p_plus|+|p_minus|=max(1,q), q>0. Since q=1-2 gamma(t)epsilon+o(epsilon), g=max(0,-2gamma), including the factor two in Eq.(4). This agrees with both the differential equation and the channel probability representation. No optimization appears.

A physical finite-interval check is gamma=sin(t), cumulative integral 1-cos(t)>=0, so the whole family is CPTP. On [0,2pi], I=-2 integral_pi^(2pi) sin(t)dt=4, D=.8. For gamma=tan(t), the negative interval (pi/2,pi) gives integral from pi/2+delta to pi of -2tan(t)=-2log(sin delta), which diverges as delta ->0+. The source's singularity caveat applies; this is not a bounded rate through a zero of the dynamical map.

The source footnote's spontaneous-emission analogy: the amplitude-damping map has excited survival eta>0 and coherence multiplier G with |G|²=eta. The intermediate map has ratio R=eta(t+epsilon)/eta(t) and multiplier G(t+epsilon)/G(t). The normalized Choi eigenvalues are (1+R)/2, (1-R)/2,0,0, so g=max(0,eta_dot/eta). A Lorentzian kernel obeys G''+lambda G'+(gamma0 lambda/2)G=0, G(0)=1,G'(0)=0; with d²=lambda²-2gamma0 lambda, G=e^(-lambda t/2)[cosh(dt/2)+(lambda/d)sinh(dt/2)]. Real d gives monotone decay, imaginary d gives revival intervals; the sign condition agrees with the source's qualitative analogy. At G=0 use intervals excluding singular times. This checks the brief remark at its stated level, not a reproduction of an external article's figure.

## Figure/source wording checks

Figure 1 shows S initially entangled to an isolated ancilla A, while only S couples to the bath. This matches rho_SA propagation by Lambda tensor id; the lower illustrative curve can revive only when CP divisibility fails. No numerical fit or redrawing is required.

Figure 3's equally spaced x ticks are printed 0, 0.5, 0.1, 0.15 in both supplied PDF and EPS. The first interior label is inconsistent with its coordinates; 0.05 is the coherent reading. This is a fixed-v2 axis-label typo, not a scientific rescaling chosen to fit.

The p.3 paragraph says that I(E) itself increases with increasing temperature for sufficiently large alpha. Its displayed endpoints in both original figures instead decrease with T. Quantitative endpoint values from the exact EPS paths are in comparison.json. The calculations reproduce that decrease and the increasing onset threshold; the sentence's literal magnitude trend is not supported by its own plotted range. A claim about alpha beyond the plotted range is not established by these figures, and we do not extrapolate it.

## Implementation/parameter/information checks for discrepancies

The pointwise-g caveat is analytic within the source's exact dephasing generator; it does not involve numerical error, missing author data, or an alternate gamma normalization. The axis-label contradiction is in both fixed source representations. The temperature sentence is compared to the fixed original vector curves and an independent reconstruction under its displayed parameters. Neither observation establishes an error in the authors' microscopic solver. Remaining numerical residuals have their own discretization checks; no cause is assigned merely from a closer curve.
