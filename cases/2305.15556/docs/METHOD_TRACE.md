# Method Trace

## NUM001 — 固定 N 对称玻色子表示

- 来源：Main Eq. (9)，Supplement Sec. I。
- 输入：粒子数、模标签、印刷的双线性生成元。
- 方法：枚举和为 N 的占据数组，精确构造 `a_i^dagger a_j` CSR 矩阵。
- 输出：SU(2) 21 维和 SU(4) 1771 维算符/状态空间。
- 检查：15 个 SU(4) 生成元的 trace Gram 矩阵对角且对角元相等。
- 代码：`src/optimal_generators/bosons.py`、`model.py`。

## NUM002 — 精确相位与 Krylov 传播

- OAT：`J_z^2` 对角，直接施加 `exp(-i tau m^2)`。
- SU(4)：`scipy.sparse.linalg.expm_multiply` 一次生成等距时间序列。
- 独立检查：小 N 稠密矩阵指数；随机生成元的保真度有限差分 QFI。
- 代码：`model.py::oat_state`、`evolve_su4`，
  `reproduction.py::_solver_parity`。

## NUM003 — 退化领先空间

- 最大本征值简单时，用符号连续的单位本征矢。
- 最大本征值简并时，保存领先空间投影算符、秩和本征残差；热图代表仅用于展示。
- 原图像素不能决定本征矢规范。
