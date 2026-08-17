# Paper Review Protocol V2

## Review Question

Can a fresh reviewer, without access to the reproduction conversation or its narrative conclusions, independently confirm or falsify the paper's numerical scope, printed formulas, parameters, generated data and the claim that T001-T003 reproduce the paper?

## Two-Phase Boundary

1. Phase 1 reads only the paper inventory bundle and commits every numerical figure, subfigure, table and quantitative claim before seeing implementation evidence.
2. Phase 2 reads the frozen inventory plus the narrative-free falsification bundle containing formula cards, code, configs, frozen generated data, tests and run attestation.
3. The reviewer must try to disprove every target through at least one limiting case, invariant, alternative derivation or independent numerical method.
4. Original reproduction-session explanations are excluded from both bundles.

## Paper-Error Threshold

A discrepancy may be promoted only when the reviewer supplies a source pinpoint, at least two distinct strong checks, an explicit falsification attempt, and evidence excluding reproduction-code fault, parameter ambiguity and compute ambiguity. This case currently emits no paper-error candidate.

## Known Open Boundary

The Sec. VII `n=11,17` simulation statement is inventoried as publication-underspecified. A reviewer should test whether the paper or its archived source actually identifies the code generators/search definition anywhere; absence of those inputs is not itself a claim that the paper's qualitative statement is false.
