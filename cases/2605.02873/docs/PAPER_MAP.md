# Paper Map

## Identity

- Paper ID: `2605.02873`
- Frozen version: `arXiv:2605.02873v1`
- Title: *Fixed-detector tilt--defocus sensing by upstream source coding in a time-reversed Young interferometer*
- Author: Jianming Wen
- Local primary inputs: `raw/paper.pdf`, `paper-source.tar.gz`
- Source bundle members read: `main.tex`, `supplement.tex`, `references.bib`,
  `figure1.png`, `figS1_width_scan.png`, and `00README.json`

## Reproduction Goal

Independently evaluate the paper's finite-width double-slit Fresnel model and
reproduce every frozen theory-numerical figure item:

- Main Fig. 1(a): normalized baseline TRY response;
- Main Fig. 1(b): normalized tilt and defocus response functions;
- Main Fig. 1(c): optimized and Gaussian-toy source codes;
- Main Fig. 1(d): optimized-versus-toy principal Fisher retention;
- Supplementary Fig. S1: defocus-to-tilt Fisher ratio versus slit width.

The source PNGs are reference-only. No source pixels, traced coordinates, or
digitized curves may enter generated data. Supplementary Table S1 is an exact
numeric reference for Fig. S1, but it is outside the figure-only execution
scope. The downstream-strategy discussion is mapped as paper context and is
not a numerical target because the paper supplies no downstream numerical
figure.

## Core Physical Model

The core object is the source-resolved fixed-detector response
\(R(y|\theta_t,\theta_f)=|E(y|\theta_t,\theta_f)|^2\). Its state is the
unperturbed Fresnel field \(E_0\), the weighted moments \(M_t,M_f\), the local
response directions \(g_t,g_f\), and the noise-metric score subspace. The
events that transform this object are:

1. choose the finite slit geometry and source coordinate;
2. evaluate the unperturbed field and aberration-weighted moments;
3. differentiate intensity to obtain \(g_t,g_f\);
4. orthogonalize the matched filters against the constant nuisance mode and
   each other;
5. project the full Fisher information into either the optimized or toy
   two-code subspace;
6. repeat the field calculation while varying slit width for Fig. S1.

The invariants are finite-aperture integration over both physical slits,
consistent \(y\)-quadrature in every inner product, a positive noise floor
\(B=0.02\max R_0\), and complete separation of generated numerics from source
image references.

## Paper Structure

| Source section | Role in the argument | Reproduction relevance |
| --- | --- | --- |
| Abstract | States fixed-detector two-parameter sensing and near-lossless compression | Claims CLM001-CLM004 |
| Introduction | Motivates tilt/focus tracking and positions TRY as upstream modal analysis | Context; no numerical target |
| Physical model | Defines the double slit, aberration phase, Fresnel field, moments, and exact response derivatives | EQC001-EQC003; Fig. 1(a,b) |
| Upstream source-coded receiver | Defines noise metric, raw/orthogonal codes, transfer matrix, covariance, and coded Fisher matrix | EQC004-EQC006; Fig. 1(c,d) |
| Numerical Example | Gives all main-figure physical parameters and reported Fisher/retention values | All Fig. 1 targets |
| Comparison with downstream strategies | Distinguishes direct intensity, ideal sorter, and full-field sensing | CLM005; mapped context |
| Conclusion | Restates finite-width, fringe-aware, near-lossless result | Claims summary |
| Supplement S1 | Independently derives the local intensity derivatives and narrow-slit limit | EQC002-EQC003 |
| Supplement S2 | Specifies finite-slit quadrature, noise-metric Gram--Schmidt, and positive-code implementation | EQC001, EQC004-EQC005 |
| Supplement S3 | Derives full/coded Fisher matrices, projector interpretation, and retention eigenvalues | EQC004, EQC006 |
| Supplement S4 | Defines the Gaussian toy basis and its physical-model Fisher retention | EQC007 |
| Supplement S5 | Derives finite-width defocus sensitivity and gives Table S1/Fig. S1 | EQC008 |
| Supplement S6 | Defines the limited downstream comparison | Context; no plotted numerical target |
| Supplement S7 | States novelty, scope, and limitations | Claim/context synthesis |

## Equation Inventory

