# Paper Map

## Identity

- Paper ID: `1803.07128`
- Title: *Quantum Machine Learning in Feature Hilbert Spaces*
- Authors: Maria Schuld, Nathan Killoran
- Publication: Physical Review Letters 122, 040504 (2019)
- DOI: `10.1103/PhysRevLett.122.040504`
- Local sources: `raw/paper.pdf`, `paper-source/featuremap_variational_cvcircuit.tex`

## Scientific structure

| Part | Role | Reproduction consequence |
| --- | --- | --- |
| Sec. II | Feature maps, kernels, RKHS | Establishes the absolute-square real-kernel rule |
| Sec. III.A--B | Quantum feature circuits and implicit/explicit approaches | Figs. 1--3 are conceptual only |
| Sec. III.C | Phase-squeezing example | Defines every numerical target in Figs. 4--8 |
| Appendix A | Quantum-system RKHS | Analytic context, no numerical target |
| Appendices B-D | Universal linear independence and separability propositions | Independent analytic target T005; not collapsed into finite Fig. 6 target T003 |

## Atomic inventory

| Figure / claim | Atomic items | Eligible | Decision |
| --- | ---: | ---: | --- |
| 1, left/right | 2 | 0 | schematics excluded |
| 2 | 1 | 0 | schematic excluded |
| 3, implicit/explicit | 2 | 0 | workflow schematics excluded |
| 4, three surfaces | 3 | 3 | T001 |
| 5, six decision maps | 6 | 6 | T002 |
| 6, three epoch maps | 3 | 3 | T003 |
| 7(a-c) | 3 | 0 | schematics excluded; equations feed T004 |
| 8, probability map + loss/inset | 2 | 2 | T004 |
| Appendices B-D universal theorem | 1 analytic claim | 1 | T005, implemented and qualified |

There are no numerical tables. The complete display inventory contains 22
atomic items: 14 theoretical numerical items and 8 excluded schematics. One
additional independent analytic claim from Appendices B-D enters the
reproduction denominator. The resulting implementation coverage is **15/15**.

The old scope combined the finite Fig. 6 observation with the paper's universal
claim. T003 covers only the reconstructed finite dataset. T005 asks whether the
published propositions actually justify linear independence and arbitrary
binary separability for the stated input domain.

## Missing paper metadata

- Fig. 5: random seeds, noise, lower-row data generator, SVC regularization.
- Fig. 6: blob generator, random seed, Fock cutoff and exact training ordering.
- Fig. 8: random seed, data noise, initialization, learning-rate policy, L2 coefficient, displacement convention and Fock cutoff.

These omissions are parameter-state facts, not permission to infer arrays from source pixels.

## Independent analytic adjudication

- **T005, Appendices B-D:** the isolated theorem probe now covers periodic
  input identity, single-mode Vandermonde rank, multi-mode Fock/analytic-Gram
  parity, and arbitrary-label interpolation. The corrected finite-set result
  passes. The missing modulo-`2*pi` domain condition, false Proposition 1
  wording and invalid pairwise-overlap proof step are recorded as
  source-discrepancy candidates pending fresh-context review.
