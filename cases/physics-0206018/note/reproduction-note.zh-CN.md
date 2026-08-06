# 介质微腔共振的边界元方法：独立数值复现说明

本 case 对应 Jan Wiersig 的
[arXiv:physics/0206018](https://arxiv.org/abs/physics/0206018) 和
[Journal of Optics A 5, 53–60 (2003)](https://doi.org/10.1088/1464-4258/5/1/308)。
我们从 Helmholtz Green 函数、边界积分方程、奇异对角元和共振求解公式出发，
独立实现数值计算；没有使用作者代码、作者数组、数字化曲线或原图像素作为
数值输入。

## 复现范围

论文 Figs. 1–4 是几何或方法示意图，因此没有重画。论文中所有数值图均已
覆盖：

- Fig. 5：平面波入射下的总散射截面与共振峰序列；
- Fig. 6：由共振边界零空间态重建的近场强度；
- Fig. 7：由同一个边界态计算的远场辐射方向图。

三个目标通过独立物理检查：线性方程残差低于约 $8\times10^{-15}$，光学
定理中位相对误差约 0.073，共振奇异值随分辨率收敛，近场具有合理的腔内/
腔外对比，远场反演残差低于约 $2\times10^{-9}$。

## 计算边界

论文使用约 1600 个边界元，但没有公布精确的圆角曲线和非均匀单元映射。
本 case 明确采用圆弧倒角与 432 个常数边界元，单次特征计算在参考 CPU 上
约 159 秒。因此它是缩减尺度的科学复现，而不是论文网格的逐点重建。

数值数组冻结后，RenderContract 只调整画幅、坐标轴、字体、灰度、线宽和
插值。它不能修改介质参数、网格、共振位置或场数组。最终前景像素分为
50.49/100（原始可比目标均值 58.16/100），全图 SSIM 为 0.7151。分数较低
主要来自稀疏窄峰对网格偏移的敏感性，而不是通过偷取像素提升分数。

## 如何运行

从 RunThePaper 仓库根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/physics-0206018/code
python scripts/run_all.py
python scripts/render_figures.py
```

公式到代码的映射见 [DERIVATION.md](../docs/DERIVATION.md)，数值方法与证据
边界见 [NUMERICAL_METHODS.md](../docs/NUMERICAL_METHODS.md)，逐图科学检查与
像素审计位于 [`outputs/checks`](../outputs/checks/)。公开包不包含论文 PDF、
原图或原图导出的数据点。
