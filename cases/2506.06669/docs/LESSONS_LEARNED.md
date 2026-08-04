# Lessons Learned

## Case summary

- Paper: *Remote Entanglement Generation Via Enhanced Quantum State Transfer*.
- PaperID: `2506.06669`.
- Current status: numerical feature reproduction; fresh review pending.
- Main result: 10 theory targets computed in 25.09 s; 9 scientific assertions pass and Fig. S10 remains quantitatively partial.
- Main blockers: unpublished control transfer functions, unreported parameters/seeds and unavailable experimental observations.

## What worked

- Reading the full Supplement before coding exposed the Eq. (8) parity typo and prevented a visually plausible but physically inverted model.
- The zero/single-excitation reduction made the entire public theory workload sub-minute on CPU.
- Analytic identities, spectral checks, trace/positivity checks and reported fidelity anchors caught scientific errors before visual tuning.
- Freezing NPZ hashes before rendering kept source-aware layout work unable to alter physical parameters or arrays.
- Predeclared theory regions excluded experimental dots/bars from the main score without hiding them from full-figure diagnostics.

## Difficulties and reusable lessons

| Lesson | Why it matters | Future practice |
| --- | --- | --- |
| Internal paper consistency outranks one isolated printed symbol | A literal Eq. (8) implementation puts high energy on the wrong parity while still looking structured | triangulate equations against spectrum, captions and Supplement derivations before opening the numeric gate |
| A reported trend is not the same as a reported quantitative landmark | Fig. S10 has the right large-`m` direction but the wrong crossover | make landmark values essential physics assertions that cap pixel scores when failed |
| Missing hardware transfer functions are information blockers | More GPU time cannot infer the physical pulse mapping | classify these as missing parameters/external evidence, not time tradeoffs |
| Mixed experimental/theory figures need region contracts | Full-canvas scores are inflated by white space and penalize source-only experiment ink | freeze theory rectangles before scoring and keep full-crop metrics diagnostic |
| Targets need claim links | The first claim-ledger run found 10/10 targets orphaned from paper claims | define a small claim graph before final audit, then require every target to reference it |

## New Failure Modes

| Failure mode | Evidence | Detection |
| --- | --- | --- |
| onsite-parity source typo | QS002 / T001 | compare Hamiltonian trace/spectrum and low-energy site weights against every independent source statement |
| phase-gauge naming mismatch | QS004 / Bell singlet text | compare populations, density magnitudes and explicit local-gauge fidelity separately |
| reconstructed pulse moves a crossover | T010: `m=10` vs `m=6` | encode the published crossover as an essential assertion, not merely a plot shape |
| renderer tick formatting loses information | Fig. 4(f) diagnostic colorbar | add a render QA check for repeated numeric tick labels before publication polish |

## Efficient implementation

| Implementation | Evidence | Disposition |
| --- | --- | --- |
| spectral propagation after one Hermitian diagonalization | exact PST errors below `5e-16` | reusable pattern |
| vacuum + one-excitation Lindblad basis | 10 targets in 25.09 s; trace errors below `1.8e-15` | candidate generic helper |
| one NPZ per target with attested hashes | stable render inputs and simple resume boundary | keep as harness convention |
| case-specific pulse/gauge/parity policies | required for this paper's omissions/typos | keep case-local |

## Reusable Checks Or Tools

| Check or tool | What it proves | Reuse boundary |
| --- | --- | --- |
| source-blind runner access log | numerical generation did not read the paper PDF, extracted figures or reference pixels | reusable for every numerical reproduction |
| frozen NPZ manifest and SHA-256 verification | rendering cannot silently alter the computed arrays | reusable for every RenderContract workflow |
| analytic state-transfer identities | the reduced Hamiltonian, phases and time conventions are internally consistent | reusable for single-excitation spin-chain cases |
| essential-landmark score cap | a visually similar curve cannot hide a failed scientific crossover or anchor | reusable whenever the paper reports quantitative landmarks |
| predeclared theory-region masks | pixel comparison measures reproduced theory while excluding unavailable experiment-only ink | reusable for mixed theory/experiment panels |

## Harness backlog

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| high | require claim graph before review packaging | initial claim ledger reported 10 orphan targets | documented in this case |
| medium | add repeated-colorbar-label render QA | Fig. 4(f) labels round to zero despite valid array | proposed |
| medium | expose formal-pixel mean separately from diagnostic fallback targets | overall 68.73 vs admissible mean 73.81 | implemented in scorecard/report |

No harness code was changed in this case; the lessons remain evidence-backed proposals until reviewed for cross-paper generality.
