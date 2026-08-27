# Paper Map

## Identity

- Paper ID: `2511.11394`
- Title: *Relaxation toward an Ideal Chern Band through Coupling to a Markovian Bath*
- Authors: Bruno Mera and Tomoki Ozawa
- Publication: *Physical Review Letters* **137**, 046601 (2026)
- Sources: `raw/paper.pdf`, `paper-source/arxiv_v2.tex`, and
  `raw/official/sm.pdf`

## Scientific Question

The paper asks whether a Markovian-bath-induced Hartree–Fock flow can reduce
the Dirichlet energy of a Chern band toward its topological lower bound,
\(E_D\geq\pi|C|\), and whether that mechanism survives beyond the
small-momentum approximation.

The executable case follows the requested derivation-first order:

1. derive the projector flow and two-band Landau–Lifshitz–Gilbert equation;
2. derive the exact extended-Hubbard convolution and its
   \(1/\pi^2\) normalization;
3. derive the small-\(q\) coupling \(\lambda_D\);
4. define the metric, Berry curvature, Dirichlet energy, and finite-mesh
   Chern diagnostics;
5. only then integrate the dynamics and compare figures.

## Core Model

For \(P=(I+\mathbf n\cdot\boldsymbol\sigma)/2\),
\[
\partial_t\mathbf n
=-\mathbf n\times\mathbf h
+\gamma\,\mathbf n\times(\mathbf n\times\mathbf h).
\]
The exact extended-Hubbard field is
\[
(2\pi)^2\mathbf h(\mathbf k)
=2\lambda_T\mathbf d(\mathbf k)
-\frac1{\pi^2}\int_{\rm BZ}d^2q\,
v(\mathbf q)\mathbf n(\mathbf k-\mathbf q),
\]
with \(v(\mathbf q)=U+2V(\cos q_x+\cos q_y)\). Its convolution reduces
exactly to five Fourier moments. The comparison flow replaces it by
\(-\lambda_D\nabla^2\mathbf n\), where
\[
\lambda_D=
\frac1{4\pi}\left[(U+4V)\frac{Q^4}{4}
-V\frac{Q^6}{6}\right].
\]
For the paper parameters this gives
\(\lambda_D=1.1828772769\ldots\), matching the reported \(1.183\).

## Paper Structure and Executable Role

| Section | Role in the argument | Executable consequence |
| --- | --- | --- |
| Markov-bath derivation | Produces a metriplectic projector flow | Formula cards EQC006–EQC009 |
| Small-\(q\) reduction | Turns interaction energy into Dirichlet energy | Target T001 |
| Massive Dirac model | Supplies \(\mathbf d(\mathbf k)\), \(M=-0.5\), and \(C=1\) | All paper targets |
| Exact extended Hubbard | Tests the mechanism without the expansion | Targets T002–T004 |
| Bubbling discussion | Explains the finite-mesh topological transition | Midpoint-grid and convergence checks |

## Numerical Figure Inventory

| Paper item | Executable target | Result |
| --- | --- | --- |
| Main Fig. 1 | T001 — small-\(q\) energy and topology | partial: mechanism matches, normalization/rate do not |
| Main Fig. 2 | T002 — exact versus small-\(q\) energy flow | reproduced at numerical-feature level |
| Main Fig. 3, initial | T003 — local trace-condition deviation | reproduced at numerical-feature level |
| Main Fig. 3, exact at \(T_{\rm short}\) | T003 — local trace-condition deviation | reproduced at numerical-feature level |
| Main Fig. 3, small-\(q\) at \(T_{\rm short}\) | T003 — local trace-condition deviation | reproduced at numerical-feature level |
| Supplemental Fig. 1, initial | T001 — small-\(q\) trace deviation | partial for the same Fig. 1 reason |
| Supplemental Fig. 1, final | T001 — small-\(q\) trace deviation | partial for the same Fig. 1 reason |
| Supplemental Fig. 2, initial | T001 — small-\(q\) metric/curvature | partial for the same Fig. 1 reason |
| Supplemental Fig. 2, final | T001 — small-\(q\) metric/curvature | partial for the same Fig. 1 reason |
| Supplemental Fig. 3, energy | T002 — exact/small-\(q\) energy | reproduced |
| Supplemental Fig. 3, Chern number | T002 — exact/small-\(q\) numerical Chern | reproduced |
| Supplemental Fig. 4, initial | T003 — metric/curvature | reproduced |
| Supplemental Fig. 4, exact at \(T_{\rm short}\) | T003 — metric/curvature | reproduced |
| Supplemental Fig. 4, small-\(q\) at \(T_{\rm short}\) | T003 — metric/curvature | reproduced |
| Supplemental Fig. 5, exact metric/curvature | T002 — long-time geometry | reproduced |
| Supplemental Fig. 5, exact curvature | T002 — long-time topology | reproduced |
| Supplemental Fig. 5, small-\(q\) metric/curvature | T002 — long-time geometry | reproduced |
| Supplemental Fig. 6, fixed-\(U\) energy | T004 — interaction sweep | reproduced at trend level |
| Supplemental Fig. 6, fixed-\(U\) Chern number | T004 — interaction sweep | reproduced at trend level |
| Supplemental Fig. 6, fixed-\(V\) energy | T004 — interaction sweep | reproduced at trend level |
| Supplemental Fig. 6, fixed-\(V\) Chern number | T004 — interaction sweep | reproduced at trend level |

## Key Reconstruction Decision

The exact dynamics forms a bubble at \((\pi,\pi)\). A node-centered grid
samples that point exactly and symmetry-pins its spin, preventing the
finite-mesh transition. A half-cell-shifted periodic grid removes this
artifact. With \(N=141\), spectral derivatives, and \(\Delta t=0.01\),
\[
E_D(4.32)=3.145154,\qquad C_{\rm num}(4.32)=0.996491,
\]
and the localized metric/curvature peak is of order \(10^2\), jointly
matching the supplement. \(N=101,141,181\) checks establish that this is a
resolution-controlled reconstruction rather than a fitted scale factor.

## Remaining Source Ambiguity

Main Fig. 1 is internally inconsistent with the printed definitions:

- its displayed \(\lambda_D E_D\) curve and lower bound are larger by a
  factor of about four;
- its \(t=15\) small-\(q\) state is much closer to ideality than the same
  printed flow and the paper's own Fig. 2 small-\(q\) trajectory imply;
- the grid, grid origin, derivative stencil, time step, and integrator are
  not reported.

The case records this as a source-level numerical-convention gap and does not
fit an arbitrary time or energy factor.
