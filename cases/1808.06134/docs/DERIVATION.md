# Analytic reconstruction, fixed arXiv:1808.06134v2

This is a same-agent derivation and independent algebraic check, not a formal proof-kernel certificate. Source locations were checked in the fixed PDF, including rendered pages 4 and 8. No later revision or paper-specific author code was used.

## Model and exact reductions

The circuit is an open chain. A complete period contains an even-link and an odd-link layer; the latter has L/2-1 gates for even L. The sentence assigning L/2 gates to both layers is incompatible with an open chain. It is resolved here by the explicit open-boundary statement and Fig.1 connectivity, without adding a periodic bond.

A UP gate first draws a Born outcome, applies its projector and normalizes, then applies an independently drawn unitary. Rank-one projectors are simultaneous measurements of Z_i and Z_{i+1}; rank-two projectors measure Z_i Z_{i+1}. They are orthogonal and sum to identity. Therefore M_alpha=U P_alpha satisfies sum M_alpha^dagger M_alpha=I, and the outcome-averaged channel is trace preserving and unital. A maximally mixed state is a fixed point, but unitality alone does not prove convergence from the stated initial state.

A1, p=1: after every covered rank-one measurement the pair is a product basis state and decoupled from the rest. After the independent U(4) gate it is a Haar two-qubit pure state. At a cut crossed by the last layer, only that pair contributes and S_2<=1 bit; at a noncrossed cut S_2=0. The unpaired edge qubits in the second layer cannot retain entanglement with the measured interior. Thus the bound holds for arbitrary L and all times after the first full covering layer. This is an exact reduction for the original observable, not a smaller substitute model.

Distinct check: use the Schmidt eigenvalue distribution of a Haar state in C^2 tensor C^2. With x=|2 lambda-1|, the density is 3x^2 on [0,1], purity is (1+x^2)/2, and

    E S_2 = integral_0^1 3 x^2 [-log_2((1+x^2)/2)] dx
          = (pi/2 - 4/3)/ln 2
          = 0.34258668306164575 bits.

Equal layer-parity sampling gives 0.17129334153082288 bits at every interior cut for even L>=4. L=2 is a control: the alternate layer has no gates, so its entropy is unchanged and its average stays 0.34258668306164575, not half this value. This predicts the exceptional L=2 point in F2c without fitting.

Thermal A1 from |+>^L: ignoring outcomes of the first full Z measurement gives I/2^L exactly; all following unital gates leave it unchanged. Thus S_th=L after that layer for every realization. This is stronger than a numerical long-time observation.

Thermal A2: the first full ZZ-dephasing layer yields rank 2^(L/2) and entropy L/2. Identity is stationary under all subsequent random channels. Generic repeated independent Haar rotations remove nonidentity components; finite-L channel simulations are used to check convergence, because a stationary identity alone is insufficient evidence. An exceptional sequence such as all identity gates need not mix, so the statement is stochastic/generic, not a guarantee for every gate history.

A2 rank-two projections alone can retain a volume-law Page state: conditioning disjoint pairs onto fixed parity leaves one two-dimensional logical degree of freedom per pair, dimension 2^(L/2). A cut between pairs therefore retains extensive Haar entanglement. This is a kinematic statement about a single measurement layer, not evidence for a volume law under the full p=1 hybrid dynamics.

## Literal CNOT formulas, Eqs.(16),(17), page 4

As printed, C = (I+Z_1)/2 + (I-Z_1) X_2. On the Z_1=+1 sector C=I; on Z_1=-1 it is 2X_2. Therefore C^dagger C has spectrum {1,1,4,4}; ||C|10>||=2. It is not a unitary gate and not a Clifford element. The swapped-control formula has the same defect.

Distinct verification: write the standard computational-basis permutation CNOT and evaluate both expressions as explicit 4x4 matrices. The correct standard identity is [(I+Z_1)+(I-Z_1)X_2]/2, with C^dagger C=I. The generator used here is this standard CNOT, consistent with the text's explicit uniform two-qubit Clifford group, rather than the nonunitary literal expression. The all-720-element conjugation oracle checks that this representation produces actual Clifford transformations. This establishes a fixed-v2 formula error; it does not establish that the authors used a nonunitary gate numerically.

There are no fitted parameters or hidden initial conditions in this counterexample. It is exact arithmetic on the source's Pauli convention. Both source TeX and rendered PDF agree, ruling out an extraction/OCR cause. The intended corrected operator passes the same test, so the counterexample is specific rather than a rejection of Clifford dynamics.

