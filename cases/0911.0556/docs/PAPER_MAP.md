# Full-paper numerical inventory

## Publication

- Paper ID: `0911.0556`
- DOI: `10.1103/PhysRevLett.104.160601`
- Main paper: five pages; no supplement or tables.
- Official source: manuscript TeX and three figure PDFs only.
- Author computational code/numerical arrays: none found and none used.

## Whole-paper item scope

W1 全文复核把图内每条独立数值序列作为一个 item；只有没有图承载的独立定量
结论才另计 claim。结果为：

- 27 个图示 item：24 个理论数值序列、3 个非数值示意图；
- 3 个独立正文 claim；
- 27 个可复现 item，全部已有独立目标与证据；
- item coverage：`27/27 = 100%`。

| Publication item | Classification | Decision | Target |
| --- | --- | --- | --- |
| Fig. 1A | two-level schematic | exclude | — |
| Fig. 1B | analytic `theta(s)`, `k(s)`, `Q(s)` | reproduce | T001 |
| Fig. 1C | rate function and Poisson comparator | reproduce | T002 |
| Fig. 1D | three theoretical quantum-jump event records | reproduce numerically | T003 |
| Fig. 2A | three-level schematic | exclude | — |
| Fig. 2B | tilted-Liouvillian `theta(s)` plus two-level comparator | reproduce | T004 |
| Fig. 2C | `k(s)`, `Q(s)/10` and two-level activity | reproduce | T005 |
| Fig. 2D | Legendre rate function and Poisson comparator | reproduce | T006 |
| Fig. 2E | inactive/active theoretical event records | reproduce numerically | T007 |
| Fig. 3A | micromaser schematic | exclude | — |
| Fig. 3B | micromaser `theta(s)` and `k(s)/10`, `alpha=1.2pi` | implement/reproduce with reconstructed public parameters | T008 |
| Fig. 3C | micromaser `theta(s)` and `k(s)/10`, `alpha=2pi` | implement/reproduce with reconstructed public parameters | T009 |
| Fig. 3D | three biased cavity photon distributions | implement/reproduce with reconstructed public parameters | T010 |
| General quantum Doob mapping | quantitative operator identity | verify | T011 |
| Two-level mapped dynamics | rate/time rescaling by `exp(-s/3)` | verify | T011 |
| Three-level inactive-side mapped realization | additional strong `|1>-|2>` laser, dressed detuning and emission suppression | reproduce numerically | T012 |

The original paper does not print the micromaser excitation number or thermal occupation. The complete Fig. 3 algorithm is still implemented, while `N_ex=100` and `nu=0.15` are explicitly traced to the later public same-author paper arXiv:1103.0919 and therefore remain reconstructed rather than paper-exact.

`T012` 已作为独立目标补齐：直接使用正文模型与 Eqs. (6)-(7)，在映射后跳跃
算符定义的规范基中提取 `|1~>-|2~>` 耦合、dressed-state detuning 与稳态发射
率。代码未参考作者数值实现，隔离 runner 也不能访问原图或 `raw/`。当前仅待
fresh-context 评审尝试证伪该定性机制。
