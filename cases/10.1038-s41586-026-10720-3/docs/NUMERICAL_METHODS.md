# Numerical methods

## Input boundary

The scientific runner receives only paper equations, disclosed scalar values,
standard material constants, and labelled surrogate assumptions. It cannot
read the PDFs, original figures, author code, author arrays, digitized curves,
or post-freeze rendering assets.

## Methods by target

| Targets | Method | Current scale |
| --- | --- | --- |
| T_F2A-C | Sellmeier-plus-capillary dispersion, co-moving transform, bracketed roots | one attested smoke assumption; seven paper assumptions coded |
| T_S1A-C | analytic-signal UPPE, positive-frequency projection, conjugated-SPM ablation | three attested points per panel; eleven points per panel coded |
| T_F4A-F | direct evaluation of Methods D.1 sensitivity family | six attested analytic units |
| T_F5C | shared-slope identity from Methods D.2-D.3 | attested and verified |

Each work unit writes NPZ/JSON artifacts bound to configuration and
implementation hashes. The isolated runner records actual argv, Git state,
input/output hashes, file access, sandbox assurance, and runtime.

The 17-unit smoke validates execution only. The 47-unit paper profile remains
deferred because it cannot resolve the dominant missing-input and method-
normalization questions by itself.
