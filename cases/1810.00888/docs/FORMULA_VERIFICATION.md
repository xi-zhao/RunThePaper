# Formula verification

8 张公式卡全部通过 source_and_symbolic gate。

- EQ001：维数、Hermiticity、零对角和小尺寸全谱一致。
- EQ002：四个 Gamma 态的本征残差均低于 2e-15。
- EQ003：闭式局域分布与直接 MPS 期望最大差 1.84e-15。
- EQ004：Xi1 的能量与方差复现论文打印值。
- EQ005：构造恰好 27 个 FSA 态，并复现负能塔标注序列。
- EQ006：Upsilon1 的能量与方差复现打印值；tilde-Upsilon 的小偏差受打印参数舍入限制。
- EQ007：六个尺寸、五个态族的 Schmidt 概率均归一。
- EQ008：13 维广义本征态均在 Gram 度量下归一。

待独立复核事项 REV001：正文写衰减长度 2 ln(3)，补充材料的精确因子 3^(-b) 按物理格点距离推导出 2/ln(3)。在 fresh-context 审查完成前不判论文错误。
