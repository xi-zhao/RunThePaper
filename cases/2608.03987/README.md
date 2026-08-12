# 2608.03987: Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators

Preprint: [arXiv:2608.03987v2 — Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators](https://arxiv.org/abs/2608.03987)

Formal publication: **Not recorded as of 2026-08-08**

Public status: **Partial scientific reproduction** · Audit score: **72.00/100**

A clean-room Python tensor-network implementation evaluates all 67 paper circuits without executing or translating the authors' Rust crates. Figure 8's exact realification law passes on every circuit (maximum residual 4.44e-16; post-hoc overhead correlation 0.9881). Figure 9 remains optimizer-sensitive: 57/67 independent trees, versus 66/67 in the paper, fall below the 5e-4 transfer-gap threshold.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Full path-free contraction-tree records (JSONL)](outputs/data/independent_tree_records.jsonl)
- [Figure 8 independent data (CSV)](outputs/data/fig8_cost_law.csv)
- [Figure 9 independent data (CSV)](outputs/data/fig9_pipeline.csv)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| Figure 8 | Exact realification cost law and analytic band on all 67 circuits | [PNG](outputs/figures/fig8_cost_law.png) | [JSON](outputs/checks/numerical_feature_checks.json) |
| Figure 9 | Independent contraction-order transfer study with the retained 57/67 versus 66/67 threshold mismatch | [PNG](outputs/figures/fig9_pipeline.png) | [JSON](outputs/checks/numerical_feature_checks.json) |

### Figure 8: Exact realification cost law and analytic band on all 67 circuits

![Figure 8 reproduction](outputs/figures/fig8_cost_law.png)

### Figure 9: Independent contraction-order transfer study with the retained 57/67 versus 66/67 threshold mismatch

![Figure 9 reproduction](outputs/figures/fig9_pipeline.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install cotengra==0.7.5 opt_einsum==3.4.0
cd cases/2608.03987/code
python scripts/fetch_benchmark_inputs.py
python scripts/run_independent_reimplementation.py --preset smoke --scope random --circuit test
```

### Full clean-room 67-circuit rerun

The full preset fixes seed 42, ten generic cotengra candidates, 600,000 NNI steps per objective, and 60,000 polish steps. The completed records sum to about 29.3 CPU-minutes; parallel wall time depends on how the circuit set is sharded.

```bash
cd cases/2608.03987/code
python scripts/run_independent_reimplementation.py --preset full --output-dir ../outputs/data/independent_python_full
python scripts/run_reproduction.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: This is not a complete reproduction of the paper. The independent optimizer differs from the published optimizer and reproduces only 58/67 Figure-9 threshold labels. The package evaluates contraction-tree arithmetic, not Ascend 910/A800 tensor kernels, so it does not reproduce device wall clocks, precision, or end-to-end acceleration tables. The official Zenodo ZIP is downloaded separately; the primary optimizer opens only its 122 raw circuit and observable payloads, while author results are used only for post-hoc comparison.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
