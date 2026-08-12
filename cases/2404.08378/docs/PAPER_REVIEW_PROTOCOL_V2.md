# Protocol-v2 Paper Review

## Current verdict boundary

- Reproducer-side scientific audit: passed for the declared independent models.
- Protocol-v2 paper assessment: `inconclusive`.
- `paper_error_candidate`: no.
- Independent-review gate: not satisfied.

The review bundles are frozen and ready, but no genuinely fresh-context reviewer result is fabricated. The current observations therefore remain hypotheses to falsify, not corrections to the paper.

## Observation 1 — brightness normalization

Using the printed rounded values `>5800 pairs/s`, approximately `13 dB` loss per photon and approximately `10 µW` pump gives `2.309021589e8 pairs/s/mW`. Dividing by the separately printed normalized brightness `7.7e6 pairs/s/nm/mW` implies `29.99 nm`, while the text elsewhere describes an approximately `50 nm` photon bandwidth.

Independent checks:

1. direct two-photon loss arithmetic with units;
2. reverse calculation from total to normalized brightness.

The observation remains `inconclusive` because the inputs are rounded/inequality values and the two bandwidth statements may use different definitions or operating conditions.

## Observation 2 — HOM width convention

For a 71.9 fs Gaussian width at 1562 nm, the named `0.441` time-bandwidth convention gives `49.92 nm`; a common HOM-autocorrelation convention gives `70.64 nm`. The paper does not state which mathematical width its fitted value denotes.

This is a parameter-definition ambiguity, not a demonstrated numerical error. The implementation reports both results and refuses to choose one by visual agreement.

## Falsification required before promotion

A fresh reviewer must independently inventory the paper, derive the formulas, inspect the frozen code/data, and try to explain each discrepancy through rounding, width definitions, spectral shapes and operating conditions. A paper-error candidate requires a source pinpoint, paper-exact inputs, two distinct strong independent checks, explicit falsification of plausible alternatives and a valid protocol-v2 submission.

Machine record: `outputs/checks/paper_review_protocol_v2.json`.