| Card | Paper locations | Role | Gate basis |
| --- | --- | --- | --- |
| EQC001 | main Eq. 1; supplement S23 | Finite double-slit support | Exact interval decomposition |
| EQC002 | main Eqs. 2-4; supplement S1-S5 | Fresnel field and baseline response | Direct substitution at zero perturbation |
| EQC003 | main Eqs. 5-9; supplement S6-S19 | Weighted moments and exact local response | Differentiation under the integral and \(\mathrm{Re}(iz)=-\mathrm{Im}(z)\) |
| EQC004 | main Eqs. 11-12; supplement S25, S40-S41 | Noise metric and full Fisher matrix | Weighted-score Gram identity |
| EQC005 | main Eqs. 14-15; supplement S26-S33 | Matched filters and nuisance-orthogonal codes | Noise-metric Gram--Schmidt checks |
| EQC006 | main Eqs. 16-18; supplement S42-S51 | Coded Fisher matrix and principal retention | Projection/basis-invariance derivation |
| EQC007 | supplement S52-S70 | Gaussian toy-code construction | Same physical scores and same metric as optimized lane |
| EQC008 | supplement S71-S84 | Finite-width defocus mechanism and width-scan ratio | Point-slit limit plus independent width scan |

## Complete Figure, Panel, Visible-Series, and Table Inventory

| Item | Visible numerical content | Classification | Frozen execution item |
| --- | --- | --- | --- |
| Fig. 1(a) / FIG001A | One black line: normalized \(R_0(y)\) | `numeric_reproduction` / `theory_numerical` | T-FIG001A |
| Fig. 1(b) / FIG001B | Blue solid normalized \(g_t\); red dashed normalized \(g_f\) | `numeric_reproduction` / `theory_numerical` | T-FIG001B |
| Fig. 1(c) / FIG001C | Optimized \(w_t,w_f\) and toy \(h_1,h_2\), four visible lines | `numeric_reproduction` / `theory_numerical` | T-FIG001C |
| Fig. 1(d) / FIG001D | Toy/optimized retention for principal modes 1 and 2, four bars | `numeric_reproduction` / `theory_numerical` | T-FIG001D |
| Table S1 / TABLES001 | Five exact \((a,\rho)\) rows | Numeric reference table | Excluded from figure-only execution |
| Fig. S1 / FIGS001 | One line with five markers for \(\rho(a)=F_{ff}/F_{tt}\) | `numeric_reproduction` / `theory_numerical` | T-FIGS001 |

No experimental measurements, experimental images, or schematics occur in
the paper's figure inventory. All visible series above are theory-numerical.
Fig. 1(d) is present in the source asset and PDF although the Fig. 1 caption
enumerates only panels (a)-(c); the text and supplement supply its four
retention values.

## Claim-to-Target Map

| Claim | Statement | Formula dependencies | Target evidence |
| --- | --- | --- | --- |
| CLM001 | The finite-width Fresnel model produces the plotted source-resolved baseline and exact first-order tilt/defocus responses. | EQC001-EQC003 | T-FIG001A, T-FIG001B |
| CLM002 | Noise-metric nuisance orthogonalization produces fringe-locked optimized codes rather than smooth parity-only codes. | EQC003-EQC005 | T-FIG001C |
| CLM003 | Two optimized codes retain essentially all full-record Fisher information, with principal fractions \(0.99980958\) and \(1\). | EQC004-EQC006 | T-FIG001D |
| CLM004 | The Gaussian toy pair retains only about \(0.07988\) and \(0.53729\), showing that parity alone misses the physical score subspace. | EQC004, EQC006-EQC007 | T-FIG001C, T-FIG001D |
| CLM005 | Finite slit width makes the quadratic defocus mode first-order visible; \(\rho(a)\) rises from \(1.75\times10^{-5}\) at \(20\,\mu\mathrm m\) to \(1.56\) at \(250\,\mu\mathrm m\). | EQC001-EQC004, EQC008 | T-FIGS001 |
| CLM006 | TRY's advantage over an ideal downstream matched-mode sorter is architectural, while a single near-focus intensity plane can be rank-deficient for defocus. | Supplement S6 | Context only; no numerical figure |

## Paper Parameters

- \(\lambda=633\,\mathrm{nm}\)
- \(L_1=L_2=0.35\,\mathrm m\)
- \(d=500\,\mu\mathrm m\), \(W=d/2\)
- Main-figure slit width \(a=250\,\mu\mathrm m\)
- \(X_D=-L_2\lambda/(4d)=-110.775\,\mu\mathrm m\)
- \(y\in[-1.5,1.5]\,\mathrm{mm}\)
- \(B=0.02\max_y R_0(y)\)
- Fig. S1 widths \(a\in\{20,40,80,150,250\}\,\mu\mathrm m\)

## Assumptions and Boundaries

- Scalar monochromatic Fresnel propagation; overall constant Fresnel
  prefactors are omitted exactly as in the supplement.
- The local Fisher calculation treats the noise weight as parameter
  independent at the operating point.
- Signed codes are mathematical readout weights; their positive/negative
  physical decomposition does not alter the covariance because the supports
  are disjoint.
- Code normalization and sign are basis conventions. Observable Fisher
  retention is invariant under nonsingular rotations or rescalings.
- The source images are used only for visual/pixel comparison. Exact values
  quoted in prose and Table S1 are textual numeric references, not digitized
  image data.
