# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| scientific checks passed | 5 | Every target passes its analytic/numerical contract. |
| pixel numerical-feature band (>=60) | 4 | T001-T004. |
| pixel below feature band | 1 | T005 layout/marker fidelity. |
| paper-exact target | 1 | T005. |
| paper-subset targets | 4 | Public source omits a discrete convention or plotting choice. |
| excluded schematic | 1 | Fig. S2(a). |

## Per-target consistency

| Target | Key scientific evidence | Pixel evidence | Verdict |
| --- | --- | --- | --- |
| T001 | root residual `1.94e-14`; four positive-winding localized states | foreground 67.15; full 92.35 | scientific feature reproduced |
| T002 | both GBZ classes; Ronkin flat counts `2999/1/2` | foreground 72.28; full 90.93 | scientific feature reproduced |
| T003 | endpoint `8.09e-8`; winding residual `1.14e-7` | foreground 84.80; full 94.15 | strongest match |
| T004 | density correlation `0.9964`; support IoU `0.9314` | foreground 65.25; full 92.54 | scientific feature reproduced |
| T005 | open/constituent median distance `0.00607` | foreground 56.93; full 94.10 | science passed; raster below band |

Source pixels are used only by post-run evidence. The isolated numerical runner never opens them.
