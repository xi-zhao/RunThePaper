# 非厄米拓扑能带理论：完整数值复现说明

本文复现 Shen、Zhen 与 Fu 在 2018 年 PRL 发表的 *Topological Band Theory
for Non-Hermitian Hamiltonians*。这里的“复现”不是描图：我们先通读正文与
补充材料，跟随拓扑不变量、广义 Dirac 模型、畴壁匹配、例外点绕数与晶格
圆柱模型的推导，再从公式和独立本征求解器生成数值数据。

## 复现范围

论文中所有可复现的理论数值图都纳入范围，共 6 个目标、15 个数值子图：

- Main Fig. 1：复能谱体带与局域畴壁边缘支；
- Main Fig. 2(a–c)：例外点 Riemann 面、绕圈换支与平方根截线；
- Main Fig. 3(a–b)：相图、例外点轨迹及相反的半整数拓扑荷；
- Supplement Fig. 2：畴壁边缘能量曲面与零能平面；
- Supplement Fig. 3(a–b) 的实部/虚部：$n=40$ 圆柱谱与边缘态；
- Supplement Fig. 4(a–b) 的实部/虚部及两条截线：混合例外点色散。

Supplement Fig. 1 是示意图，Supplement Table I 是背景分类表，因此不冒充
数值复现对象。若子图包含示意或实验成分，本项目只接受由理论公式定义的
数值部分。

## 科学结论

六个目标全部通过。关键数值包括：解析谱与直接对角化误差不超过
$1.03\times10^{-15}$；畴壁共同自旋量残差不超过
$1.43\times10^{-14}$；例外点绕一周后两支交换且绕数绝对值为 $1/2$；
两条例外点轨迹带有 $+1/2$ 与 $-1/2$ 拓扑荷；混合点沿正交方向的拟合指数
分别为 $0.5$ 和 $1.0$；圆柱的最大归一化本征残差为
$1.60\times10^{-15}$，匹配边缘态的最小边界权重为 $0.985$。

科学数值分为 90/100。由于作者未提供原始数值数组，评分上限按规则设为
90，而不是假装达到作者数据逐点等价。初始像素呈现分为 60.28/100；它只
衡量画幅、相机、字体、线密度等下游呈现，不给科学正确性加分。

## 如何运行

在仓库根目录安装依赖后：

```bash
cd cases/1706.07435/code
python -m unittest discover -s tests -v
python scripts/run_main_fig1.py
python scripts/run_main_fig2.py
python scripts/run_main_fig3.py
python scripts/run_supp_fig2.py
python scripts/run_supp_fig3.py
python scripts/run_supp_fig4.py
```

脚本会先写入结构化数据与 JSON 检查，再渲染 PNG。公开包不包含论文 PDF、
独立原图或从原图数字化得到的点集；生成路径也没有任何原图输入。

进一步阅读：[公式推导](../docs/DERIVATION.md)、[数值方法](../docs/NUMERICAL_METHODS.md)、
[科学与像素评分说明](../docs/SIMILARITY_SCORECARD.md)。
