# Liouvillian skin effect: dark-state structure and the H3 entropy discrepancy

**Dark-state structure and bounded finite-system calculations are supported. A fixed unnormalized diagnostic greatly reduces the H3 discrepancy, but it neither identifies the authors' implementation nor completes the large-ensemble/cutoff study.** This partial reproduction addresses Halati, Jin and Moessner, [Constructing Large and Structured Decoherence-Free Subspaces in Hybrid Quantum Systems, arXiv:2610.12348v1](https://arxiv.org/abs/2610.12348v1), with evidence dated 13 October 2026.

[中文报告](reproduction-note.zh-CN.md) · [Code](../code/README.md) · [Evidence map](../docs/EVIDENCE_INDEX.md) · [Quantification](../docs/QUANTIFICATION.md)

## Scientific question and model

Loss need not select a unique simple state. Coupling quantum matter to a lossy cavity can select the null space of a matter operator. Directed motion produces boundary accumulation, while symmetries constrain both the dynamics and surviving states. A large decoherence-free subspace and the Liouvillian skin effect are related but distinct claims.

For an open chain at fixed particle number,

$$O=\sum_{j=1}^{L-1}c_j^\dagger c_{j+1},\qquad
H/\hbar=\delta a^\dagger a-g(a^\dagger O+aO^\dagger),$$

$$\dot\rho=-i[H/\hbar,\rho]+\Gamma\bigl(a\rho a^\dagger-\tfrac12\{a^\dagger a,\rho\}\bigr).$$

If $O|\psi\rangle=0$, both the Hamiltonian and jump operator annihilate $|0\rangle_{\rm cavity}|\psi\rangle$. Coherences within this subspace are stationary as well. This establishes the constructed subspace, not an unrestricted converse about every steady state of a generalized model.

We use Fock-sector null-space calculations and photon-counting quantum trajectories. Vacuum initial cavity, photon cutoff and ODE tolerances are explicit assumptions. Coherent GS trajectories retain superpositions across total-charge sectors: dephasing can preserve certain linear means while changing trajectory distributions and nonlinear entropies. See [derivation](../docs/DERIVATION.md) and [numerical methods](../docs/NUMERICAL_METHODS.md).

## Static results and statistical comparisons

At $N=8$, fermions have $L=16$ and bosons $L=9$. The total dark-space counting formula gives 526 for each. We computed 23 selected $(X,N_p)$ sectors, including density, correlations and entropy. The largest null-space and pairing residuals are about $2.61\times10^{-14}$ and $9.88\times10^{-14}$.

![Independently generated dark-state correlations](../outputs/figures/fig10.png)

The [comparison guide](../docs/COMPARISONS.md) provides source-panel context. Finite-size profiles alone do not prove an asymptotic volume law.

The Haar study sampled 512 complete orthonormal bases for each of 23 sectors, 11776 basis draws. Linear-mean trace invariance held within approximately $4.88\times10^{-15}$. Of 344 previously located source mean points, 300 were reliably read and 44 remain unknown; that is reference-reading coverage, not reproduction success.

The standard-deviation convention matters. For the readable, dimension-matched subset, the joint finite-sample comparison with `ddof=1` gave $p\approx0.214$. Non-rejection does not identify the same numerical arrays, and does not cover occluded points. Sector-dimension labels and other panels remain open.

## H1: observable identity

The H1 axis uses $\langle O_+O\rangle$, while the caption and adjacent prose use $\langle O^\dagger O\rangle$, even though $O_+\ne O^\dagger$. For the unweighted $O$ at $N=8$, $\|O\|\le8$, so a normalized state satisfies $\langle O^\dagger O\rangle\le64$. Values above 100 cannot simultaneously satisfy these conditions.

![H1 observables under the same dynamics](../outputs/figures/h1-observables-v2.png)

Twelve initial states with 500 trajectories each were calculated. The explicitly Hermitian candidate $2\operatorname{Re}\langle O_+O\rangle$ was compatible with 94/94 fixed reference readings; the unweighted observable was compatible with 0/94. The candidate came from earlier initial-state checks, without fitting the Hamiltonian. It is not positive semidefinite, so approaching zero cannot replace a null-space norm criterion. This locates an observable-definition ambiguity, not the authors' actual measurement implementation.

## H2: a corrected numerical issue

For a fixed-charge Fock trajectory, $X=Q-\langle n_{\rm ph}\rangle$. A tiny positive photon tail can place the true expectation just left of an integer. We use

