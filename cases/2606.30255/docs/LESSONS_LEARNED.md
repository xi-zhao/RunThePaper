# Lessons Learned

## Case Summary

- Paper: *Photonic Violation of Wigner's Inequality*
- PaperID: `2606.30255`
- Final status: four frozen theory targets reproduced; scientific and pixel gates pass
- Main reproduced targets: `FIG003-THEORY`, `FIG004-THEORY`,
  `FIG005A-THEORY`, `FIG005B-THEORY`
- Main blockers: none

## What Worked

- 先读完整论文，再把“测量态—密度矩阵—Born 概率—角度几何—Wigner
  组合—解析极限”压缩为六张 equation cards，使四张图共享同一干净
  核心模型。
- 用显式矩阵迹生成，用单独标量收缩核验，能捕获相位、basis ordering
  和固定/旋转观察者互换等真正的物理错误。
- 科学 lane 完成后才引入作者图做 reference，使像素调优无法污染 CSV。
- 理论-only 的 series contract 把“混合图全部理论曲线”与“禁止实验
  marker”同时变成机器检查。

## What Was Difficult

- Figure 5 的 caption/正文需要结合角度定义，才能确定 Alice-fixed 与
  Bob-fixed 的 origin mapping，而不能靠原图形状猜测。
- 原图同时含实验与理论层；pixel score 会合法地惩罚缺失实验墨迹，
  因此必须把科学分和像素分分离解释。
- Figure 4 的 printed fidelity 与由 rounded \(w,v\) 重算值相差
  0.0053；若不单独记录，很容易误把 metadata 舍入问题当成模型错误。
- 末端 \(360^\circ\) tick label 一度触边；这是版式合同失败，不应
  触发对曲线数值或物理参数的修改。

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| 混合图按 series 而不是整图定义范围 | 避免为了视觉相似复制实验数据 | coverage ledger 同时列 theory target 和 excluded experimental item |
| 生成路径与核验路径应在实现上分离 | 防止同一 bug 自证正确 | 小模型优先保留 matrix-vs-scalar 双路径 |
| 参数舍入差异属于独立证据项 | 避免反向拟合 reference 图 | 设置透明 tolerance，并报告 observed delta |
| Pixel 调优只消费冻结 CSV | 样式变化不会改变物理结论 | renderer 不导入模型求值函数 |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Python/JSON 布尔混用 | 首次 FIG003 payload 使用 `false` 导致命令退出 | 在写 artifact 前运行最小 payload construction test |
| 过松 pixel contract | 初始阈值不足以表达已实现的版式精度 | 先测量，再把合同收紧到有余量但有区分度的值 |
| 末端 tick 越界 | 360° label 接触右边界 | 首末 tick label 朝轴内对齐并检查 ink margin |
| 用 fidelity 倒推 curve 参数 | rounded metadata 不完全自洽 | 曲线参数以 figure/section 明示值为准，fidelity 只做非关键检查 |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| 全文 map 后再建公式 gate | figure caption 依赖正文定义时 | 六张 cards 覆盖四个 target 且无局部公式补丁 |
| 完整 visible-theory series assertion | theory+experiment 混合图 | 四个 checks 均确认五条理论曲线且 experimental list 为空 |
| Reference 延迟引入 | 禁止原图作为生成输入时 | source PNG 只进入 comparison/pixel artifacts |
| 记录 accepted 与 discarded timing | 首次运行可能失败时 | 1.303271 s accepted 与 11.25 s discarded 分开记录 |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Payload-language literal mismatch | `run_theory_target.py` 首次 FIG003 run | 单元测试或 smoke run 覆盖最终 JSON 构造分支 |
| Border-touching endpoint annotation | pixel evidence 初次严格检查 | `ink_margin_min_pixels` 与 border-touch 列表必须进入合同 |
| Rounded fit metadata inconsistency | Figure 4/5 parameters | 从报告参数重算 auxiliary quantities，并作为 non-essential assertion |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| matrix-vs-analytic dual-path assertion pattern | 适合所有小 Hilbert-space closed-form 模型 | 保持 case-local 示例；未来另行评估是否抽象 |
| theory-only visible-series contract | 适合所有实验/理论混合图 | 可作为未来 Harness 设计输入 |
| endpoint label margin check | 对任何 0–360° 周期图有效 | 现有 pixel evidence 已能表达，无需本 Trial 改 Harness |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| 显式 \(4\times4\) Born trace | 四目标纯数值共 0.381648 s | case-local |
| 从 frozen CSV 独立 pixel redraw | 四图共 0.476397 s | case-local |
| 同一 target specification 驱动模型与 renderer | 无重复参数散落 | case-local domain model |

## Harness Backlog Items

本冻结 Trial 明确禁止修改 protected Harness，因此没有把经验写入
`private validation harness/HARNESS_BACKLOG.md`。下列仅作 case-local 记录：

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| low | audit 将 case-local verdict 的顶层 status 作为通用要求 | 初版 verdict 触发 missing-status warning | case adapter 已修复 |
| low | 把 endpoint annotation margin 纳入模板提醒 | 360° tick 曾触边 | existing checker 足够，未改 Harness |

## Prompt Or Workflow Changes

- 在混合图冻结 trial 中，明确要求“先生成所有 theory series，再允许
  reference-only source extraction”能形成可审计时序。
- 最终报告应同时给出 scientific score、pixel score 和证据上限，避免
  把三者混成一个“复现成功率”。
