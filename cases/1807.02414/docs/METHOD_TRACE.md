# Method Trace

| Method | Inputs | Output | Status |
| --- | --- | --- | --- |
| MTH_TBA | EQ001-EQ003, ell, rapidity grid | stationary densities and velocities | verified |
| MTH_ONSAGER | EQ005-EQ006, dressed state | `(D C)_SzSz` | verified |
| MTH_PROFILE | EQ004 and EQ007, x/t grid | six Fig. 1 theory curves | verified with declared reduced operator projection |
| MTH_FULL_GHD | EQ009, complete spectral mode state, x/t grid | full-operator Fig. 1 solid curves | code ready; four-variant A100 convergence run not executed |
| MTH_RENDER | frozen arrays and render contract | PNG/SVG/PDF | verified; numerical hashes unchanged |
| MTH_TDMRG | EQ008, finite XXZ chain, purified mixed state, TEBD controls | independent benchmark markers at t=10/20/40 | code ready; final A100 convergence campaign not run |

The low-cost numerical runner receives case-local formula code and
`config/paper_exact.json`. The full-GHD and T003 runners receive only their
case-local formula/TEBD code and respective paper-scale configs; neither can
read paper/source or reference-image trees. Rendering remains a post-freeze
method and may inspect the source figure only for layout comparison.
