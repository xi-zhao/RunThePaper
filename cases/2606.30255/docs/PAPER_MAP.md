# Paper Map

## Identity

- Paper ID: `2606.30255`
- Title: *Photonic Violation of Wigner's Inequality*
- Authors: Maximilian Rottensteiner, Dorian Schiffer, Tobias Pausch, Alois Mair, Anton Zeilinger
- Frozen source: arXiv `2606.30255v1`, 29 June 2026
- Local PDF: `raw/paper.pdf` (10 pages)
- Local source: `paper-source.tar.gz`
- Frozen author data: `raw/experimental-data.zip`

## Reproduction Goal

The paper is an experimental/data paper, but its reader-visible numerical
figures contain independently generable quantum-model curves. The frozen scope
is the theory lane of Figure 3, Figure 4, and both panels of Figure 5:

- the three modelled joint probabilities
  \(P_{++}^{\hat a\hat b'}\), \(P_{++}^{\hat b\hat c'}\), and
  \(P_{++}^{\hat a\hat c'}\);
- the calculated Wigner value
  \(\mathcal W=P_{++}^{\hat a\hat b'}+P_{++}^{\hat b\hat c'}
  -P_{++}^{\hat a\hat c'}\);
- the visible ideal-violation reference line.

That is five visible theory sequences per target and twenty theory sequences
overall. They are generated only from the reported state, density matrix,
measurement projectors, scan geometry, and fitted parameters.

Experimental markers, error bars, coincidence counts, optical schematics,
measurement-basis drawings, and Table I remain reference/context evidence.
They never feed a generated theory dataset.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Abstract and I. Introduction | Main motivation | Positions Wigner's inequality as a pedagogical Bell-type test and announces open raw data. |
| II. Motivation | Conceptual assumptions | Defines realism, locality, and local hidden variables. |
| III. Wigner's Inequality | Classical set-theoretic claim | Eqs. (1)-(6) derive \(\mathcal W\geq0\) under perfect anti-correlation. |
| III.A Quantum mechanical probabilities | Core theory | Eqs. (7)-(10) define polarization projectors, Born probabilities, and the quantum Wigner value. |
| III.B Extremal analysis | Analytic checks | Eqs. (12)-(13) give the symmetric \(-1/8\) and asymmetric \(1/4-\sqrt3/4\) extrema. |
| IV. Experimental Setup | Experimental context | Describes the Sagnac source, state in Eq. (18), and coincidence apparatus. |
| IV.A Data Analysis | Reference-data method | Eq. (19) normalizes four coincidence outcomes into a joint probability. |
| V.A Relative angle | Frozen target `T-FIG003` | Figure 3, \(w=0.50\), \(v=0.98\), equal fixed absolute bases. |
| V.B Symmetric absolute angles | Frozen target `T-FIG004` | Figure 4, \(w=0.36\), \(v=0.99\), both bases rotate together with \(30^\circ\) spacing. |
| V.C Asymmetric absolute angles | Frozen targets `T-FIG005A/B` | Figure 5, one basis fixed and the other rotated; target-specific \(w,v\). |
| V.D Results | Claim-level observations | Reports measured minima/significances and the two violation regions. |
| VI. Conclusion | Interpretation | Summarizes the pedagogical experiment and its experimental limitations. |

## Equation Inventory

| Paper equation | Durable ID | Role | Execution status |
| --- | --- | --- | --- |
| (1)-(3) | `MAP-EQ001-003` | Hidden-variable joint-probability identities | Context, independently checked algebraically |
| (4)-(6) | `MAP-EQ004-006` | Wigner inequality, Wigner value, and LHV bound | Claim context; Eq. (5) is numerical dependency `EQC-WIGNER` |
| (7) | `EQC-MEASUREMENT` | Polarization measurement ket | Numerical dependency |
| (8) | `MAP-EQ008` | Tensor-product joint measurement | Incorporated into `EQC-BORN` |
| (9) | `EQC-BORN` | Singlet-state Born probability | Numerical dependency and analytic limit |
| (10) | `EQC-SINGLET-LIMIT` | Singlet Wigner value as three sine-squared terms | Analytic verification dependency |
| (11) | `MAP-EQ011` | Quantum violation condition | Claim context |
| (12) | `MAP-EQ012` | Symmetric extremal angles | Analytic check |
| (13) | `MAP-EQ013` | Asymmetric extremal angles | Analytic check |
| (14)-(17) | `MAP-EQ014-017` | Bell-state basis | Context; singlet in (14) is the \(w=1/2,\xi=\pi\) limit |
| (18) | `EQC-SOURCE-STATE` | Non-maximally entangled source state | Numerical dependency |
| (19) | `MAP-EQ019` | Coincidence normalization | Reference lane only |
| (20) | `EQC-DENSITY` | White-noise density matrix | Numerical dependency |
| (21) | `EQC-FIDELITY` | Fidelity to a pure target | Independent consistency check |

## Claim Map

| Claim ID | Paper claim | Formula/method support | Target binding |
| --- | --- | --- | --- |
| `CLM-LHV-BOUND` | The stated perfect-anticorrelation LHV model obeys \(\mathcal W\geq0\). | Eqs. (1)-(6) | Context for all four targets |
| `CLM-BORN` | A singlet gives \(P_{++}=\frac12\sin^2\Delta\). | Eqs. (7)-(9) | Analytic check for all targets |
| `CLM-SYMMETRIC-EXTREMUM` | Symmetric \(30^\circ,30^\circ,60^\circ\) separations give \(\mathcal W=-1/8\). | Eqs. (10), (12) | `T-FIG003`, `T-FIG004` |
| `CLM-ASYMMETRIC-EXTREMUM` | \(15^\circ,15^\circ,45^\circ\) separations give \(1/4-\sqrt3/4\approx-0.183\). | Eqs. (10), (13) | `T-FIG005A`, `T-FIG005B` |
| `CLM-FIG003-MODEL` | The \(w=0.50,v=0.98\) state generates the Figure 3 model curves. | Eqs. (18), (20), Born rule; `MTH-SCANS` | `T-FIG003` |
| `CLM-FIG004-MODEL` | The \(w=0.36,v=0.99\) state produces absolute-angle modulation in Figure 4. | Eqs. (18), (20), Born rule; `MTH-SCANS` | `T-FIG004` |
| `CLM-FIG005A-MODEL` | Alice-fixed asymmetric rotation uses \(w=0.35,v=0.89\). | Eqs. (18), (20), Born rule; `MTH-SCANS` | `T-FIG005A` |
| `CLM-FIG005B-MODEL` | Bob-fixed asymmetric rotation uses \(w=0.41,v=0.90\). | Eqs. (18), (20), Born rule; `MTH-SCANS` | `T-FIG005B` |
| `CLM-EXPERIMENT` | Measured data violate the classical bound with reported \(30\sigma\)-\(56\sigma\) significances. | Eq. (19), Poisson errors | Experimental reference only |

## Figure And Table Inventory

| Item | Visible contents | Class | Frozen decision |
| --- | --- | --- | --- |
| Table I | Eight predetermined LHV outcome sets | non-numeric table | excluded |
| Figure 1(a,b) | Alice/Bob basis diagrams | schematic context | excluded |
| Figure 2(a-c) | Source, measurement, coincidence apparatus | experimental schematic | excluded |
| Figure 3 | Experimental points plus 5 theory sequences | mixed numerical figure | theory bundle `FIG003-THEORY` targeted; experiment excluded |
| Figure 4 | Experimental points plus 5 theory sequences | mixed numerical figure | theory bundle `FIG004-THEORY` targeted; experiment excluded |
| Figure 5 top | Experimental points plus 5 theory sequences | mixed numerical panel | theory bundle `FIG005A-THEORY` targeted; experiment excluded |
| Figure 5 bottom | Experimental points plus 5 theory sequences | mixed numerical panel | theory bundle `FIG005B-THEORY` targeted; experiment excluded |

## Source Bundle Map

| Asset | Source role | Generated-data permission |
| --- | --- | --- |
| `Photonic_Violation_of_Wigner___s_Inequality.tex` | Canonical equation, caption, parameter, and figure-order trace | source tracing only |
| `basis_alice.pdf`, `basis_bob.pdf` | Figure 1 basis schematics | reference/context only |
| `Schematic_paper_v2.pdf` | Figure 2 apparatus schematic | reference/context only |
| `tequila_hat_paper_leastsquare.pdf` | Figure 3 author render | reference pixels only |
| `both_move_paper_leastsquare.pdf` | Figure 4 author render | reference pixels only |
| `A_fixed_paper_leastsquare.pdf` | Figure 5 top author render | reference pixels only |
| `B_fixed_paper_leastsquare.pdf` | Figure 5 bottom author render | reference pixels only |
| Four frozen TSV-formatted CSV files | Official coincidence counts and derived measured probabilities | reference-side comparison only |

## Assumptions And Boundaries

- The polarization convention is the paper's Eq. (7):
  \(|\theta\rangle=\sin\theta|H\rangle+\cos\theta|V\rangle\);
  therefore \(0^\circ\) denotes \(|V\rangle\).
- Within a basis the settings are
  \((a,b,c)=(\theta_{\mathrm{start}},\theta_{\mathrm{start}}+\phi,
  \theta_{\mathrm{start}}+2\phi)\), with the same construction for primed Bob
  settings. Figure 4 labels the central setting \(b\) by \(\Theta\), so its
  basis start is \(\theta_{\mathrm{start}}=\Theta-\phi\). The released
  `starting_angle=0` probabilities independently resolve this otherwise
  ambiguous origin: the reported model gives
  \((P_{ab'},P_{bc'},P_{ac'})=(0.0916,0.1609,0.3663)\), close to the official
  row \((0.089,0.148,0.359)\); using a zero start gives a visibly incorrect
  30-degree phase shift. No source pixels or measured values enter the
  generated curves after this coordinate convention is fixed.
- The reported fit phase is fixed at \(\xi=\pi\).
- The white-noise term is the four-dimensional identity divided by four.
- The paper reports fit parameters to two decimals. Fidelity differences at
  the few \(10^{-3}\) level are treated as rounding effects and reported
  explicitly, not silently tuned.
- The paper does not close locality or perfect-anticorrelation loopholes; this
  case reproduces its stated model, not a loophole-free Bell test.
