# Target ledger

本 case 把“论文中的科学对象”作为目标，而不是把一整张图或一整段正文压成一个模糊任务。
数值图、数值表和正文定量主张共形成 29 个可独立检查的 target；Fig. 2 仅为示意图，
但其可计算的楔形角度另由 T020 覆盖。

| Target | Paper item | Scientific object | Formula/method basis | Generated evidence | Status |
|---|---|---|---|---|---|
| T001 | Main Fig. 1 | massless real spectrum for \(1<N\le5\) | EQ001–EQ004; contour FD + Riccati | `outputs/data/fig1_massless_spectrum.csv` | reproduced; fresh review pending |
| T002 | Table I, N=3 | exact and WKB levels \(n=0..4\) | EQ001–EQ003 | `outputs/data/table_i_exact_wkb.csv` | reproduced; fresh review pending |
| T003 | Table I, N=4 | exact and WKB levels \(n=0..3\) | EQ001–EQ003 | `outputs/data/table_i_exact_wkb.csv` | reproduced; fresh review pending |
| T004 | Table II | exact and Eq. (11) ground-state energies at seven \(\epsilon\) values | EQ001, EQ004, EQ005; Riccati + contour FD + asymptotic solve | `outputs/data/table_ii_near_one.csv` | reproduced; discrepancy requires refreshed review |
| T005 | Main Fig. 3 | \(m^2=3/16\) spectrum | EQ001, EQ006; contour FD + exact N=1 anchor | `outputs/data/fig3_massive_spectrum.csv` | reproduced; fresh review pending |
| T006 | Main Fig. 3 | \(m^2=5/16\) spectrum | EQ001, EQ006; contour FD + exact N=1 anchor | `outputs/data/fig3_massive_spectrum.csv` | reproduced; fresh review pending |
| T007 | Main Fig. 3 | \(m^2=7/16\) spectrum | EQ001, EQ006; contour FD + exact N=1 anchor | `outputs/data/fig3_massive_spectrum.csv` | reproduced; fresh review pending |
| T008 | Eq. (5) | complete complex-WKB spectrum and validity probes | EQ002, EQ003 | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T009 | paragraph after Table I | Hermitian \(|x|^N\) spectrum and square-well limit | EQ010; independent Hermitian FD | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T010 | Eqs. (8)–(11) | near-one \(( -\ln\epsilon)^{2/3}\) scaling | EQ005, EQ011; log-domain roots and fit | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T011 | opening paragraph | Bessis cubic has real positive low spectrum | EQ001; contour FD | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T012 | opening paragraph | PT/non-PT cubic-plus-linear contrast | EQ001; independent low-spectrum solve | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T013 | oscillator paragraph | \(E_n=2n+1\) | EQ007; analytic completion of square | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T014 | oscillator paragraph | imaginary shift \(E_n=2n+5/4\) | EQ007 | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T015 | oscillator paragraph | real shift \(E_n=2n+3/4\) | EQ007 | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T016 | oscillator paragraph | combined shift \(E_n=2n+1+i/2\) | EQ007 | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T017 | massless-phase paragraph | real-positive phase for \(N\ge2\) and large-N divergence | EQ001, EQ003; FD + WKB | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T018 | Fig. 1 caption | broken phase and first printed threshold | EQ001, EQ002; independent discriminant root at four grid resolutions, without feeding the printed threshold to the solver | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T019 | Fig. 1 caption / Eqs. (6)–(11) | \(N\to1^+\) divergence and no real state at \(N=1\) | EQ004, EQ005, EQ008 | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T020 | Eq. (3) | anti-Stokes centers, openings and limiting angles | EQ002; exact evaluation | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T021 | text after Eq. (3) | isospectrality under admissible contour deformation | EQ001, EQ002; three-contour cross-check | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T022 | Eq. (4) | turning-point equation and half-plane transition | EQ003; exact substitution | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T023 | numerical-method paragraph | agreement of independent differential and matrix solvers | EQ001, EQ004; same-\(N\) Riccati vs real-axis FD at four near-critical exponents | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T024 | text around Eqs. (4)–(5) | WKB contour fails below \(N=2\) | EQ002, EQ003; explicit turning-point segment / principal-branch-cut intersection | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T025 | Eqs. (6)–(7) | exact Airy matching obstruction at \(N=1\) | EQ008; Wronskian identity + probes | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T026 | near-\(N=2\) paragraph | adjacent-level coalescence and high-level-first ordering | EQ012; two-level harmonic-basis reduction | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T027 | Eq. (12) | finite classical period for \(N\ge2\) | EQ009; log-gamma evaluation | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T028 | text after Eq. (12) | subcritical spiral and quantum-merger correspondence | EQ009, EQ012; unwrapped Riemann-sheet Hamiltonian orbit, turning-point events, and level-by-level merger/event ordering | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |
| T029 | massive-case paragraph | exact \(N=0,1,2\) anchors and pairwise reality changes | EQ001, EQ006, EQ013; analytic + FD | `outputs/data/quantitative_claim_checks.json` | reproduced; fresh review pending |

All 29 targets were executed by isolated run
`physics-9712001-paper-exact-v6`. The numerical runner had no access to raw paper
assets or original figures. Reference figures remain confined to post-freeze
render comparison.
