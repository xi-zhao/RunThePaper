# arXiv:2608.03987 独立复现笔记

## 论文与复现对象

- 论文：[arXiv:2608.03987v2](https://arxiv.org/abs/2608.03987)，*Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators*。
- 原始基准输入：[Zenodo 10.5281/zenodo.21791682](https://doi.org/10.5281/zenodo.21791682)，数据许可为 CC-BY-4.0。
- 当前公开包复现论文的 Figure 8 和 Figure 9，共 67 个电路：12 个随机电路、24 个 Clifford+T、10 个 QAOA、21 个 VQE。

## 独立性边界

核心计算是我们从论文公式独立实现的 Python 张量网络模型，不是作者 Rust 代码的重跑、翻译或封装。主优化路径只从公开 ZIP 中读取 122 个原始输入载荷：12 个 qsim 电路、55 个结构化电路 JSON 和 55 个观测量文件。输入审计确认它没有读取作者的 Rust crate、收缩树、优化计划或结果 CSV。

第三方 `cotengra==0.7.5` 只用于生成通用 FLOP 收缩树候选；张量网络降级、实化代价模型、pass/ride/merge 分类、NNI 模拟退火、树哈希和统计均由本公开包实现。作者结果只在独立结果生成完成后用于比较，不反馈给优化器。

## 结果

综合证据评分为 **72/100**，属于数值特征复现，而不是完全数值复现。

- **Figure 8：通过。** 67/67 个电路满足精确关系
  `o = 1 + 2m + r` 及解析区间 `[1+2m, 2+m]`，最大残差为
  `4.44e-16`。与作者结果事后比较时，开销相关系数为 `0.9881`，
  MAE 为 `0.0600`。
- **Figure 9：部分复现。** 论文报告 66/67 个电路低于
  `5e-4` 的迁移差距；独立优化器达到 57/67。阈值分类有 58/67
  一致，差异主要出现在 Clifford+T 和 VQE。最大的真实代价差距为
  `20.35%`。

因此，实化张量网络的精确算术规律得到独立验证；“骨架网络的最优收缩树几乎总能无损迁移到实化网络”这一经验结论，在不同优化器下仍然大体成立，但没有论文报告得那么强。差异被保留，而不是通过放宽阈值隐藏。

## 快速运行

从本案例目录运行：

```bash
# 下载并校验官方数据发布包
python code/scripts/fetch_benchmark_inputs.py

# 只跑 5-qubit 测试电路，验证独立主路径
python code/scripts/run_independent_reimplementation.py \
  --preset smoke --scope random --circuit test
```

完整 67 电路复现：

```bash
python code/scripts/run_independent_reimplementation.py \
  --preset full \
  --output-dir outputs/data/independent_python_full
python code/scripts/run_reproduction.py
```

已有结果见 [Figure 8](../outputs/figures/fig8_cost_law.png)、
[Figure 9](../outputs/figures/fig9_pipeline.png) 和
[机器可读检查](../outputs/checks/numerical_feature_checks.json)。

## 计算与边界

完整配置固定 seed 42、10 个 cotengra 候选、每个目标 600,000 次 NNI
退火和 60,000 次低温 polish。各电路记录的运行时间合计约 29.3 分钟；
此前以三个本地进程并行时墙钟约 14 分钟。

Figure 8/9 计算的是收缩树组合代价，并不执行大型张量收缩，所以 A100
不是当前瓶颈。公开包也没有复现论文在 Ascend 910/A800 上的内核墙钟、精度
和端到端加速表；这些属于另一个 GPU/NPU 执行层目标。
