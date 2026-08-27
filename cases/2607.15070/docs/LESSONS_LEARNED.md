# Lessons Learned

## Case Summary

- Paper: spatially varying effective-mass Casimir energy
- Paper ID: `2607.15070`
- Final status: complete numerical and pixel reproduction
- Main targets: paper Figs. 2(a,b) and 3
- Main blockers: none
- Scientific caveat: three independently confirmed printed formula errors

## What Worked

- Starting from the radial operator exposed a factor-two issue before plotting.
- A log-proper-time variable and Poisson-resummed plate sum made the full paper
  grids cheap and stable.
- An independently derived Bessel representation gave a strong numerical oracle
  without reading values from paper images.
- Separating data, checks, rendering, and comparison prevented style tuning
  from changing numerical evidence.

## What Was Difficult

- The paper's plotted integrals are internally computable even though the
  upstream spectrum is inconsistent; the report must preserve that distinction.
- The correction term is singular as \(\alpha_0\to0^+\), so the visible axis
  begins at zero while numerical sampling begins at 0.1.
- Pixel matching was driven mainly by canvas margins, label placement, and ink
  density after scientific curves had already passed.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Check the lowest eigenstate directly | catches normalization factors hidden by special-function notation | substitute a simple analytic state before authorizing numerics |
| Derive a second representation | separates quadrature bugs from paper-formula bugs | seek Poisson/Bessel/spectral alternatives for improper sums |
| Treat displayed integrals as conditional objects when necessary | enables honest reproduction without endorsing flawed derivations | state the conditional boundary in claims and reports |
| Tune pixels only after frozen data checks | prevents visual optimization from corrupting science | make style-only repairs explicit and re-run pixel contracts |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Trusting printed asymptotics | Eqs. (31) and (36) had wrong functional forms | derive limiting powers and exponents independently |
| Inferring values from source curves | vector figures were available but had no tables | use images only for layout and registered comparison |
| Overflow in hyperbolic denominators | large \(\alpha_0\tau^2\) | use scaled exponential algebra |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Guard every numerical phase by target and stage | multi-target cases | T001/T002 have isolated output sets |
| Preserve row-level data provenance | every final figure | 3,164 CSV rows marked `independent_numerics` |
| Record formula discrepancies as accepted assertions | plots can pass despite paper errors | T001 scientific check contains three diagnostics |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Upstream spectrum and downstream plotted formula disagree | paper Eqs. (11), (25), (27) | carry a formula dependency graph and conditional-verification label |
| Correct qualitative asymptotic claim with wrong printed exponent | paper Eq. (31) | compare actual values with both printed and derived leading terms |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| log-\(\tau\) quadrature with Poisson-resummed Gaussian sum | stable for many proper-time Casimir integrals | keep case-local until a second paper confirms the interface |
| analytic-state eigenvalue check | inexpensive symbolic/numeric consistency test | formula-card checklist |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| vector-valued adaptive quadrature over all \(\alpha_0\) values | complete data generation took about 0.05 s per target | integration kernel may generalize; physics weights remain case-local |
| positive Bessel sums used only at diagnostic points | relative errors \(2.1\times10^{-11}\) or better | keep case-local oracle |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| low | allow generated phase records to require a top-level status | audit warned on otherwise valid data/render records | resolved case-locally |
| low | add conditional-formula wording to report template | reproduced integrals can coexist with an upstream derivation error | recorded here; frozen Harness intentionally unchanged |

## Prompt Or Workflow Changes

No Harness or prompt file was changed because this Trial freezes those
boundaries. The case demonstrates that “derive, generate, check, render,
compare” is a sufficient deterministic loop for this problem class.
