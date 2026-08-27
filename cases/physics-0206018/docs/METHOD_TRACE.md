# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### METHOD001 — driven scattering and optical-theorem observable

- Source: Eqs. (17)-(22), Eqs. (27)-(30), Sec. 7 and Fig. 5.
- Role: construct the TM boundary system and reproduce the cross-section scan.
- Inputs: independently generated `N=1600` boundary mesh, refractive indices,
  incidence angle, quadrature order and the frozen 153-point `kR` grid.
- Outputs: boundary solutions, residuals, Eq. (22) `sigma/R`, independent
  angular-integral estimates and their relative differences.
- Algorithm steps: assemble interior/exterior blocks; apply the incident plane
  wave; solve the dense complex system; evaluate Eq. (22); separately integrate
  the far-field intensity as a consistency check.
- Code pointer: `src/bem.py::solve_scattering`, `src/bem.py::cross_section`,
  `scripts/run_paper_scale.py::_scan_stage`.
- Checks: circle benchmark, linear residual, nonnegative cross section, optical
  theorem consistency, scan spacing and printed resonance anchor.
- Status: verified; the plotted array is explicitly bound to Eq. (22).
- Open questions: the method is fixed, but Sec. 5 prose and Fig. 4 disagree on
  the geometry's vertical displacement sign; the runner follows Fig. 4 and
  records the source discrepancy.

### METHOD002 — resonance boundary state and field reconstruction

- Source: Eqs. (34)-(38), final `k_res R` paragraph, Figs. 6-7.
- Role: obtain one boundary null vector and derive both near- and far-field
  observables without independent fitting.
- Inputs: printed `k_res R=22.94444-0.09696i`, the same mesh contract as
  METHOD001 and four declared convergence meshes.
- Outputs: smallest singular values, boundary vector, normalized near-field
  map and normalized far-field angular curve.
- Algorithm steps: SVD at the printed complex resonance; freeze the final null
  vector; reconstruct the Cartesian field; evaluate the outgoing far field.
- Code pointer: `src/bem.py::resonance_boundary_state`,
  `src/bem.py::reconstruct_field`, `src/bem.py::far_field`.
- Checks: singular-value mesh trend, boundary residual, finite/nonzero fields,
  shared-state identity and pi-rotation intensity symmetry.
- Status: verified at paper scale by the isolated acceptance artifact.
- Open questions: fresh review of the displacement-sign source discrepancy.

### METHOD003 — post-freeze RenderContract

- Source: Figs. 5-7 presentation geometry only.
- Role: turn immutable arrays into paper-comparable images.
- Inputs: hashed independent NPZ plus comparison-only source figures.
- Outputs: reader figures, registered figures, crops and pixel evidence.
- Algorithm steps: render frozen arrays; adjust only canvas, axes, fonts, line
  style, grayscale and interpolation; build predeclared full scientific crops.
- Code pointer: `scripts/render_figures.py`, `RENDER_CONTRACT.md`.
- Checks: source/generated provenance, unchanged NPZ hash, target contracts and
  scientific-region pixel acceptance.
- Status: executed after data freeze; Fig. 6 passes high fidelity, while Figs. 5
  and 7 remain below the predeclared 80-point render threshold.
- Open questions: typography and subpixel line placement only; the numerical
  arrays remain frozen.
