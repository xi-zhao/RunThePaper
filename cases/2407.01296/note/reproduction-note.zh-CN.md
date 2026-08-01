# 任意维非厄米趋肤效应：复现说明

## 结论

本案例完成了正式论文主文 Fig. 1–5 的科学复现。Fig. 2(a–c)、Fig. 3 和
Fig. 4(a–f) 由 Python/SciPy 从论文模型重新计算；Fig. 1 与 Fig. 5 是解析示意图
重绘。Fig. 2(d) 是唯一的来源辅助数值面板：它使用作者公开的有限尺寸 ED 表，
但图中观测量由本案例重新计算。当前扩展还从 Eq. (S24)–(S26) 独立计算了
Supplementary Fig. S4，并从 Eq. (S28) 独立计算了 Supplementary Fig. S6。

这不是论文原图的像素副本。所有正式画布都已按出版尺寸注册，但严格阈值
`SSIM >= 0.95` 没有通过。主文科学证据链已闭合。Supplementary Fig. S6 的
绕数和费米点电荷检查全部通过。Supplementary Fig. S4 属于科学部分复现：正文
列出的尺寸和逆尺寸局域化标度已完成，但灰色热力学极限曲线诚实地用独立计算的
有限 `L=160` OBC 代理表示。Supplementary Fig. S2、S5 和 S7 仍待完成。

## 补充材料方程检查

对于 Supplementary Fig. S4，代码直接构造 Eq. (S24) 的双链 OBC 矩阵，完成
图注中的 `L=20,40,60,80` 全部尺寸，并按 Eq. (S25) 拟合中心态的逆局域化长度。
拟合得到 `R²=0.9990`、截距 `-0.00559`，选定本征对残差低于 `3.7e-15`。

对于 Supplementary Fig. S6，代码在独立采样的动量切片上计算 Eq. (S28) 的闭环
相位绕数，并独立求解复 Bloch 哈密顿量的零点。普通模型的绕数集合为 `{0,1}`，
有两个电荷相反的费米点；临界菱形模型的绕数集合为 `{-1,1}`，有四个费米点且
总电荷守恒。

## Fig. 3 的画法

针对早期版本中 Fig. 3(a) 线条和 Fig. 3(b) 视角的问题，当前版本作了三项修正：

- Fig. 3(a) 从规则 `101 x 101` 动量网格投影到两个 beta 平面，不再直接连接
  不规则求解点；
- Fig. 3(b) 对周期动量面做无缝插值，消除边界接缝；
- 三维视角固定为仰角 `24°`、方位角 `-41°`，并统一三轴比例。

科学门禁全部通过，但整图 SSIM 为 `0.6969`，因此状态仍是
`pixel_registered_not_identical`。差异主要来自采样密度、曲面插值、视角投影、
字体和抗锯齿，而不是把独立计算结果说成像素完全一致。

## Fig. 4 的画法

Fig. 4 的六个面板均有独立数值检查。整图 SSIM 为 `0.5823`；各面板分别为
`0.9107`、`0.5717`、`0.7042`、`0.4353`、`0.4181`、`0.4946`。其中较低的
面板受论文未报告的选态序列、整数边界顶点、随机种子、能量探针网格和排版细节
影响。这些不确定性保留在机器检查中，没有通过复制论文像素来隐藏。

## 公开内容与边界

公开包包含独立数值内核、轻量运行脚本、生成数据、生成图、机器检查，以及带明确
出处的有限对照板。它不包含论文 PDF、独立原图、矢量路径、数字化曲线或内部试错
记录。对照板只用于审计视觉结构；数值计算不读取其中的像素。

## 快速运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2407.01296/code
python scripts/run_reproduction_smoke.py
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig6.py
```

smoke runner 运行缩小尺度的 Fig. 2 几何依赖与 Fig. 4(d) 边界比例检查；两个
补充材料 runner 按声明的科学设置复现 S4 与 S6。论文尺度生成结果已随案例发布，
方法和计算边界见
[`../docs/NUMERICAL_METHODS.md`](../docs/NUMERICAL_METHODS.md) 与
[`../docs/SIMILARITY_SCORECARD.md`](../docs/SIMILARITY_SCORECARD.md)。
