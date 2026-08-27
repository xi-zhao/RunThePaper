# Figure Classification

`figure_coverage.json` is the machine-readable authority. It enumerates all 117
display items in the 24-page paper, down to individual curves when theory and
experiment share a panel. This document summarizes that atomic inventory.

## Classification rule

- `theory_numerical`: formula/model-defined curve or panel; enters coverage.
- `experimental_measurement`: requires new device observations; enumerated but
  excluded from the computational denominator.
- `schematic_context`: qualitative diagram; excluded.
- `source_parameter`: measured input table; audited as provenance, not output.
- `analytic_claim`: independently falsifiable no-display claim; enters coverage.

A theoretical counterpart that PRAgent chose to calculate does not turn a
source experimental panel into a reproduced display item. Such calculations
remain useful diagnostic evidence but do not inflate paper coverage.

## Exact whole-paper counts

| Class | Count | Eligible? |
| --- | ---: | --- |
| theory numerical display item | 56 | yes |
| experimental measurement item | 53 | no |
| schematic | 7 | no |
| source-parameter table | 1 | no |
| no-display analytic claim | 4 | yes |
| **eligible total** | **60** | denominator |

## Grouped display classification

| Paper group | Atomic decomposition | Reproduction decision |
| --- | --- | --- |
| Main Fig. 1(a-d) | 4 schematics | excluded; T001 is auxiliary diagnostic evidence |
| Main Fig. 2(a-f) | 6 measured panels | excluded; no source theory curves are present |
| Main Fig. 3(a-b) | 10 theory curves + 10 measured series | theory curves targeted by T004; dots excluded |
| Main Fig. 3(c-d) | 2 measured tomography panels | excluded; ideal dashed support is not a separate numerical panel |
| Main Fig. 3(e) | 3 measured noise series | excluded; supplemental simulations are counted separately |
| Main Fig. 4(a-c) | 3 measured population maps | excluded |
| Main Fig. 4(d) | 4 theory curves + 4 measured series | theory curves targeted by T007; dots excluded |
| Main Fig. 4(e) | measured tomography | excluded |
| Main Fig. 4(f) | ideal W-state density matrix | targeted by T007 |
| Supp. Fig. S1(a-b) | 2 schematics | excluded |
| Supp. Table S1 | measured device parameters | excluded input; consumers recorded |
| Supp. Figs. S2, S3(a-h) | 9 simulated panels | targeted by T002 |
| Supp. Fig. S4(a) | calibration flowchart | excluded |
| Supp. Figs. S4(b-c), S5(a-c), S6(a-c) | 8 hardware-calibration items | excluded measurements |
| Supp. Fig. S7(a-c) | 9 measured series | excluded |
| Supp. Fig. S7(d-f) | 12 theory series | targeted by T008 |
| Supp. Fig. S8(a-c) | 7 measured series | excluded |
| Supp. Fig. S8(d-f) | 12 theory series | targeted by T006 |
| Supp. Fig. S9(a-d) | 1 fidelity curve + 3 density matrices | targeted by T009 |
| Supp. Fig. S10(a) | 1 fidelity curve | targeted by D001; uncovered |
| Supp. Fig. S10(b-d) | 3 population maps | targeted by T010; covered |

## No-display claims

| Claim | Target | Coverage |
| --- | --- | --- |
| Main Eq. (1) Hermiticity as printed | C001 | uncovered |
| zig-zag PST for every allowed integer `m` | C002 | uncovered |
| large-`m` reduction to the stated half-chain | C003 | uncovered |
| FST endpoint Bell state under a declared phase gauge | C004 | uncovered |

Current paper-level coverage is **55/60 = 91.67%**. The 53 experimental
measurements are not part of the missing five; they are explicit noncomputable
reference items under this reproduction contract.
