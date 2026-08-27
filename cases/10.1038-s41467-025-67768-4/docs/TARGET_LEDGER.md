# Target Ledger

| Target | Paper item | Scientific object | Formula gate | Parameter match | Status | Planned outputs |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2(c), simulation component | Feedback/post-selection response under Pauli injection | FB001 | `paper_subset`: literal disclosed injection model, not the undisclosed plotted simulator | `failed_alignment` | exact 64-pattern check passes; high-r source curve does not |
| T002 | Main Fig. 3(c) and Supp. Fig. 4, simulation components | One-round repetition-code corrected/uncorrected expectations | REP001 | `paper_subset` (aggregate calibration only) | `feature_reproduced` | distance ordering and overlap reproduced |
| T003 | Main Fig. 3(e), simulation component | Multi-round distance-7 expectations | REP001 | `paper_subset` (aggregate calibration only) | `feature_reproduced` | M=1 close; M=2-4 too optimistic |
| T004 | Main Fig. 4(b,c) and Supp. Fig. 7(a,c,e), simulation components | Distance-3 surface-code logical Pauli channel | SURF001 | `paper_subset` (surface injection unit rate unstated) | `feature_reproduced` | exact 4^9 Pauli channel and Bloch circles generated |
| T005 | Supp. Fig. 8 | Complete versus injection-only ZNE | ZNE002, ZNE003, REP001 | `paper_subset` (aggregate calibration model) | `feature_reproduced` | registered SSIM 0.6695; suppression too large |
| T006 | Supp. Fig. 9 | Large-scale logical-memory ZNE | ZNE002, ZNE003, MEM001 | `paper_exact` for published analytic fit | `paper_exact` | registered SSIM 0.7005; analytic anchor exact |
| T007 | Supp. Table 3 | Approximately fixed cumulative-error schedule | REP001 | `paper_exact` table values; invariant is approximate | `table_exact_with_scientific_caveat` | registered SSIM 0.4764; cumulative spread 1.9005% |
| T008 | Supp. Fig. 2 | `[[72,12,6]]` qLDPC logical-error multiplicity distribution | benchmark definition missing | `unknown` | `blocked_publication_underspecified` | 0/1 item covered; circuit/noise/decoder/trial contract required |
| T009 | Supp. Fig. 10(b,c) | Circuit-level lattice-surgery logical-CNOT expectation and ZNE bias/overhead | ZNE002, ZNE003; circuit benchmark missing | `unknown` | `blocked_publication_underspecified` | 0/2 items covered; schedule/rounds/decoder/sampling contract required |

## Uncovered target ledger

- T008 / Supp. Fig. 2: **one uncovered item**. Direct cause:
  indispensable benchmark inputs are unavailable. Root cause: publication
  underspecification. Code assessment: not applicable until a full contract
  exists.
- T009 / Supp. Fig. 10(b,c): **two uncovered items**. Direct cause:
  indispensable benchmark inputs are unavailable. Root cause: publication
  underspecification. Code assessment: not applicable until a full contract
  exists. This is an information blocker before it is a compute blocker.
- Experimental-only panels and tables are outside the user's scientific
  simulation scope and are never reconstructed from pixels.
- The case remains partial because T001 fails source alignment, five targets
  lack paper-exact calibration metadata, and no fresh-context independent
  scientific review has yet been returned.
