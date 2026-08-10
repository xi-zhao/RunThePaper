# Lessons Learned

## Case Summary

- Paper: *Entanglement transition in a monitored free fermion chain -- from extended criticality to area law*
- PaperID: `2005.09722`
- Final status: `partial`; 31/31 numerical axes physically consistent at reduced scale.
- Main blockers: L=200-800 paper sizes, 5000-trajectory histograms, unpublished seeds/counts/fit windows, and missing fresh-context review.

## What Worked

- 一个 Slater-orbital 核心模型同时支撑 QSD、QSDc、QJ、随机跃迁以及所有熵/互信息/关联观测量，避免为每幅图写局部脚本。
- FFT 均匀跃迁、事件驱动 QJ 和 reduced QR 把全轴 pilot 控制在 4.1 分钟。
- 在数值冻结后才开放原图的比较通道，既能校正画幅/标注，又不会污染科学数据。
- 31 个 target 在执行前全部枚举，示意图单独排除，没有用“次要图”名义静默跳过。

## What Was Difficult

- 论文尺寸跨度到 L=800，且多数轨迹数和所有随机种子未公布，短 session 不适合强行宣称 paper-exact。
- autocorrelation 的远尾单点在有限尺寸和小样本下会反转排序；第一次正式 run 因此被正确拒绝。
- QSD 与 QSDc 共享平均 Lindblad 动力学，却在非线性轨迹观测量上不同，归一化和测量反作用的边界必须在核心模型中明确。

## Generalized Experience

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| 随机衰减曲线不要用远尾单点作唯一验收 | 有限尺寸噪声地板会产生假失败或假通过 | 预声明有限物理时间窗积分，并保留远尾点作为诊断 |
| 全图覆盖和 paper-exact 是两个正交状态 | 可以完整覆盖全部轴但仍然是缩尺度 | coverage 单独计数；parameter_match 决定生命周期上限 |
| GPU 可用不等于 GPU 更快 | 大量中小 QR 和 Python 调度可能更适合 CPU | 先做同 seed 的端到端 backend benchmark |
| stochastic 图不能强做像素配准 | 不同 seed/样本数没有像素级一一对应 | 使用带标签的科学对照板，pixel_status 明确 N/A |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | Prevention |
| --- | --- | --- |
| 用 tau=100 的一个点判断 Zeno 变慢 | v1 中弱监测值 0.00751 略高于强监测 0.00666 | 使用 tau=0..20 积分；v1 失败 attestation 永久保留 |
| 把 BKT 坐标画出来就称为证明普适类 | L<=96 也能画出变换 | 缩尺度只验证公式和形态，临界点/普适性留给 L=200-800 campaign |
| 直方图样本过少却比较细峰 | 当前 192 vs 论文 5000 | 只验均值和结构方向；细分布列为 scale-up |

## New Failure Modes

| Failure mode | Detection | Future action |
| --- | --- | --- |
| `far_tail_single_point_noise_floor` | 单点趋势与固定窗积分趋势相反 | 失败并要求多尺度/多窗口稳定性检查 |
| `complete_axis_coverage_but_reduced_scale` | coverage=100% 但 parameter_match 全为 reduced_scale | 状态保持 partial，禁止以“全覆盖”晋级 complete |

## Reusable Checks Or Tools

| Candidate | Value | Destination |
| --- | --- | --- |
| stochastic decay window-integral sentinel | 比远尾单点更稳健 | case-local now; generalized backlog entry |
| backend benchmark with identical seed/hash | 避免凭硬件型号猜性能 | future scale-up harness helper |

## Efficient Reproduction Implementations

| Implementation | Evidence | Decision |
| --- | --- | --- |
| FFT uniform hopping | dense-expm unit test and 248 s all-axis run | keep case-local until a second paper reuses it |
| event-driven occupied-orbital QJ | covariance identity to 5e-13 | suitable future generic Gaussian-trajectory helper |

## Harness Backlog Items

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| P1 | Add a robust time-series acceptance template requiring window metrics plus tail diagnostics | v1 false far-tail verdict | copied_to_backlog |
| P2 | Add CPU/GPU identical-seed microcampaign benchmark helper | A100 availability does not resolve QR throughput | copied_to_backlog |

## Prompt Or Workflow Changes

- 在随机时间序列 target 的公式卡之后、正式 run 之前，必须明确“积分窗口、尾部诊断、样本量敏感性”三件事。
- 对全覆盖缩尺度 case，报告应同时给出 `31/31 coverage` 和 `31 reduced_scale`，避免用户把覆盖率误读为 paper-exact 完成度。
