# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| paper-exact theory | 9 | Printed parameters and formulas are evaluated directly. |
| paper-subset theory | 6 | The full ideal/theoretical component is reproduced inside a mixed experimental panel. |
| proxy-model partial | 3 | Runnable disclosed mechanism; indispensable calibration is absent. |
| missing-author-data | 17 | Experimental arrays are unavailable and were not digitized. |
| non-numeric excluded | 3 | Schematics or qualitative path drawings. |

All 18 implemented targets pass their declared internal scientific assertions. The `83.83/100` aggregate is lower than the exact targets because paper-subset and proxy-model targets are capped rather than being promoted by visual resemblance.

## Per-Target Consistency

| Targets | Paper items | Level | Evidence | Remaining difference |
| --- | --- | --- | --- | --- |
| T001-T002 | Main Fig. 2 theory | paper-exact | `target_checks.json`, v3 attestation | experimental points absent |
| T003-T004 | Main Fig. 3 theory counterparts | paper-subset | normalized wavefunction densities | camera samples absent |
| T005-T008 | Main Fig. 4 theory and Supp. S1 | paper-exact | analytic formulas and invariants | S1 common energy-zero discrepancy |
| T009-T011 | Supp. S2 | proxy-model partial | executable contact/quartic/unitary solvers | unpublished coupled-channel and drive calibration |
| T012-T015 | Supp. S3 theory | paper-subset | printed frequencies/coherence and exact two-level evolution | fitted amplitudes/phases and samples absent |
| T016-T018 | Supp. S4/S6 theory | paper-exact | closed uniform/Gaussian formulas | experimental histograms/samples absent |

## Paper Review Findings

Two source-level discrepancies are machine-recorded in `outputs/checks/paper_consistency_checks.json`:

1. Supplement Fig. S1 is shifted by approximately `-0.5 hbar*omega` relative to printed Eq. (S2), while all gaps and degeneracies agree. An implicit energy-zero convention remains a viable explanation.
2. Supplement Fig. S3(c) prints 21.4(1) Hz in the caption and 19.6(1) Hz in the body text. The available material cannot establish whether these denote the same fitted quantity.

Neither is promoted to `paper_error_candidate` without a fresh-context reviewer and a successful attempt to falsify alternative interpretations.
