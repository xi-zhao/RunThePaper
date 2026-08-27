# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 1 | Table I values match all printed paper values. |
| feature_match | 0 | Scientific or algorithmic feature matches at paper scale. |
| partial_match | 4 | Formula-derived features pass at reduced scale. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 7 | Six exact CUDA series plus one publication-defined IID class have terminal external evidence. |
| not_in_scope | 0 | Schematic, experimental, or external context. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2 main | partial_match | `target_checks.json`, `pixel_evidence.json` | Long-time finite-L plateau is near `2^8`, not `2^15`. | Explicit Hilbert-size and ensemble reduction. |
| T002 | Fig. 2 inset | partial_match | same frozen SFF data | Early-time fluctuation amplitudes differ. | Smaller Hilbert space and ensemble. |
| T003 | Fig. 3 left | partial_match | frozen Arnoldi residuals | Missing paper `t=10..15`; sparse `t=9`. | `4^t` transfer-vector scaling. |
| T004 | Fig. 3 right | partial_match | frozen Arnoldi residuals | Plateau/transition positions differ. | Generated `t=7`; paper `t=13`. |
| T005 | Table I | exact_match | 32 cell falsification checks | None in numerical cells. | Full formula-derived paper range executed. |
| T003-T10..T15 | Fig. 3 left atomic curves | externally_blocked | isolated smoke plus resource benchmark | Exact paper-time curves absent. | Local host lacks the declared CUDA lane; the `t=15` preflight is 72 GiB. |
| T006 | unrestricted IID law | externally_blocked | source trace plus resonant counterexample | Necessary non-resonance condition is not stated. | Publication underspecification; fresh paper-error review not claimed. |
