# Lessons Learned

## Case Summary

- Paper：*Lyapunov formulation of band theory for disordered non-Hermitian systems*
- PaperID：`2507.09447`
- Final status：`physically_consistent` / `numerical_feature_reproduction`
- Main targets：Fig. 3–5。
- Main blockers：paper-scale 统计和未公开的 QR/grid/seed/alpha 细节。

## What Worked

- 一个 `LongRangeModel` 同时支撑 OBC、PBC、twist、LE、势、绕数和状态分类。
- 在绘图之前写 CSV 和 JSON 物理 checks，使验收不依赖肉眼。
- 用 clean beta limit 和 Hamiltonian recurrence 把公式错误挡在昂贵运行之前。
- 用 twisted determinant 独立验证 LE winding，避免“同一公式自证”。

## What Was Difficult

- arXiv v1 与 2026 正式发表版的标题、术语和补充证据不同，需要严格版本边界。
- branch-selected essential LE 不是全局连续场，直接 contour 会产生假迁移边。
- 小 L twisted chain 对谱洞 winding 有明显有限尺寸误差。
- 少量 ensemble 的 `delta Phi(L)` 噪声足以扭曲幂律指数。

## Generalized Experience

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| 同一领域对象应产生所有下游 observable | 减少图间公式漂移 | 先建 model/state/event/invariant，再写 target 脚本 |
| 独立数值路径比视觉相似更强 | 漂亮图可能共享同一个 bug | 至少为核心拓扑量提供第二实现 |
| 版本证据必须带 provenance | 后发表 supplement 不能倒灌进 preprint claim | 分开记录 target version 与 method evidence version |
| 大样本标度先增加 ensemble | 幂律对噪声比单图更敏感 | 用 endpoint decrease + exponent 两级 gate |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| 对分支选择后的 signed `gamma_ess` 直接画 `=0` contour | Fig. 5 初版出现不物理竖线 | contour underlying continuous `gamma_M`/`gamma_M+1`，并检查拓扑突跳 |
| twisted chain 太短导致 winding 区域误判 | Fig. 4 初版 `L=80` 左谱洞不匹配 | 对每个 probe 做 `L` 收敛或至少两档长度一致性 |
| 小 ensemble 产生伪标度指数 | Fig. 3 初版 32 samples 波动大 | 提升 realization，并记录 exponent gap 与首末误差同时通过 |
| 把正式版补充材料当作 arXiv v1 原始信息 | method reconstruction | 每条证据记录 source version 和使用角色 |

## Reusable Checks Or Tools

| Candidate | Why reusable | Suggested destination |
| --- | --- | --- |
| composite-field contour checker | 分段/branch-selected 场普遍可能制造假零线 | harness feature validator |
| finite-size dual winding check | 非厄米拓扑量易受 finite L 影响 | case template / numerical sanity gate |
| paper-version provenance field | preprint/journal/supplement 经常漂移 | paper map schema |
| paper-size single-sample benchmark | 将“算力不足”变成实测时间预算 | performance profiler |

## Efficient Reproduction Implementations

| Implementation | Evidence | Decision |
| --- | --- | --- |
| energy-batched `4×4` QR | 三图数据 30.40 s | batch pattern 可抽象，物理矩阵留 case |
| seed-parallel dense ED | 单 `L=1000` 样本 <1 s/边界 | promotion candidate：checkpointed seed runner |
| sparse direct winding probes | 4/4 与 LE 一致 | 保持 case-local acceptance rule |

## Harness Backlog Items

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| high | 新增 composite-field contour continuity gate | Fig. 5 假竖线 | added as H062 |
| medium | target evidence 加 source-version/role 字段 | arXiv v1 vs formal supplement | recorded in experience |

## Prompt Or Workflow Changes

- 迁移边类目标先声明“被 contour 的连续原始场”，禁止只写一个派生 composite field。
- paper-scale 任务采用 `pilot → medium → final` loop；每阶段检查物理 gate、资源和
  checkpoint，超过一小时或使用远端算力前由用户授权。
