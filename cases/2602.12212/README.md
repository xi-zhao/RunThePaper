# 2602.12212: Quantum-Coherent Thermodynamics: Leaf Typicality via Minimum-Variance Foliation

Preprint: [arXiv:2602.12212v3 — Quantum-Coherent Thermodynamics: Leaf Typicality via Minimum-Variance Foliation](https://arxiv.org/abs/2602.12212v3)

Formal publication: **Not recorded as of 2026-07-26**

Public status: **Scientific reproduction — visual review pending** · Audit score: **72.05/100**

Case scaffolded from framework/templates/paper_case.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### t001 source vs reproduction comparison

![t001 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t001_source_vs_reproduction.png)

### t002 source vs reproduction comparison

![t002 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t002_source_vs_reproduction.png)

### t003 source vs reproduction comparison

![t003 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t003_source_vs_reproduction.png)

### t004 source vs reproduction comparison

![t004 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t004_source_vs_reproduction.png)

### t005 source vs reproduction comparison

![t005 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t005_source_vs_reproduction.png)

### t006 source vs reproduction comparison

![t006 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t006_source_vs_reproduction.png)

### t007 source vs reproduction comparison

![t007 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t007_source_vs_reproduction.png)

### t008a source vs reproduction comparison

![t008a source vs reproduction paper reference versus independent reproduction](docs/comparisons/t008a_source_vs_reproduction.png)

### t008b source vs reproduction comparison

![t008b source vs reproduction paper reference versus independent reproduction](docs/comparisons/t008b_source_vs_reproduction.png)

### t009 source vs reproduction comparison

![t009 source vs reproduction paper reference versus independent reproduction](docs/comparisons/t009_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2602.12212/code
python scripts/run_reproduction.py --config config/paper_scale_closure.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 10 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: All active v3 numerical figures were regenerated independently at the paper's published sizes. Boundary, shell-edge, and confidence-interval conventions omitted by the paper are disclosed reconstructions.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![eth scaling summary](outputs/figures/eth_scaling_summary.png)

![t001 spin1 foliation](outputs/figures/implementation_probe/t001_spin1_foliation.png)

![t003 dynamics](outputs/figures/implementation_probe/t003_dynamics.png)

![local canary l6](outputs/figures/local_canary_l6.png)

![t003 dynamics](outputs/figures/paper_scale_full_shell/t003_dynamics.png)

![t001 spin1 foliation](outputs/figures/t001_spin1_foliation.png)

![t002 main typicality](outputs/figures/t002_main_typicality.png)

![t003 dynamics](outputs/figures/t003_dynamics.png)

![t004 s1 beta025](outputs/figures/t004_s1_beta025.png)

![t005 s2 beta075](outputs/figures/t005_s2_beta075.png)

![t006 s3 beta175](outputs/figures/t006_s3_beta175.png)

![t007 s4 integrable](outputs/figures/t007_s4_integrable.png)

![t008a main compression](outputs/figures/t008a_main_compression.png)

![t008b supp compression](outputs/figures/t008b_supp_compression.png)

![t009 entropy gain](outputs/figures/t009_entropy_gain.png)
