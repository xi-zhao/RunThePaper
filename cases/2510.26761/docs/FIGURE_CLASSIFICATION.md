# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 explanatory arrows, equations, and labels | `schematic_context` | No | These elements explain the two theorems but contain no independently generated data. |
| Main Fig. 1 central three-dimensional Wigner cut | `numeric_reproduction` | Yes, `T001` | It is generated from the explicitly printed collective-mode Fock state. |
| Main Fig. 1 equal-coordinate slice, reduced center-of-mass Wigner function, and smoothed function | `numeric_reproduction` | Yes, `T001` | These surfaces carry the two theorem demonstrations and have analytic validation values. |
| Main Fig. 2(a) W-state Wigner slice | `numeric_reproduction` | Yes, `T002` | The paper gives the exact function, finite-disk integral, and threshold radius. |
| Main Fig. 2(b) W-state characteristic slice | `numeric_reproduction` | Yes, `T002` | The paper gives the exact function, the seven-point set, 19 differences, and witness value. |
| Supplemental S1--S5 | `not_in_scope` | No separate figure target | These are analytic proofs; their equations feed validation targets `V001`--`V003`. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`

## Panel Ledger

| Target | Panel | Physical object | Acceptance evidence |
| --- | --- | --- | --- |
| `T001` | `full_cut` | \(W_\psi(\alpha_+,\alpha_-,0)\) on the stated 3D cut | correct positive/negative lobe topology and exact Fock-state normalization |
| `T001` | `equal_slice` | \(W_\psi(\alpha\mathbf1)\) | signed integral \(-52/(75\pi^2)\) and converged negative volume |
| `T001` | `center_of_mass` | Wigner function of \(\rho_+=\mathrm{tr}_{-}\rho\) | unit trace and Fock populations \(0.4,0.1,0.4,0.1\) for \(n=1,2,3,4\) |
| `T001` | `smoothed_center_of_mass` | \(W_{\rho_+}*K\) | \(\widetilde W(0)=-7/(16\pi)\) |
| `T002` | `wigner_slice` | \(W_{|W_3\rangle}(\alpha\mathbf1)\) | zero ring \(r=1/(2\sqrt3)\), \(r_{\rm crit}=0.699195\), and \(V(0.7)>1/(2\sqrt2)\) |
| `T002` | `characteristic_slice` | \(\chi_{|W_3\rangle}(\xi\mathbf1)\) | 19 unique differences and minimum witness eigenvalue \(-0.0175804\) |
