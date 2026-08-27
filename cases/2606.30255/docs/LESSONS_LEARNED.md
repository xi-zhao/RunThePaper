# Lessons Learned

## Case Summary

- Paper：*Photonic Violation of Wigner's Inequality*
- Paper ID：`2606.30255`
- Final status：4/4 frozen theory targets reproduced
- Main targets：Figures 3, 4, 5 top, 5 bottom theory bundles
- Main remaining boundary：实验采集和探测器级损耗模型不在冻结理论范围

## What Worked

- 先建立完整 paper/claim/target map，再开始计算，避免遗漏 Figure 5 的两个独立面板。
- 用一个小而深的核心模型统一四个目标：测量 ket、源态、白噪声密度矩阵、Born 投影和扫描几何。
- 每个 runner 强制读取显式 target ID 和 `final_reproduction` guard，阻止跨目标写入。
- 把作者 TSV 放在生成后的 reference lane，既获得 100 分证据上限，又保持生成 provenance 干净。
- 科学门通过后再调画布、轴框和图例，避免视觉优化掩盖物理错误。

## What Was Difficult

- Figure 4 横轴 \(\Theta\) 表示中间设置的绝对角，而不是三设置基组的起点。若直接把 \(\Theta\) 当作起点，Wigner 线仍保持常数，但三条概率曲线整体错相 30°。
- 四个源图都是理论线与实验标记的混合图；必须逐序列分类，否则很容易把实验点误当成需要生成的数值。
- 作者参数只保留两位小数，直接重算 fidelity 会与正文值产生最多 0.0053 的小差异。

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| 不变量不能单独证明坐标映射正确 | Figure 4 的 W 不变量掩盖了概率曲线的相位错误 | 每个混合观测量都应检查组成项，而不只检查最终组合量 |
| 横轴语义属于方法合同 | 相同角度数值可指基组起点、中心设置或相对间隔 | 在 method card 中显式写 coordinate-to-state mapping |
| reference lane 应晚于 generation lane | 可防止作者数据被用于隐式拟合或追踪 | runner 记录 `reference_inputs_read=[]`，另设后验 comparison 脚本 |
| 混合图应拆成可见序列账本 | 范围授权通常只覆盖理论或实验的一部分 | figure coverage 对每条可见序列标注 theory/experiment/context |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| 只看 Wigner 曲线 | 错误 Figure 4 映射仍给出正确常数 W | 同时对 \(P_{ab},P_{bc},P_{ac}\) 做相位与 author-data 检查 |
| 用正文 fidelity 反推隐藏参数 | 舍入参数与正文 fidelity 略不一致 | 保持论文公开参数，记录舍入边界，不做未授权再拟合 |
| 全图像素分混合科学与实验差异 | 源图含范围外实验点 | 科学分与像素分分离，源图标记只留在 reference side |
| 精确轴边框但数据坐标仍错位 | Matplotlib 默认留白影响 0°/360° 网格位置 | 像素合同同时记录画布尺寸、轴边框和 plot range |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| 解析极限 + 密度矩阵数值双轨检查 | 有闭式极限且正文图使用非理想态时 | \(-1/8\)、\((1-\sqrt3)/4\) 与四组混态曲线同时通过 |
| 每目标独立 CSV | 同一论文有多个构型扫描时 | 4 个 721×6 数据集均可独立审计 |
| 作者数据只做后验插值比较 | 作者发布原始数据但冻结范围为理论时 | 4 个目标获得 RMSE、相关系数和相位证据，无生成污染 |
| 注册后再生成 comparison board | 原图尺寸和边距可恢复时 | 轴框 IoU 达 0.9908–0.9920 |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `invariant_masks_coordinate_origin_error` | Figure 4 初始角度解释 | 对所有组成概率做至少一个已发布坐标的数值断言 |
| `rounded_fit_parameters_disagree_with_reported_derived_metric` | Figures 4、5 fidelity | 同时记录参数精度、重算值、正文值和容差 |
| `mixed_panel_scope_contamination` | Figures 3–5 | 对每条可见序列声明 scientific role 和生成 provenance |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| 组成量相位检查 | 能发现组合不变量掩盖的坐标错误 | 未来的 scan-method validation helper |
| `reference_inputs_read` runner 字段 | 能直接审计生成与参考的因果隔离 | 通用 target-run contract |
| 舍入参数派生量检查 | 适合所有只报告有限有效数字的拟合论文 | formula/scientific evidence helper |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Decision |
| --- | --- | --- |
| 4×4 密度矩阵逐角投影 | 每个 721 点目标约 0.038 s | 保持 case-local，接口可复用 |
| 矢量 PDF 160 dpi 原尺寸渲染 | 四个像素目标无尺寸误差 | 使用既有 harness helper |

## Harness Backlog Items

本次冻结 campaign 禁止修改 harness，因此上述候选只记录在案例内，没有对共享代码做变更。

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| medium | scan 组成量相位断言模板 | Figure 4 的 30° 原点错误 | recorded_case_local |
| low | 舍入参数派生量容差模板 | fidelity 最大差 0.0053 | recorded_case_local |

## Prompt Or Workflow Changes

- 未来遇到组合观测量不变量时，必须同时验证至少一个组成量的绝对相位。
- 在 author-data 可用时，明确区分“用数据生成/拟合”和“生成后独立验算”。
