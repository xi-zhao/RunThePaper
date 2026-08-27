# Paper Map

## Identity And Source Bundle

- Paper: *Enhancing Nonreciprocity through Squeezing-Induced Symmetry Breaking*.
- arXiv: `2607.00718v2`.
- Publication: *Physical Review Letters* 136, 253602 (2026).
- DOI: `10.1103/kh36-7z76`.
- Author data: Zenodo `10.5281/zenodo.17231964`.
- Primary evidence: PDF, TeX, supplemental derivations, vector figures, and
  deposited MATLAB arrays.
- Secondary-only discovery source: Aurora blog post 1434.

## Full Figure Inventory

| Item | Scientific object | Decision | Target and final state |
| --- | --- | --- | --- |
| Fig. 1(a-b) | model and symmetry schematics | excluded context | no numerical target |
| Fig. 1(c) | effective NRC polar family | reproduce | T001 reproduced |
| Fig. 2(a-b) | battery energy dynamics and power | reproduce | T002A reproduced |
| Fig. 2(c) | steady energy enhancement | reproduce | T002C reproduced |
| Fig. 2(d) | ergotropy enhancement | reproduce | T002D reproduced |
| Fig. 3(a-d) | steady energy maps and cut | reproduce | T003 reproduced |
| Fig. 4(a-b) | optical transmission | reproduce | T004 partial; stale released data |
| Fig. S1(a-d) | detuned battery dynamics | reproduce and audit | TS01 partial; quantitative cutoff claim rejected |
| Fig. S2(a-c) | coupling derivative maps | reproduce | TS02 reproduced |
| Fig. S3(a-c) | energy-enhancement-versus-squeezing cuts | reproduce and audit | TS03 reproduced; published axis label corrected |
| Fig. S4(a-b) | passive-state energy | reproduce | TS04 reproduced |

There are 23 selected theory-numerical panels and no numerical tables.

## Claim Map

| Claim | Result | Main evidence |
| --- | --- | --- |
| CLM001 symmetry breaking enables squeezing enhancement | verified | T001 / EQ001 |
| CLM002 squeezing enhances stored energy and ergotropy | verified | Figure 2, S1, S3, S4 |
| CLM003 optimum coupling and squeezing thresholds | verified | Figure 3 and S2 |
| CLM004 unidirectional amplified transmission | verified | Figure 4 / EQ004 |
| CLM005 published S1 is quantitatively converged | rejected | exact Gaussian versus finite-cutoff audit |

## Source-Version Findings

The Zenodo record uses the earlier title *Conditional Enhancement of
Dissipation-Induced Nonreciprocity by Quantum Squeezing*. Its battery arrays
match the final formulas, but its transmission arrays peak near 10 while the
final formula and Figure 4 peak near 27.3. Those arrays remain provenance
evidence but are not treated as final-version ground truth.

The supplement also omits the finite-Hilbert cutoff used for Figure S1. Source
pixels are therefore retained only for post-generation diagnosis, not as a
numerical target.

Figure S3 has a separate source inconsistency: its label says
`E_i^ss/omega_b`, whereas the visible unit intercepts and all endpoint scales
follow `E_i^ss/E^ss`. The case retains both formula-derived observables and
renders the curve-consistent normalized one.
