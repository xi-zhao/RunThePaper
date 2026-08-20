# Consistency Report

## Result

All seven numerical targets have independent formula-based implementations. The
attested reduced campaign passes 12/12 scientific checks. Main Fig. 2(a) is
paper-exact; the remaining exact-diagonalization targets are reduced-scale and
must not be described as paper-exact.

| Target | Level | Direct cause of remaining gap | Root cause | Code fault assessment |
| --- | --- | --- | --- | --- |
| T001 | feature match | paper-scale run not executed | confirmed compute-capacity shortfall | not found after unit, invariant, attestation and benchmark checks |
| T002 | feature match | paper-scale run not executed | confirmed compute-capacity shortfall | not found after checks |
| T003 | analytic exact match | none | none | not applicable |
| T004 | feature match | paper-scale run not executed | confirmed compute-capacity shortfall | not found after checks |
| T005 | feature match | printed spectral-function definition is not unique | confirmed publication underspecification | not found after unit, invariant and source-trace checks |
| T006 | feature match | printed drive durations are mutually incompatible | confirmed publication underspecification | not found after unit, invariant and source-trace checks |
| T007 | feature match | paper-scale run not executed | confirmed compute-capacity shortfall | not found after checks |

The source ambiguities are **not** classified as paper errors. They remain
questions for fresh-context protocol-v2 review. The initial v3 isolation failure
was a run-contract defect involving `MPLCONFIGDIR`; v4 fixed the contract and
ran with zero forbidden accesses. It was not a scientific-code failure.

## Published-form checks

- Eq. (7), read literally without an absolute square, produces a complex
  quantity (imaginary RMS `0.042894`) and cannot directly be the positive
  plotted spectral density. The implemented positive Lehmann form satisfies
  the half sum rule to `1.22e-15`.
- Eq. (8), the numerical paragraph and the Fig. 2 caption do not define one
  compatible tuple `(T,T1,T2)`. The primary run uses the explicit
  `T1=1,T2=pi/2` branch and records that assumption.
- The Fig. 2(d) reduced result uses `L=8`, so the maximum separation is even;
  the paper uses `L=10`, where it is odd. The resulting sign presentation is a
  finite-size parity effect, not a render correction and not a code fix.

Machine-readable evidence is in
`outputs/checks/similarity_scorecard.json` and
`outputs/checks/science_checks.json`.