## Static scaling, Eqs.(22)-(25)

Assume S(L,delta)=L^gamma F(delta L^(1/nu)), delta=p-p_c, at fixed c=L_A/L. If F(x) is a power |x|^a at large negative argument, S~|delta|^a L^(gamma+a/nu). Volume-law scaling forces a=nu(1-gamma). On the positive side, size-independent entropy forces a=-nu gamma. Hence

    s_infinity = lim S/L ~ |delta|^[nu(1-gamma)], delta<0;
    S_infinity ~ delta^(-nu gamma), delta>0.

Distinct check: rescale L by any positive factor b at fixed delta. These branches scale as b and 1 respectively; incorrect signs do not. This is conditional algebra, not an independent derivation of the empirical scaling ansatz or critical exponents.

Using the paper's actual fitted parameter pairs gives:

| Model | gamma | nu | nu(1-gamma) | nu gamma |
|---|---:|---:|---:|---:|
| B1 | 0.30 | 1.85 | 1.295 | 0.555 |
| B2 | 0.33 | 1.75 | 1.1725 | 0.5775 |

Thus 4/3 and 2/3 in the prose are rough summaries based on gamma~1/3 and nu~2, not the exact products of the quoted fits. No uncertainty on the fit exponents is supplied, so this should not be presented as high-precision equality.

## Dynamic scaling, Eqs.(26)-(29), page 8

Assume S=L^gamma F(delta L^(1/nu),t L^(-z)). At delta=0, locality and a size-independent early-time limit require f(x)~x^(gamma/z), yielding S~t^(gamma/z). Choosing the scale b=t^(1/z) gives S=t^(gamma/z) G(delta t^(1/(z nu))). For a weak-phase ballistic entropy growth S~v_E t, a large-negative-argument power G(y)~|y|^a must satisfy gamma/z+a/(z nu)=1. Therefore

    a=nu(z-gamma), v_E~|delta|^[nu(z-gamma)].

The sentence between Eqs.(28),(29) instead prints G(y)~|y|^[nu(gamma-z)], the opposite sign. Direct substitution gives time exponent 2 gamma/z-1, which equals -0.4 for B1 gamma=.30,z=1; doubling t then gives a factor 2^(-.4)=0.757858283255199 instead of 2. It also predicts a diverging coefficient |delta|^(-1.295), contradicting the following Eq.(29).

Distinct check: solve the linear exponent equation a+nu gamma=nu z, or compare homogeneity under t->b t. Both select +nu(z-gamma). Eq.(29) and its vanishing-velocity conclusion are consistent with the corrected sign. The critical t^(gamma/z) argument does not use the mistaken sign. No simulation or author code is needed for this exact fixed-v2 inconsistency.

## Crossover statement, Eq.(30)

At fixed p<p_c, writing late-time entropy as proportional to L_A is legitimate. Close to criticality its proportionality coefficient cannot be dropped when predicting a crossover time. Let s_A(p) denote the volume-law entropy per site in A. Matching v_E t to s_A(p) L_A gives

    t_sat ~ s_A(p) L_A/v_E ~ L_A |delta|^[nu(1-z)].

This differs from the literal t_star=L_A/v_E if v_E is the entropy-production rate defined in Eq.(29). Similarly a well-separated intermediate regime requires L_A >> xi~|delta|^(-nu), since v_E tau/s_A has this scaling. The printed condition L_A >> v_E tau omits s_A. At fixed p these are finite prefactors; a uniformly near-critical interpretation is inconsistent with Eq.(24). The simulation in this attempt tests F6 at p_c and does not separately measure the off-critical velocity law or all three crossover regimes. Keep that empirical claim unfinished rather than using dimensional matching as experimental proof.

## Universality and scope

B1/B2 exponent closeness supports the paper's *suggestion* of common universality, but finite-size collapse does not prove uniqueness of scaling form or asymptotic exponents. The extension to Haar transition exponents is explicitly a suspicion in the source, not a demonstrated numerical panel. Its definitions are consistent; no new Haar critical experiment is required to check a conjecture at the level actually stated. A1/A2 strong-measurement data do not themselves establish that Haar universality conjecture.

No supplement or appendix occurs in the fixed 10-page PDF or the source TeX. The archive contains the main TeX and figure PDFs, but no author numerical arrays; the complete vector line paths provide calibrated comparison data. This is sufficient for pointwise reference comparison; the original Monte Carlo variances and seeds remain unspecified.
