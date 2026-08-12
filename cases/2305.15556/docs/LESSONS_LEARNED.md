# Lessons Learned

## Case Summary

- Paper：Optimal Generators for Quantum Sensing
- PaperID：`2305.15556`
- 数值范围：6/6；算力阻塞：无
- 当前边界：fresh-context 独立评审缺失

## 可复用经验

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| 固定粒子数对称空间是核心降维 | SU(4) 的全张量空间随 N 指数增长，而对称空间仅 `C(N+3,3)` | 多模玻色子论文优先检查粒子数和置换对称性 |
| 退化本征矢不是唯一物理对象 | 源图热图可能随 LAPACK、时间步或任意规范跳变 | 保存领先空间 projector、秩、残差；像素不用于选规范 |
| 论文自洽性要检查“文字+显式 ket+算符定义” | 相邻轴标签可能与可执行表达式冲突 | 对“某态是某算符本征态”自动做方差零检验 |
| 原图对照必须在数据冻结后 | 既能优化展示，又切断偷像素路径 | RenderContract 验证对照前后数据哈希不变 |

## 效率

稀疏 Krylov + 1771 维对称空间使完整运行仅 4.70 秒。A100 会增加环境切换成本，
没有收益。该方法可保留为 case-local 物理实现；固定 N 玻色子基底未来可抽成 Harness
科学工具，但需要另行测试不同模数和大 N 的索引性能。

## Harness Backlog

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| P1 | 为本征矢图增加 `gauge_invariant_comparator` 合同 | Fig. 2(b) 的早期简并导致逐像素系数不可判定 | proposed |
| P1 | 为本征态文字声明增加方差零审查 | 本文 `K_y`/`K_z` 矛盾 | proposed |

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| 用源图选择简并本征矢规范 | Main Fig. 2(b) | 比较领先 projector 而不是逐像素系数 |
| 文字本征轴与显式 ket 冲突 | SU(4) 初态段落 | 自动计算候选轴的生成元方差 |

## Reusable Checks Or Tools

| Candidate | Why reusable | Suggested destination |
| --- | --- | --- |
| leading-space projector comparator | 适用于所有退化谱和规范自由度图 | Harness physics assertions |
| variance-zero eigenstate audit | 可审查论文中的本征态文字声明 | Harness formula falsification |
