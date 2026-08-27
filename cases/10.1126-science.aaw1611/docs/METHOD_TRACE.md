# Method Trace

| Method | Targets | Implementation | Evidence |
| --- | --- | --- | --- |
| Fixed-sector exact dynamics | T001-T004 | `src/quantum_walk.py` | T001-T004 checks |
| Dispersion and observables | T002 | analytic/spectral routines | T002 checks |
| Disorder ensemble | T005 S9-S10 | printed uniform disorder and effective hopping, 50 realizations | T005 checks |
| Fidelity/Lindblad reconstruction | T005 S11 | printed bounds plus explicit standard reconstruction | T005 checks and parameter provenance |
| Isolated orchestration | all 38 | `scripts/run_paper_exact.py` under run contract | run attestation |
| Frozen-array rendering | all current figures | `scripts/render_frozen_outputs.py` | rendered figure manifest |

The scientific runner cannot read raw or original-figure directories. `digitize_s20_reference.py` is a separate post-run comparison tool and cannot write scientific parameters or arrays.
