# 10.1038-s41467-025-67768-4: Demonstrating quantum error mitigation on logical qubits

Preprint: [arXiv:2501.09079 — Demonstrating quantum error mitigation on logical qubits](https://arxiv.org/abs/2501.09079)

Published as: [Demonstrating quantum error mitigation on logical qubits](https://doi.org/10.1038/s41467-025-67768-4)

Formal citation: Nature Communications 17, 1021 (2026) · DOI `10.1038/s41467-025-67768-4` · Locator `1021`

Public status: **Scientific reproduction — invalid** · Audit score: **72.25/100**

Publishes the independently generated numerical artifacts retained by the historical case: 7 public generated data files, 10 public generated figures, and 9 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| MAIN_FIG2C | Feedback/post-selection expectation under amplified Pauli injection. | [PNG](outputs/figures/main_fig2c_feedback.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| MAIN_FIG3C | One-round corrected and uncorrected repetition-code expectations. | [PNG](outputs/figures/main_fig3c_repetition.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| MAIN_FIG3C | One-round corrected and uncorrected repetition-code expectations. | [PNG](outputs/figures/supp_fig4_repetition.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| MAIN_FIG3E | Multi-round distance-7 repetition-code expectation at approximately fixed total error. | [PNG](outputs/figures/main_fig3e_repetition.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| MAIN_FIG4BC | Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables. | [PNG](outputs/figures/main_fig4b_bloch.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| MAIN_FIG4BC | Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables. | [PNG](outputs/figures/main_fig4c_surface.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| MAIN_FIG4BC | Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables. | [PNG](outputs/figures/supp_fig7ace_surface.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| SUPP_FIG8 | Complete versus injection-only ZNE bias and sampling overhead. | [PNG](outputs/figures/supp_fig8_complete_zne.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| SUPP_FIG9 | Large-scale surface-code logical-memory ZNE bias and overhead. | [PNG](outputs/figures/supp_fig9_logical_memory.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| SUPP_TABLE3 | Per-layer unit-error probabilities intended to preserve cumulative injected error. | [PNG](outputs/figures/supp_table3_fixed_error.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### MAIN_FIG2C: Feedback/post-selection expectation under amplified Pauli injection.

![MAIN_FIG2C reproduction](outputs/figures/main_fig2c_feedback.png)

### MAIN_FIG3C: One-round corrected and uncorrected repetition-code expectations.

![MAIN_FIG3C reproduction](outputs/figures/main_fig3c_repetition.png)

### MAIN_FIG3C: One-round corrected and uncorrected repetition-code expectations.

![MAIN_FIG3C reproduction](outputs/figures/supp_fig4_repetition.png)

### MAIN_FIG3E: Multi-round distance-7 repetition-code expectation at approximately fixed total error.

![MAIN_FIG3E reproduction](outputs/figures/main_fig3e_repetition.png)

### MAIN_FIG4BC: Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables.

![MAIN_FIG4BC reproduction](outputs/figures/main_fig4b_bloch.png)

### MAIN_FIG4BC: Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables.

![MAIN_FIG4BC reproduction](outputs/figures/main_fig4c_surface.png)

### MAIN_FIG4BC: Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables.

![MAIN_FIG4BC reproduction](outputs/figures/supp_fig7ace_surface.png)

### SUPP_FIG8: Complete versus injection-only ZNE bias and sampling overhead.

![SUPP_FIG8 reproduction](outputs/figures/supp_fig8_complete_zne.png)

### SUPP_FIG9: Large-scale surface-code logical-memory ZNE bias and overhead.

![SUPP_FIG9 reproduction](outputs/figures/supp_fig9_logical_memory.png)

### SUPP_TABLE3: Per-layer unit-error probabilities intended to preserve cumulative injected error.

![SUPP_TABLE3 reproduction](outputs/figures/supp_table3_fixed_error.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1038-s41467-025-67768-4/code
python scripts/verify_public_artifacts.py
```

### Independent numerical rerun

This command recomputes the scientific numerical arrays from the public equation-based implementation. It does not read a paper image, digitized source curve, or author numerical code; runtime varies from seconds to CPU minutes.

```bash
cd cases/10.1038-s41467-025-67768-4/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: T001=failed, T002=partially_reproduced, T003=partially_reproduced, T004=partially_reproduced, T005=partially_reproduced, T007=partially_reproduced, T008=blocked_missing_method, T009=blocked_missing_method. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
