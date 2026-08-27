# Method Trace

## MTH-SCANS - Measurement-pair scan construction

- Source: Figure 1 and Sections V.A-V.C.
- Role: map one plotted angle coordinate to the three joint measurements used
  in Eq. (5).
- Inputs: target ID, \(w\), \(v\), \(\xi=\pi\), fixed or scanned
  \(\theta_A,\theta_B,\phi\), and a deterministic angle grid.
- Outputs: angle, \(P_{ab'}\), \(P_{bc'}\), \(P_{ac'}\), \(\mathcal W\),
  and the panel's analytic violation limit.

Algorithm:

1. Construct Alice settings
   \((a,b,c)=(\theta_A,\theta_A+\phi,\theta_A+2\phi)\).
2. Construct Bob settings
   \((a',b',c')=(\theta_B,\theta_B+\phi,\theta_B+2\phi)\).
3. Evaluate `EQC-BORN` for \((a,b')\), \((b,c')\), and \((a,c')\).
4. Evaluate `EQC-WIGNER` pointwise.
5. Append the visible analytic limit from `EQC-SINGLET-LIMIT`.
6. Preserve the same sorted angle coordinate for all five series; do not
   connect across targets.

Target modes:

- `T-FIG003`: scan \(\phi\), with \(\theta_A=\theta_B=0^\circ\).
- `T-FIG004`: scan the common central setting \(\Theta\), with
  \(\theta_A=\theta_B=\Theta-\phi\) and \(\phi=30^\circ\). This panel-specific
  origin is verified against the released `starting_angle=0` probability row:
  the independent model gives `(0.0916, 0.1609, 0.3663)` versus the official
  `(0.089, 0.148, 0.359)`, whereas treating \(\Theta\) as the start setting
  shifts all three model curves by \(30^\circ\).
- `T-FIG005A`: scan \(\theta_B\), with \(\theta_A=0^\circ\) and
  \(\phi=30^\circ\).
- `T-FIG005B`: scan \(\theta_A\), with \(\theta_B=0^\circ\) and
  \(\phi=30^\circ\).

Parameters:

- paper range: \(0^\circ\) through \(360^\circ\), inclusive;
- generated line grid: \(0.5^\circ\) spacing (rendering resolution, not a
  changed physical parameter);
- all calculations use double precision and no random sampling.

Checks:

- the equal-basis singlet reduction yields separations
  \((\phi,\phi,2\phi)\);
- a common rotation leaves the ideal singlet Wigner value invariant;
- each projector and every resulting curve is \(180^\circ\)-periodic;
- swapping which party is fixed changes the asymmetric phase as described in
  Section V.D without changing the equations.
- the Figure 4 coordinate-origin check uses author data only as a
  reference-side method discriminator; the selected origin is then applied to
  a fully independent Born evaluation.

- Method gate: `verified`.
- Code pointer: `src/wigner_model.py::scan_target`.
- Open questions: none. The model is fully specified at the paper's reported
  two-decimal parameter precision.
