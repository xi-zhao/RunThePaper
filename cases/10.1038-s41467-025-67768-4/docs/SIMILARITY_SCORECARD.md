# Similarity Scorecard

## Case Score

- Overall score: **72.25/100**.
- Similarity level: **numerical feature reproduction**.
- Historical scored target contracts: 9.
- Explicit uncovered target contracts: 2 (T008 and T009), representing 3
  separately counted items.
- Whole-paper item coverage: **13/16 = 81.25%**.
- Covered-item mean fidelity: **72.01/100**.
- Whole-paper reproduction degree: **58.51/100**.
- Generated-data provenance: independent numerics for all 9.
- Formula gates: verified for all 9.
- Essential physics failures: T001 only.

The score measures scientific agreement and registered rendering fidelity. It
is not a lifecycle state and cannot make the case complete.

## Scoring Model

Each item receives up to 50 points for physical-feature agreement, 35 for
numeric closeness, and 15 for paper-scope coverage. For the three pure
numerical assets, registered SSIM directly constrains numeric closeness. Mixed
experimental/simulation panels have `pixel_status=not_applicable`; they are
scored from independent formula checks and source-vs-feature inspection.

## Figure Scores

| Item | Weight | Feature /50 | Numeric /35 | Scope /15 | Final score |
| --- | ---: | ---: | ---: | ---: | ---: |
| T001 Main Fig. 2(c) | 1.2 | 28.0 | 12.0 | 15.0 | **55.0** |
| T002-MAIN Main Fig. 3(c) | 1.5 | 45.0 | 24.0 | 15.0 | **70.0** (source-reference cap) |
| T002-SUPP Supp. Fig. 4 | 0.6 | 44.0 | 23.0 | 15.0 | **70.0** (source-reference cap) |
| T003 Main Fig. 3(e) | 1.2 | 42.0 | 21.0 | 15.0 | **70.0** (source-reference cap) |
| T004-MAIN Main Fig. 4 | 1.5 | 47.0 | 27.0 | 15.0 | **70.0** (source-reference cap) |
| T004-SUPP Supp. Fig. 7 | 0.8 | 47.0 | 26.0 | 15.0 | **70.0** (source-reference cap) |
| T005 Supp. Fig. 8 | 1.2 | 45.0 | 23.43 | 15.0 | **80.0** (visual-contract cap) |
| T006 Supp. Fig. 9 | 1.2 | 49.0 | 24.52 | 15.0 | **88.52** |
| T007 Supp. Table 3 | 0.6 | 48.0 | 16.67 | 15.0 | **79.67** |
| T008 Supp. Fig. 2 | 0.0 | 0.0 | 0.0 | 0.0 | **uncovered; excluded from historical aggregate** |
| T009 Supp. Fig. 10(b,c) | 0.0 | 0.0 | 0.0 | 0.0 | **2 items uncovered; excluded from historical aggregate** |

## Evaluation Metadata

| Item | Stage | Parameter match | Pixel status | Main limitation |
| --- | --- | --- | --- | --- |
| T001 | exploratory | paper_subset | not_applicable | source/model mismatch |
| T002-MAIN | exploratory | paper_subset | not_applicable | missing calibration |
| T002-SUPP | exploratory | paper_subset | not_applicable | missing calibration/random instances |
| T003 | exploratory | paper_subset | not_applicable | missing round-level noise map |
| T004-MAIN | exploratory | paper_subset | not_applicable | surface injection rate unstated |
| T004-SUPP | exploratory | paper_subset | not_applicable | surface calibration unstated |
| T005 | exploratory | paper_subset | scored, 0.6695 | aggregate proxy |
| T006 | final_reproduction | paper_exact | scored, 0.7005 | no scientific gap found |
| T007 | final_reproduction | paper_exact table | scored, 0.4764 | invariant only approximate |
| T008 | exploratory | unknown | not_comparable | qLDPC benchmark contract unpublished; 0/1 item covered |
| T009 | exploratory | unknown | not_comparable | lattice-surgery benchmark contract unpublished; 0/2 items covered |

## Why The Score Is Not Higher

- Six scored items have only original-figure visual references, so the
  scorecard caps them at 70 without digitized/author/benchmark numerical data.
- Five central simulation targets lack gate-level or surface-code calibration
  parameters.
- T001 fails an essential source-alignment assertion.
- T007's low registered SSIM reflects font/layout residual, while its scientific
  caveat is the non-exact total-error schedule.
- T008 and T009 are not low-scoring approximations: their three items are
  explicitly uncovered because the publication does not provide enough input
  to define the calculations. No code fault has been established, and more
  compute alone cannot close them.

The authoritative machine-readable record is
`outputs/checks/similarity_scorecard.json`.
