# Consistency Report

## Formula Consistency

- Status: `passed`
- Evidence: `outputs/checks/formula_verification.json`

The implemented equations match the paper's definitions for `chi_n`, regularized `chi_n^r`, typical/average susceptibility, rescaling, and the open-boundary Anderson Hamiltonian.

## Numerical Feature Consistency

- Status: `partial`
- Evidence: `outputs/checks/anderson_feature_checks.json`

Accepted local features:

- `largest_size_weak_enhancement_ratio = 4.14`, so weak-disorder sensitivity enhancement is visible.
- High-disorder gap ratio is lower than the moderate-disorder maximum.
- High-disorder IPR is much larger than moderate-disorder IPR.
- `chi_av^r / chi_typ^r` grows in the localized regime.

Not accepted locally:

- Strict monotonic `W_1^*` finite-size scaling.
- Quantitative `W_2^*≈16.5` peak extraction.
- Quantitative `W_3^*≈27.92` extraction.
- Spectral-function exponent `a≈0.52`.

## Similarity Consistency

- Current whole-paper score: `35.46/100`
- Level: `feature_not_accepted`
- Reason: ten targets have independent feature/paper-subset evidence, while
  seven unexecuted targets remain at zero and nine numerical figure items are
  compute-deferred with runnable paper-scale code.

The historical `60.41/100` described only the early local subset and must not
be used as a whole-paper score. The current lower score is not a regression in
the solver; it is the consequence of enumerating previously omitted figures.