$$\lfloor Q-p\rfloor=Q-\lceil p\rceil\quad(Q\in\mathbb Z,\ p\ge0)$$

to avoid losing that tail in floating-point subtraction. All 5000 stored Fock trajectories agreed with a 400-digit Decimal check; 1616 differ from the old float-floor bins. Forty additional terminal-segment controls produced no bin changes. They constrain finite propagation sensitivity, not exact physical bin membership for arbitrarily small signals.

![H2 CDF comparison](../docs/comparisons/h2-cdf.png)

This necessary Fig. H2 comparison contains reference content excluded from the repository content license. Gray ranges reflect source-reading uncertainty, not author error bars. Red dashed curves use the old floating-point `floor` bins; blue curves use the corrected bins. Two fully readable curves are compatible with conservative two-sample bounds. Occlusion and sample size limit the other comparisons.

## H3: the normalization hypothesis

Let $w$ be the actual squared norm at the end of a no-jump segment, and $\rho$ a unit-trace reduced density matrix. Taking the spectrum of $w\rho$ gives

$$S_{\rm raw}=-\operatorname{Tr}(w\rho\ln(w\rho))=wS(\rho)-w\ln w.$$

We record $w$ from each trajectory and apply this identity before averaging. No reference-fitted weights, scales, offsets or seeds are used. **This raw quantity is scale-dependent and is not normalized von Neumann entropy.** A simple change of logarithm base cannot produce its positive offset.

![Physical and raw entropy from the same arrays](../outputs/figures/h3-generated.png)

![H3 fixed-reference comparison](../docs/comparisons/h3-normalization.png)

The second figure compares with fixed readings of Fig. H3 from the linked v1. Its reference content is excluded from the repository content license and does not supply independent generation data.

| Evidence | Result and scope |
|---|---|
| New original-parameter samples | 704: ten Fock initial states with 64 each, two GS initial states with 32 each |
| Parameter stress tests | 36 groups, 576 evaluations; random streams are paired across groups |
| Physical-entropy RMSE at 126 fixed reference points | 0.96745 nats |
| Raw-diagnostic RMSE | 0.07732 nats, about 92.0% residual reduction |
| Per-initial-state bootstrap | All 12 pointwise 95% improvement intervals have positive lower bounds |
| Separate small-system algorithms | 72 trajectories; maximum entropy/raw differences about $3.05\times10^{-12}$/$5.26\times10^{-12}$ |

The 92.0% figure is residual reduction, not paper completion. Separate intervals do not give simultaneous 95% coverage for all curves. They omit unknown author sampling error and some source-reading/numerical uncertainties.

Earlier 64-pair controls per statistics under cutoff $8\to10$ found maximum mean entropy changes of $6.59\times10^{-6}$ nats for fermions and $0.001745$ for bosons. Rare trajectory branch changes remain; this is not a strict cutoff-convergence certificate.

The planned larger study has 12 initial states, each with 512 trajectories at cutoff 8 and 128 paired trajectories at each of cutoffs 10 and 12: $12\times(512+128+128)=9216$ evaluations. Current inspection finds the worker stopped with no completion receipt and no recorded exit cause. It contributes no completed-sample or convergence claim. It is not classified as missing author information or proven insufficient hardware.

## Conclusions, boundaries and rerun

The independent implementation reproduces nonreciprocal operators, structured dark spaces and bounded dynamical checks, and corrects our own H2 binning error. H1 and H3 have specific diagnostic explanations, not full source-implementation identification. Larger-ensemble/cutoff tests, remaining figures, near-dark-state error analysis and some general propositions still need work. Author information that could remove ambiguity is listed separately from feasible calculations in [boundaries](../docs/BOUNDARIES.md). No author email was sent. The compared figures are theoretical/numerical, so laboratory access is not used as an exemption.

Install `code/requirements.txt`, then run:

```bash
python cases/2610.12348/code/scripts/run_reproduction.py --mode quick
python cases/2610.12348/code/scripts/run_reproduction.py --mode statics
python cases/2610.12348/code/scripts/run_reproduction.py --mode h3
```

Quick mode executes small null-space and trajectory controls. Static mode recomputes 23 original-size sectors. H3 mode repeats the completed 1280-evaluation diagnosis, historically about 24 minutes; it does not restart the unfinished 9216-evaluation study. New outputs use a new temporary directory. Verification reanalyzes frozen arrays; rendering redraws the generated figure. See [numerical methods](../docs/NUMERICAL_METHODS.md).
