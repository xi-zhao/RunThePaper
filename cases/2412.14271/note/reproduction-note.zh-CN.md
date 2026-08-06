# 双光子 Dicke 模型耗散相变：独立数值复现说明

本文对应 [arXiv:2412.14271](https://arxiv.org/abs/2412.14271) 与
[Physical Review Letters 135, 173602 (2025)](https://doi.org/10.1103/mz92-6l9g)。
目标不是描摹论文图片，而是从 Hamiltonian、Lindblad 方程和二阶累积量
方程出发，独立生成论文中的数值对象，再把生成图与论文图做后验比较。

## 复现了什么

- Fig. 2：单光子损耗下的解析分支、有限截断量子轨迹与 Fock 分布；
- Fig. 3：双损耗下的有限尺寸分布和热力学极限分支；
- Fig. 4：由独立生成的光子约化密度矩阵计算 Wigner 函数；
- Fig. S1、S2：固定点的 Bogoliubov 稳定性谱；
- Fig. S5：轨迹数量收敛趋势；
- 纯双光子损耗补充图：Liouvillian 零模与宇称守恒。

共 8 组数值目标，其中 7 组具有可运行、可检查的独立数值产物。正式补充
材料的 Figs. S3–S4 因关键参数无法确认而保持 blocked，没有臆造参数补图。
主量子图采用每个任务 6–16 条轨迹，是机制级/特征级复现，不宣称达到论文
的大样本精度。

## 最重要的科学发现

Fig. 3(g) 中下方点划线分支的光子数对应 squeezed-high 固定点。独立计算
发现它没有正的 Bogoliubov 本征值，而是含有零模；沿光子零模展开后，
$\dot r=0.4r^3+O(r^5)$，因此它是非线性不稳定的。也就是说，论文把该线
画成不稳定分支是可以成立的，但“存在正 Bogoliubov 本征值”的证据与已
公开方程不一致。完整证据见
[Fig. 3(g) / Fig. S2 discrepancy](../docs/PAPER_DISCREPANCY.md)。

## 如何运行

从 RunThePaper 仓库根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install qutip
cd cases/2412.14271/code
python scripts/run_analytic.py
python scripts/render_figures.py
```

快速路径重算解析分支和稳定性，并使用随 case 发布的冻结量子数组重新渲染
全部图。完整量子重算命令见 [code/README](../code/README.md)，在参考 CPU
上约需十余分钟，具体时间依机器而变。

## 怎样阅读结果

公式与代码映射见 [DERIVATION.md](../docs/DERIVATION.md)，数值边界见
[NUMERICAL_METHODS.md](../docs/NUMERICAL_METHODS.md)。最终前景像素分为
46.71/100，全画布 SSIM 约 0.768；低分主要来自缩减轨迹数和排版差异，
不能替代科学检查。逐图检查和冻结数据哈希均位于
[`outputs/checks`](../outputs/checks/)。

本公开包不包含论文 PDF、原图、数字化曲线或作者数值数据。论文图像只在
独立数值数组冻结之后用于渲染诊断，绝未作为物理参数或数值数组的来源。
