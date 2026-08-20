# Method Trace

| Method | 输入 | 输出 | 代码 | 独立检查 |
| --- | --- | --- | --- | --- |
| DENSE_TILTED | Hamiltonian、jump operators、bias `s` | dominant eigenvalue | `src/quantum_jumps/liouvillian.py`、`models.py` | 两能级闭式、trace identity |
| RATE_DUAL | `theta(s)` 网格 | `phi(k)` | `src/quantum_jumps/large_deviation.py` | 解析 CMP rate function |
| QUANTUM_JUMPS | 物理模型、固定 seed | event times | `src/quantum_jumps/trajectories.py` | 经验 activity 与目标 rate |
| MICROMASER_BIRTH_DEATH | 论文 jump operators、光子 cutoff | SCGF、activity、分布 | `src/quantum_jumps/micromaser.py` | cutoff convergence、独立本征求解器 |
| DOOB_SIMILARITY | tilted operator、左本征矩阵 | trace-preserving driven generator | `src/quantum_jumps/doob.py` | identity left-zero-mode |
| RENDER_ONLY | 冻结 CSV/JSON | PNG | `scripts/render_figures.py` | 数据哈希前后不变 |

数值 runner 的 declared inputs 只包含配置和实现代码；`raw/`、`references/` 与网络均禁止读取。RenderContract 是冻结后的独立通道，只能调整画幅、轴、字体、线型、颜色和插值。
