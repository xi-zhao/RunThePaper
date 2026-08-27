# Similarity Scorecard

## Case score

- Overall: **84.29/100**
- Level: **numerical feature reproduction**
- Coverage: **21/21 numerical axes**
- Provenance: **4/4 targets use independent numerics; source pixels are
  terminal evaluation only**

The 35-point numerical-closeness component is tied directly to full-canvas
pixel SSIM, as requested. Feature correctness is checked first, so a visually
similar but scientifically failed output cannot earn the feature band.

| Target | Weight | Feature `/50` | Pixel closeness `/35` | Scope `/15` | Final |
| --- | ---: | ---: | ---: | ---: | ---: |
| T001 Main Fig. 1 | 7 | 50 | 28.21 (`SSIM=0.805955`) | 15 | 90 |
| T002 Main Fig. 3 | 5 | 44 | 29.49 (`SSIM=0.842656`) | 15 | 80 cap |
| T003 Supp. Fig. S1 | 7 | 45 | 28.46 (`SSIM=0.813283`) | 15 | 80 cap |
| T004 Supp. Fig. S2 | 2 | 50 | 28.21 (`SSIM=0.806125`) | 15 | 90 |

## Why the two caps remain

- T002 uses the paper's reported physical coefficients, but missing transient
  settings force a stationary neutral-growth reconstruction. Its score is
  capped at the visual-feature-contract level even though its SSIM is highest.
- T003 uses exact paper parameters for the eigensystems, but the source never
  defines how edge states were counted. Its fixed boundary-weight classifier is
  therefore exploratory evidence.

The full normalized record, component reasons, physics assertions, panel
ledger, and evidence paths are in
`outputs/checks/similarity_scorecard.json`.
