# Lessons Learned

## Case Summary

- Paper: *Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates*
- PaperID: `10.1103-PRXQuantum.6.010331`
- Final status: `partial_reproduction`; analytic target contracts passed, while exact figure fine structure remains partial
- Main targets: Fig. 15 and Fig. 6(a)
- Main blockers: exact Fig. 15 phase trajectory, raw PSD arrays, full calibrated hardware model

## What Worked

- 先建立公式卡和参数来源链，再写求解器，及时发现“被引协议”不等于“目标图所用精确脉冲”。
- Appendix-L 解析函数与缩放关系形成了很小但有力的核心模型，可覆盖两个图的正式目标。
- 正式数据和 reconstructed 诊断分开存储，避免 provenance 污染。
- Fourier 因子化把直接响应计算降到一次轨迹加频率变换，0.21 秒即可完成最终诊断网格。

## What Was Difficult

- 当前论文只描述 time-optimal sinusoidal protocol，没有给 Fig. 15 专用优化轨迹。
- 被引 Evered 参数确实生成高质量 CZ，因此只检查门保真度会产生“参数已匹配”的假象。
- 必须同时检查门标量、响应曲线特征和来源身份，才能定位为 missing parameters 而非数值错误。

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| 命名相同的协议不能证明目标参数相同 | 优化控制通常存在多个都能实现同一门的轨迹，但 filter response 完全不同 | 为 target-specific waveform 建立独立 parameter-identity gate |
| 成功实现标量目标只是必要条件 | 多条脉冲都能产生 CZ，却有不同噪声谱响应 | 同时检查最敏感的曲线特征或频域 observable |
| 解析拟合可以是正式复现，但 provenance 必须明确 | 它精确复现公开公式，不等于独立恢复隐藏数值轨迹 | 使用 `analytic_reference`，并把独立诊断单列 |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| 把被引文献参数提升为当前图的 paper_exact 参数 | 通用 Evered pulse 的 CZ 指标很好，但响应 NRMSE 最高 0.411 | 要求当前论文明确绑定参数到目标图，否则标记 reconstructed |
| 用更密网格追逐模型不匹配 | 2001 与 4001 网格已在 `5e-7` 内一致 | 先做收敛诊断，再决定是 solver 还是 model/provenance 问题 |
| 把 source fit 当 independent numerics | Appendix L 可直接生成漂亮曲线 | 数据列和 check JSON 必须写 `analytic_reference` |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| trajectory-to-reference gate | 控制波形由优化产生且正文只给协议名时 | 高保真 CZ 与 Fig. 15 响应仍显著不同 |
| dual-lane artifacts | 有可信重构模型但缺目标身份时 | T001/T002 正式，D001 exploratory，报告边界清楚 |
| feature checks before visual review | 参考只有图或解析拟合时 | 第二峰、sanity value、缩放塌缩都可机器验证 |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `protocol_identity_without_trajectory_identity` | EQ002 / D001 | 门标量通过而敏感响应曲线失败，且 target-specific coefficients 无来源 |
| `analytic_reproduction_overclaimed_as_independent` | T001 | 检查 generated-data provenance 是否为 analytic_reference |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| target-specific waveform identity check | 适用于量子控制、最优控制和脉冲整形论文 | future harness parameter gate |
| direct-vs-analytic diagnostic split | 可防止 source formulas 与 independent numerics 混淆 | reproduction report template |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Heisenberg-operator Fourier factorization | 4001 x 1001 x dimension-8 response约 0.21 s | case-local until a second paper validates reuse |

## Harness Feedback

抽象经验已复制到 `PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`；可执行的
target-specific waveform identity gate 已作为 `H065` 复制到
`PRAgent-workflow/HARNESS_BACKLOG.md`（`copied_to_backlog`）。

## Prompt Or Workflow Changes

- 在“公式门通过”之后增加“目标参数身份门”：来源必须明确绑定到目标图或表。
- 当标量门成功但高维 observable 失败时，优先分类为参数/模型身份问题，而不是继续加密网格。
