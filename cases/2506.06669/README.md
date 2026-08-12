# 2506.06669: Remote Entanglement Generation Via Enhanced Quantum State Transfer

Preprint: [arXiv:2506.06669 — Remote Entanglement Generation Via Enhanced Quantum State Transfer](https://arxiv.org/abs/2506.06669)

Published as: [Remote Entanglement Generation Via Enhanced Quantum State Transfer](https://doi.org/10.1103/4x8d-cmyx)

Formal citation: PRX Quantum 7, 010348 (2026) · DOI `10.1103/4x8d-cmyx` · Locator `010348`

Public status: **Scientific reproduction — invalid** · Audit score: **68.73/100**

Publishes the independently generated numerical artifacts retained by the historical case: 10 public generated data files, 11 public generated figures, and 10 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| FIG1CD | Zig-zag spectrum and signed eigenfunction parity structure. | [PNG](outputs/figures/T001_fig1cd.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG2ABC_S2_S3 | Analytic three-site PST solution space and detuning-time spectra. | [PNG](outputs/figures/T002_figS3.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG2ABC_S2_S3 | Analytic three-site PST solution space and detuning-time spectra. | [PNG](outputs/figures/T002_solution.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG2DEF | Five-site PST population spectra and even-site suppression. | [PNG](outputs/figures/T003_fig2def.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG3AB | Master-equation FST dynamics for m=0 and m=4. | [PNG](outputs/figures/T004_fig3ab.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG3CD | Theory density support for remote Bell generation. | [PNG](outputs/figures/T005_fig3cd.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG3E_S8DEF | FST robustness under even-frequency, odd-frequency and coupling noise. | [PNG](outputs/figures/T006_figS8def.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG4_ACDF | Separable 3x3 FST dynamics and ideal four-corner W density. | [PNG](outputs/figures/T007_fig4_theory.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIGS7DEF | PST robustness under three independent parameter-noise channels. | [PNG](outputs/figures/T008_figS7def.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIGS9 | One-dimensional Lindblad Bell fidelity versus m and theory density matrices. | [PNG](outputs/figures/T009_figS9.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIGS10 | Two-dimensional Lindblad W fidelity versus m and population spectra. | [PNG](outputs/figures/T010_figS10.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG1CD: Zig-zag spectrum and signed eigenfunction parity structure.

![FIG1CD reproduction](outputs/figures/T001_fig1cd.png)

### FIG2ABC_S2_S3: Analytic three-site PST solution space and detuning-time spectra.

![FIG2ABC_S2_S3 reproduction](outputs/figures/T002_figS3.png)

### FIG2ABC_S2_S3: Analytic three-site PST solution space and detuning-time spectra.

![FIG2ABC_S2_S3 reproduction](outputs/figures/T002_solution.png)

### FIG2DEF: Five-site PST population spectra and even-site suppression.

![FIG2DEF reproduction](outputs/figures/T003_fig2def.png)

### FIG3AB: Master-equation FST dynamics for m=0 and m=4.

![FIG3AB reproduction](outputs/figures/T004_fig3ab.png)

### FIG3CD: Theory density support for remote Bell generation.

![FIG3CD reproduction](outputs/figures/T005_fig3cd.png)

### FIG3E_S8DEF: FST robustness under even-frequency, odd-frequency and coupling noise.

![FIG3E_S8DEF reproduction](outputs/figures/T006_figS8def.png)

### FIG4_ACDF: Separable 3x3 FST dynamics and ideal four-corner W density.

![FIG4_ACDF reproduction](outputs/figures/T007_fig4_theory.png)

### FIGS7DEF: PST robustness under three independent parameter-noise channels.

![FIGS7DEF reproduction](outputs/figures/T008_figS7def.png)

### FIGS9: One-dimensional Lindblad Bell fidelity versus m and theory density matrices.

![FIGS9 reproduction](outputs/figures/T009_figS9.png)

### FIGS10: Two-dimensional Lindblad W fidelity versus m and population spectra.

![FIGS10 reproduction](outputs/figures/T010_figS10.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2506.06669/code
python scripts/verify_public_artifacts.py
```

### Independent numerical rerun

This command recomputes the scientific numerical arrays from the public equation-based implementation. It does not read a paper image, digitized source curve, or author numerical code; runtime varies from seconds to CPU minutes.

```bash
cd cases/2506.06669/code
python scripts/run_reproduction.py --config config/paper_reconstruction.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: T001=figure_rendered, T002=figure_rendered, T003=figure_rendered, T004=figure_rendered, T005=figure_rendered, T006=figure_rendered, T007=figure_rendered, T008=figure_rendered, T009=figure_rendered, T010=figure_rendered. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
