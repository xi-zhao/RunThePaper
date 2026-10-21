# 这次复现学到了什么

同一物理演化可以相对于不同的合法稳态参考作图。有限周期链存在暗模时，先求稳态方程得到的参考解，与指定初态的无限时间极限可能不同；偏移不代表动力学计算错误。明确参考态以后，三条残余周期曲线与原图坐标精度相容。

比较约定应给出可检验的预测。本例的预测是偏移恒为每胞元 1/(2L)，并随链长变化；独立 SVD、奇偶链与开链控制支持这一解释。图线支持的链长推断和作者确认仍须区分。

The useful lesson is to make the reference observable explicit and test a predicted finite-size offset. Agreement with a permissible reference does not identify the authors' private solver. The principal physical findings remain supported.
