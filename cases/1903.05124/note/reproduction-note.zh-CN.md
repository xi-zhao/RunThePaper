# 扰乱动力学中的量子纠错：科学数值复现说明

本公开包复现 Choi、Bao、Qi 与 Altman 发表于 Phys. Rev. Lett. **125**,
030505 (2020) 的 *Quantum Error Correction in Scrambling Dynamics and
Measurement-Induced Phase Transition*。这里的“复现”不是描图：我们先跟随
解耦界、Clifford frame potential、稳定子熵和有限尺寸标度的推导，再由独立
Clifford/稳定子模拟与对生成数据的拟合得到全部数值数组。论文像素只在最后
的比较板中用于呈现审计，从不进入数值生成路径。

## 范围与结论

Main Fig. 2(b–e) 与 Supplement Figs. S2–S6 中 44 个可见理论数值子图和
inset 均已覆盖；电路、信道和张量网络示意图不冒充数值复现对象。其中 20
项达到论文尺度：S2 四个 frame-potential 子图采用 `n=22`、22 个深度、每个
深度 50,000 个样本；S3 十六个子图采用 `L=32,m=11`、每组 240 条轨迹。
其余 24 项均有独立公式数值证据，但系统尺寸或统计量缩减，因此明确标为
feature scale，而不是论文精度。

科学审计分为 **78.41/100**。T001、T002、T003、T004 和 T006 均为 80；
T005 为 70，因为临界点位置通过，但在 `L<=24` 下拟合得到的临界指数随深度
变化仍偏大。下游像素呈现分为 **68.30/100**，只用于衡量画幅、线密度、
字体和独立 Monte Carlo 噪声，不给科学正确性加分。

关键结果包括：论文尺度的 `F1,F2,F3` 向 Haar 值靠近；晚深度
`F4=29.00±0.85`，其 95% 下界仍高于 24；强扰乱下测量导致的熵损失在饱和
前受到抑制；Main Fig. 2 与 S5 独立拟合的 `p_c` 相对论文汇总表的平均绝对
误差分别为 `0.00409` 和 `0.00484`。S6 覆盖论文全部六个 block size 并保持
精确 `d/m=3`，同时如实保留 `L<=24` 的有限尺寸边界。

## 运行与检查

在仓库根目录执行：

```bash
python -m unittest discover -s cases/1903.05124/code/tests -v
python cases/1903.05124/code/scripts/run_supp_fig_s2.py --render-only
python cases/1903.05124/code/scripts/run_supp_fig_s3.py --render-only
python cases/1903.05124/code/scripts/run_supp_fig_s4.py \
  --refinement-input cases/1903.05124/outputs/data/supp_fig_s5_refinement_numerical_data.csv
python cases/1903.05124/code/scripts/run_supp_fig_s5.py \
  --refinement-input cases/1903.05124/outputs/data/supp_fig_s5_refinement_numerical_data.csv
```

模拟脚本还提供快速 `--scale smoke`，并在适用处提供 feature/paper 模式。
脚本会先写结构化 CSV/NPZ 数据和 JSON 科学检查，再渲染 PNG。

公开包不包含论文 PDF、独立原图或从原图数字化得到的曲线。进一步阅读：
[公式推导](../docs/DERIVATION.md)、[方法链路](../docs/METHOD_TRACE.md)和
[评分边界](../docs/SIMILARITY_SCORECARD.md)。
